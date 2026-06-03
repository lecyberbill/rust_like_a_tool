# [WFGY] Zone: SAFE | λ: 0.1 | Action: Integration test for metrics and chunk_cumulative primitives
import os
import sys
import json
import asyncio
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator

# Test data sets
CSV_INVOICES = """id,amount
1,150.0
2,120.0
3,50.0
4,200.0
"""

CSV_EMAILS = """id,email
1,valid@example.com
2,invalid-email
3,another.valid@domain.org
4,bad@@email
"""

async def run_metrics_test():
    print("[TEST] Setting up complex metrics test files...")
    
    # Setup directories
    Path("test_results").mkdir(exist_ok=True)
    
    # Cleanup previous output files
    for f in Path("test_results").glob("chunk_out_part_*"):
        try:
            f.unlink()
        except OSError:
            pass
            
    # Write inputs
    invoices_file = "test_results/invoices_input.csv"
    emails_file = "test_results/emails_input.csv"
    
    with open(invoices_file, "w", encoding="utf-8") as f:
        f.write(CSV_INVOICES)
        
    with open(emails_file, "w", encoding="utf-8") as f:
        f.write(CSV_EMAILS)

    # Build the recipe statically to avoid flaky LLM calls in execution tests
    recipe = {
        "plan_id": "test_metrics_complex_flow",
        "intent_analysis": "Calcul de metriques, condition logique et cumulative chunking",
        "steps": [
            {
                "step": 1,
                "primitive": "data.metrics",
                "args": {
                    "source": invoices_file,
                    "column_name": "amount",
                    "operation": "sum",
                    "limit_rows": 3,
                    "destination_variable": "SUM_AMOUNT"
                }
            },
            {
                "step": 2,
                "primitive": "core.condition",
                "depends_on": [1],
                "args": {
                    "expression": "${SUM_AMOUNT} > 200",
                    "then_steps": [
                        {
                            "step": 21,
                            "primitive": "data.chunk_cumulative",
                            "args": {
                                "source": invoices_file,
                                "destination_prefix": "test_results/chunk_out",
                                "accumulate_column": "amount",
                                "threshold": 130.0
                            }
                        }
                    ]
                }
            },
            {
                "step": 3,
                "primitive": "data.metrics",
                "args": {
                    "source": emails_file,
                    "column_name": "email",
                    "operation": "non_match_regex",
                    "regex_pattern": ".*@.*",
                    "destination_variable": "INVALID_EMAILS_COUNT"
                }
            },
            {
                "step": 4,
                "primitive": "core.condition",
                "depends_on": [3],
                "args": {
                    "expression": "${INVALID_EMAILS_COUNT} == 1",
                    "then_steps": [
                        {
                            "step": 41,
                            "primitive": "io.copy",
                            "args": {
                                "source": invoices_file,
                                "destination": "test_results/invoices_backup.csv",
                                "mode": "text"
                            }
                        }
                    ]
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("\n[TEST] Running the metrics recipe...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")
    
    if not success:
        print("[TEST FAILURE] Orchestrator execution failed.")
        sys.exit(1)

    print("\n[TEST] Verifying outputs...")
    
    # 1. Verify SUM_AMOUNT in context
    sum_val = orchestrator.execution_context.get("SUM_AMOUNT")
    print(f"Propagated SUM_AMOUNT: {sum_val} (Expected: 320.0)")
    assert float(sum_val) == 320.0, f"Expected 320.0, got {sum_val}"

    # 2. Verify INVALID_EMAILS_COUNT in context
    invalid_count = orchestrator.execution_context.get("INVALID_EMAILS_COUNT")
    print(f"Propagated INVALID_EMAILS_COUNT: {invalid_count} (Expected: 1)")
    assert int(invalid_count) == 1, f"Expected 1, got {invalid_count}"

    # 3. Verify chunk files
    chunk_files = sorted(list(Path("test_results").glob("chunk_out_part_*")))
    print(f"Found chunk files: {[f.name for f in chunk_files]}")
    # Threshold is 130.0.
    # Row 1: 150.0 >= 130.0 -> chunk 1: row 1.
    # Row 2: 120.0. Row 3: 50.0. 120+50 = 170 >= 130.0 -> chunk 2: rows 2 & 3.
    # Row 4: 200.0 >= 130.0 -> chunk 3: row 4.
    # Total chunk files expected: 3
    assert len(chunk_files) == 3, f"Expected 3 chunk files, got {len(chunk_files)}"

    # Check content of chunk 1
    with open(chunk_files[0], "r", encoding="utf-8") as f:
        chunk1_lines = f.readlines()
    print(f"Chunk 1 lines: {chunk1_lines}")
    
    # 4. Verify invoices_backup.csv
    backup_file = Path("test_results/invoices_backup.csv")
    assert backup_file.exists(), "Backup file not found!"
    print(f"Backup file exists: {backup_file.name}")

    print("\n[VERIFICATION_GATE] SUCCESS: All invariants and verification checks passed.")

if __name__ == "__main__":
    asyncio.run(run_metrics_test())
