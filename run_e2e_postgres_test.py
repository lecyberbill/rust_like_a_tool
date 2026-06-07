# [WFGY] Zone: SAFE | λ: 0.2 | Action: End-to-end stress test with 20000 rows and real PostgreSQL insertion

import os
import sys
import csv
import json
import time
import asyncio
from pathlib import Path

# Add brain directory to python path
sys.path.append(str(Path(__file__).parent / "brain"))

from orchestrator import load_env, Orchestrator
from planner import RecipePlanner
from schema_validator import SchemaValidator

# Default PostgreSQL Connection String
DEFAULT_PG_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# Files
BASE_DIR = Path(__file__).parent
CSV_SRC = BASE_DIR / "large_users.csv"
CSV_FILTERED = BASE_DIR / "large_users_filtered.csv"
CSV_CLEAN = BASE_DIR / "large_users_clean.csv"
QUERY_OUT = BASE_DIR / "test_pg_query_out.json"

def cleanup():
    for f in [CSV_SRC, CSV_FILTERED, CSV_CLEAN, QUERY_OUT]:
        if f.exists():
            f.unlink()
    checkpoint = Path(__file__).parent / "brain" / ".run_checkpoint.json"
    if checkpoint.exists():
        checkpoint.unlink()

def generate_large_csv(filename, count=20000):
    print(f"[PREPARE] Generating {count} mock user rows in {filename}...")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "age", "email"])
        for i in range(1, count + 1):
            name = f"User{i}"
            age = 10 + (i % 70)  # Ages ranging from 10 to 79
            email = f"user_{i}@example.com"
            writer.writerow([i, name, age, email])
    print("[PREPARE] Generation complete.")

async def run_e2e_test(pg_url):
    print("==========================================================")
    print("=== STARTING END-TO-END STRESS TEST (20,000 ROWS) ===")
    print("==========================================================\n")
    
    # Generate mock data
    generate_large_csv(CSV_SRC, 20000)
    
    env_config = load_env("dev")
    # Set the custom database URL in env configuration and OS environment
    env_config["DATABASE_URL"] = pg_url
    os.environ["DATABASE_URL"] = pg_url
    os.environ["SECRET_POSTGRES_CONNECTION_STRING"] = pg_url
    os.environ["POSTGRES_CONNECTION_STRING"] = pg_url
    
    # Auto-toggle to Gemini if API key is present in system environment
    if os.environ.get("GEMINI_API_KEY"):
        env_config["LLM_PROVIDER"] = "gemini"
        env_config["LLM_MODEL"] = "gemini-2.5-flash"
        env_config["LLM_API_KEY"] = os.environ.get("GEMINI_API_KEY")
        print("[ENV] Detected GEMINI_API_KEY in environment. Switched provider to Google Gemini.")
    
    # Prompt representing the user intent
    prompt = (
        f"Prendre le fichier large_users.csv, filtrer les lignes où l'âge est supérieur ou égal à 18 (has_headers=true, operator='greater_than', value='17'), "
        f"anonymiser les emails en appliquant la stratégie 'email:mask_email', "
        f"et insérer les utilisateurs propres dans la table PostgreSQL 'clean_users' avec le mode replace."
    )
    
    print(f"User Request Prompt:\n\"{prompt}\"\n")
    
    # 1. AI Planning Phase
    print("[PHASE 1] Initializing Planner...")
    planner = RecipePlanner(env_config)
    
    # Detect if LLM is offline, fallback to structured recipe
    is_offline = False
    try:
        if env_config.get("LLM_PROVIDER") != "gemini":
            import urllib.request
            url = env_config.get("LLM_BASE_URL", "http://localhost:1234/v1")
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as _:
                pass
    except Exception:
        is_offline = True
        print("[NOTICE] LLM server is offline. Activating recipe generation fallback.")
        
    recipe = None
    if not is_offline:
        try:
            recipe = planner.plan(prompt)
            print("[PHASE 1] Recipe planned successfully via Live LLM.")
        except Exception as e:
            print(f"[PHASE 1] LLM Plan execution error: {e}. Falling back to pre-defined recipe.")
            
    if not recipe:
        # Structured Recipe Fallback matching the requested flow
        recipe = {
            "plan_id": "postgres_e2e_stress_test",
            "intent_analysis": "Filtrage d'âge, anonymisation d'emails et insertion PostgreSQL",
            "steps": [
                {
                    "step": 1,
                    "primitive": "data.filter",
                    "depends_on": [],
                    "ui": {
                        "label": "Filtrer Majeurs",
                        "color": "#4A90E2",
                        "position": {"x": 100, "y": 200}
                    },
                    "args": {
                        "source": str(CSV_SRC),
                        "destination": str(CSV_FILTERED),
                        "column_name": "age",
                        "operator": "greater_than",
                        "value": "17",
                        "has_headers": True
                    }
                },
                {
                    "step": 2,
                    "primitive": "data.anonymize",
                    "depends_on": [1],
                    "ui": {
                        "label": "Masquer Emails",
                        "color": "#4A90E2",
                        "position": {"x": 300, "y": 200}
                    },
                    "args": {
                        "source": str(CSV_FILTERED),
                        "destination": str(CSV_CLEAN),
                        "rules": "email:mask_email"
                    }
                },
                {
                    "step": 3,
                    "primitive": "db.insert",
                    "depends_on": [2],
                    "ui": {
                        "label": "Insert Postgres",
                        "color": "#4A90E2",
                        "position": {"x": 500, "y": 200}
                    },
                    "args": {
                        "connection_string": pg_url,
                        "table_name": "clean_users",
                        "source": str(CSV_CLEAN),
                        "mode": "replace",
                        "schema_drift": True
                    }
                }
            ]
        }
        
    print(f"\nPlanned recipe structure:\n{json.dumps(recipe, indent=2)}\n")
    
    # 2. Validation Checks
    print("[PHASE 2] Checking Recipe Schema compliance...")
    validator = SchemaValidator(Path(__file__).parent / "brain" / "registry.json")
    errors = []
    for s in recipe.get("steps", []):
        ok, msg = validator.validate_step(s.get("primitive"), s.get("args", {}))
        if not ok:
            errors.append(f"Step {s.get('step')} ({s.get('primitive')}) validation failed: {msg}")
            
    if errors:
        print(f"[FATAL] Schema validation failed:\n" + "\n".join(errors))
        return False
    print("[PHASE 2] Recipe Schema is perfectly compliant.")
    
    # 3. Execution Phase
    print("\n[PHASE 3] Executing recipe via Orchestrator...")
    orch = Orchestrator()
    start_time = time.perf_counter()
    
    success = await orch.run_recipe(recipe)
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    if not success:
        print("[FATAL] Recipe execution encountered an error.")
        return False
        
    print(f"\n[PHASE 3] Recipe executed successfully in {duration:.2f} seconds.")
    
    # 4. Verification in database
    print("\n[PHASE 4] Verifying data in PostgreSQL database...")
    verify_recipe = {
        "plan_id": "postgres_verify_query",
        "intent_analysis": "Query database to verify count and email mask",
        "steps": [
            {
                "step": 1,
                "primitive": "db.query",
                "depends_on": [],
                "args": {
                    "connection_string": pg_url,
                    "query": "SELECT count(*) as count, min(age) as min_age, count(case when email like '%*%' then 1 end) as masked_count FROM clean_users",
                    "destination": str(QUERY_OUT)
                }
            }
        ]
    }
    
    verify_success = await orch.run_recipe(verify_recipe)
    if not verify_success or not QUERY_OUT.exists():
        print("[FATAL] Verification query failed.")
        return False
        
    with open(QUERY_OUT, "r", encoding="utf-8") as f:
        res_data = json.load(f)
        row = res_data[0] if isinstance(res_data, list) and len(res_data) > 0 else res_data
        
        print("\nVerification Results from PG:")
        print(f"  - Total records inserted: {row.get('count')}")
        print(f"  - Minimum age in database: {row.get('min_age')}")
        print(f"  - Number of masked emails: {row.get('masked_count')}")
        
        # We expect count around ~17714 since ages 10 to 17 are excluded out of 20000 (roughly 8/70 excluded)
        # Specifically, ages range from 10 to 79 (size 70). Under 18 are 10,11,12,13,14,15,16,17 (8 ages).
        # So 8/70 of 20000 = ~2285 rows filtered out, leaving ~17715.
        cnt = int(row.get('count', 0))
        masked_cnt = int(row.get('masked_count', 0))
        min_age = int(row.get('min_age', 0))
        
        assert cnt > 15000, f"Expected > 15000 records, got {cnt}"
        assert min_age >= 18, f"Expected min age >= 18, got {min_age}"
        assert cnt == masked_cnt, f"Expected all emails to be masked, got {masked_cnt}/{cnt}"
        
    print("\n==========================================================")
    print("=== E2E STRESS TEST COMPLETED SUCCESSFULLY! ALL GREEN ===")
    print("==========================================================")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run E2E PostgreSQL Stress Test.")
    parser.add_argument("--pg-url", default=DEFAULT_PG_URL, help="PostgreSQL connection string")
    args = parser.parse_args()
    
    cleanup()
    try:
        asyncio.run(run_e2e_test(args.pg_url))
    finally:
        cleanup()
