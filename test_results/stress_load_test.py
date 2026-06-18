"""Test de charge — exécute N recettes en parallèle pour valider la robustesse."""
import sys, os, json, time, subprocess, threading, statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "brain"))
os.environ["SECRET_VAULT_KEY"] = "wfgy_core_secret_key_12345"

RECIPE = {
    "plan_id": "stress_load_test",
    "steps": [
        {"step": 1, "primitive": "data.generate_fake",
         "args": {"columns": "id:id,name:full_name,email:email,age:integer", "count": 100, "format": "csv"}},
        {"step": 2, "primitive": "data.filter", "depends_on": [1],
         "args": {"column_name": "age", "operator": "greater_than", "value": "18", "has_headers": "true"}},
    ]
}

RESULTS = []
LOCK = threading.Lock()

def run_one(recipe, idx):
    from orchestrator import Orchestrator
    o = Orchestrator()
    start = time.perf_counter()
    try:
        ok = asyncio_run(o.run_recipe(recipe))
        dur = int((time.perf_counter() - start) * 1000)
    except Exception as e:
        ok, dur = False, 0
    with LOCK:
        RESULTS.append({"ok": ok, "dur_ms": dur, "idx": idx})

def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"[LOAD TEST] Lancement de {count} recettes en parallele...")
    threads = [threading.Thread(target=run_one, args=(RECIPE, i)) for i in range(count)]
    start = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    total = int((time.perf_counter() - start) * 1000)
    ok_count = sum(1 for r in RESULTS if r["ok"])
    durs = [r["dur_ms"] for r in RESULTS if r["ok"]]
    print(f"\n=== RESULTATS ===")
    print(f"Total: {count} recettes en {total}ms")
    print(f"Succes: {ok_count}/{count}")
    print(f"Temps moyen: {statistics.mean(durs):.0f}ms" if durs else "N/A")
    print(f"Temps min/max: {min(durs):.0f}/{max(durs):.0f}ms" if durs else "N/A")
    print(f"Debit: {ok_count/(total/1000):.1f} recettes/seconde" if total > 0 else "N/A")
    return 0 if ok_count == count else 1

if __name__ == "__main__":
    sys.exit(main())
