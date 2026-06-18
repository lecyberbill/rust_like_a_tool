"""Recipe versioning — snapshots, rollback, listing."""
import json
import time
import shutil
from pathlib import Path

VERSIONS_DIR = Path(__file__).parent / "history_recipes" / "versions"

def _ensure_dir():
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

def save_snapshot(workspace_id: str, recipe: dict) -> dict:
    _ensure_dir()
    version = int(time.time())
    safe = workspace_id.replace(" ", "_").replace("/", "_")
    path = VERSIONS_DIR / f"{safe}_{version}.json"
    snapshot = {"version": version, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "workspace_id": workspace_id, "recipe": recipe}
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"version": version, "timestamp": snapshot["timestamp"]}

def list_versions(workspace_id: str, limit: int = 20) -> list[dict]:
    _ensure_dir()
    safe = workspace_id.replace(" ", "_").replace("/", "_")
    versions = []
    for f in sorted(VERSIONS_DIR.glob(f"{safe}_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            versions.append({"version": data["version"], "timestamp": data["timestamp"]})
        except Exception:
            continue
    return versions[:limit]

def get_snapshot(workspace_id: str, version: int) -> dict | None:
    _ensure_dir()
    safe = workspace_id.replace(" ", "_").replace("/", "_")
    path = VERSIONS_DIR / f"{safe}_{version}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def rollback(workspace_id: str, version: int) -> dict | None:
    snap = get_snapshot(workspace_id, version)
    if not snap:
        return None
    return snap["recipe"]
