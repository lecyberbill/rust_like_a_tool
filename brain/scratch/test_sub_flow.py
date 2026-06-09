# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create sub-flow integration test
import asyncio
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from orchestrator import Orchestrator

async def test_sub_flow():
    recipe = {
        "plan_id": "test_nested_workflows",
        "intent_analysis": "Vérification de l'exécution récursive de core.sub_flow",
        "steps": [
            {
                "step": 1,
                "primitive": "core.sub_flow",
                "ui": {
                    "label": "Sous-flux de Nettoyage et Archivage"
                },
                "args": {
                    "steps": [
                        {
                            "step": 11,
                            "primitive": "io.write_file",
                            "ui": { "label": "Création du fichier temporaire" },
                            "args": {
                                "path": "test_results/subflow_temp.txt",
                                "content": "Données écrites par le sous-flux"
                            }
                        },
                        {
                            "step": 12,
                            "primitive": "io.copy",
                            "depends_on": [11],
                            "ui": { "label": "Copie de sauvegarde" },
                            "args": {
                                "source": "test_results/subflow_temp.txt",
                                "destination": "test_results/subflow_temp_bak.txt",
                                "conflict": "overwrite"
                            }
                        }
                    ]
                }
            },
            {
                "step": 2,
                "primitive": "io.delete",
                "depends_on": [1],
                "ui": {
                    "label": "Suppression du fichier d'origine"
                },
                "args": {
                    "path": "test_results/subflow_temp.txt",
                    "secure": "permanent"
                }
            }
        ]
    }

    # Ensure output dir exists
    Path("test_results").mkdir(exist_ok=True)

    orchestrator = Orchestrator()
    print("--- Lancement du test d'intégration des sous-flux ---")
    success = await orchestrator.run_recipe(recipe)
    
    if success:
        bak_file = Path("test_results/subflow_temp_bak.txt")
        orig_file = Path("test_results/subflow_temp.txt")
        if bak_file.exists() and not orig_file.exists():
            print("\n[VERIFICATION] SUCCESS: Le sous-flux s'est exécuté et l'étape principale dépendante s'est enchaînée correctement.")
            # Cleanup
            try:
                bak_file.unlink()
            except Exception:
                pass
        else:
            print("\n[VERIFICATION] FAIL: Fichier de sauvegarde absent ou fichier temporaire non supprimé.")
    else:
        print("\n[VERIFICATION] FAIL: L'orchestrateur a renvoyé un échec d'exécution.")

if __name__ == "__main__":
    asyncio.run(test_sub_flow())
