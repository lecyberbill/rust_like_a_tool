"""Tests PostgreSQL primitives (schema + retry, sans serveur réel)"""
import json, time
from unittest.mock import AsyncMock, patch

import pytest

from schema_validator import SchemaValidator
from orchestrator import Orchestrator


class TestPostgresSchema:
    def test_insert_valid_args(self, validator):
        ok, msg = validator.validate_step("db.insert", {
            "connection_string": "postgresql://u:p@localhost:5432/db",
            "table_name": "users",
            "source": "/tmp/data.csv",
            "mode": "replace",
        })
        assert ok, msg

    def test_insert_missing_required(self, validator):
        ok, msg = validator.validate_step("db.insert", {
            "table_name": "users",
        })
        assert not ok
        assert "connection_string" in msg or "required" in msg

    def test_query_valid_args(self, validator):
        ok, msg = validator.validate_step("db.query", {
            "connection_string": "postgresql://u:p@localhost:5432/db",
            "query": "SELECT 1",
            "destination": "/tmp/out.json",
        })
        assert ok, msg

    def test_query_missing_query(self, validator):
        ok, msg = validator.validate_step("db.query", {
            "connection_string": "postgresql://u:p@localhost:5432/db",
        })
        assert not ok
        assert "query" in msg or "required" in msg


@pytest.mark.asyncio
class TestRetryMechanism:
    async def test_retry_success_on_second_attempt(self, orchestrator):
        bridge = AsyncMock()
        # First call fails, second succeeds
        bridge.execute.side_effect = [
            (1, "", "ERR_GENERIC: transient"),
            (0, '{"ok": true}', ""),
        ]
        orchestrator.bridge = bridge

        recipe = {
            "plan_id": "retry_test",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": "/a", "destination": "/b"},
                "retry": {"attempts": 2, "delay_seconds": 0.01},
            }]
        }

        success = await orchestrator.run_recipe(recipe)
        assert success, "Should succeed after retry"
        assert bridge.execute.call_count == 2

    async def test_retry_fails_after_all_attempts(self, orchestrator):
        bridge = AsyncMock()
        bridge.execute.return_value = (1, "", "ERR_GENERIC: always fails")
        orchestrator.bridge = bridge

        recipe = {
            "plan_id": "retry_fail",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": "/a", "destination": "/b"},
                "retry": {"attempts": 3, "delay_seconds": 0.01},
            }]
        }

        success = await orchestrator.run_recipe(recipe)
        assert not success, "Should fail after exhausting retries"
        assert bridge.execute.call_count == 3

    async def test_retry_respects_timeout(self, orchestrator):
        bridge = AsyncMock()
        bridge.execute.return_value = (14, "", "ERR_TIMEOUT")
        orchestrator.bridge = bridge

        recipe = {
            "plan_id": "retry_timeout",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": "/a", "destination": "/b"},
                "retry": {"attempts": 2, "delay_seconds": 0.01, "timeout_seconds": 1},
            }]
        }

        t0 = time.perf_counter()
        success = await orchestrator.run_recipe(recipe)
        elapsed = time.perf_counter() - t0
        assert not success
        assert bridge.execute.call_count == 2
        # Should be fast (only delay between retries), not waiting for real timeout
        assert elapsed < 3, f"Took too long: {elapsed:.2f}s"


@pytest.mark.asyncio
class TestDeadLetterQueue:
    async def test_dlq_saves_on_failure(self, orchestrator):
        bridge = AsyncMock()
        bridge.execute.return_value = (1, "", "ERR_GENERIC: fatal")
        orchestrator.bridge = bridge

        dlq_dir = orchestrator.root_dir / "workspace" / ".dlq"
        if dlq_dir.exists():
            for f in dlq_dir.iterdir():
                f.unlink()

        recipe = {
            "plan_id": "dlq_test",
            "steps": [{
                "step": 1,
                "primitive": "io.copy",
                "args": {"source": "/a", "destination": "/b"},
                "retry": {"attempts": 1},
            }]
        }

        success = await orchestrator.run_recipe(recipe)
        assert not success

        entries = orchestrator.list_dlq()
        matching = [e for e in entries if e["plan_id"] == "dlq_test"]
        assert len(matching) >= 1, "DLQ entry should exist"
        assert matching[0]["primitive"] == "io.copy"
        assert matching[0]["exit_code"] == 1

    async def test_dlq_list_empty_when_no_failures(self, orchestrator):
        dlq_dir = orchestrator.root_dir / "workspace" / ".dlq"
        if dlq_dir.exists():
            for f in dlq_dir.iterdir():
                if f.name.startswith("dlq_clean"):
                    f.unlink()

        entries = orchestrator.list_dlq(plan_id="dlq_clean_test")
        assert entries == []
