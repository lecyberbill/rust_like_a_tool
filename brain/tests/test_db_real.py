"""Tests d'integration avec bases de donnees reelles (PostgreSQL Docker + MongoDB demo)."""
import pytest
import os, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["SECRET_VAULT_KEY"] = "wfgy_core_secret_key_12345"

BINARY = Path(__file__).parent.parent.parent / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"
OUTPUT = Path(__file__).parent.parent.parent / "workspace" / "output"

PG_DSN = "postgresql://user_test:user_test@localhost:5432/postgres"
MONGO_URI = os.environ.get("SECRET_MONGO_URI", "mongodb://localhost:27017")


def pg_available():
    try:
        import psycopg2
        c = psycopg2.connect(host="localhost", port=5432, user="user_test", password="user_test", dbname="postgres", connect_timeout=3)
        c.close()
        return True
    except Exception:
        return False


def run_recipe(recipe: dict) -> dict:
    from orchestrator import Orchestrator
    import asyncio
    o = Orchestrator()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            success = pool.submit(asyncio.run, o.run_recipe(recipe)).result()
    else:
        success = asyncio.run(o.run_recipe(recipe))
    return {"success": success}


class TestPostgreSQLReel:
    """Tests avec une vraie base PostgreSQL (Docker)."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        if not pg_available():
            pytest.skip("PostgreSQL non disponible — lancer le conteneur Docker")
        import psycopg2
        self.conn = psycopg2.connect(host="localhost", port=5432, user="user_test", password="user_test", dbname="postgres")
        self.cur = self.conn.cursor()
        self.cur.execute("DROP TABLE IF EXISTS test_integration CASCADE")
        self.conn.commit()
        yield
        self.cur.execute("DROP TABLE IF EXISTS test_integration CASCADE")
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def test_pg_select_version(self):
        """Verifie la connexion PostgreSQL."""
        self.cur.execute("SELECT version()")
        v = self.cur.fetchone()[0]
        assert "PostgreSQL" in v
        print(f"[OK] PostgreSQL: {v[:40]}")

    def test_pg_generate_then_insert(self):
        """Genere des donnees → insere dans PostgreSQL via db.insert."""
        dest = str(OUTPUT / "_test_pg_insert.csv")
        recipe = {
            "plan_id": "test_pg_insert",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,name:full_name,email:email,age:integer",
                          "count": 10, "destination": dest, "format": "csv"}},
                {"step": 2, "primitive": "db.insert", "depends_on": [1],
                 "args": {"connection_string": PG_DSN, "table_name": "test_integration",
                          "source": "", "mode": "replace"}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]

        self.cur.execute("SELECT COUNT(*) FROM test_integration")
        count = self.cur.fetchone()[0]
        assert count == 10, f"Attendu 10 lignes, obtenu {count}"
        print(f"[OK] db.insert: {count} lignes inserees dans PostgreSQL")

    def test_pg_generate_then_upsert(self):
        """Genere → upsert dans PostgreSQL (table avec PK)."""
        # Creer la table avec une contrainte unique sur id
        self.cur.execute("""
            CREATE TABLE test_integration (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        """)
        self.conn.commit()

        dest = str(OUTPUT / "_test_pg_upsert.csv")
        recipe = {
            "plan_id": "test_pg_upsert",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,name:full_name,email:email",
                          "count": 5, "destination": dest, "format": "csv"}},
                {"step": 2, "primitive": "db.upsert", "depends_on": [1],
                 "args": {"connection_string": PG_DSN, "table_name": "test_integration",
                          "source": "", "keys": "id"}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        self.cur.execute("SELECT COUNT(*) FROM test_integration")
        count = self.cur.fetchone()[0]
        assert count == 5, f"Attendu 5, obtenu {count}"
        print(f"[OK] db.upsert: {count} lignes upsert dans PostgreSQL")


class TestMongoDBReel:
    """Tests avec une vraie base MongoDB (Atlas ou Docker)."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        from pymongo import MongoClient
        self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client["test_integration"]
        self.collection = self.db["test_integration"]
        self.collection.delete_many({})
        yield
        self.collection.delete_many({})
        self.client.close()

    def test_mongo_connection(self):
        """Verifie la connexion MongoDB."""
        info = self.client.server_info()
        assert "version" in info
        print(f"[OK] MongoDB: {info['version']}")

    def test_mongo_generate_then_insert(self):
        """Genere → insere dans MongoDB."""
        dest = str(OUTPUT / "_test_mongo_insert.csv")
        recipe = {
            "plan_id": "test_mongo",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,name:full_name,email:email",
                          "count": 8, "destination": dest, "format": "csv"}},
                {"step": 2, "primitive": "mongodb.insert", "depends_on": [1],
                 "args": {"connection_string": MONGO_URI, "database": "test_integration",
                          "collection": "test_integration", "source": "", "mode": "replace"}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        count = self.collection.count_documents({})
        assert count == 8, f"Attendu 8, obtenu {count}"
        print(f"[OK] mongodb.insert: {count} documents inseres")

    def test_mongo_find(self):
        """Insere → interroge MongoDB."""
        dest = str(OUTPUT / "_test_mongo_find.csv")
        recipe = {
            "plan_id": "test_mongo_find",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,name:full_name,email:email",
                          "count": 3, "destination": dest, "format": "csv"}},
                {"step": 2, "primitive": "mongodb.insert", "depends_on": [1],
                 "args": {"connection_string": MONGO_URI, "database": "test_integration",
                          "collection": "test_integration", "source": "", "mode": "replace"}},
                {"step": 3, "primitive": "mongodb.find", "depends_on": [2],
                 "args": {"connection_string": MONGO_URI, "database": "test_integration",
                          "collection": "test_integration", "filter": "{}",
                          "destination": str(OUTPUT / "_test_mongo_result.json")}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        output_file = OUTPUT / "_test_mongo_result.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert len(data) == 3
        print(f"[OK] mongodb.find: {len(data)} documents trouves")
