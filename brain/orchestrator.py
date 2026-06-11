# [WFGY] Zone: TRANSIT | λ: 0.4 | Action: Move step_map definition before checkpoint block to resolve scope crash
import os
import sys
import json
import asyncio
import subprocess
import time
import datetime
import logging
from pathlib import Path
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
# Suppress noisy library logs
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
log = logging.getLogger("wfgy.orchestrator")

# Dynamically add Chromatix path to sys.path
# Dynamically add Chromatix path to sys.path
_chromatix_path = os.environ.get("CHROMATIX_PATH") or "d:/image_to_text/chromatix"
sys.path.append(str(Path(_chromatix_path)))

# Ensure brain/ is on sys.path for imports like from vault import StealthVault
_brain_dir = str(Path(__file__).parent)
if _brain_dir not in sys.path:
    sys.path.insert(0, _brain_dir)

try:
    from chromatix_cps.core import CPSPacket
    from PIL import Image
    HAS_CHROMATIX = True
    log.info("Chromatix Pixel Standard Engine loaded")
except ImportError:
    HAS_CHROMATIX = False
    log.warning("Chromatix Engine not found — running in legacy flat-file fallback mode")
from vault import StealthVault
from auth import validate_token, get_tenant_id

# Try to import jsonschema for advanced validation, fallback to manual if not present
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

def load_env(env_name="dev"):
    """
    Rudimentary .env parser to avoid extra dependency like python-dotenv.
    Supports environment-specific files (.env.test, .env.dev, .env.prod) and falls back to .env.
    """
    filename = ".env"
    if env_name == "test":
        filename = ".env.test"
    elif env_name == "prod":
        filename = ".env.prod"
    elif env_name == "dev":
        filename = ".env.dev"
    
    env_path = None
    for candidate_dir in [Path.cwd(), Path(__file__).parent, Path(__file__).parent.parent]:
        candidate_path = candidate_dir / filename
        if candidate_path.exists():
            env_path = candidate_path
            break
            
    # Fallback to standard .env
    if not env_path:
        for candidate_dir in [Path.cwd(), Path(__file__).parent, Path(__file__).parent.parent]:
            candidate_path = candidate_dir / ".env"
            if candidate_path.exists():
                env_path = candidate_path
                break
                
    config = {}
    if env_path and env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
        return config
    return config

def extract_file_headers(filepath: str) -> list[str]:
    path = Path(filepath)
    if not path.exists():
        # Check relative to cwd
        path = Path.cwd() / filepath
        if not path.exists():
            return []
    
    ext = path.suffix.lower()
    if ext == ".csv":
        try:
            with open(path, "r", encoding="utf-8") as f:
                header_line = f.readline().strip()
                if header_line:
                    delims = [",", ";", "\t", "|"]
                    delim = ","
                    for d in delims:
                        if d in header_line:
                            delim = d
                            break
                    return [h.strip().replace("\"", "").replace("'", "") for h in header_line.split(delim) if h.strip()]
        except Exception as e:
            print(f"[SCHEMA ERROR] Failed to read CSV headers: {e}")
            
    elif ext == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(4096).strip()
                if content.startswith("["):
                    end_idx = content.find("}")
                    if end_idx != -1:
                        obj_str = content[1:end_idx+1]
                        import json
                        obj = json.loads(obj_str)
                        return list(obj.keys())
                elif content.startswith("{"):
                    import json
                    obj = json.loads(content)
                    return list(obj.keys())
        except Exception as e:
            print(f"[SCHEMA ERROR] Failed to read JSON headers: {e}")
            
    return []

def extract_file_preview(filepath: str, max_rows: int = 10) -> dict:
    path = Path(filepath)
    if not path.exists():
        path = Path.cwd() / filepath
        if not path.exists():
            return {"headers": [], "rows": [], "error": f"Fichier introuvable : {filepath}"}
            
    ext = path.suffix.lower()
    headers = []
    rows = []
    
    if ext == ".csv":
        try:
            import csv
            with open(path, "r", encoding="utf-8-sig") as f:
                sample = f.read(2048)
                f.seek(0)
                delim = ","
                for d in [";", ",", "\t", "|"]:
                    if d in sample:
                        delim = d
                        break
                reader = csv.reader(f, delimiter=delim)
                try:
                    headers = next(reader)
                except StopIteration:
                    return {"headers": [], "rows": []}
                
                headers = [h.strip().replace('"', '').replace("'", "") for h in headers]
                
                count = 0
                for r in reader:
                    if count >= max_rows:
                        break
                    row_dict = {}
                    for idx, h in enumerate(headers):
                        val = r[idx] if idx < len(r) else ""
                        row_dict[h] = val.strip()
                    rows.append(row_dict)
                    count += 1
                    
            return {"headers": headers, "rows": rows}
        except Exception as e:
            return {"headers": [], "rows": [], "error": f"Erreur de lecture CSV : {str(e)}"}
            
    elif ext == ".json":
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if isinstance(data, dict):
                data = [data]
                
            if isinstance(data, list) and data:
                all_keys = []
                for item in data[:max_rows]:
                    if isinstance(item, dict):
                        for k in item.keys():
                            if k not in all_keys:
                                all_keys.append(k)
                headers = all_keys
                
                for item in data[:max_rows]:
                    if isinstance(item, dict):
                        row_dict = {k: str(item.get(k, "")) for k in headers}
                        rows.append(row_dict)
                return {"headers": headers, "rows": rows}
            return {"headers": [], "rows": []}
        except Exception as e:
            return {"headers": [], "rows": [], "error": f"Erreur de lecture JSON : {str(e)}"}
            
    return {"headers": [], "rows": [], "error": f"Format d'aperçu non supporté : {ext}"}

# Load environment configuration
env_mode = os.environ.get("WFGY_ENV", "dev")
ENV_CONFIG = load_env(env_mode)
from worker_bridge import WorkerBridge, ERROR_TRANSLATIONS
from schema_validator import SchemaValidator
from metrics import METRICS
from checkpoint import save_checkpoint, load_checkpoint, delete_checkpoint

class Orchestrator:
    """
    Main Orchestrator coordinating flow recipes.
    """
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.validator = SchemaValidator(self.root_dir / "registry.json")
        self.bridge = WorkerBridge(env_config=ENV_CONFIG)
        import socket
        import getpass
        from datetime import datetime
        now = datetime.now()
        
        try:
            username = getpass.getuser()
        except Exception:
            username = os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
            
        self.execution_context = {
            "CURRENT_YEAR": str(now.year),
            "TODAY": now.strftime("%Y-%m-%d"),
            "NOW": now.strftime("%Y-%m-%d %H:%M:%S"),
            "HOSTNAME": socket.gethostname(),
            "USERNAME": username,
            "OS_NAME": "windows" if os.name == "nt" else "linux"
        }

    def get_data_lineage(self, recipe_data: dict) -> dict:
        """
        Parses the recipe to build a data lineage map.
        Identifies which step produces which file, and which steps consume it.
        """
        steps = recipe_data.get("steps", [])
        lineage = {}  # file_path -> {"producer": step_num, "consumers": []}

        # Helper to clean up file paths to make comparisons robust
        def normalize_path(p):
            if not p or not isinstance(p, str):
                return None
            p_clean = p.strip().replace("\\", "/").lower()
            # Remove environment variables or placeholders for normalization if matching prefix/suffix
            return p_clean

        for step in steps:
            step_num = step.get("step")
            primitive = step.get("primitive")
            args = step.get("args", {})

            # List of arguments commonly acting as source (input)
            inputs = []
            # List of arguments commonly acting as destination (output)
            outputs = []

            for k, v in args.items():
                if not isinstance(v, str):
                    continue
                k_lower = k.lower()
                if "source" in k_lower or "src" in k_lower or "input" in k_lower or k_lower in ["path", "local_path", "file_path", "lookup_file", "target"]:
                    # Distinguish input vs output based on naming
                    if "destination" in k_lower or "dest" in k_lower or "output" in k_lower or k_lower == "quarantine":
                        outputs.append(v)
                    else:
                        inputs.append(v)
                elif "destination" in k_lower or "dest" in k_lower or "output" in k_lower or k_lower == "quarantine":
                    outputs.append(v)

            # Register producers
            for out_file in outputs:
                norm = normalize_path(out_file)
                if norm:
                    if norm not in lineage:
                        lineage[norm] = {"file_path": out_file, "producer": step_num, "consumers": []}
                    else:
                        lineage[norm]["producer"] = step_num

            # Register consumers
            for in_file in inputs:
                norm = normalize_path(in_file)
                if norm:
                    if norm not in lineage:
                        lineage[norm] = {"file_path": in_file, "producer": None, "consumers": [step_num]}
                    else:
                        if step_num not in lineage[norm]["consumers"]:
                            lineage[norm]["consumers"].append(step_num)

        return lineage

    def resolve_secrets(self, args: dict, local_env: dict = None, target_env: str = "dev") -> dict:
        resolved = {}
        if local_env is None:
            local_env = {}
            
        # If local_env has env-specific configurations, extract the current target
        # e.g., local_env = {"dev": {...}, "test": {...}, "prod": {...}}
        env_vars = local_env
        if target_env in local_env and isinstance(local_env[target_env], dict):
            env_vars = local_env[target_env]

        for k, v in args.items():
            if isinstance(v, str):
                # Remplacement de tous les placeholders comme ${VAR} par leur valeur
                import re
                placeholders = re.findall(r"\$\{([^}]+)\}", v)
                resolved_val = v
                for var_name in placeholders:
                    # Priorité: 1. local execution_context, 2. local_env[target_env], 3. OS env, 4. ENV_CONFIG
                    val = self.execution_context.get(var_name)
                    if val is None:
                        val = env_vars.get(var_name)
                    if val is None:
                        val = local_env.get(var_name)
                    if val is None:
                        val = os.environ.get(var_name)
                    if val is None:
                        val = ENV_CONFIG.get(var_name, f"${{{var_name}}}")
                    
                    resolved_val = resolved_val.replace(f"${{{var_name}}}", str(val))
                resolved[k] = resolved_val
            elif isinstance(v, list):
                # Recursively resolve variables inside nested arrays (like then_steps / else_steps)
                resolved_list = []
                for item in v:
                    if isinstance(item, dict):
                        resolved_list.append(self.resolve_secrets(item, local_env, target_env))
                    else:
                        resolved_list.append(item)
                resolved[k] = resolved_list
            else:
                resolved[k] = v
        return resolved

    def _save_to_dlq(self, plan_id: str, step_num: int, primitive: str, args: dict, code: int, stderr: str, attempts: int):
        dlq_dir = self.root_dir / "workspace" / ".dlq"
        dlq_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "plan_id": plan_id,
            "step": step_num,
            "primitive": primitive,
            "args": args,
            "exit_code": code,
            "error": stderr.strip(),
            "attempts": attempts,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        filename = f"{plan_id}_step{step_num}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = dlq_dir / filename
        path.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[DLQ] Failed step saved to {path}")

    def list_dlq(self, plan_id: str = None) -> list:
        """Liste les entrées de la dead-letter queue (optionnellement filtré par plan_id)."""
        dlq_dir = self.root_dir / "workspace" / ".dlq"
        if not dlq_dir.exists():
            return []
        entries = []
        for f in sorted(dlq_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.suffix == ".json":
                if plan_id is None or f.name.startswith(plan_id):
                    try:
                        entries.append(json.loads(f.read_text(encoding="utf-8")))
                    except Exception:
                        pass
        return entries

    def replay_dlq(self, entry: dict) -> None:
        """Relance une étape échouée depuis le DLQ (synchrone, usage externe)."""
        print(f"[DLQ] Replaying step {entry['step']} ({entry['primitive']})...")
        asyncio.create_task(self._replay_dlq_entry(entry))

    async def _replay_dlq_entry(self, entry: dict):
        """Coroutine interne pour rejouer une entrée DLQ."""
        fake_recipe = {
            "plan_id": f"dlq_replay_{entry['plan_id']}",
            "steps": [{
                "step": 1,
                "primitive": entry["primitive"],
                "args": entry["args"],
                "retry": {"attempts": 1},
            }]
        }
        result = await self.run_recipe(fake_recipe)
        if result:
            print(f"[DLQ] Replay succeeded for step {entry['step']} ({entry['primitive']})")
        else:
            print(f"[DLQ] Replay failed for step {entry['step']} ({entry['primitive']})")

    async def run_recipe(self, recipe_data: dict, status_callback=None, ask_user_callback=None, target_env: str = "dev") -> bool:
        plan_id = recipe_data.get("plan_id", "unknown")
        intent = recipe_data.get("intent_analysis", "No intent specified")
        steps = recipe_data.get("steps", [])
        local_env = recipe_data.get("env", {})

        log.info("Starting plan execution", extra={"plan_id": plan_id, "target_env": target_env, "steps": len(steps)})
        log.info("User intent", extra={"intent": intent[:200]})
        METRICS.counter_inc("wfgy_plan_runs_total", {"target_env": target_env})

        # 1. Détection de cycles dans le graphe de dépendances (DAG)
        parents = {}
        for step in steps:
            step_num = step.get("step")
            dep_val = step.get("depends_on", [])
            if isinstance(dep_val, list):
                parents[step_num] = dep_val
            else:
                parents[step_num] = [dep_val]

        visited = {}
        def has_cycle(node):
            if visited.get(node) == 1:  # en cours de visite
                return True
            if visited.get(node) == 2:  # déjà visité
                return False
            visited[node] = 1
            for parent in parents.get(node, []):
                if has_cycle(parent):
                    return True
            visited[node] = 2
            return False

        for step in steps:
            step_num = step.get("step")
            if step_num not in visited:
                if has_cycle(step_num):
                    log.error("Cycle detected in recipe DAG", extra={"step": step_num})
                    return False

        # 2. Préparation des structures de contrôle asynchrones
        step_events = {step.get("step"): asyncio.Event() for step in steps}
        failed_steps = set()
        completed_steps = set()
        step_performance = {}

        # Index des étapes par numéro pour résolution des dépendances et checkpoints
        step_map = {s.get("step"): s for s in steps}

        # Charger le checkpoint SQLite s'il existe pour ce plan_id
        checkpoint_data = load_checkpoint(plan_id)
        if checkpoint_data:
            completed_steps = checkpoint_data["completed_steps"]
            step_performance = checkpoint_data["step_performance"]
            # Valider que les fichiers de sortie des étapes complétées existent encore
            valid_steps = set()
            for sn in list(completed_steps):
                s = step_map.get(sn)
                if s:
                    dest = s.get("args", {}).get("destination", "")
                    if dest and Path(dest).exists():
                        valid_steps.add(sn)
                    elif not dest:
                        valid_steps.add(sn)
            orphaned = completed_steps - valid_steps
            if orphaned:
                log.warning("Checkpoint orphaned steps — files missing", extra={"orphaned": list(orphaned)})
                completed_steps = valid_steps
            self.execution_context.update(checkpoint_data["execution_context"])
            for step_num in completed_steps:
                if step_num in step_events:
                    step_events[step_num].set()
            log.info("Resumed from SQLite checkpoint", extra={"plan_id": plan_id, "steps_done": len(completed_steps)})

        def save_current_checkpoint():
            try:
                serializable_context = {k: v for k, v in self.execution_context.items() if isinstance(v, (str, int, float, bool))}
                save_checkpoint(plan_id, list(completed_steps), step_performance, serializable_context)
            except Exception as save_err:
                log.warning("Checkpoint save failed", extra={"error": str(save_err)})

        run_start = time.perf_counter()

        async def run_single_step(step_item):
            step_num = step_item.get("step")
            primitive = step_item.get("primitive")
            args = step_item.get("args", {})
            dep_list = parents.get(step_num, [])

            if step_num in completed_steps:
                print(f"[ORCHESTRATOR] Étape {step_num} déjà complétée avec succès (reprise). Passage à l'étape suivante.")
                if status_callback:
                    status_callback(step_num, "success", "Étape déjà complétée avec succès (reprise).")
                step_events[step_num].set()
                return True

            # Attente de tous les parents
            for pid in dep_list:
                if pid in step_events:
                    await step_events[pid].wait()
                    if pid in failed_steps:
                        failed_steps.add(step_num)
                        step_performance[step_num] = {
                            "step": step_num,
                            "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                            "duration_ms": 0,
                            "status": "skipped"
                        }
                        step_events[step_num].set()
                        return False
                else:
                    # Parent non déclaré dans la recette, on continue
                    pass

            if failed_steps:
                failed_steps.add(step_num)
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                    "duration_ms": 0,
                    "status": "skipped"
                }
                step_events[step_num].set()
                return False

            # AUTO-RÉSOLUTION : source héritée du parent
            if dep_list and not args.get("source"):
                for parent_num in dep_list:
                    parent_step = step_map.get(parent_num)
                    if parent_step:
                        parent_dest = parent_step.get("args", {}).get("destination", "")
                        if parent_dest:
                            args["source"] = parent_dest
                            print(f"[ORCHESTRATOR] Étape {step_num}: source auto-résolue depuis l'étape {parent_num} → {parent_dest}")
                            break

            # AUTO-GÉNÉRATION : destination si vide et si supporté par le schéma du registre
            if not args.get("destination"):
                spec = self.validator.registry.get("primitives", {}).get(primitive, {})
                params = spec.get("parameters", {}).get("properties", {})
                if "destination" in params:
                    args["destination"] = f"workspace/output/step_{step_num}_{primitive.replace('.', '_')}.csv"
                    print(f"[ORCHESTRATOR] Étape {step_num}: destination auto-générée → {args['destination']}")

            if status_callback:
                status_callback(step_num, "running", f"Exécution de l'étape ({target_env.upper()})...")

            step_start = time.perf_counter()

            # Gestion spécifique de core.wait (Primitive d'attente/rétention)
            if primitive == "core.wait":
                resolved_args = self.resolve_secrets(args, local_env, target_env)
                duration_raw = resolved_args.get("duration", "0")
                duration_seconds = 0
                
                # Parsing du format duration (HH:MM:SS, MM:SS, ou secondes brutes)
                try:
                    duration_str = str(duration_raw).strip()
                    if ":" in duration_str:
                        parts = duration_str.split(":")
                        if len(parts) == 3:  # HH:MM:SS
                            duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2:  # MM:SS
                            duration_seconds = int(parts[0]) * 60 + int(parts[1])
                        else:
                            raise ValueError("Format temporel invalide")
                    else:
                        duration_seconds = float(duration_str)
                except Exception as wait_err:
                    print(f"[ORCHESTRATOR ERROR] Durée de wait invalide : {duration_raw} ({wait_err}). Utilisation de 0s.")
                    duration_seconds = 0
                
                print(f"[ORCHESTRATOR] Wait en cours pour {duration_seconds} secondes...")
                if status_callback:
                    status_callback(step_num, "running", f"Attente de {duration_seconds} secondes ({duration_raw})...")
                
                await asyncio.sleep(duration_seconds)
                
                step_end = time.perf_counter()
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Attente {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": "success"
                }
                completed_steps.add(step_num)
                save_current_checkpoint()
                if status_callback:
                    status_callback(step_num, "success", f"Attente terminée ({duration_seconds}s).")
                step_events[step_num].set()
                return True

            # Gestion spécifique de core.condition (Orchestration logique récursive)
            if primitive == "core.condition":
                resolved_args = self.resolve_secrets(args, local_env, target_env)
                expr = resolved_args.get("expression", "false")
                eval_expr = expr.strip()
                print(f"[ORCHESTRATOR] Évaluation de l'expression : '{eval_expr}'")
                condition_met = False
                try:
                    eval_expr_py = eval_expr.replace("true", "True").replace("false", "False")
                    allowed_chars = "0123456789. ><=!&|()TrueFalse\"' "
                    if all(char in allowed_chars for char in eval_expr_py):
                        condition_met = bool(eval(eval_expr_py))
                    else:
                        print(f"[ORCHESTRATOR WARNING] Expression conditionnelle non résolue ou suspecte : {eval_expr}")
                except Exception as e:
                    print(f"[ORCHESTRATOR ERROR] Échec de l'évaluation de la condition '{eval_expr}': {e}")

                print(f"[ORCHESTRATOR] Résultat condition : {condition_met}")
                if status_callback:
                    status_callback(step_num, "success", f"Condition évaluée à : {condition_met}")

                target_branch = "then_steps" if condition_met else "else_steps"
                branch_steps = args.get(target_branch, [])
                if branch_steps:
                    print(f"[ORCHESTRATOR] Exécution de la branche '{target_branch}'...")
                    sub_recipe = {
                        "plan_id": f"{plan_id}_branch",
                        "intent_analysis": f"Sous-branche conditionnelle : {target_branch}",
                        "steps": branch_steps,
                        "env": local_env
                    }
                    sub_success = await self.run_recipe(sub_recipe, status_callback, ask_user_callback, target_env)
                    if not sub_success:
                        failed_steps.add(step_num)
                        step_end = time.perf_counter()
                        step_performance[step_num] = {
                            "step": step_num,
                            "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                            "duration_ms": int((step_end - step_start) * 1000),
                            "status": "error"
                        }
                        step_events[step_num].set()
                        return False
                
                step_end = time.perf_counter()
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": "success"
                }
                completed_steps.add(step_num)
                save_current_checkpoint()
                step_events[step_num].set()
                return True

            # Gestion spécifique de core.sub_flow (Sous-flux)
            if primitive == "core.sub_flow":
                sub_steps = args.get("steps", [])
                print(f"[ORCHESTRATOR] Exécution du sous-flux (Étape {step_num}) comprenant {len(sub_steps)} étapes...")
                if status_callback:
                    status_callback(step_num, "running", f"Démarrage du sous-flux ({len(sub_steps)} étapes)...")
                
                sub_recipe = {
                    "plan_id": f"{plan_id}_sub_{step_num}",
                    "intent_analysis": f"Sous-flux de l'étape {step_num}",
                    "steps": sub_steps,
                    "env": local_env
                }
                sub_success = await self.run_recipe(sub_recipe, status_callback, ask_user_callback, target_env)
                
                step_end = time.perf_counter()
                status_str = "success" if sub_success else "error"
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Sous-flux {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": status_str
                }
                
                if sub_success:
                    completed_steps.add(step_num)
                    save_current_checkpoint()
                    if status_callback:
                        status_callback(step_num, "success", "Sous-flux exécuté avec succès.")
                else:
                    failed_steps.add(step_num)
                    if status_callback:
                        status_callback(step_num, "error", "Le sous-flux a échoué.")
                        
                step_events[step_num].set()
                return sub_success

            # Gestion spécifique de core.switch (Aiguillage dynamique)
            if primitive == "core.switch":
                switch_val_raw = args.get("value", "")
                cases = args.get("cases", {})
                
                # Résoudre les placeholders/variables sur la valeur de switch
                resolved_args = self.resolve_secrets({"val": switch_val_raw}, local_env, target_env)
                resolved_val = resolved_args.get("val", "")
                
                print(f"[ORCHESTRATOR] Évaluation core.switch Étape {step_num} (Valeur résolue : '{resolved_val}')")
                if status_callback:
                    status_callback(step_num, "running", f"Évaluation de l'aiguillage switch = '{resolved_val}'...")

                # Trouver les étapes associées à cette valeur
                sub_steps = cases.get(resolved_val)
                if sub_steps is None:
                    # Tenter un cas par défaut "default" s'il est déclaré
                    sub_steps = cases.get("default", [])
                    print(f"[ORCHESTRATOR] Valeur '{resolved_val}' non trouvée dans les cas. Utilisation du cas par défaut.")
                    
                print(f"[ORCHESTRATOR] Exécution de la branche sélectionnée ({len(sub_steps)} étapes)...")
                
                sub_recipe = {
                    "plan_id": f"{plan_id}_switch_{step_num}_{resolved_val}",
                    "intent_analysis": f"Branche '{resolved_val}' de l'étape {step_num}",
                    "steps": sub_steps,
                    "env": local_env
                }
                switch_success = await self.run_recipe(sub_recipe, status_callback, ask_user_callback, target_env)
                
                step_end = time.perf_counter()
                status_str = "success" if switch_success else "error"
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Aiguillage {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": status_str
                }
                
                if switch_success:
                    completed_steps.add(step_num)
                    save_current_checkpoint()
                    if status_callback:
                        status_callback(step_num, "success", f"Branche '{resolved_val}' exécutée avec succès.")
                else:
                    failed_steps.add(step_num)
                    if status_callback:
                        status_callback(step_num, "error", f"La branche '{resolved_val}' a échoué.")
                        
                step_events[step_num].set()
                return switch_success


            # Gestion spécifique de core.loop (Boucle d'exécution)
            if primitive == "core.loop":
                loop_over = args.get("loop_over")
                items_source_raw = args.get("items_source", "")
                sub_steps = args.get("steps", [])
                
                # Resolve secrets & environment variables in the source path/string
                resolved_args = self.resolve_secrets({"src": items_source_raw}, local_env, target_env)
                items_source = resolved_args.get("src", "")

                print(f"[ORCHESTRATOR] Boucle Étape {step_num} sur '{loop_over}' (Source: {items_source})")
                if status_callback:
                    status_callback(step_num, "running", f"Démarrage de la boucle ({loop_over})...")

                # 1. Collect elements to iterate over
                items = []
                if loop_over == "variables":
                    items = [x.strip() for x in items_source.split(",") if x.strip()]
                elif loop_over == "files":
                    src_path = Path(items_source)
                    pattern = args.get("pattern", "*")
                    if src_path.exists() and src_path.is_dir():
                        candidates = [f for f in src_path.glob(pattern) if f.is_file()]
                        
                        # Récupérer les filtres
                        max_age_hours = args.get("max_age_hours")
                        min_age_hours = args.get("min_age_hours")
                        min_size_mb = args.get("min_size_mb")
                        max_size_mb = args.get("max_size_mb")
                        
                        filtered_files = []
                        now_ts = time.time()  # epoch timestamp locale (toujours comparée de manière homogène)
                        
                        for f in candidates:
                            stat = f.stat()
                            mtime = stat.st_mtime
                            size_bytes = stat.st_size
                            size_mb = size_bytes / (1024 * 1024)
                            
                            # Calcul de l'âge du fichier en heures
                            age_hours = (now_ts - mtime) / 3600.0
                            
                            # Filtre âge maximal
                            if max_age_hours is not None and max_age_hours != "" and str(max_age_hours).lower() != "none":
                                if age_hours > float(max_age_hours):
                                    continue
                                    
                            # Filtre âge minimal (ancienneté)
                            if min_age_hours is not None and min_age_hours != "" and str(min_age_hours).lower() != "none":
                                if age_hours < float(min_age_hours):
                                    continue
                                    
                            # Filtre taille minimale
                            if min_size_mb is not None and min_size_mb != "" and str(min_size_mb).lower() != "none":
                                if size_mb < float(min_size_mb):
                                    continue
                                    
                            # Filtre taille maximale
                            if max_size_mb is not None and max_size_mb != "" and str(max_size_mb).lower() != "none":
                                if size_mb > float(max_size_mb):
                                    continue
                                    
                            filtered_files.append(str(f.resolve()))
                        items = filtered_files
                    else:
                        print(f"[ORCHESTRATOR WARNING] Dossier source introuvable pour la boucle files : {items_source}")
                elif loop_over == "rows":
                    src_file = Path(items_source)
                    if src_file.exists():
                        ext = src_file.suffix.lower()
                        if ext == ".csv":
                            try:
                                import csv
                                with open(src_file, "r", encoding="utf-8-sig") as f:
                                    # Sniff delimiter
                                    sample = f.read(2048)
                                    f.seek(0)
                                    delim = ","
                                    for d in [";", ",", "\t", "|"]:
                                        if d in sample:
                                            delim = d
                                            break
                                    reader = csv.reader(f, delimiter=delim)
                                    headers = next(reader)
                                    headers = [h.strip().replace('"', '').replace("'", "") for h in headers]
                                    for row in reader:
                                        row_dict = {}
                                        for idx, h in enumerate(headers):
                                            val = row[idx] if idx < len(row) else ""
                                            row_dict[h] = val.strip()
                                        items.append(json.dumps(row_dict, ensure_ascii=False))
                            except Exception as csv_err:
                                print(f"[ORCHESTRATOR ERROR] Failed to read CSV for loop rows: {csv_err}")
                        elif ext == ".json":
                            try:
                                with open(src_file, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                if isinstance(data, list):
                                    items = [json.dumps(item, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item) for item in data]
                                elif isinstance(data, dict):
                                    items = [json.dumps(data, ensure_ascii=False)]
                            except Exception as json_err:
                                print(f"[ORCHESTRATOR ERROR] Failed to read JSON for loop rows: {json_err}")
                    else:
                        print(f"[ORCHESTRATOR WARNING] Fichier source introuvable pour la boucle rows : {items_source}")

                print(f"[ORCHESTRATOR] Boucle initialisée avec {len(items)} éléments à traiter.")

                # 2. Save existing ITER_ITEM keys to restore them later (for nested loops)
                previous_iter_keys = {}
                for k, v in list(self.execution_context.items()):
                    if k == "ITER_ITEM" or k.startswith("ITER_ITEM."):
                        previous_iter_keys[k] = v
                        del self.execution_context[k]

                loop_success = True
                try:
                    for idx, item in enumerate(items):
                        # Clear current iteration keys from context
                        for k in list(self.execution_context.keys()):
                            if k == "ITER_ITEM" or k.startswith("ITER_ITEM."):
                                del self.execution_context[k]
                                
                        iter_env = local_env.copy() if local_env else {}
                        self.execution_context["ITER_ITEM"] = item
                        
                        try:
                            parsed_item = json.loads(item)
                            if isinstance(parsed_item, dict):
                                for prop_k, prop_v in parsed_item.items():
                                    self.execution_context[f"ITER_ITEM.{prop_k}"] = str(prop_v)
                        except Exception:
                            pass

                        print(f"[ORCHESTRATOR] --- Itération {idx+1}/{len(items)} : ITER_ITEM={item} ---")
                        
                        sub_recipe = {
                            "plan_id": f"{plan_id}_loop_{step_num}_iter_{idx}",
                            "intent_analysis": f"Itération {idx} de l'étape {step_num}",
                            "steps": sub_steps,
                            "env": iter_env
                        }
                        
                        iter_success = await self.run_recipe(sub_recipe, status_callback, ask_user_callback, target_env)
                        if not iter_success:
                            print(f"[ORCHESTRATOR ERROR] L'itération {idx+1} a échoué.")
                            loop_success = False
                            break
                finally:
                    # Clean current iteration keys
                    for k in list(self.execution_context.keys()):
                        if k == "ITER_ITEM" or k.startswith("ITER_ITEM."):
                            del self.execution_context[k]
                    # Restore previous iteration keys
                    self.execution_context.update(previous_iter_keys)

                # 3. Handle status and performance telemetry
                step_end = time.perf_counter()
                status_str = "success" if loop_success else "error"
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Boucle {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": status_str
                }

                if loop_success:
                    completed_steps.add(step_num)
                    save_current_checkpoint()
                    if status_callback:
                        status_callback(step_num, "success", f"Boucle terminée avec succès ({len(items)} itérations).")
                else:
                    failed_steps.add(step_num)
                    if status_callback:
                        status_callback(step_num, "error", f"La boucle a échoué à l'itération {idx+1}.")

                step_events[step_num].set()
                return loop_success

            # 3. Injection des valeurs par défaut du registre
            prim_spec = self.validator.registry.get("primitives", {}).get(primitive, {})
            param_specs = prim_spec.get("parameters", {}).get("properties", {})
            for pname, pspec in param_specs.items():
                if pname not in args and "default" in pspec:
                    args[pname] = pspec["default"]

            # 4. Validation de l'étape de recette
            is_valid, err_msg = self.validator.validate_step(primitive, args)
            if not is_valid:
                METRICS.counter_inc("wfgy_validation_errors_total", {"primitive": primitive, "step": str(step_num)})
                print(f"[ERROR] Validation failed for Step {step_num}: {err_msg}")
                if status_callback:
                    status_callback(step_num, "error", f"Validation failed: {err_msg}")
                failed_steps.add(step_num)
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                    "duration_ms": 0,
                    "status": "error"
                }
                step_events[step_num].set()
                return False

            # Gestion des conflits pour io.copy
            if primitive == "io.copy":
                resolved_args = self.resolve_secrets(args, local_env, target_env)
                src = resolved_args.get("source")
                dest = resolved_args.get("destination")
                if src and dest:
                    src_path = Path(src)
                    dest_path = Path(dest)
                    resolved_dest = dest_path
                    is_dir = dest.endswith('/') or dest.endswith('\\') or (dest_path.exists() and dest_path.is_dir())
                    if is_dir and src_path.exists():
                        resolved_dest = dest_path / src_path.name
                    if resolved_dest.exists() and not args.get("conflict"):
                        if ask_user_callback:
                            if status_callback:
                                status_callback(step_num, "running", f"Conflit détecté pour '{resolved_dest.name}'. En attente de choix...")
                            choice = await ask_user_callback(step_num, str(resolved_dest))
                            args["conflict"] = choice

            # 4. Configuration des tentatives (Retry mechanism)
            retry_cfg = step_item.get("retry", {})
            attempts = retry_cfg.get("attempts", 1)
            delay = retry_cfg.get("delay_seconds", 1.0)
            if not isinstance(attempts, int) or attempts < 1:
                attempts = 1

            code = -1
            stdout = ""
            stderr = ""

            step_timeout = retry_cfg.get("timeout_seconds", 300)
            for attempt in range(1, attempts + 1):
                resolved_args = self.resolve_secrets(args, local_env, target_env)
                code, stdout, stderr = await self.bridge.execute(primitive, resolved_args, timeout_seconds=step_timeout)

                if code == 0:
                    break
                else:
                    print(f"[ORCHESTRATOR] Échec de l'étape {step_num} (tentative {attempt}/{attempts}) : {stderr.strip()}")
                    if attempt < attempts:
                        if status_callback:
                            status_callback(step_num, "retrying", f"Échec (tentative {attempt}/{attempts}). Réessai dans {delay}s...")
                        await asyncio.sleep(delay)

            # Traitement des sorties
            if stdout.strip():
                print(f"[RUST STDOUT] (Step {step_num}):\n{stdout.strip()}")
            if stderr.strip():
                print(f"[RUST STDERR] (Step {step_num}):\n{stderr.strip()}")

            if code != 0:
                METRICS.counter_inc("wfgy_step_failures_total", {"primitive": primitive, "code": str(code)})
                print(f"[ERROR] Step {step_num} failed after {attempts} attempts. Code: {code}")
                translated_error = ERROR_TRANSLATIONS.get(code, f"Erreur d'exécution inconnue (Code: {code})")
                if status_callback:
                    status_callback(step_num, "error", f"{translated_error} | Détails: {stderr.strip()}")
                failed_steps.add(step_num)
                step_end = time.perf_counter()
                step_performance[step_num] = {
                    "step": step_num,
                    "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                    "duration_ms": int((step_end - step_start) * 1000),
                    "status": "error"
                }
                self._save_to_dlq(plan_id, step_num, primitive, args, code, stderr, attempts)
                step_events[step_num].set()
                return False

            # Propagation du contexte io.metadata
            if primitive == "io.metadata" and code == 0:
                try:
                    meta = json.loads(stdout.strip())
                    self.execution_context["FILE_EXISTS"] = str(meta.get("exists", False)).lower()
                    self.execution_context["FILE_SIZE"] = meta.get("size_bytes", 0)
                    self.execution_context["IS_DIR"] = str(meta.get("is_dir", False)).lower()
                    print(f"[ORCHESTRATOR] Context updated by metadata: FILE_EXISTS={self.execution_context['FILE_EXISTS']}")
                except Exception as e:
                    print(f"[ORCHESTRATOR WARNING] Failed to parse metadata stdout: {e}")

            # Propagation du contexte data.metrics
            if primitive == "data.metrics" and code == 0:
                try:
                    json_line = None
                    for line in stdout.strip().split("\n"):
                        if line.strip().startswith("{") and "value" in line:
                            json_line = line.strip()
                            break
                    if json_line:
                        res = json.loads(json_line)
                        val = res.get("value")
                        dest_var = resolved_args.get("destination_variable")
                        if dest_var:
                            self.execution_context[dest_var] = val
                            print(f"[ORCHESTRATOR] Context updated by metric: {dest_var}={val}")
                except Exception as e:
                    print(f"[ORCHESTRATOR WARNING] Failed to parse metrics stdout: {e}")

            step_end = time.perf_counter()
            duration_ms = int((step_end - step_start) * 1000)
            METRICS.observe("wfgy_step_duration_seconds", duration_ms / 1000.0, {"primitive": primitive})
            METRICS.counter_inc("wfgy_steps_total", {"primitive": primitive, "status": "success"})
            step_performance[step_num] = {
                "step": step_num,
                "label": step_item.get("ui", {}).get("label") or f"Étape {step_num}",
                "duration_ms": duration_ms,
                "status": "success"
            }

            if status_callback:
                status_callback(step_num, "success", stdout.strip())

            completed_steps.add(step_num)
            save_current_checkpoint()
            step_events[step_num].set()
            return True

        # Lancement de toutes les étapes en tâches concurrentes
        tasks = [asyncio.create_task(run_single_step(step)) for step in steps]
        await asyncio.gather(*tasks)

        run_end = time.perf_counter()
        total_duration_ms = int((run_end - run_start) * 1000)

        # Nettoyer le checkpoint si le run s'est terminé avec succès
        if len(failed_steps) == 0:
            delete_checkpoint(plan_id)
            log.info("Checkpoint deleted after successful run", extra={"plan_id": plan_id})

        # Enregistrement de l'historique des runs
        try:
            import datetime
            run_record = {
                "run_id": f"run_{int(time.time())}",
                "workspace_id": plan_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error" if failed_steps else "success",
                "duration_ms": total_duration_ms,
                "steps": list(step_performance.values())
            }

            history_path = Path(__file__).parent / "run_history.json"
            history_data = []
            if history_path.exists():
                try:
                    with open(history_path, "r", encoding="utf-8") as f:
                        history_data = json.load(f)
                except Exception:
                    history_data = []

            history_data.insert(0, run_record)
            history_data = history_data[:100]

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)

            # --- JOURNAL D'AUDIT IMMUABLE (LOT B) ---
            audit_path = Path(__file__).parent / "audit_trail.json"
            audit_data = []
            if audit_path.exists():
                try:
                    with open(audit_path, "r", encoding="utf-8") as f:
                        audit_data = json.load(f)
                except Exception:
                    audit_data = []

            # Calcul du lineage pour le run courant
            recipe_lineage = self.get_data_lineage(recipe_data)

            audit_entry = {
                "run_id": run_record["run_id"],
                "workspace_id": plan_id,
                "timestamp": run_record["timestamp"],
                "username": self.execution_context.get("USERNAME", "unknown"),
                "hostname": self.execution_context.get("HOSTNAME", "localhost"),
                "os_name": self.execution_context.get("OS_NAME", "unknown"),
                "status": run_record["status"],
                "duration_ms": total_duration_ms,
                "steps_executed": [
                    {
                        "step": step_perf.get("step"),
                        "label": step_perf.get("label"),
                        "status": step_perf.get("status"),
                        "duration_ms": step_perf.get("duration_ms")
                    } for step_perf in step_performance.values()
                ],
                "data_lineage": {
                    f: {"producer": info["producer"], "consumers": info["consumers"]}
                    for f, info in recipe_lineage.items()
                }
            }

            audit_data.insert(0, audit_entry)
            audit_data = audit_data[:200]  # Limite d'audit de 200 entrées historiques

            with open(audit_path, "w", encoding="utf-8") as f:
                json.dump(audit_data, f, indent=2, ensure_ascii=False)

            from registry import broadcast
            asyncio.create_task(broadcast(json.dumps({
                "type": "RUN_HISTORY_UPDATE",
                "workspace_id": plan_id,
                "last_run": run_record
            }, ensure_ascii=False)))
            
            # Diffuser la mise à jour de l'audit
            asyncio.create_task(broadcast(json.dumps({
                "type": "AUDIT_TRAIL_UPDATE",
                "audit": audit_entry
            }, ensure_ascii=False)))
        except Exception as e:
            print(f"[ORCHESTRATOR WARNING] Failed to save run history: {e}")

        return len(failed_steps) == 0
from planner import RecipePlanner
from registry import load_workspaces_registry, save_workspaces_registry, broadcast, broadcast_workspaces_list, ACTIVE_CONNECTIONS
from scheduler import cron_scheduler_loop, directory_watcher_loop, handle_http_request, get_next_cron_execution

# WebSocket Server implementation
async def handler(websocket, path=None):
    orchestrator = Orchestrator()
    planner = RecipePlanner(ENV_CONFIG)
    current_recipe = None
    pending_confirmations = {}
    
    vault_key = os.environ.get("SECRET_VAULT_KEY") or ENV_CONFIG.get("SECRET_VAULT_KEY")
    if not vault_key:
        print("[CRITICAL SECURITY ERROR] SECRET_VAULT_KEY is not defined in environment variables.")
        sys.exit(1)
    
    # Extraire tenant_id depuis le token JWT dans l'URL (query string)
    # ws://host:8765/?token=xxx
    tenant_id = "default"
    if path and "token=" in path:
        import urllib.parse
        qs = urllib.parse.urlparse(path).query
        token = urllib.parse.parse_qs(qs).get("token", [None])[0]
        if token:
            payload = validate_token(token)
            if payload:
                tenant_id = payload.get("tenant_id", "default")
                print(f"[WS SERVER] Authenticated: {payload.get('username')} (tenant: {tenant_id})")
    
    vault = StealthVault(vault_key, tenant_id=tenant_id)
    saved_secrets = vault.load_secrets()
    
    ACTIVE_CONNECTIONS.add(websocket)
    METRICS.gauge_set("wfgy_active_connections", len(ACTIVE_CONNECTIONS))
    print(f"[WS SERVER] Client connected. Sending loaded vault secrets & workspace list...")
    try:
        await websocket.send(json.dumps({
            "type": "VAULT_SECRETS",
            "env": saved_secrets
        }))

        # Load active workspace immediately on connection
        registry = load_workspaces_registry()
        active_w = registry.get("active_workspace")
        if active_w and active_w in registry.get("workspaces", {}):
            w_info = registry["workspaces"][active_w]
            recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
            if recipe_path.exists():
                try:
                    with open(recipe_path, "r", encoding="utf-8") as f:
                        current_recipe = json.load(f)
                    if "env" not in current_recipe or not current_recipe["env"]:
                        current_recipe["env"] = saved_secrets
                except Exception as e:
                    print(f"[WS SERVER] Failed to read active recipe: {e}")

        # Send workspace list to UI
        workspaces = registry.get("workspaces", {})
        for w_id, w_info in workspaces.items():
            trig = w_info.get("trigger", {})
            if trig.get("enabled") and trig.get("type") == "cron":
                w_info["next_run"] = get_next_cron_execution(trig.get("cron_expression", ""))
            else:
                w_info["next_run"] = "N/A"

        await websocket.send(json.dumps({
            "type": "WORKSPACES_LIST",
            "active_workspace": active_w,
            "workspaces": workspaces
        }))

        if current_recipe:
            await websocket.send(json.dumps({
                "type": "PLAN_RECEIVED",
                "steps": current_recipe.get("steps", []),
                "plan_id": current_recipe.get("plan_id", "unknown"),
                "intent_analysis": current_recipe.get("intent_analysis", ""),
                "env": current_recipe.get("env", {})
            }))

        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                print(f"[WS SERVER] Received message type: {msg_type}")
            except json.JSONDecodeError:
                print(f"[WS SERVER] Received invalid JSON message: {message[:100]}...")
                await websocket.send(json.dumps({"type": "LOG", "message": "Invalid JSON format"}))
                continue

            if data.get("type") == "USER_CONFIRMATION_RESPONSE":
                step = data.get("step")
                choice = data.get("choice")
                if step in pending_confirmations:
                    try:
                        pending_confirmations[step].set_result(choice)
                    except asyncio.InvalidStateError:
                        pass
                continue

            if data.get("type") == "LIST_WORKSPACES":
                await broadcast_workspaces_list()
                continue

            if data.get("type") == "GET_SCHEMA":
                filepath = data.get("filepath", "")
                headers = extract_file_headers(filepath)
                await websocket.send(json.dumps({
                    "type": "SCHEMA_DETAILS",
                    "filepath": filepath,
                    "headers": headers
                }, ensure_ascii=False))
                continue

            if data.get("type") == "GET_PRIMITIVE_DOC":
                prim_name = data.get("primitive", "")
                registry_path = Path(__file__).parent / "registry.json"
                if registry_path.exists():
                    with open(registry_path, "r", encoding="utf-8") as f:
                        reg = json.load(f)
                    spec = reg.get("primitives", {}).get(prim_name, {})
                    await websocket.send(json.dumps({
                        "type": "PRIMITIVE_DOC",
                        "primitive": prim_name,
                        "description": spec.get("description", ""),
                        "parameters": spec.get("parameters", {})
                    }, ensure_ascii=False))
                else:
                    await websocket.send(json.dumps({
                        "type": "PRIMITIVE_DOC",
                        "primitive": prim_name,
                        "description": "",
                        "parameters": {}
                    }))
                continue

            if data.get("type") == "GET_RUN_HISTORY":
                history_path = Path(__file__).parent / "run_history.json"
                history_data = []
                if history_path.exists():
                    try:
                        with open(history_path, "r", encoding="utf-8") as f:
                            history_data = json.load(f)
                    except Exception as e:
                        print(f"[WS SERVER] Failed to read run history: {e}")
                await websocket.send(json.dumps({
                    "type": "RUN_HISTORY_RESULT",
                    "history": history_data
                }, ensure_ascii=False))
                continue

            if data.get("type") == "GET_AUDIT_TRAIL":
                audit_path = Path(__file__).parent / "audit_trail.json"
                audit_data = []
                if audit_path.exists():
                    try:
                        with open(audit_path, "r", encoding="utf-8") as f:
                            audit_data = json.load(f)
                    except Exception as e:
                        print(f"[WS SERVER] Failed to read audit trail: {e}")
                await websocket.send(json.dumps({
                    "type": "AUDIT_TRAIL_RESULT",
                    "audit": audit_data
                }, ensure_ascii=False))
                continue

            if data.get("type") == "GET_DATA_LINEAGE":
                # Compute lineage dynamically for current_recipe if active
                recipe_lineage = {}
                if current_recipe:
                    recipe_lineage = orchestrator.get_data_lineage(current_recipe)
                await websocket.send(json.dumps({
                    "type": "DATA_LINEAGE_RESULT",
                    "lineage": recipe_lineage
                }, ensure_ascii=False))
                continue

            if data.get("type") == "GET_DATA_PREVIEW":
                filepath = data.get("filepath", "")
                preview = extract_file_preview(filepath, max_rows=10)
                await websocket.send(json.dumps({
                    "type": "DATA_PREVIEW_RESULT",
                    "filepath": filepath,
                    "headers": preview.get("headers", []),
                    "rows": preview.get("rows", []),
                    "error": preview.get("error")
                }, ensure_ascii=False))
                continue

            if data.get("type") == "CREATE_WORKSPACE":
                name = data.get("name", "Nouveau Flux")
                w_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name.lower()).strip("_")
                registry = load_workspaces_registry()
                base_id = w_id or "workflow"
                counter = 1
                while w_id in registry.get("workspaces", {}) or not w_id:
                    w_id = f"{base_id}_{counter}"
                    counter += 1
                
                recipes_dir = Path(__file__).parent / "history_recipes"
                recipes_dir.mkdir(exist_ok=True)
                recipe_filename = f"recipe_{w_id}.json"
                recipe_filepath = recipes_dir / recipe_filename
                
                new_recipe = {
                    "plan_id": w_id,
                    "intent_analysis": f"Flux de travail: {name}",
                    "steps": [],
                    "env": {}
                }
                
                with open(recipe_filepath, "w", encoding="utf-8") as f:
                    json.dump(new_recipe, f, indent=2, ensure_ascii=False)
                
                registry["workspaces"][w_id] = {
                    "name": name,
                    "recipe_file": f"history_recipes/{recipe_filename}",
                    "created_at": datetime.datetime.now().isoformat(),
                    "last_run": None,
                    "trigger": {
                        "enabled": False,
                        "type": "none"
                    }
                }
                save_workspaces_registry(registry)
                await websocket.send(json.dumps({"type": "LOG", "message": f"Flux '{name}' créé avec succès."}))
                await websocket.send(json.dumps({
                    "type": "WORKSPACE_CREATED",
                    "workspace_id": w_id,
                    "name": name
                }))
                await broadcast_workspaces_list()
                continue

            if data.get("type") == "RENAME_WORKSPACE":
                w_id = data.get("workspace_id")
                new_name = data.get("new_name")
                registry = load_workspaces_registry()
                if w_id in registry.get("workspaces", {}):
                    registry["workspaces"][w_id]["name"] = new_name
                    save_workspaces_registry(registry)
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Flux renommé en '{new_name}'."}))
                    await broadcast_workspaces_list()
                continue

            if data.get("type") == "DELETE_WORKSPACE":
                w_id = data.get("workspace_id")
                registry = load_workspaces_registry()
                if w_id in registry.get("workspaces", {}):
                    w_info = registry["workspaces"][w_id]
                    recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
                    if recipe_path.exists():
                        try:
                            recipe_path.unlink()
                        except Exception as e:
                            print(f"[WS SERVER] Failed to delete recipe file: {e}")
                    del registry["workspaces"][w_id]
                    if registry.get("active_workspace") == w_id:
                        keys = list(registry["workspaces"].keys())
                        registry["active_workspace"] = keys[0] if keys else None
                    save_workspaces_registry(registry)
                    await websocket.send(json.dumps({"type": "LOG", "message": "Flux supprimé."}))
                    await broadcast_workspaces_list()
                continue

            if data.get("type") == "SELECT_WORKSPACE":
                w_id = data.get("workspace_id")
                registry = load_workspaces_registry()
                if w_id in registry.get("workspaces", {}):
                    registry["active_workspace"] = w_id
                    save_workspaces_registry(registry)
                    w_info = registry["workspaces"][w_id]
                    recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
                    
                    if recipe_path.exists():
                        try:
                            with open(recipe_path, "r", encoding="utf-8") as f:
                                current_recipe = json.load(f)
                            if "env" not in current_recipe or not current_recipe["env"]:
                                current_recipe["env"] = vault.load_secrets()
                        except Exception as e:
                            print(f"[WS SERVER] Failed to load recipe: {e}")
                            current_recipe = {"plan_id": w_id, "intent_analysis": w_info["name"], "steps": [], "env": {}}
                    else:
                        current_recipe = {"plan_id": w_id, "intent_analysis": w_info["name"], "steps": [], "env": {}}
                    
                    await websocket.send(json.dumps({
                        "type": "PLAN_RECEIVED",
                        "steps": current_recipe.get("steps", []),
                        "plan_id": current_recipe.get("plan_id", "unknown"),
                        "intent_analysis": current_recipe.get("intent_analysis", ""),
                        "env": current_recipe.get("env", {})
                    }))
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Flux '{w_info['name']}' sélectionné."}))
                    await broadcast_workspaces_list()
                continue

            if data.get("type") == "SAVE_WORKSPACE":
                recipe_data = data.get("recipe")
                registry = load_workspaces_registry()
                w_id = registry.get("active_workspace")
                if w_id and w_id in registry.get("workspaces", {}):
                    w_info = registry["workspaces"][w_id]
                    recipe_path = Path(__file__).parent / w_info.get("recipe_file", "")
                    recipe_data["env"] = vault.load_secrets()
                    current_recipe = recipe_data
                    try:
                        with open(recipe_path, "w", encoding="utf-8") as f:
                            json.dump(recipe_data, f, indent=2, ensure_ascii=False)
                        await websocket.send(json.dumps({"type": "LOG", "message": f"Flux '{w_info['name']}' sauvegardé."}))
                    except Exception as e:
                        await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur de sauvegarde: {e}"}))
                continue

            if data.get("type") == "UPDATE_WORKSPACE_TRIGGER":
                w_id = data.get("workspace_id")
                trigger_data = data.get("trigger", {})
                registry = load_workspaces_registry()
                if w_id in registry.get("workspaces", {}):
                    registry["workspaces"][w_id]["trigger"] = trigger_data
                    save_workspaces_registry(registry)
                    await websocket.send(json.dumps({"type": "LOG", "message": "Déclencheur mis à jour."}))
                    await broadcast_workspaces_list()
                continue

            if data.get("type") == "CLEAR_RECIPE":
                current_recipe = None
                await websocket.send(json.dumps({"type": "LOG", "message": "Workflow courant effacé."}))
                continue

            if data.get("type") == "SAVE_GLOBAL_SECRETS":
                global_secrets = data.get("secrets", {})
                vault.save_secrets(global_secrets)
                await websocket.send(json.dumps({"type": "LOG", "message": "Secrets enregistrés avec succès."}))
                await websocket.send(json.dumps({
                    "type": "VAULT_SECRETS",
                    "env": global_secrets
                }))
                continue

            if data.get("type") == "LOAD_RECIPE":
                current_recipe = data.get("recipe", {})
                steps = current_recipe.get("steps", [])
                if "env" not in current_recipe or not current_recipe["env"]:
                    current_recipe["env"] = vault.load_secrets()
                await websocket.send(json.dumps({
                    "type": "PLAN_RECEIVED",
                    "steps": steps,
                    "plan_id": current_recipe.get("plan_id", "unknown"),
                    "intent_analysis": f"Recette chargée : {current_recipe.get('intent_analysis', '')}",
                    "env": current_recipe.get("env", {})
                }))
                await websocket.send(json.dumps({"type": "LOG", "message": "Recette chargée."}))
                continue

            if data.get("type") == "UPDATE_LLM_SETTINGS":
                prov = data.get("provider")
                mdl = data.get("model")
                url = data.get("base_url")
                planner.client = None
                new_cfg = {
                    "LLM_PROVIDER": prov,
                    "LLM_MODEL": mdl,
                    "LLM_BASE_URL": url,
                    "LLM_API_KEY": ENV_CONFIG.get("LLM_API_KEY")
                }
                try:
                    planner.__init__(new_cfg)
                    await websocket.send(json.dumps({
                        "type": "LOG",
                        "message": f"[IA CONFIG] Modèle basculé avec succès sur '{mdl}' ({prov})."
                    }))
                except Exception as config_err:
                    await websocket.send(json.dumps({
                        "type": "LOG",
                        "message": f"[IA CONFIG ERROR] Échec du rechargement IA : {config_err}"
                    }))
                continue

            if data.get("type") == "SUBMIT_INTENT":
                intent = data.get("intent", "")
                mode_etude = data.get("study_mode", False)
                if mode_etude:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"[ETUDE] Démarrage de l'analyse d'intention..."}))
                    try:
                        study_res = planner.study(intent)
                        await websocket.send(json.dumps({
                            "type": "STUDY_QUESTIONS",
                            "analysis": study_res.get("analysis", ""),
                            "questions": study_res.get("questions", []),
                            "original_intent": intent
                        }))
                    except Exception as study_err:
                        await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur d'analyse d'étude : {study_err}"}))
                    continue
                
                await websocket.send(json.dumps({"type": "LOG", "message": f"Intent received. Planning..."}))
                try:
                    recipe = planner.plan(intent, current_recipe)
                    steps = recipe.get("steps", [])
                    if steps:
                        current_recipe = recipe
                        current_recipe["env"] = vault.load_secrets()
                        
                        # Auto-save to historical timestamped file
                        try:
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            history_dir = Path("history_recipes")
                            history_dir.mkdir(exist_ok=True)
                            filename = f"recipe_{timestamp}.json"
                            with open(history_dir / filename, "w", encoding="utf-8") as f:
                                json.dump(current_recipe, f, indent=2, ensure_ascii=False)
                            await websocket.send(json.dumps({
                                "type": "LOG",
                                "message": f"[PERSISTANCE] Recette sauvegardée sous '{history_dir}/{filename}'."
                            }))
                        except Exception as save_err:
                            print(f"[WS SERVER] Auto-save failed: {save_err}")
                    
                    await websocket.send(json.dumps({
                        "type": "PLAN_RECEIVED",
                        "steps": steps,
                        "plan_id": recipe.get("plan_id", "unknown"),
                        "intent_analysis": recipe.get("intent_analysis", "No plan created"),
                        "env": current_recipe.get("env", {})
                    }))
                except Exception as planner_err:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Planning Error: {planner_err}"}))
                continue

            if data.get("type") == "SUBMIT_STUDY_CHAT":
                intent = data.get("original_intent", "")
                chat_history = data.get("chat_history", [])
                await websocket.send(json.dumps({"type": "LOG", "message": "[ETUDE] Prise en compte de vos réponses..."}))
                try:
                    study_res = planner.study(intent, chat_history)
                    await websocket.send(json.dumps({
                        "type": "STUDY_QUESTIONS",
                        "analysis": study_res.get("analysis", ""),
                        "questions": study_res.get("questions", []),
                        "original_intent": intent
                    }))
                except Exception as err:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur : {err}"}))
                continue

            if data.get("type") == "GENERATE_STUDY_RECIPE":
                intent = data.get("original_intent", "")
                chat_history = data.get("chat_history", [])
                await websocket.send(json.dumps({"type": "LOG", "message": "[ETUDE] Alignement validé. Génération..."}))
                try:
                    full_intent = f"Intention : {intent}\n\nAlignement & Clarifications :\n"
                    for msg in chat_history:
                        full_intent += f"- {msg.get('role').upper()}: {msg.get('content')}\n"
                    recipe = planner.plan(full_intent, current_recipe)
                    steps = recipe.get("steps", [])
                    if steps:
                        current_recipe = recipe
                        current_recipe["env"] = vault.load_secrets()
                        try:
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            history_dir = Path("history_recipes")
                            history_dir.mkdir(exist_ok=True)
                            filename = f"recipe_{timestamp}.json"
                            with open(history_dir / filename, "w", encoding="utf-8") as f:
                                json.dump(current_recipe, f, indent=2, ensure_ascii=False)
                        except Exception as save_err:
                            print(f"[WS SERVER] Auto-save failed: {save_err}")
                    await websocket.send(json.dumps({
                        "type": "PLAN_RECEIVED",
                        "steps": steps,
                        "plan_id": recipe.get("plan_id", "unknown"),
                        "intent_analysis": recipe.get("intent_analysis", "No plan created"),
                        "env": current_recipe.get("env", {})
                    }))
                    await websocket.send(json.dumps({"type": "LOG", "message": "Recette finale générée."}))
                except Exception as planner_err:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur de génération : {planner_err}"}))
                continue

            if data.get("type") == "RUN_RECIPE":
                recipe_to_run = data.get("recipe", current_recipe)
                target_env = data.get("target_env", "dev")
                if not recipe_to_run or not recipe_to_run.get("steps"):
                    await websocket.send(json.dumps({"type": "LOG", "message": "Erreur : aucune recette active."}))
                    continue
                current_recipe = recipe_to_run
                if "env" in recipe_to_run:
                    vault.save_secrets(recipe_to_run["env"])
                
                await websocket.send(json.dumps({"type": "LOG", "message": f"Exécution en cours en mode {target_env.upper()}..."}))
                try:
                    def status_update(step_num, status, log_message):
                        asyncio.create_task(websocket.send(json.dumps({
                            "type": "STEP_STATUS",
                            "step": step_num,
                            "status": status,
                            "log": log_message
                        })))

                    async def ask_user(step_num, filepath):
                        loop = asyncio.get_running_loop()
                        fut = loop.create_future()
                        pending_confirmations[step_num] = fut
                        await websocket.send(json.dumps({
                            "type": "USER_CONFIRMATION_REQUIRED",
                            "step": step_num,
                            "message": f"Le fichier '{Path(filepath).name}' existe déjà. Action :",
                            "options": [
                                {"value": "overwrite", "label": "Écraser"},
                                {"value": "skip", "label": "Ignorer"},
                                {"value": "newer", "label": "Plus récent uniquement"}
                            ]
                        }))
                        try:
                            choice = await asyncio.wait_for(fut, timeout=120.0)
                        except asyncio.TimeoutError:
                            await websocket.send(json.dumps({
                                "type": "LOG",
                                "message": f"Timeout pour l'étape {step_num}. Option 'Ignorer' sélectionnée."
                            }))
                            choice = "skip"
                        finally:
                            if step_num in pending_confirmations:
                                del pending_confirmations[step_num]
                        return choice

                    success = await orchestrator.run_recipe(
                        recipe_to_run, 
                        status_update,
                        ask_user,
                        target_env=target_env
                    )
                    await websocket.send(json.dumps({
                        "type": "PLAN_FINISHED",
                        "success": success
                    }))
                except Exception as exec_err:
                    await websocket.send(json.dumps({
                        "type": "LOG", 
                        "message": f"Execution Error: {exec_err}"
                    }))
                    await websocket.send(json.dumps({
                        "type": "PLAN_FINISHED",
                        "success": False
                    }))
                continue

    except websockets.exceptions.ConnectionClosedOK:
        print("[WS SERVER] Connection closed normally.")
    except Exception as e:
        print(f"[WS SERVER] Error: {e}")
    finally:
        ACTIVE_CONNECTIONS.discard(websocket)
        METRICS.gauge_set("wfgy_active_connections", len(ACTIVE_CONNECTIONS))
        print("[WS SERVER] Cleaning up pending confirmations...")
        for step_num, fut in list(pending_confirmations.items()):
            if not fut.done():
                fut.cancel()
        pending_confirmations.clear()

async def main():
    vault_key = os.environ.get("SECRET_VAULT_KEY") or ENV_CONFIG.get("SECRET_VAULT_KEY")
    if not vault_key:
        log.critical("SECRET_VAULT_KEY not configured — aborting")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        port = int(ENV_CONFIG.get("PORT", 8765))
        ssl_cert = ENV_CONFIG.get("SSL_CERT")
        ssl_key = ENV_CONFIG.get("SSL_KEY")
        ssl_context = None
        if ssl_cert and ssl_key:
            import ssl
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(ssl_cert, ssl_key)
            log.info("SSL enabled", extra={"cert": ssl_cert})
        
        import logging
        logging.getLogger("websockets").setLevel(logging.WARNING)
        proto = "wss" if ssl_context else "ws"
        log.info("Starting WebSocket server", extra={"port": port, "env": env_mode, "proto": proto})
        
        async with websockets.serve(handler, "0.0.0.0", port, ssl=ssl_context):
            log.info(f"WebSocket ready on {proto}://0.0.0.0:{port}")
            
            http_port = int(ENV_CONFIG.get("HTTP_PORT", 8766))
            log.info("Starting HTTP webhook server", extra={"port": http_port})
            http_server = await asyncio.start_server(handle_http_request, "0.0.0.0", http_port)
            log.info(f"HTTP ready on http://0.0.0.0:{http_port}")
            
            asyncio.create_task(cron_scheduler_loop())
            asyncio.create_task(directory_watcher_loop())
            
            await asyncio.Future()
    else:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  Run recipe:  python orchestrator.py <recipe_json_file_path>")
            print("  Start server: python orchestrator.py --server")
            sys.exit(1)

        recipe_path = Path(sys.argv[1])
        if not recipe_path.exists():
            print(f"Error: Recipe file '{recipe_path}' not found.")
            sys.exit(1)

        try:
            with open(recipe_path, "r", encoding="utf-8") as f:
                recipe = json.load(f)
        except Exception as e:
            print(f"Error reading recipe file: {e}")
            sys.exit(1)

        orchestrator = Orchestrator()
        success = await orchestrator.run_recipe(recipe)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting orchestrator.")
