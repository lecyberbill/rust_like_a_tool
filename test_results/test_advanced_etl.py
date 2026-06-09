import os
import subprocess
import csv
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
RUST_BIN = BASE_DIR / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"

TARGET_CSV = BASE_DIR / "test_target.csv"
SOURCE_CSV = BASE_DIR / "test_source.csv"

UPSERT_OUT = BASE_DIR / "test_upserts.csv"
DELETE_OUT = BASE_DIR / "test_deletes.csv"
SYNC_OUT = BASE_DIR / "test_synced.csv"

CAST_SRC = BASE_DIR / "test_cast_src.csv"
CAST_OUT = BASE_DIR / "test_cast_out.csv"

def cleanup():
    for f in [TARGET_CSV, SOURCE_CSV, UPSERT_OUT, DELETE_OUT, SYNC_OUT, CAST_SRC, CAST_OUT]:
        if f.exists():
            f.unlink()

def run_primitive(primitive, args_dict):
    cmd = [str(RUST_BIN), primitive]
    for k, v in args_dict.items():
        kebab_key = k.replace("_", "-")
        cmd.extend([f"--{kebab_key}", str(v)])
    
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing {primitive}: {res.stderr}")
    return res.returncode, res.stdout, res.stderr

def test_delta():
    # 1. Prepare target (historical) data
    with open(TARGET_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "age", "last_updated"])
        writer.writerow(["1", "Jean", "20", "2026-06-01"])
        writer.writerow(["2", "Marie", "25", "2026-06-01"])
        writer.writerow(["3", "Pierre", "30", "2026-06-01"])

    # 2. Prepare source (new stream) data
    with open(SOURCE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "age", "last_updated"])
        writer.writerow(["1", "Jean", "21", "2026-06-07"]) # Updated
        writer.writerow(["2", "Marie", "25", "2026-06-01"]) # Unchanged
        writer.writerow(["4", "Sophie", "28", "2026-06-07"]) # Inserted
        # ID 3 is missing, which means it was deleted

    # 3. Run data.delta primitive
    code, out, err = run_primitive("data.delta", {
        "source": str(SOURCE_CSV),
        "target": str(TARGET_CSV),
        "keys": "id",
        "destination_upsert": str(UPSERT_OUT),
        "destination_delete": str(DELETE_OUT),
        "destination_sync": str(SYNC_OUT)
    })
    
    assert code == 0, f"data.delta failed: {err}"

    # 4. Verify outputs
    # Upserts should contain Jean (age 21), Marie, Sophie
    with open(UPSERT_OUT, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        print("Upserts:", rows)
        assert len(rows) == 3
        ids = {r["id"] for r in rows}
        assert "1" in ids and "2" in ids and "4" in ids
        jean = next(r for r in rows if r["id"] == "1")
        assert jean["age"] == "21"

    # Deletes should contain Pierre (id 3)
    with open(DELETE_OUT, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        print("Deletes:", rows)
        assert len(rows) == 1
        assert rows[0]["id"] == "3"

    # Synced should contain 1 (Jean 21), 2 (Marie 25), 4 (Sophie 28) and 3 (Pierre)
    with open(SYNC_OUT, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        print("Synced:", rows)
        assert len(rows) == 4
        ids = {r["id"] for r in rows}
        assert "1" in ids and "2" in ids and "4" in ids and "3" in ids

    print("--- Test delta: SUCCESS ---")

def test_type_cast():
    # 1. Prepare source data with string representation of diverse types
    with open(CAST_SRC, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "price", "active", "date"])
        writer.writerow(["1", "10.5", "true", "2026-06-07"])
        writer.writerow(["2", "24.0", "false", "2026-06-08"])

    # 2. Run data.type_cast
    casts = {
        "id": "int",
        "price": "float",
        "active": "bool",
        "date": "date:%Y-%m-%d"
    }
    
    code, out, err = run_primitive("data.type_cast", {
        "source": str(CAST_SRC),
        "destination": str(CAST_OUT),
        "casts": json.dumps(casts)
    })
    
    assert code == 0, f"data.type_cast failed: {err}"

    # 3. Verify output values
    with open(CAST_OUT, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        print("Typed Output:", rows)
        assert len(rows) == 2
        assert rows[0]["price"] == "10.5"
        assert rows[1]["active"] == "false"
        assert rows[0]["date"] == "2026-06-07"

    print("--- Test type_cast: SUCCESS ---")

if __name__ == "__main__":
    cleanup()
    try:
        test_delta()
        test_type_cast()
        print("=== ALL TESTS PASSED SUCCESSFULLY! ===")
    finally:
        cleanup()
