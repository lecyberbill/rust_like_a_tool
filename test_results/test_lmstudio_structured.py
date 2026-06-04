# [WFGY] Zone: SAFE | λ: 0.1 | Action: Diagnostic script for LM Studio HTTP 400 error details

import urllib.request
import urllib.error
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from orchestrator import load_env

def test_structured():
    config = load_env("dev")
    base_url = config.get("LLM_BASE_URL", "http://localhost:1234/v1").rstrip("/")
    model = config.get("LLM_MODEL", "lfm2.5-8b-a1b")
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer unused"
    }
    
    # Let's test standard call (no response_format) to see if that works
    payload_simple = {
        "model": model,
        "messages": [
            {"role": "user", "content": "hello"}
        ],
        "max_tokens": 10
    }
    
    print("[DIAG] 1. Testing simple request without response_format...")
    try:
        data = json.dumps(payload_simple).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            print("[DIAG] Simple request SUCCESS")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"[DIAG] Simple request FAILED: {e.code} {e.reason}\nBody: {error_body}")
        return

    # Let's test json_object
    payload_json = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Dis bonjour au format JSON avec les cles 'status' et 'message'."}
        ],
        "max_tokens": 50,
        "response_format": {"type": "json_object"}
    }
    
    print("\n[DIAG] 2. Testing response_format = json_object...")
    try:
        data = json.dumps(payload_json).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            print("[DIAG] json_object request SUCCESS")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"[DIAG] json_object request FAILED: {e.code} {e.reason}\nBody: {error_body}")

    # Let's test json_schema
    recipe_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": ["status", "message"]
    }
    
    payload_schema = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Dis bonjour."}
        ],
        "max_tokens": 50,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "hello_schema",
                "schema": recipe_schema
            }
        }
    }
    
    print("\n[DIAG] 3. Testing response_format = json_schema...")
    try:
        data = json.dumps(payload_schema).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            print("[DIAG] json_schema request SUCCESS")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"[DIAG] json_schema request FAILED: {e.code} {e.reason}\nBody: {error_body}")

if __name__ == "__main__":
    test_structured()
