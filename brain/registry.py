# [WFGY] Zone: SAFE | λ: 0.2 | Action: Workspace registry metadata loader & WebSocket broadcast helpers

import json
import asyncio
import datetime
from pathlib import Path
import json

REGISTRY_FILE = Path(__file__).parent / "workspaces.json"
ACTIVE_CONNECTIONS = set()

def load_workspaces_registry() -> dict:
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[REGISTRY ERROR] Failed to load registry: {e}")
    
    # Default structure
    default_registry = {
        "active_workspace": "default_workflow",
        "workspaces": {
            "default_workflow": {
                "name": "Flux de travail par défaut",
                "recipe_file": "history_recipes/recipe_default.json",
                "created_at": datetime.datetime.now().isoformat(),
                "last_run": None,
                "trigger": {
                    "enabled": False,
                    "type": "none"
                }
            }
        }
    }
    
    recipes_dir = Path(__file__).parent / "history_recipes"
    recipes_dir.mkdir(exist_ok=True)
    default_recipe_file = recipes_dir / "recipe_default.json"
    if not default_recipe_file.exists():
        default_recipe = {
            "plan_id": "default_workflow",
            "intent_analysis": "Flux par défaut initial",
            "steps": [],
            "env": {}
        }
        with open(default_recipe_file, "w", encoding="utf-8") as f:
            json.dump(default_recipe, f, indent=2, ensure_ascii=False)
            
    save_workspaces_registry(default_registry)
    return default_registry

def save_workspaces_registry(registry: dict):
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[REGISTRY ERROR] Failed to save registry: {e}")

async def broadcast(message: dict):
    if ACTIVE_CONNECTIONS:
        payload = json.dumps(message, ensure_ascii=False)
        tasks = []
        for ws in list(ACTIVE_CONNECTIONS):
            try:
                tasks.append(asyncio.create_task(ws.send(payload)))
            except Exception:
                pass
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

async def broadcast_workspaces_list():
    from scheduler import get_next_cron_execution
    registry = load_workspaces_registry()
    workspaces = registry.get("workspaces", {})
    for w_id, w_info in workspaces.items():
        trig = w_info.get("trigger", {})
        if trig.get("enabled") and trig.get("type") == "cron":
            w_info["next_run"] = get_next_cron_execution(trig.get("cron_expression", ""))
        else:
            w_info["next_run"] = "N/A"
            
    await broadcast({
        "type": "WORKSPACES_LIST",
        "active_workspace": registry.get("active_workspace"),
        "workspaces": workspaces
    })

def load_run_history() -> list:
    path = Path(__file__).parent / "run_history.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
