# [WFGY] Zone: SAFE | λ: 0.1 | Action: Test script validating Wait primitive and Age/Size file filters
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "brain"))

import os
import time
import json
import asyncio
from brain.orchestrator import Orchestrator

async def test_wait_and_filters():
    print("=== DÉMARRAGE DE LA VÉRIFICATION DES NOUVELLES FONCTIONNALITÉS ===")
    orchestrator = Orchestrator()
    
    # 1. Test de core.wait (durées différentes)
    print("\n--- Test 1 : Validation de core.wait ---")
    wait_recipe = {
        "plan_id": "test_wait",
        "intent_analysis": "Test de pause avec format flexible",
        "steps": [
            {
                "step": 1,
                "primitive": "core.wait",
                "args": {
                    "duration": "00:00:03"  # 3 secondes au format HH:MM:SS
                }
            },
            {
                "step": 2,
                "depends_on": [1],
                "primitive": "core.wait",
                "args": {
                    "duration": "2"  # 2 secondes brutes
                }
            }
        ]
    }
    
    t0 = time.perf_counter()
    success = await orchestrator.run_recipe(wait_recipe)
    duration = time.perf_counter() - t0
    print(f"Statut d'exécution : {success} | Durée mesurée : {duration:.2f}s (Attendu: ~5.00s)")
    assert success, "La recette wait a échoué"
    assert 4.8 <= duration <= 6.5, f"La durée mesurée ({duration:.2f}s) est hors tolérance"
    
    # 2. Test de core.loop (filtres de fichiers par âge et taille)
    print("\n--- Test 2 : Validation des filtres locaux dans core.loop ---")
    # Création de fichiers de test locaux
    test_dir = Path("test_sandbox")
    test_dir.mkdir(exist_ok=True)
    
    file_old = test_dir / "old_file.txt"
    file_new_small = test_dir / "new_small.txt"
    file_new_large = test_dir / "new_large.txt"
    
    # Fichier récent et petit
    file_new_small.write_text("Petit fichier de test récent")
    
    # Fichier récent et grand (supérieur à 1 Mo)
    # 1.5 Mo
    with open(file_new_large, "wb") as f:
        f.write(b"0" * (1024 * 1024 * 3 // 2))
        
    # Fichier ancien (on modifie sa date de modification)
    file_old.write_text("Ancien fichier de test")
    past_time = time.time() - (3600 * 48)  # il y a 48h
    os.utime(file_old, (past_time, past_time))
    
    # Recette de test de boucle filtrée
    # Objectif: Parcourir uniquement les fichiers modifiés depuis < 24h et d'une taille < 1.0 Mo (donc seulement new_small.txt)
    loop_recipe = {
        "plan_id": "test_filtered_loop",
        "intent_analysis": "Filtrage de fichiers locaux",
        "steps": [
            {
                "step": 1,
                "primitive": "core.loop",
                "args": {
                    "loop_over": "files",
                    "items_source": "test_sandbox",
                    "pattern": "*.txt",
                    "max_age_hours": "24",
                    "max_size_mb": "1.0",
                    "steps": [
                        {
                            "step": 10,
                            "primitive": "io.metadata",
                            "args": {
                                "path": "${ITER_ITEM}"
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # Capturons les sorties standard via redirection pour compter le nombre d'exécutions
    import io
    from contextlib import redirect_stdout
    f_out = io.StringIO()
    with redirect_stdout(f_out):
        success_loop = await orchestrator.run_recipe(loop_recipe)
    
    output_str = f_out.getvalue()
    print("Sorties du moteur :\n", output_str)
    
    assert success_loop, "La recette loop a échoué"
    # Vérification que seul new_small.txt a été traité
    assert "new_small.txt" in output_str, "Le fichier new_small.txt aurait dû être traité"
    assert "old_file.txt" not in output_str, "Le fichier old_file.txt aurait dû être exclu par le filtre d'âge"
    assert "new_large.txt" not in output_str, "Le fichier new_large.txt aurait dû être exclu par le filtre de taille"
    
    # Nettoyage
    for f in [file_old, file_new_small, file_new_large]:
        if f.exists():
            f.unlink()
    if test_dir.exists():
        test_dir.rmdir()
        
    print("\n=== TOUTES LES VÉRIFICATIONS SONT AU VERT ! ===")

if __name__ == "__main__":
    asyncio.run(test_wait_and_filters())
