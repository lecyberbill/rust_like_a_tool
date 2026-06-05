# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create data pivot/unpivot integration test

import asyncio
import json
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "brain"))
from orchestrator import Orchestrator

async def test_pivot_unpivot():
    # Setup test directory
    test_dir = Path("test_results")
    test_dir.mkdir(exist_ok=True)

    # 1. Create source file in long format
    source_file = test_dir / "sales_long.csv"
    with open(source_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "month", "revenue"])
        writer.writerow(["2025", "Jan", "100"])
        writer.writerow(["2025", "Feb", "120"])
        writer.writerow(["2026", "Jan", "150"])
        writer.writerow(["2026", "Feb", "180"])

    # Output paths
    pivot_dest = test_dir / "sales_wide.csv"
    unpivot_dest = test_dir / "sales_long_recovered.csv"

    # Recipe specifying pivot then unpivot
    recipe = {
        "plan_id": "test_pivot_unpivot_flow",
        "intent_analysis": "Verification de data.pivot et data.unpivot via Polars",
        "steps": [
            {
                "step": 1,
                "primitive": "data.pivot",
                "ui": {
                    "label": "Pivotement long vers large"
                },
                "args": {
                    "source": str(source_file.resolve()).replace("\\", "/"),
                    "destination": str(pivot_dest.resolve()).replace("\\", "/"),
                    "index": "year",
                    "on": "month",
                    "values": "revenue",
                    "aggregate": "sum"
                }
            },
            {
                "step": 2,
                "primitive": "data.unpivot",
                "depends_on": [1],
                "ui": {
                    "label": "Depivotement (melt) large vers long"
                },
                "args": {
                    "source": str(pivot_dest.resolve()).replace("\\", "/"),
                    "destination": str(unpivot_dest.resolve()).replace("\\", "/"),
                    "index": "year",
                    "on": "Jan,Feb",
                    "variable_name": "month",
                    "value_name": "revenue"
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("--- Lancement du test des primitives data.pivot et data.unpivot ---")
    success = await orchestrator.run_recipe(recipe)

    if not success:
        print("\n[VERIFICATION] FAIL: L'orchestrateur a renvoye un echec d'execution.")
        return

    # Verify pivot_dest.csv content
    if not pivot_dest.exists():
        print("\n[VERIFICATION] FAIL: Le fichier pivote n'existe pas.")
        return

    with open(pivot_dest, mode="r", encoding="utf-8") as f:
        pivot_rows = list(csv.DictReader(f))
        
    print("\n--- Rows after pivot: ---")
    for r in pivot_rows:
        print(r)

    # We expect columns: year, Jan, Feb
    # And row for 2025 Jan=100, Feb=120; 2026 Jan=150, Feb=180
    pivot_correct = True
    for r in pivot_rows:
        yr = r.get("year")
        jan = r.get("Jan")
        feb = r.get("Feb")
        if yr == "2025" and (jan != "100" or feb != "120"):
            pivot_correct = False
        if yr == "2026" and (jan != "150" or feb != "180"):
            pivot_correct = False

    if pivot_correct and len(pivot_rows) == 2:
        print("[VERIFICATION] PASS: data.pivot a correctement pivote le dataset.")
    else:
        print("[VERIFICATION] FAIL: data.pivot a produit des valeurs ou colonnes incorrectes.")

    # Verify unpivot_dest.csv content
    if not unpivot_dest.exists():
        print("[VERIFICATION] FAIL: Le fichier depivote n'existe pas.")
        return

    with open(unpivot_dest, mode="r", encoding="utf-8") as f:
        unpivot_rows = list(csv.DictReader(f))

    print("\n--- Rows after unpivot (recovered): ---")
    for r in unpivot_rows:
        print(r)

    # Total rows should be 4
    if len(unpivot_rows) == 4:
        print("[VERIFICATION] PASS: data.unpivot a correctement restaure le format long.")
    else:
        print(f"[VERIFICATION] FAIL: data.unpivot a echoue. Nb lignes: {len(unpivot_rows)} (attendu 4)")

if __name__ == "__main__":
    asyncio.run(test_pivot_unpivot())
