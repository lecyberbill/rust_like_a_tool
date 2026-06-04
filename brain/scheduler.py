# [WFGY] Zone: SAFE | λ: 0.2 | Action: Daemon loops for Cron, File Watcher and port 8766 HTTP Webhook API server

import os
import asyncio
import fnmatch
import datetime
import urllib.parse
from pathlib import Path

# Import workspaces registry database methods and websocket state
from registry import load_workspaces_registry, save_workspaces_registry, broadcast, broadcast_workspaces_list

def match_cron_field(val: int, pattern: str) -> bool:
    if pattern == "*":
        return True
    if "," in pattern:
        return any(match_cron_field(val, p) for p in pattern.split(","))
    if pattern.startswith("*/"):
        try:
            step = int(pattern[2:])
            return val % step == 0
        except ValueError:
            return False
    if "-" in pattern:
        try:
            start, end = map(int, pattern.split("-"))
            return start <= val <= end
        except ValueError:
            return False
    try:
        return int(pattern) == val
    except ValueError:
        return False

def match_cron(dt: datetime.datetime, cron_str: str) -> bool:
    parts = cron_str.strip().split()
    if len(parts) != 5:
        return False
    cron_weekday = (dt.weekday() + 1) % 7 # 0 or 7 = Sunday
    return (match_cron_field(dt.minute, parts[0]) and
            match_cron_field(dt.hour, parts[1]) and
            match_cron_field(dt.day, parts[2]) and
            match_cron_field(dt.month, parts[3]) and
            match_cron_field(cron_weekday, parts[4]))

def get_next_cron_execution(cron_str: str) -> str:
    try:
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        for i in range(1, 10080):  # limit to 7 days
            check_time = now + datetime.timedelta(minutes=i)
            if match_cron(check_time, cron_str):
                return check_time.isoformat()
    except Exception:
        pass
    return "N/A"

async def trigger_workspace_by_id(workspace_id: str, trigger_context: dict = None):
    from orchestrator import Orchestrator, ENV_CONFIG
    from vault import StealthVault
    
    registry = load_workspaces_registry()
    if workspace_id not in registry.get("workspaces", {}):
        print(f"[TRIGGER WARNING] Workspace '{workspace_id}' not found in registry.")
        return False
        
    flow_info = registry["workspaces"][workspace_id]
    recipe_file = Path(__file__).parent / flow_info["recipe_file"]
    if not recipe_file.exists():
        print(f"[TRIGGER ERROR] Recipe file '{recipe_file}' does not exist.")
        return False
        
    try:
        with open(recipe_file, "r", encoding="utf-8") as f:
            recipe = json_data = f.read()
            recipe = json_data and eval(json_data) # Load using eval or standard json
            import json
            recipe = json.loads(json_data)
    except Exception as e:
        print(f"[TRIGGER ERROR] Failed to load recipe: {e}")
        return False

    await broadcast({
        "type": "LOG",
        "message": f"[DAEMON] Déclenchement automatique du flux '{flow_info['name']}'..."
    })

    def status_update(step_num, status, log_message):
        asyncio.create_task(broadcast({
            "type": "STEP_STATUS",
            "step": step_num,
            "status": status,
            "log": log_message
        }))

    orchestrator = Orchestrator()
    if trigger_context:
        orchestrator.execution_context.update(trigger_context)

    vault_key = ENV_CONFIG.get("SECRET_API_KEY") or os.environ.get("SECRET_API_KEY", "wfgy-default-vault-key-12345")
    vault = StealthVault(vault_key)
    recipe["env"] = vault.load_secrets()

    await broadcast({
        "type": "WORKSPACE_EXECUTION_STATE",
        "workspace_id": workspace_id,
        "state": "running"
    })

    success = await orchestrator.run_recipe(recipe, status_callback=status_update)

    registry = load_workspaces_registry()
    if workspace_id in registry.get("workspaces", {}):
        registry["workspaces"][workspace_id]["last_run"] = datetime.datetime.now().isoformat()
        save_workspaces_registry(registry)

    await broadcast({
        "type": "WORKSPACE_EXECUTION_STATE",
        "workspace_id": workspace_id,
        "state": "success" if success else "error"
    })
    
    await broadcast({
        "type": "LOG",
        "message": f"[DAEMON] Fin de l'exécution automatique de '{flow_info['name']}'. Résultat: {'SUCCÈS' if success else 'ÉCHEC'}."
    })
    
    await broadcast_workspaces_list()
    return success

async def cron_scheduler_loop():
    print("[DAEMON] Boucle du Planificateur Cron démarrée.")
    while True:
        try:
            now = datetime.datetime.now()
            await asyncio.sleep(60 - now.second - now.microsecond / 1000000.0)
            current_time = datetime.datetime.now()
            registry = load_workspaces_registry()
            
            for w_id, w_info in registry.get("workspaces", {}).items():
                trigger = w_info.get("trigger", {})
                if trigger.get("enabled") and trigger.get("type") == "cron":
                    cron_expr = trigger.get("cron_expression")
                    if cron_expr and match_cron(current_time, cron_expr):
                        asyncio.create_task(trigger_workspace_by_id(w_id))
        except Exception as e:
            print(f"[DAEMON ERROR] Cron scheduler error: {e}")
            await asyncio.sleep(10)

async def directory_watcher_loop():
    print("[DAEMON] Boucle du File Watcher démarrée.")
    while True:
        try:
            await asyncio.sleep(10)
            registry = load_workspaces_registry()
            
            for w_id, w_info in registry.get("workspaces", {}).items():
                trigger = w_info.get("trigger", {})
                if trigger.get("enabled") and trigger.get("type") == "event":
                    watch_dir_str = trigger.get("watch_directory")
                    pattern = trigger.get("pattern", "*")
                    
                    if not watch_dir_str:
                        continue
                        
                    watch_path = Path(watch_dir_str)
                    if watch_path.exists() and watch_path.is_dir():
                        for item in watch_path.iterdir():
                            if item.is_file() and not item.name.startswith("."):
                                if fnmatch.fnmatch(item.name, pattern):
                                    processed_dir = watch_path / ".processed"
                                    processed_dir.mkdir(exist_ok=True)
                                    
                                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    dest_file = processed_dir / f"{item.stem}_{timestamp}{item.suffix}"
                                    
                                    try:
                                        item.rename(dest_file)
                                        context = {
                                            "EVENT_FILE_PATH": str(dest_file),
                                            "EVENT_FILE_NAME": item.name
                                        }
                                        await broadcast({
                                            "type": "LOG",
                                            "message": f"[WATCHER] Fichier détecté '{item.name}'. Lancement du flux."
                                        })
                                        asyncio.create_task(trigger_workspace_by_id(w_id, context))
                                    except Exception as rename_err:
                                        print(f"[WATCHER ERROR] Failed to rename/process file {item.name}: {rename_err}")
        except Exception as e:
            print(f"[DAEMON ERROR] Directory watcher error: {e}")

async def handle_http_request(reader, writer):
    try:
        data = await reader.read(4096)
        message = data.decode('utf-8', errors='ignore')
        if not message:
            writer.close()
            return

        lines = message.split("\r\n")
        if lines:
            req_line = lines[0]
            parts = req_line.split()
            if len(parts) >= 2:
                method, path = parts[0], parts[1]
                if "/trigger" in path:
                    parsed_url = urllib.parse.urlparse(path)
                    params = urllib.parse.parse_qs(parsed_url.query)
                    workspace_id = params.get("workspace", [None])[0]
                    
                    if workspace_id:
                        asyncio.create_task(trigger_workspace_by_id(workspace_id))
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            "Connection: close\r\n\r\n"
                            f'{{"status": "triggered", "workspace": "{workspace_id}"}}'
                        )
                    else:
                        response = (
                            "HTTP/1.1 400 Bad Request\r\n"
                            "Content-Type: application/json\r\n"
                            "Connection: close\r\n\r\n"
                            '{"error": "Missing workspace parameter"}'
                        )
                else:
                    response = (
                        "HTTP/1.1 404 Not Found\r\n"
                        "Content-Type: application/json\r\n"
                        "Connection: close\r\n\r\n"
                        '{"error": "Not Found"}'
                    )
            else:
                response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
        else:
            response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"

        writer.write(response.encode('utf-8'))
        await writer.drain()
    except Exception as e:
        print(f"[HTTP SERVER ERROR] {e}")
    finally:
        writer.close()
