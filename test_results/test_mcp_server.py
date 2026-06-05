# [WFGY] Zone: TEST | λ: 0.1 | Action: Python integration test for MCP server spec handshake & tools
import os
import sys
import json
import subprocess
import time
from pathlib import Path

def run_test():
    print("=== RUNNING MCP SERVER INTEGRATION TEST ===")
    
    server_script = Path(__file__).parent.parent / "brain" / "mcp_server.py"
    python_exe = sys.executable
    
    # Start the MCP server process
    proc = subprocess.Popen(
        [python_exe, str(server_script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    
    time.sleep(0.5)
    
    try:
        # Step 1: Send Initialize Request
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "TestClient", "version": "1.0"}
            }
        }
        
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        # Read Initialize Response
        resp_line = proc.stdout.readline().strip()
        print(f"[TEST CLIENT] Received Init Response: {resp_line}")
        resp = json.loads(resp_line)
        
        assert resp["id"] == 1, "ID mismatch"
        assert resp["result"]["protocolVersion"] == "2024-11-05", "Protocol mismatch"
        assert resp["result"]["serverInfo"]["name"] == "ETL-Orchestrator-MCP", "Server info mismatch"
        print("[TEST] Handshake (Initialize): SUCCESS")

        # Step 2: Send Tools List Request
        list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        proc.stdin.write(json.dumps(list_req) + "\n")
        proc.stdin.flush()
        
        # Read Tools List Response
        resp_line = proc.stdout.readline().strip()
        print(f"[TEST CLIENT] Received Tools Response: {resp_line}")
        resp = json.loads(resp_line)
        
        assert resp["id"] == 2, "ID mismatch"
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        assert "list_flows" in tool_names, "Missing list_flows tool"
        assert "get_flow_details" in tool_names, "Missing get_flow_details tool"
        assert "run_flow" in tool_names, "Missing run_flow tool"
        print("[TEST] List Tools: SUCCESS")

        # Step 3: Call list_flows Tool
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_flows",
                "arguments": {}
            }
        }
        
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()
        
        # Read Call Tool Response
        resp_line = proc.stdout.readline().strip()
        print(f"[TEST CLIENT] Received Call Response: {resp_line}")
        resp = json.loads(resp_line)
        
        assert resp["id"] == 3, "ID mismatch"
        content = resp["result"]["content"]
        assert content[0]["type"] == "text", "Expected text content"
        text_val = content[0]["text"]
        
        # Verify it lists our default workspace flow
        assert "default_workflow" in text_val or "recipe" in text_val, "Workspace listing failed"
        print("[TEST] Call Tool (list_flows): SUCCESS")
        
        print("\n[VERIFICATION_GATE]")
        print("- Invariant 13 [Agentic Model Context Protocol (MCP)]: SUCCESS")

    finally:
        # Shutdown server process
        proc.stdin.close()
        proc.terminate()
        proc.wait(timeout=2)
        print("[TEST] MCP Server stopped.")

if __name__ == "__main__":
    run_test()
