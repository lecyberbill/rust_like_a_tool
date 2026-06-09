# [WFGY] Zone: TEST | λ: 0.15 | Action: Integration test for data.clean relation join (inner/left/outer) using Polars

import os
import sys
import json
import subprocess
from pathlib import Path

def run_test():
    print("=== RUNNING DATA.CLEAN RELATION JOIN INTEGRATION TEST ===")
    
    # 1. Create source datasets (users and roles)
    users_data = """id,name,role_id
1,Jean,10
2,Marie,20
3,Pierre,99
4,Sophie,10
5,Lucas,30
"""
    roles_data = """role_id,role_name,clearance
10,Admin,High
20,User,Medium
30,Guest,Low
40,SuperAdmin,Max
"""
    
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)
    
    users_file = test_dir / "users.csv"
    roles_file = test_dir / "roles.csv"
    destination_file = test_dir / "joined_users.csv"
    
    with open(users_file, "w", encoding="utf-8") as f:
        f.write(users_data)
    with open(roles_file, "w", encoding="utf-8") as f:
        f.write(roles_data)
        
    print(f"Created users dataset at '{users_file}'")
    print(f"Created roles dataset at '{roles_file}'")
    
    # Locate the built rust_muscle binary
    exe_ext = ".exe" if os.name == "nt" else ""
    binary_path = Path(__file__).parent.parent / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
    
    if not binary_path.exists():
        print(f"Error: Compiled binary not found at '{binary_path}'")
        sys.exit(1)
        
    # Test LEFT JOIN
    print("\n--- Testing LEFT JOIN ---")
    cmd_left = [
        str(binary_path),
        "data.clean",
        "--source", str(users_file),
        "--destination", str(destination_file),
        "--right-source", str(roles_file),
        "--left-on", "role_id",
        "--right-on", "role_id",
        "--how-join", "left",
        "--select-columns", "id,name,role_id,role_name,clearance",
        "--fill-na", "role_name:Unknown,clearance:None"
    ]
    
    print(f"Executing: {' '.join(cmd_left)}")
    result = subprocess.run(cmd_left, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {result.returncode}")
    if result.returncode != 0:
        print(f"Error output:\n{result.stderr}")
        sys.exit(1)
        
    with open(destination_file, "r", encoding="utf-8") as f:
        content = f.read()
        print("Left Join Result:")
        print(content)
        
    lines = content.strip().split("\n")
    headers = lines[0].split(",")
    assert headers == ["id", "name", "role_id", "role_name", "clearance"], f"Headers mismatch: {headers}"
    assert len(lines) == 6, f"Expected 6 lines, got {len(lines)}" # 5 rows + header
    
    # Check Marie (role_id 20 -> User, Medium)
    marie_row = [l for l in lines if "Marie" in l][0].split(",")
    assert marie_row[3] == "User" and marie_row[4] == "Medium", f"Marie join failed: {marie_row}"
    
    # Check Pierre (role_id 99 -> Unknown, None via fill-na)
    pierre_row = [l for l in lines if "Pierre" in l][0].split(",")
    assert pierre_row[3] == "Unknown" and pierre_row[4] == "None", f"Pierre join failed: {pierre_row}"

    # Test INNER JOIN
    print("\n--- Testing INNER JOIN ---")
    cmd_inner = [
        str(binary_path),
        "data.clean",
        "--source", str(users_file),
        "--destination", str(destination_file),
        "--right-source", str(roles_file),
        "--left-on", "role_id",
        "--right-on", "role_id",
        "--how-join", "inner",
        "--select-columns", "id,name,role_name"
    ]
    print(f"Executing: {' '.join(cmd_inner)}")
    result = subprocess.run(cmd_inner, capture_output=True, text=True, encoding="utf-8")
    print(f"Exit code: {result.returncode}")
    if result.returncode != 0:
        print(f"Error output:\n{result.stderr}")
        sys.exit(1)
        
    with open(destination_file, "r", encoding="utf-8") as f:
        content = f.read()
        print("Inner Join Result:")
        print(content)
        
    lines = content.strip().split("\n")
    assert len(lines) == 5, f"Expected 5 lines (4 users + header), got {len(lines)}" # Pierre excluded
    assert not any("Pierre" in l for l in lines), "Pierre should be excluded in inner join"

    print("\nINTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
