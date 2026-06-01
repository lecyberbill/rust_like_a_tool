# [WFGY] Zone: SAFE | λ: 0.1 | Action: Stress Test Script for HTTP Request and Regex extraction
import os
import sys
import json
import asyncio
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator, load_env
from planner import RecipePlanner

async def run_stress_test():
    print("[TEST] Setting up temporary test files...")
    extracted_json = Path("extracted_links.json")
    if extracted_json.exists():
        extracted_json.unlink()

    print("[TEST] Initializing Planner and Orchestrator...")
    config = load_env("dev")
    planner = RecipePlanner(config)
    orchestrator = Orchestrator()

    # Formulating a clean prompt using generic HTTP capabilities
    intent = (
        "Envoyer une requête GET à 'https://www.wikipedia.org/', extraire tous les liens d'images "
        "en utilisant la regex '(?i)<img[^>]+src=\"([^\"]+)\"' et sauvegarder les correspondances "
        "dans le fichier JSON 'extracted_links.json'."
    )

    print(f"[TEST] Sending HTTP request intent to LLM Planner:\n\"{intent}\"\n")
    recipe = planner.plan(intent)
    
    print("[TEST] Generated recipe structure received from LLM:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))

    # Save recipe for reference
    with open("test_results/recipe_images_stress_test.json", "w", encoding="utf-8") as f:
        json.dump(recipe, f, indent=2, ensure_ascii=False)

    print("\n[TEST] Launching recipe execution using Orchestrator...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")

    if success:
        print("\n[TEST SUCCESS] Recipe completed successfully!")
        
        # Verify output file existence and content
        if extracted_json.exists():
            with open(extracted_json, "r", encoding="utf-8") as f:
                links = json.load(f)
            print(f"\n[TEST] Verification: Successfully extracted {len(links)} image link(s):")
            for link in links:
                print(f" - {link}")
        else:
            print(f"\n[TEST ERROR] Extracted file '{extracted_json}' was not created!")
    else:
        print("\n[TEST FAILURE] Orchestrator execution failed.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
