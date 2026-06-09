import os, sys, json, tempfile, shutil
from pathlib import Path

_root = Path(__file__).parent.parent.parent   # project root
_brain = _root / "brain"

sys.path.insert(0, str(_brain))
sys.path.insert(0, str(_root))

import pytest
from worker_bridge import WorkerBridge
from orchestrator import Orchestrator
from schema_validator import SchemaValidator


@pytest.fixture(scope="session")
def bridge():
    b = WorkerBridge()
    if b.binary_path is None or not b.binary_path.exists():
        pytest.skip(f"Rust binary not found at {b.binary_path}")
    return b

@pytest.fixture(scope="session")
def registry():
    path = _brain / "registry.json"
    return json.loads(path.read_text(encoding="utf-8"))

@pytest.fixture(scope="session")
def validator(registry):
    path = _brain / "registry.json"
    return SchemaValidator(path)

@pytest.fixture
def tmp_workspace():
    d = Path(tempfile.mkdtemp(prefix="wfgytest_"))
    yield d
    shutil.rmtree(str(d), ignore_errors=True)

@pytest.fixture
def sample_csv(tmp_workspace):
    path = tmp_workspace / "input.csv"
    path.write_text("a,b,c\n1,x,10\n2,y,20\n3,z,30\n", encoding="utf-8")
    return str(path)

@pytest.fixture
def orchestrator():
    return Orchestrator()
