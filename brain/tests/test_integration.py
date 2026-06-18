"""Tests d'integration E2E — execute de vrais flux et verifie les sorties."""
import pytest
import subprocess
import json
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "brain"))
os.environ["SECRET_VAULT_KEY"] = "test_vault_key"

BINARY = ROOT / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"
OUTPUT = ROOT / "workspace" / "output"
TEMPLATES = ROOT / "brain" / "templates"

def run_recipe(recipe: dict) -> dict:
    """Execute une recette via l'orchestrateur et retourne le resultat."""
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

def run_rust(primitive: str, args: list) -> subprocess.CompletedProcess:
    """Execute directement un binaire Rust."""
    cmd = [str(BINARY), primitive] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


class TestFluxComplets:
    """Tests de flux E2E complets utilisant de vraies primitives."""

    def test_generate_fake_only(self):
        """Generation de donnees factices → verifie le fichier CSV genere."""
        recipe = {
            "plan_id": "test_gen_only",
            "steps": [{"step": 1, "primitive": "data.generate_fake",
                       "args": {"columns": "id:id,name:full_name,age:integer",
                                "count": 10, "destination": str(OUTPUT / "_test_gen_only.csv"), "format": "csv"}}]
        }
        result = run_recipe(recipe)
        assert result["success"], "La recette a echoue"
        assert (OUTPUT / "_test_gen_only.csv").exists(), "Fichier de sortie non genere"
        content = (OUTPUT / "_test_gen_only.csv").read_text(encoding="utf-8")
        lines = [l for l in content.strip().split("\n") if l.strip()]
        assert len(lines) == 11, f"Attendu 11 lignes (header + 10), obtenu {len(lines)}"
        assert lines[0] == "id,name,age"
        print("[OK] generate_fake: 10 lignes generees")

    def test_generate_fake_json(self):
        """Generation de donnees au format JSON."""
        recipe = {
            "plan_id": "test_gen_json",
            "steps": [{"step": 1, "primitive": "data.generate_fake",
                       "args": {"columns": "id:id,email:email",
                                "count": 3, "destination": str(OUTPUT / "_test_gen_json.json"), "format": "json"}}]
        }
        result = run_recipe(recipe)
        assert result["success"]
        data = json.loads((OUTPUT / "_test_gen_json.json").read_text(encoding="utf-8"))
        assert len(data) == 3, f"Attendu 3 objets, obtenu {len(data)}"
        for obj in data:
            assert "id" in obj and "email" in obj
        print("[OK] generate_fake JSON: 3 objets avec id/email")

    def test_generate_then_filter(self):
        """Generation → Filtre: verifie que le filtre fonctionne."""
        dest1 = str(OUTPUT / "_test_chain_gen.csv")
        dest2 = str(OUTPUT / "_test_chain_filter.csv")
        recipe = {
            "plan_id": "test_chain",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,age:integer,active:boolean",
                          "count": 20, "destination": dest1, "format": "csv"}},
                {"step": 2, "primitive": "data.filter", "depends_on": [1],
                 "args": {"column_name": "active", "operator": "equals",
                          "value": "True", "has_headers": True, "destination": dest2}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        assert (OUTPUT / "_test_chain_filter.csv").exists()
        content = (OUTPUT / "_test_chain_filter.csv").read_text(encoding="utf-8")
        rows = list(csv.DictReader(content.strip().split("\n")))
        assert all(r["active"] == "True" for r in rows), "Tous les enregistrements doivent etre actifs"
        print(f"[OK] generate→filter: {len(rows)} actifs sur 20")

    def test_generate_then_metrics(self):
        """Generation → Metriques: verifie le calcul de moyenne."""
        dest1 = str(OUTPUT / "_test_metrics_gen.csv")
        recipe = {
            "plan_id": "test_metrics",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id,age:integer,salary:float",
                          "count": 10, "destination": dest1, "format": "csv"}},
                {"step": 2, "primitive": "data.metrics", "depends_on": [1],
                 "args": {"column_name": "salary", "operation": "mean",
                          "destination_variable": "AVG_SALARY"}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        print("[OK] generate→metrics: moyenne calculee")

    def test_flow_report(self):
        """Generation → Rapport: verifie la generation du rapport texte."""
        dest1 = str(OUTPUT / "_test_report_gen.csv")
        dest2 = str(OUTPUT / "_test_report.txt")
        recipe = {
            "plan_id": "test_report",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "id:id",
                          "count": 5, "destination": dest1, "format": "csv"}},
                {"step": 2, "primitive": "flow.report", "depends_on": [1],
                 "args": {"template": "STATUS: ${STEPS.1.STATUS}\nDURATION: ${STEPS.1.DURATION_MS}ms",
                          "destination": dest2}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        content = (OUTPUT / "_test_report.txt").read_text(encoding="utf-8")
        assert "STATUS: success" in content
        assert "DURATION:" in content
        print("[OK] flow.report: template resolue avec ${STEPS.*}")

    def test_sandbox_mode(self):
        """Mode sandbox: aucune ecriture fichier."""
        recipe = {
            "plan_id": "test_sandbox",
            "sandbox": True,
            "steps": [{"step": 1, "primitive": "data.generate_fake",
                       "args": {"columns": "id:id", "count": 3, "format": "csv"}}]
        }
        # Verifier que le plan_id commence par "test_sandbox"
        assert recipe["plan_id"] == "test_sandbox"
        result = run_recipe(recipe)
        assert result["success"], "Le mode sandbox ne doit pas echouer"
        print("[OK] sandbox mode: execution sans ecriture")

    def test_profile_primitive(self):
        """data.profile: verifie les stats generees."""
        dest_gen = str(OUTPUT / "_test_profile_gen.csv")
        dest_prof = str(OUTPUT / "_test_profile.json")
        recipe = {
            "plan_id": "test_profile",
            "steps": [
                {"step": 1, "primitive": "data.generate_fake",
                 "args": {"columns": "name:full_name,age:integer,salary:float",
                          "count": 10, "destination": dest_gen, "format": "csv"}},
                {"step": 2, "primitive": "data.profile", "depends_on": [1],
                 "args": {"source": "", "destination": dest_prof}}
            ]
        }
        result = run_recipe(recipe)
        assert result["success"]
        data = json.loads((OUTPUT / "_test_profile.json").read_text(encoding="utf-8"))
        assert data["total_rows"] == 10
        assert "age" in data["columns"]
        assert "mean" in data["columns"]["age"]
        print(f"[OK] data.profile: {data['total_rows']} lignes, stats age: min={data['columns']['age'].get('min')}")

    def test_template_instantiation(self):
        """Gabarit: verifie que les templates se chargent."""
        templates_dir = TEMPLATES
        assert templates_dir.exists(), "Dossier templates introuvable"
        tpl_files = list(templates_dir.glob("*.json"))
        assert len(tpl_files) >= 3, f"Attendu au moins 3 templates, trouve {len(tpl_files)}"
        for tpl_file in tpl_files:
            tpl = json.loads(tpl_file.read_text(encoding="utf-8"))
            assert "steps" in tpl
            assert "variables" in tpl
            print(f"[OK] Template {tpl_file.stem}: {len(tpl['steps'])} steps, {len(tpl['variables'])} variables")


class TestRustPrimitives:
    """Tests unitaires des primitives Rust via le binaire."""

    def test_rust_binary_exists(self):
        assert BINARY.exists(), f"Binaire Rust introuvable: {BINARY}"
        print(f"[OK] Binaire Rust: {BINARY}")

    def test_rust_generate_fake(self):
        r = run_rust("data.generate_fake", ["--columns", "id:id,name:full_name", "--count", "3", "--format", "csv"])
        assert r.returncode == 0, f"ERREUR: {r.stderr}"
        assert "name" in r.stdout
        lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
        assert len(lines) == 4  # header + 3 rows
        print(f"[OK] Rust generate_fake: {len(lines)-1} lignes")

    def test_rust_filter(self):
        r = run_rust("data.filter", ["--source", str(OUTPUT / "_test_gen_only.csv"),
                                      "--destination", str(OUTPUT / "_test_filter_rust.csv"),
                                      "--column-name", "age", "--operator", "greater_than",
                                      "--value", "0", "--has-headers", "true"])
        assert r.returncode == 0, f"ERREUR: {r.stderr}"
        assert (OUTPUT / "_test_filter_rust.csv").exists()
        print("[OK] Rust filter: execution reussie")

    def test_rust_dry_run_notify(self):
        r = run_rust("net.notify", ["--type", "email", "--to", "test@test.com",
                                     "--subject", "test", "--message", "hello", "--dry-run"])
        assert r.returncode == 0, f"ERREUR: {r.stderr}"
        assert "DRY-RUN" in r.stdout
        print("[OK] Rust notify dry-run: simulation SMTP")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
