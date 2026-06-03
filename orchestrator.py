# [WFGY] Zone: SAFE | λ: 0.1 | Action: Python orchestrator with WebSocket server & Env loading
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Dynamically add Chromatix path to sys.path
sys.path.append(str(Path("d:/image_to_text/chromatix")))

try:
    from chromatix_cps.core import CPSPacket
    from PIL import Image
    HAS_CHROMATIX = True
    print("[STEALTH VAULT] Chromatix Pixel Standard Engine successfully loaded.")
except ImportError:
    HAS_CHROMATIX = False
    print("[STEALTH VAULT] Chromatix Engine not found. Running in legacy flat-file fallback mode.")

class StealthVault:
    """
    Stealth Vault that encrypts and stores flow secrets inside a Chromatix PNG image.
    """
    def __init__(self, key: str):
        self.key = key or "default-stealth-key-99"
        self.vault_path = Path(__file__).parent / "etl_vault.png"
        self.fallback_path = Path(__file__).parent / "etl_vault.json"

    def save_secrets(self, env_data: dict) -> bool:
        try:
            raw_bytes = json.dumps(env_data, ensure_ascii=False).encode('utf-8')
            if HAS_CHROMATIX:
                cps = CPSPacket(self.key)
                img = cps.encode_raw_bytes(raw_bytes, epoch_id=999)
                img.save(self.vault_path)
                print(f"[STEALTH VAULT] Secrets successfully hidden inside '{self.vault_path.name}'.")
                # Remove fallback json if it exists for extra security
                if self.fallback_path.exists():
                    self.fallback_path.unlink()
                return True
            else:
                # Flat-file backup fallback (warning: raw text format)
                with open(self.fallback_path, "w", encoding="utf-8") as f:
                    json.dump(env_data, f, indent=2, ensure_ascii=False)
                print(f"[STEALTH VAULT] Legacy mode: Secrets saved in plaintext to '{self.fallback_path.name}'.")
                return True
        except Exception as e:
            print(f"[STEALTH VAULT ERROR] Failed to save secrets: {e}")
            return False

    def load_secrets(self) -> dict:
        try:
            if HAS_CHROMATIX and self.vault_path.exists():
                cps = CPSPacket(self.key)
                img = Image.open(self.vault_path)
                decoded_bytes = cps.decode_raw_bytes(img, epoch_id=999)
                return json.loads(decoded_bytes.decode('utf-8'))
            elif self.fallback_path.exists():
                with open(self.fallback_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[STEALTH VAULT ERROR] Failed to load secrets: {e}")
        return {"dev": {}, "test": {}, "prod": {}}

# Try to import jsonschema for advanced validation, fallback to manual if not present
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

def load_env(env_name="dev"):
    """
    Rudimentary .env parser to avoid extra dependency like python-dotenv.
    """
    root_dir = Path(__file__).parent
    filename = ".env.test" if env_name == "test" else ".env"
    env_path = root_dir / filename
    
    config = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    return config

# Load environment configuration
env_mode = os.environ.get("WFGY_ENV", "dev")
ENV_CONFIG = load_env(env_mode)

class WorkerBridge:
    """
    Bridge responsible for executing Rust Muscle primitives.
    """
    def __init__(self, binary_path: str = None):
        root_dir = Path(__file__).parent
        # Prioritize path from .env configuration
        env_bin_path = ENV_CONFIG.get("RUST_BIN_PATH")
        
        if binary_path:
            self.binary_path = Path(binary_path)
        elif env_bin_path:
            self.binary_path = Path(env_bin_path)
        else:
            exe_ext = ".exe" if os.name == "nt" else ""
            debug_bin = root_dir / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
            if debug_bin.exists():
                self.binary_path = debug_bin
            else:
                self.binary_path = None

    async def execute(self, primitive_name: str, args: dict) -> tuple[int, str, str]:
        """
        Executes a primitive by calling the Rust binary or falling back to cargo run.
        """
        if self.binary_path and self.binary_path.exists():
            cmd = [str(self.binary_path), primitive_name]
        else:
            root_dir = Path(__file__).parent
            cargo_toml = root_dir / "rust_muscle" / "Cargo.toml"
            cmd = ["cargo", "run", "--manifest-path", str(cargo_toml), "--", primitive_name]

        for key, value in args.items():
            # Standardize parameters from snake_case to kebab-case
            kebab_key = key.replace("_", "-")
            
            # Format booleans as lowercase string for Rust parser compatibility (True -> "true")
            if isinstance(value, bool):
                val_str = str(value).lower()
            else:
                val_str = str(value)
                
            cmd.extend([f"--{kebab_key}", val_str])

        print(f"[ORCHESTRATOR] Executing: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')

class SchemaValidator:
    """
    Validates recipes against the registry definition.
    """
    def __init__(self, registry_path: Path):
        with open(registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def validate_step(self, primitive_name: str, args: dict) -> tuple[bool, str]:
        if primitive_name not in self.registry.get("primitives", {}):
            return False, f"Primitive '{primitive_name}' not defined in registry."

        spec = self.registry["primitives"][primitive_name]
        schema = spec.get("parameters", {})

        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=args, schema=schema)
                return True, ""
            except jsonschema.ValidationError as e:
                return False, f"Validation error: {e.message}"
        else:
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            
            for req in required:
                if req not in args:
                    return False, f"Missing required parameter: '{req}'"

            for key, val in args.items():
                if key not in properties:
                    return False, f"Unexpected parameter: '{key}'"
                
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(val, str):
                    return False, f"Parameter '{key}' should be a string, got {type(val).__name__}"
                
                enum_vals = properties[key].get("enum")
                if enum_vals and val not in enum_vals:
                    return False, f"Parameter '{key}' has invalid value '{val}'. Must be one of {enum_vals}"

            return True, ""

# International Error Translation Mapping for Rust exit codes
ERROR_TRANSLATIONS = {
    1: "Erreur système générique ou argument invalide.",
    2: "Le fichier ou dossier source spécifié est introuvable.",
    3: "Permission refusée : accès interdit en lecture ou en écriture.",
    4: "Impossible de créer le répertoire cible de destination.",
    5: "Échec du déplacement physique inter-disques (le secours par copie a échoué).",
    6: "Impossible de déplacer l'élément dans la corbeille locale.",
    7: "Erreur réseau (téléchargement ou téléversement impossible)."
}

class Orchestrator:
    """
    Main Orchestrator coordinating flow recipes.
    """
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.validator = SchemaValidator(self.root_dir / "registry.json")
        self.bridge = WorkerBridge()
        self.execution_context = {}

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
                    # Priorité: 1. local execution_context, 2. local_env[target_env], 3. ENV_CONFIG, 4. OS env
                    val = self.execution_context.get(var_name)
                    if val is None:
                        val = env_vars.get(var_name)
                    if val is None:
                        val = local_env.get(var_name)
                    if val is None:
                        val = ENV_CONFIG.get(var_name, os.environ.get(var_name, f"${{{var_name}}}"))
                    
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

    async def run_recipe(self, recipe_data: dict, status_callback=None, ask_user_callback=None, target_env: str = "dev") -> bool:
        plan_id = recipe_data.get("plan_id", "unknown")
        intent = recipe_data.get("intent_analysis", "No intent specified")
        steps = recipe_data.get("steps", [])
        local_env = recipe_data.get("env", {})

        print(f"=== Starting Plan Execution ({target_env.upper()}): {plan_id} ===")
        print(f"User Intent: {intent}")
        print("==========================================")

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
                    err_msg = f"Détection de cycle de dépendances dans la recette (autour de l'étape {step_num})"
                    print(f"[ORCHESTRATOR ERROR] {err_msg}")
                    return False

        # 2. Préparation des structures de contrôle asynchrones
        step_events = {step.get("step"): asyncio.Event() for step in steps}
        failed_steps = set()
        completed_steps = set()

        async def run_single_step(step_item):
            step_num = step_item.get("step")
            primitive = step_item.get("primitive")
            args = step_item.get("args", {})
            dep_list = parents.get(step_num, [])

            # Attente de tous les parents
            for pid in dep_list:
                if pid in step_events:
                    await step_events[pid].wait()
                    if pid in failed_steps:
                        failed_steps.add(step_num)
                        step_events[step_num].set()
                        return False
                else:
                    # Parent non déclaré dans la recette, on continue
                    pass

            if failed_steps:
                failed_steps.add(step_num)
                step_events[step_num].set()
                return False

            if status_callback:
                status_callback(step_num, "running", f"Exécution de l'étape ({target_env.upper()})...")

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
                        step_events[step_num].set()
                        return False
                completed_steps.add(step_num)
                step_events[step_num].set()
                return True

            # 3. Validation de l'étape de recette
            is_valid, err_msg = self.validator.validate_step(primitive, args)
            if not is_valid:
                print(f"[ERROR] Validation failed for Step {step_num}: {err_msg}")
                if status_callback:
                    status_callback(step_num, "error", f"Validation failed: {err_msg}")
                failed_steps.add(step_num)
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

            for attempt in range(1, attempts + 1):
                resolved_args = self.resolve_secrets(args, local_env, target_env)
                code, stdout, stderr = await self.bridge.execute(primitive, resolved_args)

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
                print(f"[ERROR] Step {step_num} failed after {attempts} attempts. Code: {code}")
                if status_callback:
                    translated_error = ERROR_TRANSLATIONS.get(code, f"Erreur d'exécution inconnue (Code: {code})")
                    status_callback(step_num, "error", f"{translated_error} | Détails: {stderr.strip()}")
                failed_steps.add(step_num)
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

            if status_callback:
                status_callback(step_num, "success", stdout.strip())

            completed_steps.add(step_num)
            step_events[step_num].set()
            return True

        # Lancement de toutes les étapes en tâches concurrentes
        tasks = [asyncio.create_task(run_single_step(step)) for step in steps]
        await asyncio.gather(*tasks)

        if failed_steps:
            print(f"Plan Execution Failed. Failed steps: {failed_steps}")
            return False

        print("Plan Executed Successfully.")
        return True

from planner import RecipePlanner

# WebSocket Server implementation
async def handler(websocket, path=None):
    orchestrator = Orchestrator()
    planner = RecipePlanner(ENV_CONFIG)
    current_recipe = None
    pending_confirmations = {}
    
    # Instantiate the Stealth Vault using the master key from ENV
    vault_key = ENV_CONFIG.get("SECRET_API_KEY") or os.environ.get("SECRET_API_KEY", "wfgy-default-vault-key-12345")
    vault = StealthVault(vault_key)
    
    # Load initially saved secrets
    saved_secrets = vault.load_secrets()
    
    print(f"[WS SERVER] Client connected. Sending loaded vault secrets...")
    try:
        # Send initially loaded secrets to UI immediately on connect
        await websocket.send(json.dumps({
            "type": "VAULT_SECRETS",
            "env": saved_secrets
        }))

        async for message in websocket:
            print(f"[WS SERVER] Received message: {message}")
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
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

            if data.get("type") == "CLEAR_RECIPE":
                current_recipe = None
                await websocket.send(json.dumps({"type": "LOG", "message": "Workflow courant effacé."}))
                continue

            if data.get("type") == "SAVE_GLOBAL_SECRETS":
                global_secrets = data.get("secrets", {})
                vault.save_secrets(global_secrets)
                await websocket.send(json.dumps({"type": "LOG", "message": "Secrets enregistrés avec succès dans le coffre-fort."}))
                # Diffuser la mise à jour des secrets à l'application
                await websocket.send(json.dumps({
                    "type": "VAULT_SECRETS",
                    "env": global_secrets
                }))
                continue

            if data.get("type") == "LOAD_RECIPE":
                current_recipe = data.get("recipe", {})
                steps = current_recipe.get("steps", [])
                
                # Merge local vault secrets into the loaded recipe if not present
                if "env" not in current_recipe or not current_recipe["env"]:
                    current_recipe["env"] = vault.load_secrets()

                await websocket.send(json.dumps({
                    "type": "PLAN_RECEIVED",
                    "steps": steps,
                    "plan_id": current_recipe.get("plan_id", "unknown"),
                    "intent_analysis": f"Recette chargée : {current_recipe.get('intent_analysis', '')}",
                    "env": current_recipe.get("env", {})
                }))
                await websocket.send(json.dumps({"type": "LOG", "message": "Recette chargée avec succès."}))
                continue

            if data.get("type") == "SUBMIT_INTENT":
                intent = data.get("intent", "")
                mode_etude = data.get("study_mode", False)
                
                if mode_etude:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"[ETUDE] Démarrage de l'analyse d'intention en mode étude..."}))
                    try:
                        study_res = planner.study(intent)
                        print(f"[WS SERVER] Study result: {study_res}")
                        await websocket.send(json.dumps({
                            "type": "STUDY_QUESTIONS",
                            "analysis": study_res.get("analysis", ""),
                            "questions": study_res.get("questions", []),
                            "original_intent": intent
                        }))
                    except Exception as study_err:
                        print(f"[WS SERVER] Study mode error: {study_err}")
                        await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur d'analyse d'étude : {study_err}"}))
                    continue
                
                await websocket.send(json.dumps({"type": "LOG", "message": f"Intent received: '{intent}'. Planning..."}))
                
                try:
                    # Dynamic Recipe Planner using LLM
                    recipe = planner.plan(intent, current_recipe)
                    print(f"[WS SERVER] Recipe generated:\n{json.dumps(recipe, indent=2, ensure_ascii=False)}")
                    steps = recipe.get("steps", [])
                    
                    if steps:
                        current_recipe = recipe  # Maintain workflow state
                        # Initialiser l'environnement avec les secrets du coffre-fort
                        current_recipe["env"] = vault.load_secrets()
                    
                    # Send generated plan to JS for node rendering
                    await websocket.send(json.dumps({
                        "type": "PLAN_RECEIVED",
                        "steps": steps,
                        "plan_id": recipe.get("plan_id", "unknown"),
                        "intent_analysis": recipe.get("intent_analysis", "No plan created"),
                        "env": current_recipe.get("env", {})
                    }))
                    
                except Exception as planner_err:
                    print(f"[WS SERVER] Planning error: {planner_err}")
                    await websocket.send(json.dumps({
                        "type": "LOG", 
                        "message": f"Planning Error: {planner_err}"
                     }))
                continue

            if data.get("type") == "SUBMIT_STUDY_CHAT":
                intent = data.get("original_intent", "")
                chat_history = data.get("chat_history", [])
                
                await websocket.send(json.dumps({"type": "LOG", "message": "[ETUDE] Prise en compte de vos réponses par l'IA..."}))
                try:
                    # Relancer study avec l'historique pour affiner ou générer de nouvelles questions
                    study_res = planner.study(intent, chat_history)
                    print(f"[WS SERVER] Next study phase: {study_res}")
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
                
                await websocket.send(json.dumps({"type": "LOG", "message": "[ETUDE] Alignement validé. Génération de la recette finale..."}))
                try:
                    # Concaténer l'intention d'origine avec l'historique des réponses d'alignement pour le planneur final
                    full_intent = f"Intention : {intent}\n\nAlignement & Clarifications :\n"
                    for msg in chat_history:
                        full_intent += f"- {msg.get('role').upper()}: {msg.get('content')}\n"
                    
                    recipe = planner.plan(full_intent, current_recipe)
                    steps = recipe.get("steps", [])
                    if steps:
                        current_recipe = recipe
                        current_recipe["env"] = vault.load_secrets()
                    
                    await websocket.send(json.dumps({
                        "type": "PLAN_RECEIVED",
                        "steps": steps,
                        "plan_id": recipe.get("plan_id", "unknown"),
                        "intent_analysis": recipe.get("intent_analysis", "No plan created"),
                        "env": current_recipe.get("env", {})
                    }))
                    await websocket.send(json.dumps({"type": "LOG", "message": "Recette finale générée et rendue sur le graphe."}))
                except Exception as planner_err:
                    await websocket.send(json.dumps({"type": "LOG", "message": f"Erreur de génération : {planner_err}"}))
                continue

            if data.get("type") == "RUN_RECIPE":
                recipe_to_run = data.get("recipe", current_recipe)
                target_env = data.get("target_env", "dev")
                if not recipe_to_run or not recipe_to_run.get("steps"):
                    await websocket.send(json.dumps({"type": "LOG", "message": "Erreur : aucune recette active à exécuter."}))
                    continue
                
                # Conserver la recette exécutée en mémoire locale
                current_recipe = recipe_to_run

                # Persist the environment variables/secrets back to the Chromatix PNG Vault
                if "env" in recipe_to_run:
                    vault.save_secrets(recipe_to_run["env"])

                await websocket.send(json.dumps({"type": "LOG", "message": f"Lancement de l'exécution du workflow en mode {target_env.upper()}..."}))
                try:
                    def status_update(step_num, status, log_message):
                        # Schedule sending status update without blocking caller
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
                        
                        # Send confirmation request to frontend
                        await websocket.send(json.dumps({
                            "type": "USER_CONFIRMATION_REQUIRED",
                            "step": step_num,
                            "message": f"Le fichier '{Path(filepath).name}' existe déjà dans la destination ({target_env.upper()}). Choisissez une action :",
                            "options": [
                                {"value": "overwrite", "label": "Écraser"},
                                {"value": "skip", "label": "Ignorer le fichier"},
                                {"value": "newer", "label": "Plus récent uniquement"}
                            ]
                        }))
                        
                        try:
                            # 120 seconds timeout before defaulting to skip
                            choice = await asyncio.wait_for(fut, timeout=120.0)
                        except asyncio.TimeoutError:
                            print(f"[WS SERVER] Timeout waiting for user choice on step {step_num}. Defaulting to 'skip'.")
                            await websocket.send(json.dumps({
                                "type": "LOG",
                                "message": f"Pas de réponse après 120s pour l'étape {step_num}. Option 'Ignorer' sélectionnée par défaut."
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
                    print(f"[WS SERVER] Execution error: {exec_err}")
                    await websocket.send(json.dumps({
                        "type": "LOG", 
                        "message": f"Execution Error: {exec_err}"
                    }))
                    await websocket.send(json.dumps({
                        "type": "PLAN_FINISHED",
                        "success": False
                    }))

    except websockets.exceptions.ConnectionClosedOK:
        print("[WS SERVER] Connection closed normally.")
    except Exception as e:
        print(f"[WS SERVER] Error: {e}")
    finally:
        # Cancel all pending futures to prevent hanging on connection drop
        print("[WS SERVER] Cleaning up pending confirmations...")
        for step_num, fut in list(pending_confirmations.items()):
            if not fut.done():
                fut.cancel()
        pending_confirmations.clear()

async def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        port = int(ENV_CONFIG.get("PORT", 8765))
        print(f"[WS SERVER] Starting WebSocket server on port {port} in '{env_mode}' mode...")
        async with websockets.serve(handler, "localhost", port):
            await asyncio.Future()  # Keep running forever
    else:
        # Standard CLI Recipe File run
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
        success = orchestrator.run_recipe(recipe)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting orchestrator.")
