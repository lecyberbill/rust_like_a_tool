# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create loop iteration integration test
import asyncio
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from orchestrator import Orchestrator

async def test_loops():
    # Scenario: Loop over country codes to simulate translating/mapping values
    recipe = {
        "plan_id": "test_country_mapping_loop",
        "intent_analysis": "Parcours d'une liste de pays et écriture de fichiers de configuration individuels",
        "steps": [
            {
                "step": 1,
                "primitive": "core.loop",
                "ui": {
                    "label": "Boucle sur les Codes Pays"
                },
                "args": {
                    "loop_over": "variables",
                    "items_source": "FR,US,CA,JP",
                    "steps": [
                        {
                            "step": 11,
                            "primitive": "io.write_file",
                            "ui": { "label": "Création config pays" },
                            "args": {
                                "path": "test_results/config_${ITER_ITEM}.json",
                                "content": "{\"country\": \"${ITER_ITEM}\", \"active\": true}"
                            }
                        }
                    ]
                }
            }
        ]
    }

    # Ensure output dir exists
    Path("test_results").mkdir(exist_ok=True)

    orchestrator = Orchestrator()
    print("--- Lancement du test d'intégration des boucles (core.loop) ---")
    success = await orchestrator.run_recipe(recipe)
    
    if success:
        # Verify that all 4 files were created
        countries = ["FR", "US", "CA", "JP"]
        all_exist = True
        for c in countries:
            file_path = Path(f"test_results/config_{c}.json")
            if not file_path.exists():
                all_exist = False
                print(f"[VERIFICATION] Fichier manquant : {file_path}")
            else:
                # Cleanup
                try:
                    file_path.unlink()
                except Exception:
                    pass
        
        if all_exist:
            print("\n[VERIFICATION] SUCCESS: La boucle d'itération core.loop a traité tous les éléments et résolu le placeholder ${ITER_ITEM} avec succès.")
        else:
            print("\n[VERIFICATION] FAIL: Certaines itérations n'ont pas produit le fichier attendu.")
    else:
        print("\n[VERIFICATION] FAIL: L'orchestrateur a renvoyé un échec d'exécution.")

if __name__ == "__main__":
    asyncio.run(test_loops())
