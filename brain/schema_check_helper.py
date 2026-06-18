"""data.schema_check — vérifie la conformité d'un dataset face à un schéma attendu."""
import sys
import json
import csv

def check_schema(source, expected_schema_json):
    with open(source, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        actual_cols = list(reader.fieldnames) if reader.fieldnames else []
    try:
        expected = json.loads(expected_schema_json)
    except json.JSONDecodeError:
        expected = [c.strip() for c in expected_schema_json.split(",")]
    missing = [c for c in expected if c not in actual_cols]
    extra = [c for c in actual_cols if c not in expected]
    return {"ok": len(missing) == 0, "actual": actual_cols, "expected": expected, "missing": missing, "extra": extra}

def main():
    if len(sys.argv) < 4:
        print("Usage: python schema_check_helper.py <source> <expected_schema> <destination>", file=sys.stderr)
        sys.exit(1)
    source, expected_json, destination = sys.argv[1], sys.argv[2], sys.argv[3]
    result = check_schema(source, expected_json)
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    if result["ok"]:
        print(f"SUCCESS: Schema OK ({len(result['actual'])} columns)")
    else:
        print(f"SCHEMA_DRIFT: Missing={result['missing']} Extra={result['extra']}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
