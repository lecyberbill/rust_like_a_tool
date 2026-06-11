# [WFGY] Zone: SAFE | λ: 0.15 | Action: Integration test for data.generate_fake primitive
import os
import sys
import json
import csv
import subprocess
from pathlib import Path

def run_test():
    print("=================================================================")
    print("=== TESTING DATA.GENERATE_FAKE PRIMITIVE ===")
    print("=================================================================\n")

    base_dir = Path(__file__).parent.parent
    binary_path = base_dir / "rust_muscle" / "target" / "debug" / ("rust_muscle.exe" if os.name == "nt" else "rust_muscle")

    if not binary_path.exists():
        print(f"[FATAL] Compiled binary not found at '{binary_path}'")
        sys.exit(1)

    dest_csv = Path(__file__).parent / "stress_data" / "test_fake_out.csv"
    dest_json = Path(__file__).parent / "stress_data" / "test_fake_out.json"

    # Cleanup
    for f in (dest_csv, dest_json):
        if f.exists():
            f.unlink()

    # Define columns to generate
    columns = "client_id:id,name:fullName,email:email,country:country,age:integer,pattern_val:pattern"
    
    # 1. Test CSV generation
    print("[TEST 1] Running data.generate_fake for CSV (50 rows)...")
    cmd_csv = [
        str(binary_path),
        "data.generate_fake",
        "--columns", columns,
        "--count", "50",
        "--destination", str(dest_csv),
        "--format", "csv",
        "--generator-path", "D:/Projet/fake_GEN"
    ]
    
    print(f"Executing: {' '.join(cmd_csv)}")
    res = subprocess.run(cmd_csv, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {res.returncode}")
    if res.returncode != 0:
        print(f"[FATAL] CSV Generation failed: {res.stderr}")
        sys.exit(1)

    assert dest_csv.exists(), "CSV Output file not created"
    
    # Validate CSV contents
    with open(dest_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"  - Generated {len(rows)} rows.")
        assert len(rows) == 50, f"Expected 50 rows, got {len(rows)}"
        
        # Check headers
        expected_headers = ["client_id", "name", "email", "country", "age", "pattern_val"]
        assert list(rows[0].keys()) == expected_headers, f"Headers mismatch: {list(rows[0].keys())}"
        
        # Check types & content
        for idx, row in enumerate(rows):
            assert row["client_id"] == str(1 + idx), f"ID mismatch: expected {1+idx}, got {row['client_id']}"
            assert "@" in row["email"], f"Invalid email format: {row['email']}"
            assert row["country"] != "", "Country shouldn't be empty"
            assert int(row["age"]) >= 0, f"Age should be integer: {row['age']}"

    print("[TEST 1] CSV validation PASSED.\n")

    # 2. Test JSON generation
    print("[TEST 2] Running data.generate_fake for JSON (30 rows)...")
    cmd_json = [
        str(binary_path),
        "data.generate_fake",
        "--columns", columns,
        "--count", "30",
        "--destination", str(dest_json),
        "--format", "json",
        "--generator-path", "D:/Projet/fake_GEN"
    ]

    print(f"Executing: {' '.join(cmd_json)}")
    res = subprocess.run(cmd_json, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {res.returncode}")
    if res.returncode != 0:
        print(f"[FATAL] JSON Generation failed: {res.stderr}")
        sys.exit(1)

    assert dest_json.exists(), "JSON Output file not created"

    # Validate JSON contents
    with open(dest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"  - Generated {len(data)} JSON records.")
        assert len(data) == 30, f"Expected 30 records, got {len(data)}"
        
        for idx, row in enumerate(data):
            assert row["client_id"] == str(1 + idx), f"ID mismatch: expected {1+idx}, got {row['client_id']}"
            assert "@" in row["email"], f"Invalid email format: {row['email']}"
            assert int(row["age"]) >= 0, f"Age should be integer: {row['age']}"

    print("[TEST 2] JSON validation PASSED.\n")
    print("=================================================================")
    print("=== ALL GENERATION TESTS PASSED SUCCESSFULLY! ===")
    print("=================================================================")

if __name__ == "__main__":
    run_test()
