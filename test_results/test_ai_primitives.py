import os
import sys
import json
import time
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

PORT = 8090
SUCCESS = True

class MockLLMHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress standard logging prints
        pass

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        req_json = json.loads(post_data.decode('utf-8'))
        
        system_prompt = ""
        user_prompt = ""
        for msg in req_json.get("messages", []):
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            elif msg.get("role") == "user":
                user_prompt = msg.get("content", "")

        response_content = ""
        # Inspect prompts to see if we are in extract or summarize mode
        if "schema" in user_prompt or "properties" in user_prompt:
            # Extract mode
            response_content = json.dumps({"nom": "Alice", "ville": "Paris"})
        else:
            # Summarize mode
            response_content = "Résumé court de l'avis client."

        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": response_content
                    }
                }
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_payload).encode('utf-8'))

def run_mock_server():
    server = HTTPServer(('127.0.0.1', PORT), MockLLMHandler)
    server.serve_forever()

def main():
    global SUCCESS
    print("=== STARTING AI PRIMITIVES INTEGRATION TEST ===")
    
    # 1. Start mock server
    server_thread = threading.Thread(target=run_mock_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    print(f"[TEST] Mock LLM Server started on port {PORT}.")

    # 2. Create dummy input CSV
    source_csv = Path("d:/image_to_text/RUST_LIKE_A_TOOL/test_results/ai_input.csv")
    source_csv.parent.mkdir(exist_ok=True)
    with open(source_csv, "w", encoding="utf-8") as f:
        f.write("id,commentaire\n1,Mon nom est Alice et j'habite à Paris. J'aime cette ville.\n")

    dest_summarize = Path("d:/image_to_text/RUST_LIKE_A_TOOL/test_results/ai_summarized.csv")
    dest_extract = Path("d:/image_to_text/RUST_LIKE_A_TOOL/test_results/ai_extracted.csv")

    exe_path = "rust_muscle/target/debug/rust_muscle.exe" if os.name == "nt" else "rust_muscle/target/debug/rust_muscle"
    
    # 3. Test ai.summarize
    print("[TEST] Running ai.summarize...")
    cmd_sum = [
        exe_path, "ai.summarize",
        "--source", str(source_csv),
        "--destination", str(dest_summarize),
        "--column", "commentaire",
        "--target-column", "resume",
        "--model-provider", "openai_compatible",
        "--base-url", f"http://127.0.0.1:{PORT}/v1",
        "--model-id", "mock-model"
    ]
    
    res = subprocess.run(cmd_sum, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FAIL] ai.summarize exited with code {res.returncode}")
        print("Stderr:", res.stderr)
        SUCCESS = False
    else:
        print("Stdout:", res.stdout)
        # Verify output file
        if dest_summarize.exists():
            with open(dest_summarize, "r", encoding="utf-8") as f:
                content = f.read()
                print("Summarized Content:\n", content)
                if "resume" in content and "Résumé court de l'avis client" in content:
                    print("[SUCCESS] ai.summarize verified!")
                else:
                    print("[FAIL] Output content verification failed for summarize")
                    SUCCESS = False
        else:
            print("[FAIL] Summarize output file not found")
            SUCCESS = False

    # 4. Test ai.extract
    print("[TEST] Running ai.extract...")
    schema_json = json.dumps({
        "type": "object",
        "properties": {
            "nom": {"type": "string"},
            "ville": {"type": "string"}
        },
        "required": ["nom", "ville"]
    })
    
    cmd_ext = [
        exe_path, "ai.extract",
        "--source", str(source_csv),
        "--destination", str(dest_extract),
        "--column", "commentaire",
        "--schema", schema_json,
        "--model-provider", "openai_compatible",
        "--base-url", f"http://127.0.0.1:{PORT}/v1",
        "--model-id", "mock-model"
    ]
    
    res = subprocess.run(cmd_ext, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FAIL] ai.extract exited with code {res.returncode}")
        print("Stderr:", res.stderr)
        SUCCESS = False
    else:
        print("Stdout:", res.stdout)
        # Verify output file
        if dest_extract.exists():
            with open(dest_extract, "r", encoding="utf-8") as f:
                content = f.read()
                print("Extracted Content:\n", content)
                if "nom" in content and "ville" in content and "Alice" in content and "Paris" in content:
                    print("[SUCCESS] ai.extract verified!")
                else:
                    print("[FAIL] Output content verification failed for extract")
                    SUCCESS = False
        else:
            print("[FAIL] Extract output file not found")
            SUCCESS = False

    # Cleanup test files
    for p in [source_csv, dest_summarize, dest_extract]:
        if p.exists():
            p.unlink()

    if SUCCESS:
        print("=== ALL AI INTEGRATION TESTS PASSED ===")
        sys.exit(0)
    else:
        print("=== AI INTEGRATION TESTS FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
