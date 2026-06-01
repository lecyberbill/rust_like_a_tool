# [WFGY] Zone: SAFE | λ: 0.1 | Action: Global Integration Testing Script
import os
import sys
import json
import asyncio
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator, load_env
from planner import RecipePlanner

# Mock sample XML file for download simulation
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<catalog name="Global Catalog" created="2026-06-01">
    <item id="1">
        <name>Module Rust</name>
        <type>Engine</type>
        <price>0.00</price>
    </item>
    <item id="2">
        <name>Orchestrator Python</name>
        <type>Brain</type>
        <price>100.00</price>
    </item>
</catalog>
"""

# Mock sample CSV file
SAMPLE_CSV = """id,name,status
101,Alice,active
102,Bob,inactive
103,Charlie,active
104,David,pending
"""

async def run_integration_test():
    print("[TEST] Setting up temporary test files...")
    # Clean up old test runs
    for f in ["users_to_import.csv", "catalog.xml", "catalog_results.json", 
              "backup_users.csv", "users_active.csv", "users_all.json", 
              "test_users_final.csv", "test_downloaded.xml"]:
        p = Path(f)
        if p.exists():
            p.unlink()

    # Create input files
    with open("users_to_import.csv", "w", encoding="utf-8") as f:
        f.write(SAMPLE_CSV)

    # Note: We will use a mock XML local server or direct file download via a public raw link or raw mock server if needed, 
    # but here we'll download a simple raw XML from a stable URL:
    # "https://raw.githubusercontent.com/lexicalpy/lexical/master/tests/test_xml.py" is wrong.
    # Let's use a stable public XML file like a RSS feed or raw XML dataset.
    
    print("[TEST] Initializing Planner and Orchestrator...")
    config = load_env("dev")
    planner = RecipePlanner(config)
    orchestrator = Orchestrator()

    intent = (
        "Télécharger le fichier XML du catalogue depuis 'https://www.w3schools.com/xml/simple.xml' vers 'test_downloaded.xml', "
        "lire ses métadonnées avec io.metadata, puis le convertir en JSON sous le nom 'catalog_results.json'. "
        "En parallèle, prendre le fichier CSV local 'users_to_import.csv', le filtrer avec data.filter pour n'extraire que les lignes "
        "dont la colonne 'status' est égale à 'active' (has_headers=true) vers 'users_active.csv', copier ce fichier filtré vers 'backup_users.csv', "
        "puis le supprimer de manière sécurisée (secure='trash') avec 1 jour de rétention."
    )

    print(f"[TEST] Sending global text intent to LLM Planner:\n\"{intent}\"\n")
    recipe = planner.plan(intent)
    
    print("[TEST] Generated recipe structure received from LLM:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))

    # Save recipe for reference
    with open("recipe_generated_test.json", "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)

    print("\n[TEST] Launching recipe execution using Orchestrator...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")

    if success:
        print("\n[TEST SUCCESS] Recipe completed successfully!")
        
        # Verify output files existence
        print("\n[TEST] Verifying generated output files:")
        # users_active.csv was deleted by step 6, so it shouldn't exist! Let's check backup_users.csv instead.
        for file in ["test_downloaded.xml", "catalog_results.json", "backup_users.csv"]:
            p = Path(file)
            if p.exists():
                print(f" - {file}: Found (Size: {p.stat().st_size} bytes)")
            else:
                print(f" - {file}: ERROR (Not Found!)")
                
        # Verify users_active.csv was successfully trashed
        trash_dir = Path(".trash")
        if trash_dir.exists():
            trash_files = list(trash_dir.glob("*_users_active.csv"))
            if trash_files:
                print(f" - Trash: Found deleted users_active.csv in trash bucket: {trash_files[0].name}")
            else:
                print(" - Trash: Deleted users_active.csv not found in trash folder.")
    else:
        print("\n[TEST FAILURE] Orchestrator execution failed.")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
