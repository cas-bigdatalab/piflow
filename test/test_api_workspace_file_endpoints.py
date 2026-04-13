from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import server


class FakeWorkspaceManager:

    ALLOWED_DIRS = {"artifacts", "outputs", "temp", "logs"}

    def __init__(self, root: Path):
        self.root = root
        self.artifacts = self.root / "artifacts"
        self.outputs = self.root / "outputs"
        self.temp = self.root / "temp"
        self.logs = self.root / "logs"

    def ensure_workspace(self):
        for path in (self.root, self.artifacts, self.outputs, self.temp, self.logs):
            path.mkdir(parents=True, exist_ok=True)

    def resolve_virtual_path(self, virtual_path: str, create_parent: bool = False) -> Path:
        raw = (virtual_path or "").strip()
        if not raw:
            raise ValueError("workspace path is empty")

        relative = raw.lstrip("/")
        resolved = (self.root / relative).resolve()
        root_resolved = self.root.resolve()

        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc

        parts = resolved.relative_to(root_resolved).parts
        if not parts:
            raise ValueError("workspace root path is not allowed")

        if parts[0] not in self.ALLOWED_DIRS:
            raise ValueError(
                f"top-level workspace dir must be one of: {sorted(self.ALLOWED_DIRS)}"
            )

        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)

        return resolved


@pytest.fixture
def client(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"

    def fake_workspace_manager():
        return FakeWorkspaceManager(workspace_root)

    monkeypatch.setattr(server, "WorkspaceManager", fake_workspace_manager)

    original_startup = list(server.app.router.on_startup)
    server.app.router.on_startup.clear()

    with TestClient(server.app) as test_client:
        yield test_client, workspace_root

    server.app.router.on_startup[:] = original_startup


def test_upload_workspace_file_saves_to_temp_by_default(client):
    test_client, workspace_root = client

    response = test_client.post(
        "/workspace/upload",
        files={"file": ("sample.txt", b"hello workspace", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "path": "/temp/sample.txt",
        "filename": "sample.txt",
        "size": 15,
        "content_type": "text/plain",
    }
    assert (workspace_root / "temp" / "sample.txt").read_bytes() == b"hello workspace"


def test_upload_workspace_file_supports_custom_target_dir_and_filename(client):
    test_client, workspace_root = client

    response = test_client.post(
        "/workspace/upload",
        data={"target_dir": "outputs", "filename": "../report.csv"},
        files={"file": ("ignored-name.csv", b"a,b\n1,2\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["path"] == "/outputs/report.csv"
    assert response.json()["filename"] == "report.csv"
    assert (workspace_root / "outputs" / "report.csv").read_text(encoding="utf-8") == "a,b\n1,2\n"


def test_upload_workspace_file_rejects_disallowed_target_dir(client):
    test_client, _ = client

    response = test_client.post(
        "/workspace/upload",
        data={"target_dir": "skills"},
        files={"file": ("sample.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "top-level workspace dir must be one of" in response.json()["detail"]


def test_download_workspace_file_returns_file_contents(client):
    test_client, workspace_root = client
    download_file = workspace_root / "outputs" / "result.csv"
    download_file.parent.mkdir(parents=True, exist_ok=True)
    download_file.write_text("id,value\n1,ok\n", encoding="utf-8")

    response = test_client.get("/workspace/download", params={"path": "/outputs/result.csv"})

    assert response.status_code == 200
    assert response.content == b"id,value\n1,ok\n"
    assert 'attachment; filename="result.csv"' in response.headers["content-disposition"]


def test_download_workspace_file_rejects_invalid_or_missing_path(client):
    test_client, _ = client

    invalid_response = test_client.get(
        "/workspace/download",
        params={"path": "/../secrets.txt"},
    )
    assert invalid_response.status_code == 400
    assert "path escapes workspace" in invalid_response.json()["detail"]

    missing_response = test_client.get(
        "/workspace/download",
        params={"path": "/outputs/missing.csv"},
    )
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "file not found"
