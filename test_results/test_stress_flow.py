# [WFGY] Stress test — Chaîne ETL sur 10K lignes (core primitives)
import os, sys, json, asyncio, csv, datetime
from pathlib import Path
_script_dir = Path(sys.argv[0]).resolve().parent
sys.path.insert(0, str(_script_dir.parent))
from brain.orchestrator import Orchestrator, load_env

DATA_DIR = Path("test_results/stress_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def generate_orders_csv(path: Path, rows: int = 10000):
    headers = ["order_id","customer_id","product","category","price","quantity","date","email","status"]
    cats = ["Electronics","Clothing","Food","Books","Sports"]
    prods = {c: [f"{c[:3]}_{i}" for i in range(1,6)] for c in cats}
    statuses = ["pending","shipped","delivered","cancelled","returned"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(headers)
        for i in range(1, rows+1):
            cat = cats[i % len(cats)]
            w.writerow([i, f"C{i%200:04d}", prods[cat][i%5], cat,
                        round(10+(i*0.73)%990,2), (i%8)+1,
                        f"2026-{(i%12)+1:02d}-{(i%28)+1:02d}",
                        f"cust{i%500}@example.com", statuses[i%len(statuses)]])
    print(f"[DATA] {rows} rows -> {path}")

def generate_products_csv(path: Path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["product","supplier","origin","margin_pct"])
        for cat in ["Electronics","Clothing","Food","Books","Sports"]:
            for i in range(1,6):
                w.writerow([f"{cat[:3]}_{i}", f"Sup_{(i*7)%20+1:02d}", "CN" if cat=="Electronics" else "FR", (i*5)%30])
    print(f"[DATA] products lookup -> {path}")

async def run_stress_test():
    print("=" * 65)
    print("  STRESS TEST - Chaine ETL 8 etapes sur 10 000 lignes")
    print("=" * 65)
    t0 = datetime.datetime.now()

    generate_orders_csv(DATA_DIR / "orders.csv", 10000)
    generate_products_csv(DATA_DIR / "products.csv")

    base = str(DATA_DIR)
    recipe = {
        "plan_id": "stress_test_core",
        "intent_analysis": "Test noyau ETL 8 etapes sur 10K lignes",
        "steps": [
            {"step":1, "primitive":"io.read_file",
             "args":{"source":f"{base}/orders.csv","destination":f"{base}/s01.csv"},
             "depends_on":[], "ui":{"label":"1. Lire CSV"}},
            {"step":2, "primitive":"data.filter",
             "args":{"column_name":"status","operator":"not_equals","value":"cancelled","delimiter":",","has_headers":True},
             "depends_on":[1], "ui":{"label":"2. Exclure annules"}},
            {"step":3, "primitive":"data.groupby",
             "args":{"groupby_columns":"category","aggregate_column":"price","operation":"sum"},
             "depends_on":[2], "ui":{"label":"3. CA/categorie"}},
            {"step":4, "primitive":"data.metrics",
             "args":{"column_name":"price","operation":"mean","destination_variable":"AVG_PRICE"},
             "depends_on":[2], "ui":{"label":"4. Prix moyen"}},
            {"step":5, "primitive":"data.type_cast",
             "args":{"casts":"{\"customer_id\":\"string\",\"price\":\"float\",\"quantity\":\"int\"}"},
             "depends_on":[2], "ui":{"label":"5. Typer colonnes"}},
            {"step":6, "primitive":"data.anonymize",
             "args":{"rules":"email:mask_email,customer_id:hash"},
             "depends_on":[5], "ui":{"label":"6. Anonymiser PII"}},
            {"step":7, "primitive":"data.deduplicate",
             "args":{"subset":"customer_id","keep":"first"},
             "depends_on":[6], "ui":{"label":"7. Dedup clients"}},
            {"step":8, "primitive":"data.pivot",
             "args":{"index":"category","on":"product","values":"quantity","aggregate":"sum"},
             "depends_on":[7], "ui":{"label":"8. Pivot qte/cat"}},
        ]
    }

    no_dest_primitives = ("data.metrics",)
    for s in recipe["steps"]:
        if not s["args"].get("destination") and s["primitive"] not in no_dest_primitives:
            s["args"]["destination"] = f"{base}/s{s['step']:02d}.csv"

    with open("test_results/stress_recipe.json","w",encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)
    print(f"[RECIPE] {len(recipe['steps'])} steps -> test_results/stress_recipe.json")

    config = load_env("dev")
    orchestrator = Orchestrator()
    print(f"\n[RUN] Execution...\n")
    success = await orchestrator.run_recipe(recipe, target_env="dev")

    elapsed = (datetime.datetime.now() - t0).total_seconds()
    print(f"\n{'=' * 65}")
    if success:
        print(f"  [SUCCES] {len(recipe['steps'])}/{len(recipe['steps'])} etapes - {elapsed:.1f}s")
        for s in recipe["steps"]:
            d = s["args"].get("destination","")
            if d:
                p = Path(d)
                if p.exists():
                    size = p.stat().st_size
                    print(f"    V {p.name}  ({size:>8,} bytes)")
                else:
                    print(f"    X {d} (introuvable)")
    else:
        print(f"  [ECHEC] apres {elapsed:.1f}s")
    print(f"{'=' * 65}")
    return success

if __name__ == "__main__":
    asyncio.run(run_stress_test())
