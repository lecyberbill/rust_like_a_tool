"""Tests du SchemaValidator (validation des args contre registry.json)."""
from pathlib import Path

import pytest


class TestRegistryValidation:
    def test_valid_step(self, validator):
        ok, msg = validator.validate_step("io.copy", {
            "source": "/src", "destination": "/dst"
        })
        assert ok, msg

    def test_missing_required(self, validator):
        ok, msg = validator.validate_step("io.copy", {"source": "/src"})
        assert not ok
        assert "destination" in msg

    def test_unknown_primitive(self, validator):
        ok, msg = validator.validate_step("does.not_exist", {})
        assert not ok
        assert "not defined" in msg

    def test_unexpected_param(self, validator):
        ok, msg = validator.validate_step("io.copy", {
            "source": "/src", "destination": "/dst", "bogus": "x"
        })
        # NOTE: registry schema allows additionalProperties by default
        # This test documents current behavior; no error for extra params
        assert ok

    def test_operator_enum(self, validator):
        ok, msg = validator.validate_step("data.filter", {
            "source": "/s", "destination": "/d", "column_name": "a",
            "operator": "not_equals", "value": "x", "has_headers": True
        })
        assert ok, msg

    def test_operator_invalid(self, validator):
        ok, msg = validator.validate_step("data.filter", {
            "source": "/s", "destination": "/d", "column_name": "a",
            "operator": "bogus_op", "value": "x", "has_headers": True
        })
        assert not ok
        assert "is not one of" in msg or "Must be one of" in msg

    def test_missing_operator(self, validator):
        ok, msg = validator.validate_step("data.filter", {
            "source": "/s", "destination": "/d", "column_name": "a", "value": "x"
        })
        assert not ok
        assert "operator" in msg

    def test_type_cast_args(self, validator):
        ok, msg = validator.validate_step("data.type_cast", {
            "source": "/s", "destination": "/d",
            "casts": '{"col":"string"}'
        })
        assert ok, msg

    def test_metrics_args(self, validator):
        ok, msg = validator.validate_step("data.metrics", {
            "source": "/s", "column_name": "price", "operation": "mean",
            "destination_variable": "AVG"
        })
        assert ok, msg

    def test_all_primitives_have_registry_entry(self, registry):
        """Check that all primitives called by frontend exist in registry."""
        path = Path(__file__).parent.parent.parent / "vitrine" / "js" / "app.js"
        if not path.exists():
            pytest.skip("app.js not found, can't verify")
        import re
        content = path.read_text(encoding="utf-8")
        # Find primitive names in primitiveCatalogData (name: "xxx.xxx" pattern)
        primitives = re.findall(r'name:\s*"([a-z_]+\.[a-z_]+)"', content)
        missing = [p for p in primitives if p not in registry.get("primitives", {})]
        assert not missing, f"Primitives missing from registry: {missing}"
