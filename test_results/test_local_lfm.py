# [WFGY] Zone: SAFE | λ: 0.1 | Action: Local LLM server detection and test integration script

import urllib.request
import json
import os
import sys
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).parent.parent))

def probe_endpoint(url):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status == 200, json.loads(response.read().decode("utf-8"))
    except Exception:
        return False, None

def update_env_file(provider, base_url, model):
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"[TEST LFM] .env file not found at {env_path}")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith("LLM_PROVIDER="):
            new_lines.append(f"LLM_PROVIDER={provider}\n")
        elif line.startswith("LLM_BASE_URL="):
            new_lines.append(f"LLM_BASE_URL={base_url}\n")
        elif line.startswith("LLM_MODEL="):
            new_lines.append(f"LLM_MODEL={model}\n")
        else:
            new_lines.append(line)

    # If LLM_BASE_URL wasn't in .env, append it
    has_base_url = any(line.startswith("LLM_BASE_URL=") for line in lines)
    if not has_base_url:
        new_lines.append(f"LLM_BASE_URL={base_url}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"[TEST LFM] Configured {env_path.name} with provider={provider}, base_url={base_url}, model={model}")

def main():
    print("[TEST LFM] Probing local LLM endpoints...")
    
    # Check LM Studio
    lm_url = "http://localhost:1234/v1/models"
    is_lm, lm_data = probe_endpoint(lm_url)
    
    # Check Ollama
    ollama_url = "http://localhost:11434/v1/models"
    is_ollama, ollama_data = probe_endpoint(ollama_url)

    target_url = None
    target_model = None
    
    if is_lm:
        print("[TEST LFM] Detected LM Studio running on http://localhost:1234/v1")
        target_url = "http://localhost:1234/v1"
        if lm_data and "data" in lm_data and len(lm_data["data"]) > 0:
            target_model = lm_data["data"][0]["id"]
            print(f"[TEST LFM] Loaded model in LM Studio: '{target_model}'")
    elif is_ollama:
        print("[TEST LFM] Detected Ollama running on http://localhost:11434/v1")
        target_url = "http://localhost:11434/v1"
        if ollama_data and "data" in ollama_data and len(ollama_data["data"]) > 0:
            # Let's find one that looks like lfm
            models = [m["id"] for m in ollama_data["data"]]
            print(f"[TEST LFM] Available Ollama models: {models}")
            lfm_models = [m for m in models if "lfm" in m.lower() or "liquid" in m.lower()]
            if lfm_models:
                target_model = lfm_models[0]
            else:
                target_model = models[0]
            print(f"[TEST LFM] Selected model in Ollama: '{target_model}'")
    else:
        print("[TEST LFM] ERROR: No local LLM server detected on port 1234 or 11434.")
        sys.exit(1)

    if not target_model:
        target_model = "liquid-lfm" # Fallback guess

    # Set temporary env configuration to test planning
    test_config = {
        "LLM_PROVIDER": "openai_compatible",
        "LLM_BASE_URL": target_url,
        "LLM_MODEL": target_model,
        "LLM_API_KEY": "unused"
    }

    # Test the RecipePlanner
    from planner import RecipePlanner
    planner = RecipePlanner(test_config)
    
    intent = "Copier le fichier source.txt vers destination.txt en mode texte."
    print(f"\n[TEST LFM] Testing planning with model '{target_model}'...")
    try:
        recipe = planner.plan(intent)
        print("[TEST LFM] SUCCESS: Recipe planned by local model:")
        print(json.dumps(recipe, indent=2, ensure_ascii=False))
        
        assert "steps" in recipe, "Missing 'steps' array in generated recipe"
        assert len(recipe["steps"]) > 0, "Steps array is empty"
        actual_primitive = recipe["steps"][0]["primitive"]
        assert actual_primitive in ["io.copy", "io.write_file"], f"Expected primitive 'io.copy' or 'io.write_file', got '{actual_primitive}'"
        
        # Update .env
        update_env_file("openai_compatible", target_url, target_model)
        
        print("\n[VERIFICATION_GATE]")
        print("- Invariant 1 [Local Inference Planning] : SUCCESS")
    except Exception as e:
        print(f"[TEST LFM] Planning test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
