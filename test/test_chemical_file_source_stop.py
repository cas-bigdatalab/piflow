from __future__ import annotations

from pathlib import Path

import pytest

import chemical.file_source_stop as module
from chemical.file_source_stop import ChemicalFileSourceStop

RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class _FakeProcess:
    def pid(self) -> str:
        return "process-1"


class _FakeProcessContext:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def get(self, key: str, default=None):
        if key == RUNNER_CONTEXT_WORKSPACE_ROOT:
            return str(self.workspace_root)
        return default

    def get_process(self):
        return _FakeProcess()


class _FakeOutputStream:
    def __init__(self):
        self.artifacts = {}

    def write(self, artifact, port="output") -> None:
        self.artifacts[port] = artifact


class _FakeJobContext:
    pass


class _FakeInputStream:
    pass


def test_chemical_file_source_stop_reads_local_workspace_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source_path = workspace / "inputs" / "sample.smi"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("CC(=O)O", encoding="utf-8")

    stop = ChemicalFileSourceStop()
    stop.set_properties({"source_type": "local", "file_path": "/inputs/sample.smi"})
    stop.initialize(_FakeProcessContext(workspace))

    outputs = _FakeOutputStream()
    stop.perform(_FakeInputStream(), outputs, _FakeJobContext())

    assert outputs.artifacts["output"].path == str(source_path.resolve())


def test_chemical_file_source_stop_downloads_remote_file(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    downloads = []

    class _FakeClient:
        def __init__(self, target: str):
            self.target = target

        def download_file(self, *, file_path: str, target_path: str | Path) -> str:
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("remote-content", encoding="utf-8")
            downloads.append((self.target, file_path, target))
            return str(target)

        def close(self) -> None:
            pass

    monkeypatch.setattr(module, "RemoteExecutionClient", _FakeClient)

    stop = ChemicalFileSourceStop()
    stop.set_properties(
        {
            "source_type": "remote",
            "remote_ip": "10.0.0.1",
            "remote_port": 50061,
            "remote_path": "/workspace/remote/input.smi",
        }
    )
    stop.initialize(_FakeProcessContext(workspace))

    outputs = _FakeOutputStream()
    stop.perform(_FakeInputStream(), outputs, _FakeJobContext())

    artifact_path = Path(outputs.artifacts["output"].path)
    assert downloads[0][0] == "10.0.0.1:50061"
    assert downloads[0][1] == "/workspace/remote/input.smi"
    assert artifact_path.read_text(encoding="utf-8") == "remote-content"
    assert artifact_path.parent == workspace / "process-1" / "chemical_inputs"


def test_chemical_file_source_stop_requires_remote_fields() -> None:
    stop = ChemicalFileSourceStop()

    with pytest.raises(ValueError):
        stop.set_properties({"source_type": "remote", "remote_ip": "10.0.0.1"})
