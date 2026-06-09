#!/usr/bin/env python3
"""Benchmark: mesure le temps d'exécution des primitives clés sur 100K et 1M lignes."""
import os, sys, json, asyncio, csv, time, datetime
from pathlib import Path
_script_dir = Path(sys.argv[0]).resolve().parent
sys.path.insert(0, str(_script_dir.parent))

from brain.orchestrator import Orchestrator
from brain.worker_bridge import WorkerBridge

DATA_DIR = Path("test_results/bench_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_csv(path: Path, rows: int):
    headers = ["id","name","category","price","quantity","active"]
    cats = ["A","B","C","D","E"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(headers)
        for i in range(1, rows+1):
            w.writerow([i, f"item_{i}", cats[i%5], round(10+i*0.5,2), (i%50)+1, "true" if i%3 else "false"])
    return path

async def bench_orchestrator(label: str, steps: list, rows: int):
    base = str(DATA_DIR)
    recipe = {
        "plan_id": f"bench_{rows}",
        "intent_analysis": f"Benchmark {rows} rows",
        "steps": steps
    }
    for s in steps:
        for k, v in list(s["args"].items()):
            if isinstance(v, str):
                s["args"][k] = v.replace("{BASE}", base).replace("{ROWS}", str(rows))
        if not s["args"].get("destination"):
            s["args"]["destination"] = f"{base}/s{s['step']:02d}.csv"

    orch = Orchestrator()
    t0 = time.perf_counter()
    ok = await orch.run_recipe(recipe, target_env="dev")
    dur = time.perf_counter() - t0
    for s in steps:
        d = s["args"].get("destination", "")
        if d:
            p = Path(d)
            status = f"exists={p.exists()}" + (f" size={p.stat().st_size}" if p.exists() else "")
            print(f"    step {s['step']}: {p.name} {status}")
    print(f"  [{label:>40}] {rows:>8,} rows  {dur:>6.2f}s  {'OK' if ok else 'FAIL'}")
    return dur, ok

async def bench_bridge(primitive: str, args: dict, label: str):
    bridge = WorkerBridge()
    t0 = time.perf_counter()
    code, stdout, stderr = await bridge.execute(primitive, args)
    dur = time.perf_counter() - t0
    print(f"  [{label:>40}]          {dur:>6.3f}s  code={code}")
    return dur, code == 0

async def main():
    print("=" * 70)
    print("  BENCHMARK - Primitives ETL")
    print("=" * 70)

    for rows in [100_000, 1_000_000]:
        print(f"\n--- {rows:,} rows ---")
        csv_path = generate_csv(DATA_DIR / f"data_{rows}.csv", rows)

        await bench_bridge("io.copy", {
            "source": str(csv_path),
            "destination": str(DATA_DIR / f"copy_{rows}.csv"),
        }, f"io.copy ({rows:,})")

        await bench_bridge("io.metadata", {
            "path": str(DATA_DIR / f"data_{rows}.csv"),
        }, f"io.metadata ({rows:,})")

        if rows <= 100_000:
            steps = [
                {"step":1, "primitive":"io.read_file",
                 "args":{"source":"{BASE}/data_{ROWS}.csv","destination":"{BASE}/s01.csv"}},
{"step":2, "primitive":"data.filter",
 "args":{"column_name":"active","operator":"equals","value":"true","has_headers":True},
                 "depends_on":[1]},
                {"step":3, "primitive":"data.groupby",
                 "args":{"groupby_columns":"category","aggregate_column":"price","operation":"mean"},
                 "depends_on":[2]},
            ]
            await bench_orchestrator(f"io.read + filter + groupby", steps, rows)

    if not any(f.name.startswith("FAIL") for f in [Path(".")]):
        pass  # OK

    print(f"\n{'=' * 70}")
    print("  BENCHMARK TERMINE")
    print(f"{'=' * 70}")

    # Cleanup
    import shutil
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(main())
