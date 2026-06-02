# [WFGY] Zone: SAFE | λ: 0.1 | Action: Control Flow & Split/Merge Integration Test
import os
import sys
import json
import asyncio
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator, load_env
from planner import RecipePlanner

# Echantillon de données d'utilisateurs
CSV_USERS_DATA = """id,username,status
1,alice,active
2,bob,inactive
3,charlie,active
4,david,pending
5,eve,inactive
"""

async def run_control_flow_test():
    print("[TEST] Setting up control flow environment...")
    
    # Nettoyage
    for f in ["users_source.csv", "split_out_active.csv", "split_out_inactive.csv", 
              "split_out_pending.csv", "merged_final.csv"]:
        p = Path(f)
        if p.exists():
            p.unlink()

    # Fichier source principal
    with open("users_source.csv", "w", encoding="utf-8") as f:
        f.write(CSV_USERS_DATA)

    config = load_env("dev")
    planner = RecipePlanner(config)
    orchestrator = Orchestrator()

    # Prompt complexes combinant métadonnées, condition, split et merge de fichiers
    intent = (
        "Lire les métadonnées de 'users_source.csv' avec io.metadata. "
        "Si le fichier existe (${FILE_EXISTS} == true), alors diviser (data.split) le fichier "
        "par rapport à la colonne 'status' avec le préfixe 'split_out'. "
        "Ensuite, fusionner (data.merge) les fichiers créés 'split_out_active.csv' et "
        "'split_out_inactive.csv' vers un unique fichier fusionné 'merged_final.csv'."
    )

    print(f"\n[TEST] Sending intent to LLM Planner:\n\"{intent}\"\n")
    recipe = planner.plan(intent)
    
    print("[TEST] Generated recipe structure:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))

    # Save recipe for reference
    with open("test_results/recipe_control_flow_test.json", "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)

    print("\n[TEST] Executing recipe...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")

    if success:
        print("\n[TEST SUCCESS] Control flow and split/merge test completed successfully!")
        
        # Verifier les sorties
        split_active = Path("split_out_active.csv")
        split_inactive = Path("split_out_inactive.csv")
        merged_file = Path("merged_final.csv")

        if split_active.exists():
            print(f" - {split_active.name}: Found (Size: {split_active.stat().st_size} bytes)")
        if split_inactive.exists():
            print(f" - {split_inactive.name}: Found (Size: {split_inactive.stat().st_size} bytes)")
            
        if merged_file.exists():
            print(f" - {merged_file.name}: Found (Size: {merged_file.stat().st_size} bytes)")
            with open(merged_file, "r", encoding="utf-8") as f:
                print("   Merged Content Sample:\n" + f.read())
        else:
            print(f" - {merged_file.name}: ERROR (Not Found!)")
    else:
        print("\n[TEST FAILURE] Execution failed.")

if __name__ == "__main__":
    asyncio.run(run_control_flow_test())
