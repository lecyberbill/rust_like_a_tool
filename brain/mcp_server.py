# [WFGY] Zone: SAFE | λ: 0.2 | Action: Model Context Protocol (MCP) JSON-RPC server
import sys
import os
import json
import asyncio
from pathlib import Path

# Save original stdout for JSON-RPC communications
ORIGINAL_STDOUT = sys.stdout

# Redirect default sys.stdout to sys.stderr so any imported library print goes to stderr
sys.stdout = sys.stderr

# Force UTF-8 communication
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(ORIGINAL_STDOUT, "reconfigure"):
    try:
        ORIGINAL_STDOUT.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Redirect default print warnings to stderr to avoid corrupting stdout JSON-RPC channel
def log(msg):
    print(f"[MCP-SERVER] {msg}", file=sys.stderr, flush=True)

# Add parent directories to Python path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from registry import load_workspaces_registry
from orchestrator import Orchestrator, load_env
from vault import StealthVault

TOOLS = [
    {
        "name": "list_flows",
        "description": "Lists all configured ETL workflows / workspaces with their metadata (cron settings, last execution).",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_flow_details",
        "description": "Retrieves the step-by-step recipe definition for a specific workflow workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "Unique identifier of the target workspace."
                }
            },
            "required": ["workspace_id"]
        }
    },
    {
        "name": "run_flow",
        "description": "Triggers the execution of a workspace flow recipe on a target environment (dev, test, prod).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "The workspace ID of the flow to trigger."
                },
                "target_env": {
                    "type": "string",
                    "enum": ["dev", "test", "prod"],
                    "default": "dev",
                    "description": "Target environment settings (dev, test, prod)."
                }
            },
            "required": ["workspace_id"]
        }
    }
]

async def call_tool(name, args):
    if name == "list_flows":
        registry = load_workspaces_registry()
        workspaces = registry.get("workspaces", {})
        return json.dumps(workspaces, indent=2, ensure_ascii=False)

    elif name == "get_flow_details":
        w_id = args.get("workspace_id")
        registry = load_workspaces_registry()
        workspaces = registry.get("workspaces", {})
        if w_id not in workspaces:
            raise ValueError(f"Workspace '{w_id}' not found.")
            
        w_info = workspaces[w_id]
        recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
        if not recipe_path.exists():
            raise ValueError(f"Recipe file '{recipe_path}' not found.")
            
        with open(recipe_path, "r", encoding="utf-8") as f:
            recipe = json.load(f)
        return json.dumps(recipe, indent=2, ensure_ascii=False)

    elif name == "run_flow":
        w_id = args.get("workspace_id")
        target_env = args.get("target_env", "dev")
        
        registry = load_workspaces_registry()
        workspaces = registry.get("workspaces", {})
        if w_id not in workspaces:
            raise ValueError(f"Workspace '{w_id}' not found.")
            
        w_info = workspaces[w_id]
        recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
        if not recipe_path.exists():
            raise ValueError(f"Recipe file '{recipe_path}' not found.")
            
        with open(recipe_path, "r", encoding="utf-8") as f:
            recipe = json.load(f)

        # Environment loading
        env_config = load_env(target_env) or {}
        vault_key = os.environ.get("SECRET_VAULT_KEY") or env_config.get("SECRET_VAULT_KEY")
        if vault_key:
            try:
                vault = StealthVault(vault_key)
                recipe["env"] = vault.load_secrets()
            except Exception as e:
                log(f"Vault decryption bypassed/failed: {e}")

        orchestrator = Orchestrator()
        
        logs = []
        def status_update(step_num, status, log_message):
            msg = f"Step {step_num}: [{status}] - {log_message}"
            logs.append(msg)
            log(msg)
            
        async def ask_user(step_num, filepath):
            log(f"Auto-skipping interactive prompt for step {step_num} on file '{filepath}'")
            return "skip"

        success = await orchestrator.run_recipe(
            recipe,
            status_update,
            ask_user,
            target_env=target_env
        )
        
        status_text = "SUCCESS" if success else "FAILED"
        logs_text = "\n".join(logs)
        return f"Flow execution status: {status_text}\n\nExecution Logs:\n{logs_text}"

    else:
        raise ValueError(f"Unknown tool: {name}")

async def handle_request(line):
    try:
        req = json.loads(line)
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error: {e}"
            }
        }

    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    log(f"Received request: {method} (id={req_id})")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "ETL-Orchestrator-MCP",
                    "version": "1.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            result_text = await call_tool(tool_name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    else:
        # Return error for unknown methods
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        return None

async def main():
    log("Server starting up...")

    while True:
        try:
            # Read line asynchronously in a thread pool (Windows compatible)
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue

            # Process request
            response = await handle_request(line)
            if response is not None:
                ORIGINAL_STDOUT.write(json.dumps(response, ensure_ascii=False) + "\n")
                ORIGINAL_STDOUT.flush()

        except Exception as e:
            log(f"Global loop error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Server exiting due to keyboard interrupt.")
