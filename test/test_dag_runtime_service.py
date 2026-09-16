from pathlib import Path

import pytest

import services.dag_runtime_service as dag_runtime_service
from services.dag_runtime_service import get_stop_log_paths_by_job_id


class FakeWorkspaceManager:

    def __init__(self, root: Path):
        self.root = root

    def to_workspace_relative_path(self, virtual_path: str) -> str:
        raw = (virtual_path or "").strip()
        if not raw:
            raise ValueError("workspace path is empty")

        path = Path(raw)
        candidate = path if path.is_absolute() else self.root / raw.lstrip("/")
        resolved = candidate.resolve()

        try:
            relative = resolved.relative_to(self.root.resolve())
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc

        if not relative.parts:
            raise ValueError("workspace root path is not allowed")

        return str(relative).replace("\\", "/")


def test_get_stop_log_paths_by_job_id_supports_absolute_workspace_log_paths(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    node_dir = workspace_root / "task_123" / "run_81234" / "node_a" / "logs"
    node_dir.mkdir(parents=True, exist_ok=True)

    stop_run = {
        "process_id": "81234",
        "dag_task_id": "task_123",
        "flow_uuid": "task_123",
        "job_id": "job_1",
        "stop_name": "node_a",
        "log_path": str(node_dir / "stop.log"),
        "stdout_log_path": str(node_dir / "stdout.log"),
        "stderr_log_path": str(node_dir / "stderr.log"),
    }

    monkeypatch.setattr(
        dag_runtime_service,
        "get_piflow_stop_log_paths_by_job_id",
        lambda job_id: stop_run if job_id == "job_1" else None,
    )
    monkeypatch.setattr(
        dag_runtime_service,
        "WorkspaceManager",
        lambda: FakeWorkspaceManager(workspace_root),
    )

    result = get_stop_log_paths_by_job_id(job_id="job_1")

    assert result == {
        "process_id": "81234",
        "dag_task_id": "task_123",
        "flow_uuid": "task_123",
        "job_id": "job_1",
        "stop_name": "node_a",
        "log_path": "task_123/run_81234/node_a/logs/stop.log",
        "stdout_log_path": "task_123/run_81234/node_a/logs/stdout.log",
        "stderr_log_path": "task_123/run_81234/node_a/logs/stderr.log",
    }


def test_get_stop_log_paths_by_job_id_rejects_path_outside_workspace(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    outside_path = tmp_path / "external" / "stdout.log"

    monkeypatch.setattr(
        dag_runtime_service,
        "get_piflow_stop_log_paths_by_job_id",
        lambda job_id: {
            "process_id": "81234",
            "dag_task_id": "task_123",
            "flow_uuid": "task_123",
            "job_id": job_id,
            "stop_name": "node_a",
            "log_path": str(outside_path),
            "stdout_log_path": None,
            "stderr_log_path": None,
        },
    )
    monkeypatch.setattr(
        dag_runtime_service,
        "WorkspaceManager",
        lambda: FakeWorkspaceManager(workspace_root),
    )

    with pytest.raises(ValueError, match="path escapes workspace"):
        get_stop_log_paths_by_job_id(job_id="job_1")
