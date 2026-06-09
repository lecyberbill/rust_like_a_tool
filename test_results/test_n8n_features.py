# Test n8n ETL Primitives Integration
import os
import subprocess
import csv
import json
import asyncio
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).parent
RUST_BIN = BASE_DIR / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"

# Files
DB_FILE = BASE_DIR / "test_n8n.db"
SOURCE_DATA = BASE_DIR / "test_n8n_src.csv"
SPLIT_SRC = BASE_DIR / "test_split_src.csv"
SPLIT_OUT = BASE_DIR / "test_split_out.csv"
ZIP_SRC = BASE_DIR / "test_zip_src"
ZIP_OUT = BASE_DIR / "test_zip_out.zip"
UNZIP_OUT = BASE_DIR / "test_unzip_out"

def cleanup():
    for f in [DB_FILE, SOURCE_DATA, SPLIT_SRC, SPLIT_OUT, ZIP_OUT]:
        if f.exists():
            f.unlink()
    if ZIP_SRC.exists():
        for f in ZIP_SRC.iterdir():
            f.unlink()
        ZIP_SRC.rmdir()
    if UNZIP_OUT.exists():
        for f in UNZIP_OUT.iterdir():
            f.unlink()
        UNZIP_OUT.rmdir()

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

def test_db_upsert():
    # 1. Initialize SQLite Database and create table
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, role TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'Jean', 'User')")
    cursor.execute("INSERT INTO users VALUES (2, 'Marie', 'Admin')")
    conn.commit()
    conn.close()

    # 2. Write CSV source containing Jean (role updated) and Sophie (inserted)
    with open(SOURCE_DATA, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "role"])
        writer.writerow(["1", "Jean", "SuperUser"]) # Updated
        writer.writerow(["3", "Sophie", "Guest"])    # New

    # 3. Run db.upsert on primary key 'id'
    code, out, err = run_primitive("db.upsert", {
        "connection_string": f"sqlite://{DB_FILE}",
        "table_name": "users",
        "source": str(SOURCE_DATA),
        "keys": "id"
    })
    assert code == 0, f"db.upsert failed: {err}"

    # 4. Verify DB content
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    print("Upsert SQLite rows:", rows)
    assert len(rows) == 3
    assert rows[0] == (1, "Jean", "SuperUser")
    assert rows[1] == (2, "Marie", "Admin")
    assert rows[2] == (3, "Sophie", "Guest")
    print("--- Test db.upsert: SUCCESS ---")

def test_data_split_out():
    # 1. Prepare CSV source containing lists / arrays
    with open(SPLIT_SRC, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "tags"])
        writer.writerow(["1", "rust,polars,etl"])
        writer.writerow(["2", "n8n,switch"])

    # 2. Run data.split_out on tags column
    code, out, err = run_primitive("data.split_out", {
        "source": str(SPLIT_SRC),
        "destination": str(SPLIT_OUT),
        "column": "tags",
        "delimiter": ","
    })
    assert code == 0, f"data.split_out failed: {err}"

    # 3. Verify exploded rows
    with open(SPLIT_OUT, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        print("Exploded tags output:", rows)
        assert len(rows) == 5
        assert rows[0]["tags"] == "rust"
        assert rows[1]["tags"] == "polars"
        assert rows[2]["tags"] == "etl"
        assert rows[3]["tags"] == "n8n"
        assert rows[4]["tags"] == "switch"
    print("--- Test data.split_out: SUCCESS ---")

def test_zip_unzip():
    # 1. Prepare source directory with temporary files
    ZIP_SRC.mkdir(parents=True, exist_ok=True)
    with open(ZIP_SRC / "test1.txt", "w") as f:
        f.write("Hello")
    with open(ZIP_SRC / "test2.txt", "w") as f:
        f.write("World")

    # 2. Zip directory
    code, out, err = run_primitive("data.zip", {
        "source": str(ZIP_SRC),
        "destination": str(ZIP_OUT)
    })
    assert code == 0, f"data.zip failed: {err}"
    assert ZIP_OUT.exists(), "Zip archive was not generated."

    # 3. Unzip archive
    code, out, err = run_primitive("data.unzip", {
        "source": str(ZIP_OUT),
        "destination": str(UNZIP_OUT)
    })
    assert code == 0, f"data.unzip failed: {err}"
    assert (UNZIP_OUT / "test1.txt").exists()
    assert (UNZIP_OUT / "test2.txt").exists()
    print("--- Test data.zip & data.unzip: SUCCESS ---")

async def test_core_switch():
    print("Testing core.switch via python orchestrator module...")
    sys.path.append(str(BASE_DIR / "brain"))
    from orchestrator import Orchestrator

    # Prepare temp files
    switch_res_1 = BASE_DIR / "test_switch_1.txt"
    switch_res_2 = BASE_DIR / "test_switch_2.txt"
    if switch_res_1.exists(): switch_res_1.unlink()
    if switch_res_2.exists(): switch_res_2.unlink()

    # Recipe containing core.switch matching "production" branch
    recipe = {
        "plan_id": "test_switch_plan",
        "intent_analysis": "test core.switch",
        "steps": [
            {
                "step": 1,
                "primitive": "core.switch",
                "args": {
                    "value": "production",
                    "cases": {
                        "staging": [
                            {
                                "step": 10,
                                "primitive": "io.write_file",
                                "args": {
                                    "path": str(switch_res_1),
                                    "content": "Staging branch"
                                }
                            }
                        ],
                        "production": [
                            {
                                "step": 20,
                                "primitive": "io.write_file",
                                "args": {
                                    "path": str(switch_res_2),
                                    "content": "Production branch"
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }

    orch = Orchestrator()
    success = await orch.run_recipe(recipe)
    assert success, "Recipe execution failed"
    assert not switch_res_1.exists(), "Staging branch should not run"
    assert switch_res_2.exists(), "Production branch should have run"
    
    # Cleanup
    if switch_res_2.exists(): switch_res_2.unlink()
    print("--- Test core.switch: SUCCESS ---")

if __name__ == "__main__":
    import sys
    cleanup()
    try:
        test_db_upsert()
        test_data_split_out()
        test_zip_unzip()
        asyncio.run(test_core_switch())
        print("=== ALL N8N PRIMITIVES TESTS PASSED SUCCESSFULLY! ===")
    finally:
        cleanup()
