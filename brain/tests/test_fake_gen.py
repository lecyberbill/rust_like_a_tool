"""Tests pour data.generate_fake."""
import subprocess
import json
import csv
import io
import sys
from pathlib import Path

BINARY = Path(__file__).parent.parent.parent / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"
OUTPUT = Path(__file__).parent.parent.parent / "workspace" / "output"


def test_fake_gen_csv():
    args = [
        str(BINARY), "data.generate_fake",
        "--columns", "id:id,nom:last_name,email:email,age:integer",
        "--count", "5",
        "--destination", str(OUTPUT / "_test_gen.csv"),
        "--format", "csv"
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, f"stderr: {r.stderr}"
    content = (OUTPUT / "_test_gen.csv").read_text(encoding="utf-8")
    lines = [l for l in content.strip().split("\n") if l.strip()]
    assert len(lines) == 6  # header + 5 rows
    assert "id,nom,email,age" in lines[0]
    # Verify data
    rows = list(csv.DictReader(io.StringIO(content)))
    assert len(rows) == 5
    assert all(r["id"].isdigit() for r in rows)
    assert all(r["age"].isdigit() for r in rows)


def test_fake_gen_json():
    args = [
        str(BINARY), "data.generate_fake",
        "--columns", "nom:last_name,email:email",
        "--count", "3",
        "--destination", str(OUTPUT / "_test_gen.json"),
        "--format", "json"
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, f"stderr: {r.stderr}"
    data = json.loads((OUTPUT / "_test_gen.json").read_text(encoding="utf-8"))
    assert len(data) == 3
    assert all("nom" in d and "email" in d for d in data)


def test_fake_gen_pattern():
    args = [
        str(BINARY), "data.generate_fake",
        "--columns", "code:pattern,email:email",
        "--count", "2",
        "--destination", str(OUTPUT / "_test_gen_pat.csv"),
        "--format", "csv"
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, f"stderr: {r.stderr}"
    content = (OUTPUT / "_test_gen_pat.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(content)))
    assert len(rows) == 2


def test_fake_gen_missing_columns():
    args = [
        str(BINARY), "data.generate_fake",
        "--count", "5",
        "--destination", str(OUTPUT / "_test_gen_err.csv"),
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode != 0
    assert "Missing required argument --columns" in r.stderr
