"""Tests d'intégration du WorkerBridge (Brain → Rust)."""
import json
from pathlib import Path

import pytest
pytestmark = pytest.mark.asyncio


class TestBridgeIoCopy:
    async def test_copy_file(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "copy.csv"
        code, out, err = await bridge.execute("io.copy", {
            "source": sample_csv, "destination": str(dst)
        })
        assert code == 0, f"err: {err}"
        assert dst.exists()
        assert dst.read_text() == Path(sample_csv).read_text()

    async def test_copy_missing_source(self, bridge, tmp_workspace):
        dst = tmp_workspace / "nope.csv"
        code, out, err = await bridge.execute("io.copy", {
            "source": "/nonexistent/file.csv", "destination": str(dst)
        })
        assert code != 0, "should fail"

    async def test_copy_missing_arg(self, bridge):
        code, out, err = await bridge.execute("io.copy", {"source": "x"})
        assert code != 0, "should fail on missing --destination"


class TestBridgeIoDelete:
    async def test_delete_permanent(self, bridge, tmp_workspace, sample_csv):
        src = Path(sample_csv)
        code, out, err = await bridge.execute("io.delete", {
            "path": str(src), "secure": "permanent"
        })
        assert code == 0, f"err: {err}"
        assert not src.exists()

    async def test_delete_nonexistent(self, bridge):
        code, out, err = await bridge.execute("io.delete", {
            "path": "/nonexistent", "secure": "permanent"
        })
        assert code == 0  # handler returns Ok if path missing


class TestBridgeIoMetadata:
    async def test_metadata_file(self, bridge, sample_csv):
        code, out, err = await bridge.execute("io.metadata", {"path": sample_csv})
        assert code == 0, f"err: {err}"
        meta = json.loads(out.strip().split("\n")[0])
        assert meta["exists"] is True
        assert meta["size_bytes"] > 0

    async def test_metadata_nonexistent(self, bridge):
        code, out, err = await bridge.execute("io.metadata", {"path": "/nonexistent"})
        assert code == 0
        meta = json.loads(out.strip())
        assert meta["exists"] is False


class TestBridgeIoWriteFile:
    async def test_write_file(self, bridge, tmp_workspace):
        dst = tmp_workspace / "written.txt"
        code, out, err = await bridge.execute("io.write_file", {
            "path": str(dst), "content": "hello world"
        })
        assert code == 0, f"err: {err}"
        assert dst.read_text() == "hello world"


class TestBridgeDataFilter:
    async def test_filter_equals(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "filtered.csv"
        code, out, err = await bridge.execute("data.filter", {
            "source": sample_csv, "destination": str(dst),
            "column_name": "a", "operator": "equals", "value": "1",
            "has_headers": True
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        assert "1,x,10" in content
        assert "2,y,20" not in content

    async def test_filter_not_equals(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "filtered.csv"
        code, out, err = await bridge.execute("data.filter", {
            "source": sample_csv, "destination": str(dst),
            "column_name": "a", "operator": "not_equals", "value": "1",
            "has_headers": True
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        assert "2,y,20" in content
        assert "3,z,30" in content
        assert "1,x,10" not in content

    async def test_filter_unsupported_operator(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "filtered.csv"
        code, out, err = await bridge.execute("data.filter", {
            "source": sample_csv, "destination": str(dst),
            "column_name": "a", "operator": "bogus", "value": "1",
            "has_headers": True
        })
        assert code != 0


class TestBridgeDataGroupby:
    async def test_groupby_sum(self, bridge, tmp_workspace):
        src = tmp_workspace / "data.csv"
        src.write_text("cat,val\na,10\na,20\nb,5\n", encoding="utf-8")
        dst = tmp_workspace / "grouped.csv"
        code, out, err = await bridge.execute("data.groupby", {
            "source": str(src), "destination": str(dst),
            "groupby_columns": "cat", "aggregate_column": "val", "operation": "sum"
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        assert "a,30" in content or "30" in content
        assert "b,5" in content or "5" in content


class TestBridgeDataMetrics:
    async def test_metrics_mean(self, bridge, tmp_workspace, sample_csv):
        code, out, err = await bridge.execute("data.metrics", {
            "source": sample_csv, "column_name": "c", "operation": "mean"
        })
        assert code == 0, f"err: {err}"
        result = json.loads(out.strip().split("\n")[0])
        assert "value" in result
        assert result["value"] == 20.0  # (10+20+30)/3

    async def test_metrics_sum(self, bridge, tmp_workspace, sample_csv):
        code, out, err = await bridge.execute("data.metrics", {
            "source": sample_csv, "column_name": "c", "operation": "sum"
        })
        assert code == 0, f"err: {err}"
        result = json.loads(out.strip().split("\n")[0])
        assert result["value"] == 60.0


class TestBridgeDataDeduplicate:
    async def test_deduplicate(self, bridge, tmp_workspace):
        src = tmp_workspace / "dups.csv"
        src.write_text("id,val\n1,a\n2,b\n1,c\n3,d\n", encoding="utf-8")
        dst = tmp_workspace / "dedup.csv"
        code, out, err = await bridge.execute("data.deduplicate", {
            "source": str(src), "destination": str(dst),
            "subset": "id", "keep": "first"
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        lines = [l for l in content.strip().split("\n") if l]
        # header + 3 unique ids (1,2,3)
        assert len(lines) == 4, f"expected 4 lines, got {len(lines)}"


class TestBridgeDataAnonymize:
    async def test_anonymize(self, bridge, tmp_workspace):
        src = tmp_workspace / "pii.csv"
        src.write_text("name,email\nalice,a@x.com\nbob,b@y.com\n", encoding="utf-8")
        dst = tmp_workspace / "anon.csv"
        code, out, err = await bridge.execute("data.anonymize", {
            "source": str(src), "destination": str(dst),
            "rules": "email:mask_email"
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        assert "@" not in content or "*" in content


class TestBridgeDataTypeCast:
    async def test_type_cast(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "casted.csv"
        code, out, err = await bridge.execute("data.type_cast", {
            "source": sample_csv, "destination": str(dst),
            "casts": '{"a": "string", "c": "float"}'
        })
        assert code == 0, f"err: {err}"
        assert dst.exists()


class TestBridgeDataPivot:
    async def test_pivot(self, bridge, tmp_workspace):
        src = tmp_workspace / "sales.csv"
        src.write_text("product,region,qty\nA,North,10\nA,South,20\nB,North,5\n", encoding="utf-8")
        dst = tmp_workspace / "pivot.csv"
        code, out, err = await bridge.execute("data.pivot", {
            "source": str(src), "destination": str(dst),
            "index": "product", "on": "region", "values": "qty", "aggregate": "sum"
        })
        assert code == 0, f"err: {err}"
        assert dst.exists()


class TestBridgeDataCsvToJson:
    async def test_csv_to_json(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "out.json"
        code, out, err = await bridge.execute("data.csv_to_json", {
            "source": sample_csv, "destination": str(dst)
        })
        assert code == 0, f"err: {err}"
        data = json.loads(dst.read_text())
        assert len(data) == 3
        assert data[0]["a"] == "1"


class TestBridgeDataJsonToCsv:
    async def test_json_to_csv(self, bridge, tmp_workspace):
        src = tmp_workspace / "data.json"
        src.write_text('[{"x":1,"y":2},{"x":3,"y":4}]', encoding="utf-8")
        dst = tmp_workspace / "out.csv"
        code, out, err = await bridge.execute("data.json_to_csv", {
            "source": str(src), "destination": str(dst)
        })
        assert code == 0, f"err: {err}"
        content = dst.read_text()
        assert "1,2" in content
        assert "3,4" in content


class TestBridgeIoReadFile:
    async def test_read_file(self, bridge, tmp_workspace, sample_csv):
        dst = tmp_workspace / "read_copy.csv"
        code, out, err = await bridge.execute("io.read_file", {
            "source": sample_csv, "destination": str(dst)
        })
        assert code == 0, f"err: {err}"
        assert dst.exists()
        assert dst.read_text() == Path(sample_csv).read_text()


@pytest.mark.asyncio
class TestBridgeErrors:
    async def test_unknown_primitive(self, bridge):
        code, out, err = await bridge.execute("does.not_exist", {})
        assert code != 0
        assert "Unknown primitive" in err

    async def test_missing_required_arg(self, bridge):
        code, out, err = await bridge.execute("io.copy", {})
        assert code != 0
