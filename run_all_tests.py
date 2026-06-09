#!/usr/bin/env python3
"""Run all tests: Rust (cargo test) + Python (pytest) + Stress test."""
import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FAILED = 0

def run(cmd, cwd=None, label="?"):
    global FAILED
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    r = subprocess.run(cmd, cwd=cwd or ROOT, shell=os.name == "nt")
    if r.returncode != 0:
        FAILED += 1
        print(f"  [FAILED] exit={r.returncode}")
    else:
        print(f"  [OK]")

# 1. Rust unit tests
run(["cargo", "test"], cwd=ROOT / "rust_muscle", label="Rust unit tests")

# 2. Rust release build (optional)
run(["cargo", "build", "--release"], cwd=ROOT / "rust_muscle", label="Rust release build")

# 3. Python integration tests
venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = ROOT / ".venv" / "bin" / "python"
run([str(venv_python), "-m", "pytest", "brain/tests/", "-v"], label="Python integration tests")

# 4. Stress test
run([str(venv_python), "test_results/test_stress_flow.py"], label="Stress test")

print(f"\n{'='*60}")
if FAILED == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {FAILED} suite(s) FAILED")
print(f"{'='*60}")
sys.exit(FAILED)
