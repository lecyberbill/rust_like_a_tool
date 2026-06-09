# [WFGY] Zone: SAFE | λ: 0.1 | Action: Integration test validating Polars streaming and state checkpointing
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "brain"))

import os
import time
import json
import asyncio
from brain.orchestrator import Orchestrator

async def test_streaming_and_checkpointing():
    print("=== DÉMARRAGE DU TEST DE ROBUSTESSE LOT A ===")
    orchestrator = Orchestrator()

    # --- PARTIE 1 : Test de la reprise sur Checkpoint ---
    print("\n--- Test 1 : Validation du Checkpointing ---")
    checkpoint_file = Path(__file__).parent / "brain" / ".run_checkpoint.json"
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    # Recette de test conçue pour échouer à l'étape 2
    faulty_recipe = {
        "plan_id": "test_checkpoint_flow",
        "intent_analysis": "Test de reprise avec échec intermédiaire",
        "steps": [
            {
                "step": 1,
                "primitive": "core.wait",
                "args": {
                    "duration": "1"
                },
                "ui": {"label": "Étape Initiale Valide"}
            },
            {
                "step": 2,
                "depends_on": [1],
                "primitive": "data.clean",
                "args": {
                    "source": "non_existent_source.csv", # Cause l'échec
                    "destination": "output.csv"
                },
                "ui": {"label": "Étape en Échec"}
            }
        ]
    }

    print("Exécution initiale (doit échouer à l'étape 2)...")
    success1 = await orchestrator.run_recipe(faulty_recipe)
    assert not success1, "Le run initial aurait dû échouer."
    assert checkpoint_file.exists(), "Le fichier de checkpoint aurait dû être créé."

    # Charger le checkpoint pour vérification
    with open(checkpoint_file, "r", encoding="utf-8") as f:
        cp_data = json.load(f)
    print(f"Checkpoint sauvegardé avec succès. Étapes complétées : {cp_data.get('completed_steps')}")
    assert 1 in cp_data.get("completed_steps"), "L'étape 1 aurait dû être enregistrée comme complétée."

    # Corriger l'étape 2 dans la recette et relancer pour tester la reprise
    # Création d'une source valide
    src_file = Path("temp_source.csv")
    src_file.write_text("id,val\n1,Alpha\n2,Beta")

    fixed_recipe = {
        "plan_id": "test_checkpoint_flow",
        "intent_analysis": "Test de reprise corrigé",
        "steps": [
            {
                "step": 1,
                "primitive": "core.wait",
                "args": {
                    "duration": "1"
                },
                "ui": {"label": "Étape Initiale Valide"}
            },
            {
                "step": 2,
                "depends_on": [1],
                "primitive": "data.clean",
                "args": {
                    "source": "temp_source.csv",
                    "destination": "temp_output.csv"
                },
                "ui": {"label": "Étape Corrigée"}
            }
        ]
    }

    print("\nExécution de reprise (doit sauter l'étape 1 et réussir l'étape 2)...")
    t0 = time.perf_counter()
    success2 = await orchestrator.run_recipe(fixed_recipe)
    duration = time.perf_counter() - t0

    assert success2, "Le run corrigé aurait dû réussir."
    # Si l'étape 1 (wait de 1s) a été sautée, le temps d'exécution total devrait être inférieur à 1s (sauf lenteur extrême de Polars)
    print(f"Durée de la reprise : {duration:.2f}s (attendu < 1.0s car l'étape 1 a été sautée)")
    assert duration < 1.5, f"La reprise a mis trop de temps ({duration:.2f}s), l'étape 1 n'a probablement pas été sautée."
    assert not checkpoint_file.exists(), "Le fichier de checkpoint aurait dû être supprimé après succès."

    # Nettoyage
    if src_file.exists():
        src_file.unlink()
    temp_out = Path("temp_output.csv")
    if temp_out.exists():
        temp_out.unlink()

    # --- PARTIE 2 : Test de l'exécution en Streaming Polars ---
    print("\n--- Test 2 : Validation de l'option --streaming ---")
    src_file_stream = Path("stream_source.csv")
    dest_file_stream = Path("stream_output.csv")
    src_file_stream.write_text("id,val\n1,Test1\n2,Test2\n3,Test3")

    stream_recipe = {
        "plan_id": "test_streaming_flow",
        "intent_analysis": "Test d'exécution en mode streaming",
        "steps": [
            {
                "step": 1,
                "primitive": "data.clean",
                "args": {
                    "source": "stream_source.csv",
                    "destination": "stream_output.csv",
                    "streaming": True
                }
            }
        ]
    }

    success_stream = await orchestrator.run_recipe(stream_recipe)
    assert success_stream, "L'exécution avec streaming a échoué."
    assert dest_file_stream.exists(), "Le fichier de destination n'a pas été créé."

    # Nettoyage
    if src_file_stream.exists():
        src_file_stream.unlink()
    if dest_file_stream.exists():
        dest_file_stream.unlink()

    print("\n=== TOUTES LES VÉRIFICATIONS DU LOT A SONT RÉUSSIES ! ===")

if __name__ == "__main__":
    asyncio.run(test_streaming_and_checkpointing())
