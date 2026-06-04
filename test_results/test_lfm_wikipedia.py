# [WFGY] Zone: SAFE | λ: 0.1 | Action: Test raw LFM generation for Wikipedia intent

import urllib.request
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from orchestrator import load_env
from planner import RecipePlanner

def test():
    config = load_env("dev")
    planner = RecipePlanner(config)
    
    intent = (
        "Envoyer une requête GET à 'https://www.wikipedia.org/', extraire tous les liens d'images "
        "en utilisant la regex '(?i)<img[^>]+src=\"([^\"]+)\"' et sauvegarder les correspondances "
        "dans le fichier JSON 'extracted_links.json'."
    )
    
    print("[TEST RAW] Running plan generation directly...")
    recipe = planner.plan(intent)
    print("[TEST RAW] Output recipe:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test()
