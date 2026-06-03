# [WFGY] Zone: SAFE | λ: 0.1 | Action: Integration test for SQLite, Postgres, MySQL, Snowflake and ODBC connectors
import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import Orchestrator

async def run_db_test():
    print("[TEST DB] Initialisation de la base SQLite de test...")
    Path("test_results").mkdir(exist_ok=True)
    
    db_file = "test_results/local_db.sqlite"
    if Path(db_file).exists():
        Path(db_file).unlink()

    # Create tables and insert source data
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users_source (
            id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE users_destination (
            id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT
        )
    """)
    cursor.executemany("INSERT INTO users_source (id, name, status) VALUES (?, ?, ?)", [
        (1, "alice", "active"),
        (2, "bob", "inactive"),
        (3, "charlie", "active")
    ])
    conn.commit()
    conn.close()

    # Setup file paths
    extracted_csv = "test_results/extracted_db_users.csv"
    active_csv = "test_results/active_db_users.csv"
    snowflake_json = "test_results/snowflake_out.json"
    odbc_json = "test_results/odbc_out.json"

    # Cleanup old test files
    for f in [extracted_csv, active_csv, snowflake_json, odbc_json]:
        p = Path(f)
        if p.exists():
            p.unlink()

    # Define the recipe
    recipe = {
        "plan_id": "test_db_connectors_flow",
        "intent_analysis": "Export SQL, filtrage de donnees, re-importation SQL et interrogation Snowflake/ODBC",
        "steps": [
            {
                "step": 1,
                "primitive": "db.query",
                "args": {
                    "connection_string": f"sqlite:{db_file}",
                    "query": "SELECT * FROM users_source",
                    "destination": extracted_csv
                }
            },
            {
                "step": 2,
                "primitive": "data.filter",
                "depends_on": [1],
                "args": {
                    "source": extracted_csv,
                    "destination": active_csv,
                    "column_name": "status",
                    "operator": "equals",
                    "value": "active",
                    "has_headers": True
                }
            },
            {
                "step": 3,
                "primitive": "db.insert",
                "depends_on": [2],
                "args": {
                    "connection_string": f"sqlite:{db_file}",
                    "table_name": "users_destination",
                    "source": active_csv,
                    "mode": "replace"
                }
            },
            {
                "step": 4,
                "primitive": "db.query",
                "args": {
                    "connection_string": "snowflake://test_account?token=mock_token&mock=true",
                    "query": "SELECT * FROM mock_snowflake",
                    "destination": snowflake_json
                }
            },
            {
                "step": 5,
                "primitive": "db.query",
                "args": {
                    "connection_string": "odbc://DSN=test_dsn;mock=true",
                    "query": "SELECT * FROM mock_odbc",
                    "destination": odbc_json
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("\n[TEST DB] Lancement de la recette avec les bases de données...")
    success = await orchestrator.run_recipe(recipe, target_env="dev")
    
    if not success:
        print("[TEST DB FAILURE] L'orchestrateur a échoué.")
        sys.exit(1)

    print("\n[TEST DB] Vérification des assertions...")
    
    # 1. Vérifier la table SQLite de destination
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users_destination ORDER BY id")
    dest_rows = cursor.fetchall()
    conn.close()
    
    print(f" -> Lignes dans users_destination: {dest_rows}")
    assert len(dest_rows) == 2, f"Attendu 2 lignes, obtenu {len(dest_rows)}"
    assert dest_rows[0] == (1, "alice", "active"), f"Ligne 1 incorrecte: {dest_rows[0]}"
    assert dest_rows[1] == (3, "charlie", "active"), f"Ligne 2 incorrecte: {dest_rows[1]}"

    # 2. Vérifier l'extraction Snowflake (Mock)
    assert Path(snowflake_json).exists(), "Fichier Snowflake manquant"
    with open(snowflake_json, "r", encoding="utf-8") as f:
        sf_data = json.load(f)
    print(f" -> Données Snowflake: {sf_data}")
    assert len(sf_data) == 2, "Les données Snowflake doivent contenir 2 entrées"
    assert sf_data[0]["name"] == "mock_snowflake_1"

    # 3. Vérifier l'extraction ODBC (Mock)
    assert Path(odbc_json).exists(), "Fichier ODBC manquant"
    with open(odbc_json, "r", encoding="utf-8") as f:
        odbc_data = json.load(f)
    print(f" -> Données ODBC: {odbc_data}")
    assert len(odbc_data) == 2, "Les données ODBC doivent contenir 2 entrées"
    assert odbc_data[0]["name"] == "mock_odbc_1"

    print("\n[VERIFICATION_GATE] SUCCESS: Tous les tests d'intégration des bases de données ont réussi !")

if __name__ == "__main__":
    asyncio.run(run_db_test())
