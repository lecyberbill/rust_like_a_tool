# [WFGY] Zone: SAFE | λ: 0.3 | Action: Run PostgreSQL 100k+ lines E2E stress test (Scenario A)

import os
import sys
import json
import time
import asyncio
from pathlib import Path

# Add brain directory to python path
sys.path.append(str(Path(__file__).parent.parent / "brain"))

from orchestrator import load_env, Orchestrator
from schema_validator import SchemaValidator

DEFAULT_PG_URL = os.environ.get("DATABASE_URL", "postgresql://user_dev:user_dev@localhost:5432/postgres")

BASE_DIR = Path(__file__).parent / "stress_data"
TX_SRC = BASE_DIR / "transactions.csv"
CLIENTS_SRC = BASE_DIR / "clients.csv"
CLEANED_OUT = BASE_DIR / "transactions_cleaned.csv"
FILTERED_OUT = BASE_DIR / "transactions_filtered.csv"
ANONYMIZED_OUT = BASE_DIR / "transactions_anonymized.csv"
QUERY_OUT = BASE_DIR / "query_verification.json"

async def main():
    print("=================================================================")
    print("=== STARTING STRESS TEST SCENARIO A (100,000+ ROWS) ===")
    print("=================================================================\n")

    if not TX_SRC.exists() or not CLIENTS_SRC.exists():
        print(f"[ERROR] Source files missing. Run: node test_results/generate_stress_data.js first.")
        sys.exit(1)

    print(f"Source Files Found:")
    print(f"  - Transactions: {TX_SRC} ({TX_SRC.stat().st_size:,} bytes)")
    print(f"  - Clients: {CLIENTS_SRC} ({CLIENTS_SRC.stat().st_size:,} bytes)\n")

    env_config = load_env("dev")
    # Make sure we use the right database URL
    os.environ["SECRET_POSTGRES_CONNECTION_STRING"] = DEFAULT_PG_URL
    os.environ["POSTGRES_CONNECTION_STRING"] = DEFAULT_PG_URL
    os.environ["DATABASE_URL"] = DEFAULT_PG_URL

    recipe = {
        "plan_id": "postgres_stress_scenario_a",
        "intent_analysis": "Join transactions with clients, filter, anonymize and insert to PostgreSQL",
        "steps": [
            {
                "step": 1,
                "primitive": "data.clean",
                "depends_on": [],
                "ui": {
                    "label": "Join & Clean",
                    "color": "#10B981"
                },
                "args": {
                    "source": str(TX_SRC),
                    "destination": str(CLEANED_OUT),
                    "right_source": str(CLIENTS_SRC),
                    "left_on": "client_id",
                    "right_on": "client_id",
                    "how_join": "left",
                    "select_columns": "transaction_id,client_id,amount,status,date,name,email,country,client_tier",
                    "fill_na": "name:Unknown,email:Unknown,country:Unknown",
                    "derive_columns": "client_tier=IF amount >= 1000.0 THEN 'VIP' ELSE 'Standard'"
                }
            },
            {
                "step": 2,
                "primitive": "data.filter",
                "depends_on": [1],
                "ui": {
                    "label": "Filter Transactions > 10",
                    "color": "#3B82F6"
                },
                "args": {
                    "source": str(CLEANED_OUT),
                    "destination": str(FILTERED_OUT),
                    "column_name": "amount",
                    "operator": "greater_than",
                    "value": "10.0",
                    "has_headers": True
                }
            },
            {
                "step": 3,
                "primitive": "data.anonymize",
                "depends_on": [2],
                "ui": {
                    "label": "Mask Emails & Hash IDs",
                    "color": "#8B5CF6"
                },
                "args": {
                    "source": str(FILTERED_OUT),
                    "destination": str(ANONYMIZED_OUT),
                    "rules": "email:mask_email,client_id:hash"
                }
            },
            {
                "step": 4,
                "primitive": "db.insert",
                "depends_on": [3],
                "ui": {
                    "label": "Postgres Insert",
                    "color": "#EF4444"
                },
                "args": {
                    "connection_string": "${SECRET_POSTGRES_CONNECTION_STRING}",
                    "table_name": "clean_transactions",
                    "source": str(ANONYMIZED_OUT),
                    "mode": "replace",
                    "schema_drift": True
                }
            }
        ]
    }

    # Validate schema using registry
    print("[PHASE 1] Validating Recipe Schema...")
    validator = SchemaValidator(Path(__file__).parent.parent / "brain" / "registry.json")
    validation_errors = []
    for s in recipe["steps"]:
        ok, msg = validator.validate_step(s["primitive"], s["args"])
        if not ok:
            validation_errors.append(f"Step {s['step']} ({s['primitive']}): {msg}")

    if validation_errors:
        print("[FATAL] Recipe validation failed:")
        for err in validation_errors:
            print(f"  - {err}")
        sys.exit(1)
    print("[PHASE 1] Recipe validated successfully against schema registry.\n")

    # Run recipe
    print("[PHASE 2] Executing ETL recipe on Orchestrator...")
    orch = Orchestrator()
    t0 = time.perf_counter()
    success = await orch.run_recipe(recipe, target_env="dev")
    t1 = time.perf_counter()
    elapsed = t1 - t0

    if not success:
        print("\n[FATAL] ETL Execution Failed.")
        sys.exit(1)

    print(f"\n[PHASE 2] Recipe executed successfully in {elapsed:.3f} seconds.")

    # Verification phase
    print("\n[PHASE 3] Running PostgreSQL database verification...")
    verify_recipe = {
        "plan_id": "postgres_verify",
        "intent_analysis": "Query PostgreSQL and verify row counts and PII masking",
        "steps": [
            {
                "step": 1,
                "primitive": "db.query",
                "depends_on": [],
                "args": {
                    "connection_string": "${SECRET_POSTGRES_CONNECTION_STRING}",
                    "query": "SELECT count(*) as total_count, count(case when email like '%*%' then 1 end) as masked_count, min(amount) as min_amount FROM clean_transactions",
                    "destination": str(QUERY_OUT)
                }
            }
        ]
    }

    verify_success = await orch.run_recipe(verify_recipe, target_env="dev")
    if not verify_success or not QUERY_OUT.exists():
        print("[FATAL] Verification query failed.")
        sys.exit(1)

    with open(QUERY_OUT, "r", encoding="utf-8") as f:
        res = json.load(f)
        row = res[0] if isinstance(res, list) and len(res) > 0 else res
        print("\n=== VERIFICATION RESULTS FROM POSTGRESQL ===")
        print(f"  - Total rows inserted: {row.get('total_count'):,}")
        print(f"  - Number of properly masked emails: {row.get('masked_count'):,}")
        print(f"  - Minimum transaction amount in database: ${float(row.get('min_amount', 0)):.2f}")
        
        # Verify correctness
        total = int(row.get('total_count', 0))
        masked = int(row.get('masked_count', 0))
        min_amt = float(row.get('min_amount', 0))

        assert total > 80000, f"Expected more than 80,000 transactions (after filtering small amounts), got {total}"
        assert total == masked, f"Expected all emails to be masked, got {masked}/{total}"
        assert min_amt > 10.0, f"Expected all amounts > 10.0, got ${min_amt:.2f}"

    print("\n=================================================================")
    print("=== E2E POSTGRES STRESS TEST COMPLETED SUCCESSFULLY! ALL GREEN ===")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(main())
