# [WFGY] Zone: SAFE | λ: 0.2 | Action: Daemon loops for Cron, File Watcher and port 8766 HTTP Webhook API server

import os
import json
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
        parts = cron_str.strip().split()
        if len(parts) != 5:
            return "N/A"
        
        # Fast optimization: If cron is */5 or similar with simple minute interval:
        # We can find the minute offset directly instead of iterating minute-by-minute for 10080 minutes.
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        
        # Limit to next 24 hours first (1440 mins) to make the common cases instant
        for i in range(1, 1440):
            check_time = now + datetime.timedelta(minutes=i)
            if match_cron(check_time, cron_str):
                return check_time.isoformat()
                
        # If not in the next 24 hours, expand limit to 7 days (10080 mins)
        # but skip minutes if parts[0] is a fixed number
        step_min = 1
        if parts[0].startswith("*/"):
            try:
                step_min = int(parts[0][2:])
            except ValueError:
                pass
        
        # Check day by day first if the cron doesn't run every hour to find matching days
        # This prevents checking 10080 minutes.
        for i in range(1440, 10080, step_min):
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

    vault_key = os.environ.get("SECRET_VAULT_KEY") or ENV_CONFIG.get("SECRET_VAULT_KEY")
    if not vault_key:
        print("[CRITICAL SECURITY ERROR] SECRET_VAULT_KEY is not defined in environment variables.")
        return False
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

from metrics import METRICS

def _extract_token(message: str) -> str:
    for line in message.split("\r\n"):
        if line.lower().startswith("authorization: bearer "):
            return line.split(" ", 2)[2]
    # Fallback: query param ?token=
    for part in message.split(" ")[1:2]:
        if "?token=" in part:
            return part.split("?token=", 1)[1].split("&", 1)[0].split(" ", 1)[0]
    return ""

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
                clean_path = path.split('?')[0]
                if path == "/api/setup-status" and method == "GET":
                    from auth import _get_db
                    conn = _get_db()
                    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
                    conn.close()
                    has_users = row["cnt"] > 0 if row else False
                    resp_body = json.dumps({"has_users": has_users})
                    resp = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/json\r\n"
                        "Access-Control-Allow-Origin: *\r\n"
                        f"Content-Length: {len(resp_body.encode('utf-8'))}\r\n"
                        "Connection: close\r\n\r\n"
                        f"{resp_body}"
                    )
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif path == "/api/register" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from auth import register
                        creds = json.loads(body_data)
                        result = register(creds.get("username", ""), creds.get("password", ""))
                        resp_body = json.dumps(result)
                        resp = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(resp_body.encode('utf-8'))}\r\n"
                            "Connection: close\r\n\r\n"
                            f"{resp_body}"
                        )
                    except ValueError as e:
                        resp_body = json.dumps({"error": str(e)})
                        resp = (
                            "HTTP/1.1 400 Bad Request\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(resp_body.encode('utf-8'))}\r\n"
                            "Connection: close\r\n\r\n"
                            f"{resp_body}"
                        )
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif path == "/api/login" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from auth import login as auth_login
                        creds = json.loads(body_data)
                        result = auth_login(creds.get("username", ""), creds.get("password", ""))
                        resp_body = json.dumps(result)
                        resp = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(resp_body.encode('utf-8'))}\r\n"
                            "Connection: close\r\n\r\n"
                            f"{resp_body}"
                        )
                    except ValueError as e:
                        resp_body = json.dumps({"error": str(e)})
                        resp = (
                            "HTTP/1.1 401 Unauthorized\r\n"
                            "Content-Type: application/json\r\n"
                            "Access-Control-Allow-Origin: *\r\n"
                            f"Content-Length: {len(resp_body.encode('utf-8'))}\r\n"
                            "Connection: close\r\n\r\n"
                            f"{resp_body}"
                        )
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                # ── Admin : gestion utilisateurs ────────────────
                elif clean_path == "/api/users" and method == "GET":
                    token = _extract_token(message)
                    try:
                        from auth import list_users
                        users = list_users(token)
                        resp_body = json.dumps(users)
                    except ValueError as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path == "/api/users/role" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from auth import update_role, validate_token
                        data = json.loads(body_data)
                        token = _extract_token(message)
                        update_role(token, int(data["user_id"]), data["role"])
                        resp_body = json.dumps({"ok": True})
                    except (ValueError, KeyError) as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path.startswith("/api/users/") and method == "DELETE":
                    try:
                        from auth import delete_user
                        token = _extract_token(message)
                        user_id = int(clean_path.split("/")[-1])
                        delete_user(token, user_id)
                        resp_body = json.dumps({"ok": True})
                    except (ValueError, KeyError) as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                # ── Recipe versioning ────────────────────────────
                elif clean_path == "/api/recipe/snapshot" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from versions import save_snapshot
                        data = json.loads(body_data)
                        result = save_snapshot(data.get("workspace_id", "unknown"), data)
                        resp_body = json.dumps(result)
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path.startswith("/api/recipe/versions/") and method == "GET":
                    ws = clean_path.split("/api/recipe/versions/", 1)[1]
                    try:
                        from versions import list_versions
                        versions = list_versions(ws)
                        resp_body = json.dumps(versions)
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path.startswith("/api/recipe/rollback/") and method == "POST":
                    parts = clean_path.split("/")
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from versions import rollback
                        data = json.loads(body_data)
                        recipe = rollback(data.get("workspace_id", ""), int(parts[-1]))
                        if recipe:
                            resp_body = json.dumps({"ok": True, "recipe": recipe})
                        else:
                            resp_body = json.dumps({"error": "Version not found"})
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                # ── Run history search ───────────────────────────
                elif clean_path == "/api/run-history" and method == "GET":
                    qs = urllib.parse.urlparse(path).query
                    params = urllib.parse.parse_qs(qs)
                    query = params.get("q", [""])[0].lower()
                    status_filter = params.get("status", [""])[0].lower()
                    try:
                        from registry import load_run_history
                        history = load_run_history()
                        if query:
                            history = [r for r in history if query in json.dumps(r).lower()]
                        if status_filter:
                            history = [r for r in history if r.get("status", "").lower() == status_filter]
                        resp_body = json.dumps(history[:100])
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                # ── Notifications ────────────────────────────────
                elif clean_path == "/api/notif/config" and method == "GET":
                    try:
                        from notifications import load_config
                        resp_body = json.dumps(load_config())
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path == "/api/notif/config" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from notifications import save_config
                        data = json.loads(body_data)
                        resp_body = json.dumps(save_config(data))
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path == "/api/notif/test" and method == "POST":
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from notifications import test_email, test_webhook
                        data = json.loads(body_data)
                        email_result = test_email(data)
                        webhook_result = test_webhook(data)
                        resp_body = json.dumps({"email": email_result, "webhook": webhook_result})
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                # ── Promotion d'environnement ─────────────────────
                elif clean_path.count("/") == 4 and clean_path.endswith("/promote") and method == "POST":
                    ws_id = clean_path.split("/")[2]
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        data = json.loads(body_data)
                        source = data.get("source_env", "dev")
                        target = data.get("target_env", "test")
                        reg = load_workspaces_registry()
                        ws = reg.setdefault("workspaces", {}).setdefault(ws_id, {})
                        recipe_file = Path(__file__).parent / ws.get("recipe_file", "history_recipes/recipe_default.json")
                        if recipe_file.exists():
                            recipe = json.loads(recipe_file.read_text(encoding="utf-8"))
                            env = recipe.setdefault("env", {})
                            if source in env and isinstance(env[source], dict):
                                env.setdefault(target, {})
                                for k, v in env[source].items():
                                    if k not in env[target] or not env[target][k]:
                                        env[target][k] = v
                                recipe_file.write_text(json.dumps(recipe, indent=2, ensure_ascii=False), encoding="utf-8")
                                resp_body = json.dumps({"ok": True, "source": source, "target": target, "vars_pushed": len(env[source])})
                            else:
                                resp_body = json.dumps({"error": f"Source env '{source}' not found or empty"})
                        else:
                            resp_body = json.dumps({"error": "Recipe file not found"})
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path.count("/") == 4 and clean_path.endswith("/notif-config") and method == "GET":
                    ws_id = clean_path.split("/")[2]
                    try:
                        from notifications import load_workspace_config
                        resp_body = json.dumps(load_workspace_config(ws_id))
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path.count("/") == 4 and clean_path.endswith("/notif-config") and method == "POST":
                    ws_id = clean_path.split("/")[2]
                    body_data = message.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in message else "{}"
                    try:
                        from notifications import save_workspace_config
                        data = json.loads(body_data)
                        resp_body = json.dumps(save_workspace_config(ws_id, data))
                    except Exception as e:
                        resp_body = json.dumps({"error": str(e)})
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\nContent-Length: {len(resp_body.encode('utf-8'))}\r\nConnection: close\r\n\r\n{resp_body}"
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif clean_path == "/metrics":
                    body = METRICS.render()
                    resp = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain; charset=utf-8\r\n"
                        f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                        "Connection: close\r\n\r\n"
                        f"{body}"
                    )
                    writer.write(resp.encode('utf-8'))
                    await writer.drain()
                elif "/trigger" in path:
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
                    writer.write(response.encode('utf-8'))
                    await writer.drain()
                else:
                    # Serve static files from vitrine directory
                    clean_path = path.split('?')[0]
                    if clean_path == "/":
                        clean_path = "/index.html"
                    
                    if ".." in clean_path:
                        response_headers = (
                            "HTTP/1.1 403 Forbidden\r\n"
                            "Connection: close\r\n\r\n"
                        )
                        writer.write(response_headers.encode('utf-8'))
                        await writer.drain()
                        writer.close()
                        return
                    
                    from pathlib import Path
                    file_path = Path(__file__).parent.parent / "vitrine" / clean_path.lstrip("/")
                    
                    if file_path.exists() and file_path.is_file():
                        suffix = file_path.suffix.lower()
                        mime_type = "text/plain"
                        if suffix == ".html":
                            mime_type = "text/html; charset=utf-8"
                        elif suffix == ".css":
                            mime_type = "text/css; charset=utf-8"
                        elif suffix in (".js", ".mjs"):
                            mime_type = "application/javascript; charset=utf-8"
                        elif suffix == ".png":
                            mime_type = "image/png"
                        elif suffix in (".jpg", ".jpeg"):
                            mime_type = "image/jpeg"
                        elif suffix == ".svg":
                            mime_type = "image/svg+xml; charset=utf-8"
                        elif suffix == ".json":
                            mime_type = "application/json; charset=utf-8"
                            
                        try:
                            content = await asyncio.to_thread(
                                lambda: open(file_path, "rb").read()
                            )
                            response_headers = (
                                "HTTP/1.1 200 OK\r\n"
                                f"Content-Type: {mime_type}\r\n"
                                f"Content-Length: {len(content)}\r\n"
                                "Access-Control-Allow-Origin: *\r\n"
                                "Connection: close\r\n\r\n"
                            )
                            writer.write(response_headers.encode('utf-8') + content)
                            await writer.drain()
                        except Exception as file_err:
                            response_body = f'{{"error": "Failed to read file: {file_err}"}}'
                            response_headers = (
                                "HTTP/1.1 500 Internal Server Error\r\n"
                                "Content-Type: application/json\r\n"
                                f"Content-Length: {len(response_body)}\r\n"
                                "Connection: close\r\n\r\n"
                            )
                            writer.write(response_headers.encode('utf-8') + response_body.encode('utf-8'))
                            await writer.drain()
                    else:
                        response_body = '{"error": "File not found"}'
                        response_headers = (
                            "HTTP/1.1 404 Not Found\r\n"
                            "Content-Type: application/json\r\n"
                            f"Content-Length: {len(response_body)}\r\n"
                            "Connection: close\r\n\r\n"
                        )
                        writer.write(response_headers.encode('utf-8') + response_body.encode('utf-8'))
                        await writer.drain()
            else:
                response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
                writer.write(response.encode('utf-8'))
                await writer.drain()
        else:
            response = "HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n"
            writer.write(response.encode('utf-8'))
            await writer.drain()
    except Exception as e:
        print(f"[HTTP SERVER ERROR] {e}")
    finally:
        writer.close()
