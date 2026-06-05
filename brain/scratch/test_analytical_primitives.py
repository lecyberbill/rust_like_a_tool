# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create analytical primitives integration test

import asyncio
import json
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from orchestrator import Orchestrator

async def test_analytical_primitives():
    # Setup test directory
    test_dir = Path("test_results")
    test_dir.mkdir(exist_ok=True)

    # 1. Create source file with duplicates and country codes
    source_file = test_dir / "source_with_dups.csv"
    with open(source_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "country_code", "salary"])
        writer.writerow(["1", "Alice", "FR", "5000"])
        writer.writerow(["2", "Bob", "US", "6000"])
        writer.writerow(["1", "Alice", "FR", "5000"])  # exact duplicate of Alice
        writer.writerow(["3", "Charlie", "FR", "5500"])
        writer.writerow(["4", "David", "DE", "4500"])

    # 2. Create dictionary/lookup file
    lookup_file = test_dir / "dict_countries.csv"
    with open(lookup_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "country_name"])
        writer.writerow(["FR", "France"])
        writer.writerow(["US", "Etats-Unis"])
        writer.writerow(["DE", "Allemagne"])

    # Output paths for recipe steps
    lookup_dest = test_dir / "after_lookup.csv"
    dedup_dest = test_dir / "after_dedup.csv"

    # Recipe specifying lookup then deduplication
    recipe = {
        "plan_id": "test_analytical_primitives_flow",
        "intent_analysis": "Verification de data.lookup et data.deduplicate via Polars",
        "steps": [
            {
                "step": 1,
                "primitive": "data.lookup",
                "ui": {
                    "label": "Jointure referentiel pays"
                },
                "args": {
                    "source": str(source_file.resolve()).replace("\\", "/"),
                    "lookup_file": str(lookup_file.resolve()).replace("\\", "/"),
                    "source_key": "country_code",
                    "lookup_key": "code",
                    "lookup_value": "country_name",
                    "destination": str(lookup_dest.resolve()).replace("\\", "/")
                }
            },
            {
                "step": 2,
                "primitive": "data.deduplicate",
                "depends_on": [1],
                "ui": {
                    "label": "Suppression des doublons sur ID"
                },
                "args": {
                    "source": str(lookup_dest.resolve()).replace("\\", "/"),
                    "subset": "id",
                    "keep": "first",
                    "destination": str(dedup_dest.resolve()).replace("\\", "/")
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("--- Lancement du test des nouvelles primitives analytiques ---")
    success = await orchestrator.run_recipe(recipe)

    if not success:
        print("\n[VERIFICATION] FAIL: L'orchestrateur a renvoye un echec d'execution.")
        return

    # Verify after_lookup.csv content
    if not lookup_dest.exists():
        print("\n[VERIFICATION] FAIL: Le fichier après lookup n'existe pas.")
        return

    with open(lookup_dest, mode="r", encoding="utf-8") as f:
        lookup_rows = list(csv.DictReader(f))
        
    print("\n--- Rows after lookup: ---")
    for r in lookup_rows:
        print(r)

    # We expect country_name to be filled correctly
    expected_countries = {
        "FR": "France",
        "US": "Etats-Unis",
        "DE": "Allemagne"
    }
    
    lookup_correct = True
    for r in lookup_rows:
        cc = r.get("country_code")
        cname = r.get("country_name")
        if expected_countries.get(cc) != cname:
            print(f"[VERIFICATION] FAIL: Pour code '{cc}', attendu '{expected_countries.get(cc)}' mais obtenu '{cname}'")
            lookup_correct = False

    if lookup_correct:
        print("[VERIFICATION] PASS: data.lookup a correctement associe le referentiel pays.")
    else:
        print("[VERIFICATION] FAIL: data.lookup a des valeurs incorrectes.")

    # Verify after_dedup.csv content
    if not dedup_dest.exists():
        print("[VERIFICATION] FAIL: Le fichier après deduplicate n'existe pas.")
        return

    with open(dedup_dest, mode="r", encoding="utf-8") as f:
        dedup_rows = list(csv.DictReader(f))

    print("\n--- Rows after deduplication: ---")
    for r in dedup_rows:
        print(r)

    # Total rows should be 4 (David, Charlie, Bob, Alice - Alice row 1 and 3 are duplicates, one should be removed)
    unique_ids = [r["id"] for r in dedup_rows]
    if len(dedup_rows) == 4 and len(set(unique_ids)) == 4:
        print("[VERIFICATION] PASS: data.deduplicate a correctement elimine le doublon.")
    else:
        print(f"[VERIFICATION] FAIL: data.deduplicate a echoue. Nb lignes: {len(dedup_rows)} (attendu 4), IDs uniques: {len(set(unique_ids))}")

if __name__ == "__main__":
    asyncio.run(test_analytical_primitives())
