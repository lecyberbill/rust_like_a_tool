# [WFGY] Zone: SAFE | λ: 0.3 | Action: AI inference helper script supporting summarize and extract modes
import os
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set path for relative imports
sys.path.append(str(Path(__file__).parent))

from llm_client import OpenAICompatibleClient, GeminiAPIClient
from vault import StealthVault

def load_env(env_name="dev"):
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

def get_llm_client(args, env_config):
    # Resolve API Key
    vault_key = os.environ.get("SECRET_VAULT_KEY") or env_config.get("SECRET_VAULT_KEY")
    vault_secrets = {}
    if vault_key:
        try:
            vault = StealthVault(vault_key)
            vault_secrets = vault.load_secrets()
        except Exception as e:
            print(f"[AI HELPER WARNING] Failed to load vault secrets: {e}", file=sys.stderr)

    env_mode = os.environ.get("WFGY_ENV", "dev")
    env_vars = vault_secrets.get(env_mode, {})

    provider = args.model_provider or env_config.get("LLM_PROVIDER") or "openai_compatible"
    model = args.model_id or env_config.get("LLM_MODEL") or "gemma"
    base_url = args.base_url or env_config.get("LLM_BASE_URL") or "http://localhost:1234/v1"
    api_key = env_vars.get("LLM_API_KEY") or os.environ.get("LLM_API_KEY") or env_config.get("LLM_API_KEY") or "unused"

    print(f"[AI HELPER] Initializing LLM client: Provider={provider}, Model={model}", file=sys.stderr)

    if provider == "gemini":
        return GeminiAPIClient(api_key=api_key, model=model)
    else:
        return OpenAICompatibleClient(base_url=base_url, model=model, api_key=api_key)

def process_row(client, mode, text, prompt, schema_dict, index):
    if not text:
        return index, {} if mode == "extract" else ""

    if mode == "summarize":
        system_prompt = prompt or "Tu es un assistant d'analyse de données. Résume le texte suivant de manière très concise."
        user_prompt = text
        try:
            response = client.generate_completion(system_prompt, user_prompt)
            return index, response.strip()
        except Exception as e:
            print(f"[AI HELPER ERROR] Failed processing row {index}: {e}", file=sys.stderr)
            return index, f"Error: {e}"

    elif mode == "extract":
        system_prompt = prompt or "Tu es un extracteur d'informations structurées précis. Extrais les champs demandés du texte utilisateur sous forme d'objet JSON valide."
        user_prompt = f"Texte à analyser :\n{text}\n\nExtrais les informations sous forme de JSON correspondant à ce schéma :\n{json.dumps(schema_dict)}"
        try:
            response = client.generate_completion(system_prompt, user_prompt, schema=schema_dict)
            # Parse response as JSON
            clean_res = response.strip()
            # Handle potential markdown code block backticks
            if clean_res.startswith("```json"):
                clean_res = clean_res[7:]
            if clean_res.startswith("```"):
                clean_res = clean_res[3:]
            if clean_res.endswith("```"):
                clean_res = clean_res[:-3]
            clean_res = clean_res.strip()
            
            parsed = json.loads(clean_res)
            return index, parsed
        except Exception as e:
            print(f"[AI HELPER ERROR] Failed extracting from row {index}: {e}", file=sys.stderr)
            return index, {}

def read_data(filepath):
    path = Path(filepath)
    ext = path.suffix.lower()
    if ext == ".csv":
        import csv
        with open(path, "r", encoding="utf-8-sig") as f:
            sample = f.read(2048)
            f.seek(0)
            delim = ","
            for d in [";", ",", "\t", "|"]:
                if d in sample:
                    delim = d
                    break
            reader = csv.DictReader(f, delimiter=delim)
            headers = reader.fieldnames or []
            rows = list(reader)
            return headers, rows, delim
    elif ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            headers = []
            for item in data:
                for k in item.keys():
                    if k not in headers:
                        headers.append(k)
            return headers, data, None
    else:
        raise ValueError(f"Format non supporté : {ext}")

def write_data(filepath, headers, rows, delim=None):
    path = Path(filepath)
    path.parent.mkdir(exist_ok=True, parents=True)
    ext = path.suffix.lower()
    if ext == ".csv":
        import csv
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=delim or ",")
            writer.writeheader()
            writer.writerows(rows)
    elif ext == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Helper AI Inference pour l'ETL")
    parser.add_argument("--mode", required=True, choices=["summarize", "extract"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--column", required=True)
    parser.add_argument("--target-column")
    parser.add_argument("--prompt")
    parser.add_argument("--schema")
    parser.add_argument("--model-provider")
    parser.add_argument("--model-id")
    parser.add_argument("--base-url")

    args = parser.parse_args()

    env_mode = os.environ.get("WFGY_ENV", "dev")
    env_config = load_env(env_mode)

    try:
        client = get_llm_client(args, env_config)
    except Exception as e:
        print(f"[AI HELPER ERROR] Failed to initialize LLM client: {e}", file=sys.stderr)
        sys.exit(1)

    # Load data
    try:
        headers, rows, delim = read_data(args.source)
    except Exception as e:
        print(f"[AI HELPER ERROR] Failed to read source data: {e}", file=sys.stderr)
        sys.exit(2)

    if not rows:
        print("[AI HELPER] Source data is empty.", file=sys.stderr)
        write_data(args.destination, headers, rows, delim)
        sys.exit(0)

    # Parse schema if extract mode
    schema_dict = None
    if args.mode == "extract":
        if args.schema:
            try:
                schema_dict = json.loads(args.schema)
            except Exception as e:
                print(f"[AI HELPER ERROR] Invalid schema JSON string: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # Fallback default schema
            schema_dict = {
                "type": "object",
                "properties": {
                    "extracted_info": {"type": "string"}
                },
                "required": ["extracted_info"]
            }

    # Parallel execution with thread pool
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for idx, row in enumerate(rows):
            text = row.get(args.column, "")
            futures.append(executor.submit(process_row, client, args.mode, text, args.prompt, schema_dict, idx))

        for fut in as_completed(futures):
            idx, res = fut.result()
            results[idx] = res

    # Append results to rows
    if args.mode == "summarize":
        target = args.target_column or f"{args.column}_summary"
        if target not in headers:
            headers.append(target)
        for idx in range(len(rows)):
            rows[idx][target] = results.get(idx, "")

    elif args.mode == "extract":
        # Determine new headers from schema properties
        new_cols = []
        if schema_dict and "properties" in schema_dict:
            new_cols = list(schema_dict["properties"].keys())
        else:
            new_cols = ["extracted_info"]

        for col in new_cols:
            if col not in headers:
                headers.append(col)

        for idx in range(len(rows)):
            res_dict = results.get(idx, {})
            for col in new_cols:
                rows[idx][col] = str(res_dict.get(col, ""))

    # Save data
    try:
        write_data(args.destination, headers, rows, delim)
        print(f"[AI HELPER] Success: Processed {len(rows)} rows into {args.destination}", file=sys.stderr)
    except Exception as e:
        print(f"[AI HELPER ERROR] Failed to write destination data: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
