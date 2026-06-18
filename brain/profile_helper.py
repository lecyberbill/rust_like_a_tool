"""data.profile — profiling de dataset (statistiques, nulls, distribution)."""
import sys
import json
import csv

def profile_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        return {"error": "Empty file", "columns": {}}
    cols = list(rows[0].keys())
    result = {"total_rows": len(rows), "columns": {}}
    for col in cols:
        vals = [r[col] for r in rows]
        num_vals = []
        for v in vals:
            try:
                num_vals.append(float(v))
            except (ValueError, TypeError):
                pass
        nulls = sum(1 for v in vals if not v or v.strip() == "")
        uniques = len(set(vals))
        stats = {"type": "numeric" if num_vals else "text", "nulls": nulls, "null_pct": round(nulls / len(vals) * 100, 1), "uniques": uniques, "samples": list(dict.fromkeys(vals))[:5]}
        if num_vals:
            stats.update({"min": min(num_vals), "max": max(num_vals), "mean": round(sum(num_vals) / len(num_vals), 2), "std": round((sum((x - sum(num_vals)/len(num_vals))**2 for x in num_vals) / len(num_vals))**0.5, 2)})
        result["columns"][col] = stats
    return result

def main():
    if len(sys.argv) < 3:
        print("Usage: python profile_helper.py <source> <destination>", file=sys.stderr)
        sys.exit(1)
    source, destination = sys.argv[1], sys.argv[2]
    result = profile_csv(source)
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"SUCCESS: Profiled {result.get('total_rows', 0)} rows -> {destination}")

if __name__ == "__main__":
    main()
