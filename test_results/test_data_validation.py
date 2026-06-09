# [WFGY] Zone: TEST | λ: 0.1 | Action: Integration test for data.validate and quarantine DLQ
import os
import sys
import json
import subprocess
from pathlib import Path

def run_test():
    print("=== RUNNING DATA.VALIDATE INTEGRATION TEST ===")
    
    # 1. Create dirty validation test dataset
    dirty_data = """id,name,score,age,email
1,Jean,85.5,20,jean@test.com
2,Marie,-10.0,17,marie@test.com
3,Pierre,45.0,22,pierre_invalid_email
4,Sophie,92.0,18,sophie@test.com
5,Lucas,,16,lucas@test.com
"""
    
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)
    
    source_file = test_dir / "validation_input.csv"
    destination_file = test_dir / "validation_valid.csv"
    quarantine_file = test_dir / "validation_quarantine.csv"
    
    for p in [destination_file, quarantine_file]:
        if p.exists():
            p.unlink()
            
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(dirty_data)
        
    print(f"Created validation source dataset at '{source_file}'")
    
    # Locate the built rust_muscle binary
    exe_ext = ".exe" if os.name == "nt" else ""
    binary_path = Path(__file__).parent.parent / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
    
    if not binary_path.exists():
        print(f"Error: Compiled binary not found at '{binary_path}'")
        sys.exit(1)
        
    # Rules:
    # 1. score must be >= 0
    # 2. email must match simple email regex
    # 3. score must be not null
    rules = [
        {"column": "score", "operator": ">=", "value": 0},
        {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"},
        {"column": "score", "operator": "is_not_null", "value": ""}
    ]
    rules_str = json.dumps(rules)
    
    cmd = [
        str(binary_path),
        "data.validate",
        "--source", str(source_file),
        "--destination", str(destination_file),
        "--quarantine", str(quarantine_file),
        "--rules", rules_str
    ]
    
    print(f"Executing command:\n{' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    print(f"Exit code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")
        
    assert result.returncode == 0, "Command failed"
    
    # Verify outputs
    assert destination_file.exists(), "Valid output file does not exist"
    assert quarantine_file.exists(), "Quarantine output file does not exist"
    
    with open(destination_file, "r", encoding="utf-8") as f:
        valid_lines = f.read().strip().split("\n")
    with open(quarantine_file, "r", encoding="utf-8") as f:
        quarantine_lines = f.read().strip().split("\n")
        
    print(f"Valid Lines ({len(valid_lines)}):")
    for line in valid_lines:
        print(f"  {line}")
        
    print(f"Quarantine Lines ({len(quarantine_lines)}):")
    for line in quarantine_lines:
        print(f"  {line}")
        
    # Expect: Header + 2 valid rows (Jean, Sophie)
    assert len(valid_lines) == 3, f"Expected 3 valid lines (including header), got {len(valid_lines)}"
    # Expect: Header + 3 invalid rows (Marie, Pierre, Lucas)
    assert len(quarantine_lines) == 4, f"Expected 4 quarantine lines (including header), got {len(quarantine_lines)}"
    
    # Assert specific row contents
    assert "Jean" in valid_lines[1]
    assert "Sophie" in valid_lines[2]
    assert "Marie" in quarantine_lines[1] # Negative score
    assert "Pierre" in quarantine_lines[2] # Invalid email
    assert "Lucas" in quarantine_lines[3] # Null score
    
    print("\nINTEGRATION TEST PASSED SUCCESSFULLY!")
    
    # Cleanup files
    for p in [source_file, destination_file, quarantine_file]:
        if p.exists():
            p.unlink()

if __name__ == "__main__":
    run_test()
