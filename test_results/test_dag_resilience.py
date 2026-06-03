# [WFGY] Zone: SAFE | λ: 0.1 | Action: Integration test for Parallel DAG and retry mechanism
import os
import sys
import json
import asyncio
import time
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator

# Setup initial source files
SRC_CONTENT = "Hello from DAG parallel test"

async def run_dag_test():
    print("[TEST DAG] Initialisation des fichiers de test...")
    Path("test_results").mkdir(exist_ok=True)
    
    # Nettoyage des anciens fichiers
    for f in ["parallel_1.txt", "parallel_2.txt", "joined_parallel.txt", "dynamic_trigger.txt", "retry_success.txt"]:
        p = Path("test_results") / f
        if p.exists():
            p.unlink()

    # Fichier source initial
    src_file = "test_results/dag_source.txt"
    with open(src_file, "w", encoding="utf-8") as f:
        f.write(SRC_CONTENT)

    # Définition de la recette avec parallélisme et retries
    recipe = {
        "plan_id": "test_dag_parallel_and_resilience",
        "intent_analysis": "Test de parallélisme DAG (étapes 1 & 2) et retry asynchrone (étape 4 résolue par étape 5)",
        "steps": [
            {
                "step": 1,
                "primitive": "io.copy",
                "args": {
                    "source": src_file,
                    "destination": "test_results/parallel_1.txt",
                    "mode": "text"
                }
            },
            {
                "step": 2,
                "primitive": "io.copy",
                "args": {
                    "source": src_file,
                    "destination": "test_results/parallel_2.txt",
                    "mode": "text"
                }
            },
            {
                "step": 3,
                "primitive": "io.copy",
                "depends_on": [1, 2],
                "args": {
                    "source": "test_results/parallel_1.txt",
                    "destination": "test_results/joined_parallel.txt",
                    "mode": "text"
                }
            },
            {
                "step": 4,
                "primitive": "io.copy",
                "retry": {
                    "attempts": 4,
                    "delay_seconds": 2.0
                },
                "args": {
                    "source": "test_results/dynamic_trigger.txt",
                    "destination": "test_results/retry_success.txt",
                    "mode": "text"
                }
            },
            {
                "step": 5,
                "primitive": "io.copy",
                "depends_on": [3],
                "args": {
                    "source": src_file,
                    "destination": "test_results/dynamic_trigger.txt",
                    "mode": "text"
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("\n[TEST DAG] Lancement de la recette DAG parallèle...")
    start_time = time.time()
    success = await orchestrator.run_recipe(recipe, target_env="dev")
    duration = time.time() - start_time
    
    print(f"\n[TEST DAG] Exécution terminée en {duration:.2f} secondes.")
    
    if not success:
        print("[TEST DAG FAILURE] L'orchestrateur a échoué.")
        sys.exit(1)

    # Vérifications des résultats
    print("\n[TEST DAG] Vérification des assertions...")
    
    p1 = Path("test_results/parallel_1.txt")
    p2 = Path("test_results/parallel_2.txt")
    joined = Path("test_results/joined_parallel.txt")
    trigger = Path("test_results/dynamic_trigger.txt")
    success_file = Path("test_results/retry_success.txt")

    assert p1.exists(), "Le fichier parallèle 1 est manquant"
    assert p2.exists(), "Le fichier parallèle 2 est manquant"
    assert joined.exists(), "Le fichier joint est manquant"
    assert trigger.exists(), "Le fichier trigger est manquant"
    assert success_file.exists(), "Le fichier de réussite du retry est manquant"

    print(" -> Tous les fichiers cibles existent.")
    print(" -> Le retry de l'étape 4 a fonctionné après la création dynamique du fichier par l'étape 5.")
    print("\n[VERIFICATION_GATE] SUCCESS: Le test de parallélisme DAG et résilience a réussi !")

if __name__ == "__main__":
    asyncio.run(run_dag_test())
