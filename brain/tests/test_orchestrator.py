"""Tests d'intégration de l'Orchestrator (run_recipe)."""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.asyncio


class TestOrchestratorSimpleRecipe:
    async def test_simple_copy_recipe(self, orchestrator, tmp_workspace, sample_csv):
        dst = tmp_workspace / "out.csv"
        recipe = {
            "plan_id": "test_simple_copy",
            "intent_analysis": "test",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": sample_csv, "destination": str(dst)},
                "depends_on": []
            }]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success, f"Recipe failed"
        assert dst.exists()

    async def test_two_step_chain(self, orchestrator, tmp_workspace, sample_csv):
        s1 = tmp_workspace / "s1.csv"
        s2 = tmp_workspace / "s2.csv"
        recipe = {
            "plan_id": "test_chain",
            "intent_analysis": "test",
            "steps": [
                {"step": 1, "primitive": "io.copy",
                 "args": {"source": sample_csv, "destination": str(s1)},
                 "depends_on": []},
                {"step": 2, "primitive": "io.copy",
                 "args": {"source": str(s1), "destination": str(s2)},
                 "depends_on": [1]}
            ]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success
        assert s2.exists()
        assert s2.read_text() == Path(sample_csv).read_text()

    async def test_auto_resolve_source(self, orchestrator, tmp_workspace, sample_csv):
        """Step 2 should auto-resolve source from step 1's destination."""
        s1 = tmp_workspace / "s1.csv"
        s2 = tmp_workspace / "s2.csv"
        recipe = {
            "plan_id": "test_auto_source",
            "intent_analysis": "test",
            "steps": [
                {"step": 1, "primitive": "io.copy",
                 "args": {"source": sample_csv, "destination": str(s1)},
                 "depends_on": []},
                {"step": 2, "primitive": "io.copy",
                 "args": {"destination": str(s2)},
                 "depends_on": [1]}
            ]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success, "Auto-resolution of source failed"
        assert s2.exists()
        assert s2.read_text() == Path(sample_csv).read_text()

    async def test_auto_generate_destination(self, orchestrator, tmp_workspace, sample_csv):
        """Step without destination should get auto-generated."""
        recipe = {
            "plan_id": "test_auto_dest",
            "intent_analysis": "test",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": sample_csv},
                "depends_on": []
            }]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success
        # auto-generated dest should be workspace/output/step_1_io_copy.csv
        dest = Path("workspace/output/step_1_io_copy.csv")
        assert dest.exists(), f"Auto-generated dest not found: {dest}"
        dest.unlink(missing_ok=True)


class TestOrchestratorFilterChain:
    async def test_filter_then_groupby(self, orchestrator, tmp_workspace):
        src = tmp_workspace / "sales.csv"
        src.write_text("cat,val\na,10\na,20\nb,5\nc,30\n", encoding="utf-8")
        filtered = tmp_workspace / "filtered.csv"
        grouped = tmp_workspace / "grouped.csv"
        recipe = {
            "plan_id": "test_filter_groupby",
            "intent_analysis": "test",
            "steps": [
                {"step": 1, "primitive": "io.read_file",
                 "args": {"source": str(src), "destination": str(filtered)},
                 "depends_on": []},
                {"step": 2, "primitive": "data.filter",
                 "args": {"column_name": "cat", "operator": "not_equals",
                          "value": "b", "has_headers": True},
                 "depends_on": [1]},
                {"step": 3, "primitive": "data.groupby",
                 "args": {"groupby_columns": "cat", "aggregate_column": "val",
                          "operation": "sum", "destination": str(grouped)},
                 "depends_on": [2]}
            ]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success, f"Filter→groupby recipe failed"
        assert grouped.exists()
        content = grouped.read_text()
        assert "a,30" in content or "30" in content
        assert "b,5" not in content

    async def test_metrics_and_destination_variable(self, orchestrator, tmp_workspace, sample_csv):
        s1 = tmp_workspace / "s1.csv"
        recipe = {
            "plan_id": "test_metrics_var",
            "intent_analysis": "test",
            "steps": [
                {"step": 1, "primitive": "io.read_file",
                 "args": {"source": sample_csv, "destination": str(s1)},
                 "depends_on": []},
                {"step": 2, "primitive": "data.metrics",
                 "args": {"column_name": "c", "operation": "mean",
                          "destination_variable": "AVG_C"},
                 "depends_on": [1]}
            ]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert success
        assert orchestrator.execution_context.get("AVG_C") == 20.0


class TestOrchestratorErrors:
    async def test_cycle_detection(self, orchestrator):
        recipe = {
            "plan_id": "test_cycle",
            "intent_analysis": "test",
            "steps": [
                {"step": 1, "primitive": "io.copy",
                 "args": {"source": "a", "destination": "b"},
                 "depends_on": [2]},
                {"step": 2, "primitive": "io.copy",
                 "args": {"source": "b", "destination": "c"},
                 "depends_on": [1]}
            ]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert not success, "Should detect cycle"

    async def test_missing_source(self, orchestrator):
        recipe = {
            "plan_id": "test_missing_source",
            "intent_analysis": "test",
            "steps": [{
                "step": 1, "primitive": "io.copy",
                "args": {"source": "/nonexistent", "destination": "out.csv"},
                "depends_on": []
            }]
        }
        success = await orchestrator.run_recipe(recipe, target_env="dev")
        assert not success, "Should fail on missing source"
