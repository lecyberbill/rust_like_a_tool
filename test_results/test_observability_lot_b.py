# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create automated test suite for observability Lot B
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "brain"))

import os
import json
import asyncio
from brain.orchestrator import Orchestrator

async def test_observability_and_lineage():
    print("=== DÉMARRAGE DU TEST D'OBSERVABILITÉ LOT B ===")
    orchestrator = Orchestrator()
    
    # Paths for test files
    src_file = Path("temp_obs_src.csv")
    dest_file = Path("temp_obs_dest.csv")
    final_file = Path("temp_obs_final.csv")
    
    # Clean up files from previous runs
    for f in [src_file, dest_file, final_file]:
        if f.exists():
            f.unlink()
            
    # Create source file
    src_file.write_text("id,val,age\n1,Alice,25\n2,Bob,30\n3,Charlie,35")
    
    # Define a two-step recipe to trace lineage
    recipe = {
        "plan_id": "test_observability_flow",
        "intent_analysis": "Verification of Audit Trail and Data Lineage",
        "steps": [
            {
                "step": 1,
                "primitive": "io.copy",
                "args": {
                    "source": "temp_obs_src.csv",
                    "destination": "temp_obs_dest.csv"
                },
                "ui": {"label": "Etape 1: Copie de fichiers"}
            },
            {
                "step": 2,
                "depends_on": [1],
                "primitive": "data.clean",
                "args": {
                    "source": "temp_obs_dest.csv",
                    "destination": "temp_obs_final.csv"
                },
                "ui": {"label": "Etape 2: Nettoyage et typage"}
            }
        ]
    }
    
    # Run the recipe
    print("Exécution de la recette d'audit/lignage...")
    success = await orchestrator.run_recipe(recipe)
    assert success, "La recette d'observabilité a échoué."
    
    # Verify files were created
    assert dest_file.exists(), "Fichier intermédiaire non créé."
    assert final_file.exists(), "Fichier final non créé."
    
    # Check audit trail file exists
    audit_file = Path(__file__).parent / "brain" / "audit_trail.json"
    assert audit_file.exists(), "Le fichier audit_trail.json n'a pas été créé."
    
    with open(audit_file, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
        
    assert len(audit_data) > 0, "Le journal d'audit est vide."
    
    # Get the latest entry
    latest_run = audit_data[0]
    print(f"Dernier run d'audit récupéré : {latest_run['run_id']}")
    
    # Assertions on audit metadata structure
    assert latest_run["workspace_id"] == "test_observability_flow"
    assert latest_run["status"] == "success"
    assert "timestamp" in latest_run
    assert "username" in latest_run
    assert "hostname" in latest_run
    assert "os_name" in latest_run
    assert latest_run["duration_ms"] > 0, "Durée du run invalide (<= 0)."
    
    # Assertions on step performance logs
    steps = latest_run["steps_executed"]
    assert len(steps) == 2, f"Nombre d'étapes incorrect dans l'audit : {len(steps)}"
    assert steps[0]["step"] == 1
    assert steps[0]["status"] == "success"
    assert steps[1]["step"] == 2
    assert steps[1]["status"] == "success"
    
    # Assertions on data lineage map
    lineage = latest_run["data_lineage"]
    assert lineage is not None, "Lignage de données manquant dans l'audit."
    
    # Normalize paths for comparison (orchestrator normalizes to forward slashes / lowercase)
    norm_src = str(src_file).replace("\\", "/").lower()
    norm_dest = str(dest_file).replace("\\", "/").lower()
    norm_final = str(final_file).replace("\\", "/").lower()
    
    print("Normalized paths traced in lineage:")
    for path, info in lineage.items():
        print(f"  - {path}: Producer={info['producer']}, Consumers={info['consumers']}")
        
    assert norm_src in lineage, f"Source '{norm_src}' manquante dans le lignage."
    assert norm_dest in lineage, f"Dest intermédiaire '{norm_dest}' manquante dans le lignage."
    assert norm_final in lineage, f"Final '{norm_final}' manquante dans le lignage."
    
    # Verify producers & consumers relationships
    assert lineage[norm_src]["producer"] is None
    assert 1 in lineage[norm_src]["consumers"]
    
    assert lineage[norm_dest]["producer"] == 1
    assert 2 in lineage[norm_dest]["consumers"]
    
    assert lineage[norm_final]["producer"] == 2
    assert lineage[norm_final]["consumers"] == []
    
    # Clean up test files
    for f in [src_file, dest_file, final_file]:
        if f.exists():
            f.unlink()
            
    print("\n=== LE TEST D'OBSERVABILITÉ ET DE LIGNAGE LOT B EST RÉUSSI AVEC SUCCÈS ! ===")

if __name__ == "__main__":
    asyncio.run(test_observability_and_lineage())
