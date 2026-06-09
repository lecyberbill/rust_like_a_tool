# [WFGY] Zone: TEST | λ: 0.1 | Action: Real MongoDB integration test
import os
import sys
import subprocess
import json
import time

def run_rust_muscle(args):
    exe_ext = ".exe" if os.name == "nt" else ""
    bin_path = os.path.join("rust_muscle", "target", "debug", f"rust_muscle{exe_ext}")
    cmd = [bin_path] + args
    print(f"[TEST] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Stdout:\n{res.stdout}")
    print(f"Stderr:\n{res.stderr}")
    return res.returncode

def main():
    mongo_uri = os.environ.get("SECRET_MONGO_URI")
    if not mongo_uri:
        print("Error: SECRET_MONGO_URI environment variable not found in system environment.", file=sys.stderr)
        sys.exit(1)

    print("[TEST] SECRET_MONGO_URI is set. Starting real MongoDB integration test...")

    db_name = "test_db"
    coll_name = "test_integration"
    local_src = "test_results/real_mongo_src.json"
    local_dest = "test_results/real_mongo_dest.json"

    # Clean up files
    for p in [local_src, local_dest]:
        if os.path.exists(p):
            os.remove(p)

    # 1. Create a dummy dataset
    data_to_insert = [
        {"name": "Real MongoDB User", "role": "tester", "timestamp": time.time()}
    ]
    with open(local_src, "w", encoding="utf-8") as f:
        json.dump(data_to_insert, f)

    try:
        # 2. Run mongodb.insert using rust_muscle
        print("\n--- Testing mongodb.insert with real DB ---")
        insert_args = [
            "mongodb.insert",
            "--connection-string", mongo_uri,
            "--database", db_name,
            "--collection", coll_name,
            "--source", local_src,
            "--mode", "replace"
        ]
        rc = run_rust_muscle(insert_args)
        assert rc == 0, f"mongodb.insert failed with code {rc}"
        print("[SUCCESS] Insert primitive execution completed.")

        # 3. Run mongodb.find using rust_muscle
        print("\n--- Testing mongodb.find with real DB ---")
        find_args = [
            "mongodb.find",
            "--connection-string", mongo_uri,
            "--database", db_name,
            "--collection", coll_name,
            "--destination", local_dest,
            "--filter", '{"role": "tester"}'
        ]
        rc = run_rust_muscle(find_args)
        assert rc == 0, f"mongodb.find failed with code {rc}"
        print("[SUCCESS] Find primitive execution completed.")

        # 4. Verify downloaded data
        assert os.path.exists(local_dest), "Destination file not created"
        with open(local_dest, "r", encoding="utf-8") as f:
            downloaded = json.load(f)
        
        print(f"\nDownloaded documents:\n{json.dumps(downloaded, indent=2)}")
        assert len(downloaded) > 0, "No documents downloaded"
        assert downloaded[0]["name"] == "Real MongoDB User", "Incorrect data found"

        print("\n[VERIFICATION_GATE]")
        print("- Invariant 30 [MongoDB Integration]: SUCCESS")

    finally:
        # Clean up files
        for p in [local_src, local_dest]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    main()
