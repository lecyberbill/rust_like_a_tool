# [WFGY] Zone: TEST | λ: 0.1 | Action: Integration test for data.clean and expression compiler

import os
import sys
import json
import subprocess
from pathlib import Path

# Add brain directory to python path for env helper
sys.path.append(str(Path(__file__).parent.parent / "brain"))
from orchestrator import load_env

def run_test():
    print("=== RUNNING DATA.CLEAN INTEGRATION TEST ===")
    
    # 1. Create dirty test dataset
    dirty_data = """id,name,score,age,city
1,Jean,85.5,20,Paris
2,Marie,,17,Lyon
3,Pierre,45.0,22,Marseille
1,Jean,85.5,20,Paris
4,Sophie,92.0,,Lille
5,Lucas,30.0,16,
"""
    
    test_dir = Path(__file__).parent
    test_dir.mkdir(exist_ok=True)
    
    source_file = test_dir / "dirty_users.csv"
    destination_file = test_dir / "clean_users.csv"
    
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(dirty_data)
        
    print(f"Created dirty source dataset at '{source_file}'")
    
    # Locate the built rust_muscle binary
    exe_ext = ".exe" if os.name == "nt" else ""
    binary_path = Path(__file__).parent.parent / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
    
    if not binary_path.exists():
        print(f"Error: Compiled binary not found at '{binary_path}'")
        sys.exit(1)
        
    # 2. Run data.clean with all parameters
    # Tasks:
    # - Select columns: id, name, score, age
    # - Rename: name:nom_complet, score:note
    # - Fill NA: note:0.0, age:18
    # - Deduplicate: true on id
    # - Derive columns:
    #   * mention = IF note >= 50 THEN 'Pass' ELSE 'Fail'
    #   * score_percent = note * 10
    # - Sort by: note descending
    
    cmd = [
        str(binary_path),
        "data.clean",
        "--source", str(source_file),
        "--destination", str(destination_file),
        "--select-columns", "id,name,score,age",
        "--rename-columns", "name:nom_complet,score:note",
        "--fill-na", "note:0.0,age:18",
        "--deduplicate", "true",
        "--deduplicate-on", "id",
        "--derive-columns", "mention = IF note >= 50 THEN 'Pass' ELSE 'Fail',score_percent = note * 10",
        "--sort-by", "note",
        "--sort-descending", "true"
    ]
    
    print(f"Executing command:\n{' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    print(f"Exit code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")
        
    # 3. Verify output dataset
    if result.returncode == 0 and destination_file.exists():
        print("Output file successfully generated. Reading content:")
        with open(destination_file, "r", encoding="utf-8") as f:
            content = f.read()
            print(content)
            
        # Parse and assert content assertions
        lines = content.strip().split("\n")
        headers = lines[0].split(",")
        print(f"Headers resolved: {headers}")
        
        # We expect: id, nom_complet, note, age, mention, score_percent
        expected_headers = ["id", "nom_complet", "note", "age", "mention", "score_percent"]
        assert headers == expected_headers, f"Header mismatch: expected {expected_headers}, got {headers}"
        
        # Verify deduplication: 5 rows expected (excluding duplicate Jean id 1, and header makes 6 lines)
        assert len(lines) == 6, f"Deduplication failed: expected 6 lines, got {len(lines)}"
        
        # Verify sort order: note (score) descending (Sophie 92.0 first, then Jean 85.5, then Pierre 45.0, then Lucas 30.0, then Marie 0.0)
        row1 = lines[1].split(",") # Sophie
        row2 = lines[2].split(",") # Jean
        row5 = lines[5].split(",") # Marie
        
        assert row1[1] == "Sophie" and row1[2] == "92.0" and row1[4] == "Pass" and row1[5] == "920.0", "Sophie validation failed"
        assert row2[1] == "Jean" and row2[2] == "85.5" and row2[4] == "Pass" and row2[5] == "855.0", "Jean validation failed"
        assert row5[1] == "Marie" and row5[5] == "0.0" and row5[4] == "Fail", "Marie validation failed" # Null score filled to 0.0, mention Fail
        
        print("\nINTEGRATION TEST PASSED SUCCESSFULLY!")
    else:
        print("\nINTEGRATION TEST FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
