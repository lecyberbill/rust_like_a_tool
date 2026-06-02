# [WFGY] Zone: SAFE | λ: 0.1 | Action: Integration test for Polars multi-format (CSV, JSON)
import os
import sys
import json
import asyncio
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator, load_env
from planner import RecipePlanner

# Echantillon de donnees CSV d'utilisateurs
CSV_USERS = """user_id,username,status
1,alice,active
2,bob,inactive
3,charlie,active
4,david,active
"""

# Echantillon de donnees JSON de transactions
JSON_TRANSACTIONS = [
    {"tx_id": 1001, "user_id": 1, "amount": 150.0},
    {"tx_id": 1002, "user_id": 2, "amount": 42.5},
    {"tx_id": 1003, "user_id": 3, "amount": 300.0},
    {"tx_id": 1004, "user_id": 1, "amount": 25.0},
    {"tx_id": 1005, "user_id": 4, "amount": 99.9}
]

async def run_analytical_test():
    print("[TEST] Setting up multi-format analytical files...")
    
    # Nettoyage des anciens fichiers de test
    for f in ["users_input.csv", "tx_input.json", "joined_output.csv", "aggregated_summary.json"]:
        p = Path(f)
        if p.exists():
            p.unlink()

    # Creer les fichiers sources
    with open("users_input.csv", "w", encoding="utf-8") as f:
        f.write(CSV_USERS)

    with open("tx_input.json", "w", encoding="utf-8") as f:
        json.dump(JSON_TRANSACTIONS, f, indent=2)

    config = load_env("dev")
    planner = RecipePlanner(config)
    orchestrator = Orchestrator()

    # Prompt demandant explicitement de combiner CSV et JSON, faire une jointure puis un groupby vers du JSON
    intent = (
        "Joindre le fichier CSV 'users_input.csv' et le fichier JSON 'tx_input.json' "
        "sur la clé 'user_id' vers le fichier CSV temporaire 'joined_output.csv'. "
        "Ensuite, faire un groupby sur 'status' pour calculer la somme des 'amount' "
        "et enregistrer le resultat dans le fichier JSON final 'aggregated_summary.json'."
    )

    print(f"\n[TEST] Sending intent to LLM Planner:\n\"{intent}\"\n")
    recipe = planner.plan(intent)
    
    print("[TEST] Generated recipe structure:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))

    # Save recipe for reference
    with open("test_results/recipe_analytical_test.json", "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)

    print("\n[TEST] Executing recipe...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")

    if success:
        print("\n[TEST SUCCESS] Analytical integration completed successfully!")
        
        # Verifier et afficher les resultats
        joined_path = Path("joined_output.csv")
        summary_path = Path("aggregated_summary.json")

        if joined_path.exists():
            print(f" - {joined_path.name}: Found (Size: {joined_path.stat().st_size} bytes)")
            with open(joined_path, "r", encoding="utf-8") as f:
                print("   Content Sample:\n" + "".join(f.readlines()[:5]))

        if summary_path.exists():
            print(f" - {summary_path.name}: Found (Size: {summary_path.stat().st_size} bytes)")
            with open(summary_path, "r", encoding="utf-8") as f:
                print("   JSON Aggregation Output:")
                print(f.read())
        else:
            print(f" - {summary_path.name}: ERROR (Not Found!)")
    else:
        print("\n[TEST FAILURE] Execution failed.")

if __name__ == "__main__":
    asyncio.run(run_analytical_test())
