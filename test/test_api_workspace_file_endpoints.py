from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import server


class FakeWorkspaceManager:
    def __init__(self, root: Path):
        self.root = root
        self.artifacts = self.root / "artifacts"
        self.outputs = self.root / "outputs"
        self.temp = self.root / "temp"
        self.logs = self.root / "logs"

    @staticmethod
    def _normalize_user_id(user_id: str) -> str:
        raw = (user_id or "").strip()
        if not raw:
            raise ValueError("user_id is required")
        if raw.startswith("/") or "\\" in raw:
            raise ValueError("user_id is invalid")
        parts = Path(raw).parts
        if len(parts) != 1 or parts[0] in {"", ".", ".."}:
            raise ValueError("user_id is invalid")
        return parts[0]

    def ensure_workspace(self):
        for path in (self.root, self.artifacts, self.outputs, self.temp, self.logs):
            path.mkdir(parents=True, exist_ok=True)

    def ensure_user_workspace(self, user_id: str):
        user_root = self.root / "users" / self._normalize_user_id(user_id)
        for path in (
            user_root,
            user_root / "artifacts",
            user_root / "outputs",
            user_root / "temp",
            user_root / "logs",
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _normalize_user_relative_path(self, user_id: str, virtual_path: str) -> str:
        normalized_user_id = self._normalize_user_id(user_id)
        raw = (virtual_path or "").strip()
        if not raw:
            raise ValueError("workspace path is empty")

        prefix = f"/users/{normalized_user_id}"
        if raw == prefix:
            raise ValueError("user workspace root path is not allowed")
        if raw.startswith(prefix + "/"):
            raw = raw[len(prefix):]
        elif raw.startswith("/users/"):
            parts = Path(raw.lstrip("/")).parts
            if len(parts) >= 2 and parts[1] != normalized_user_id:
                raise ValueError("path belongs to another user")
            if len(parts) >= 2 and parts[1] == normalized_user_id:
                raw = "/" + "/".join(parts[2:])
            else:
                raw = raw.lstrip("/")
        elif raw.startswith("/"):
            raw = raw.lstrip("/")

        relative = raw.lstrip("/")
        if not relative:
            raise ValueError("user workspace root path is not allowed")

        parts = Path(relative).parts
        if any(part in ("..", "") for part in parts):
            raise ValueError("user workspace path is invalid")

        return "/".join(parts)

    def resolve_user_virtual_path(self, user_id: str, virtual_path: str, create_parent: bool = False) -> Path:
        user_root = (self.root / "users" / self._normalize_user_id(user_id)).resolve()
        relative = self._normalize_user_relative_path(user_id, virtual_path)
        resolved = (user_root / relative).resolve()
        try:
            resolved.relative_to(user_root)
        except ValueError as exc:
            raise ValueError(f"path escapes user workspace: {virtual_path}") from exc
        if create_parent:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def to_user_relative_path(self, user_id: str, virtual_path: str) -> str:
        return "/" + self._normalize_user_relative_path(user_id, virtual_path)


@pytest.fixture
def client(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"

    def fake_workspace_manager():
        return FakeWorkspaceManager(workspace_root)

    monkeypatch.setattr(server, "WorkspaceManager", fake_workspace_manager)
    monkeypatch.setattr(
        server,
        "save_chat_file",
        lambda **kwargs: {
            "file_id": 1,
            "user_id": kwargs["user_id"],
            "thread_id": kwargs["thread_id"],
            "message_id": kwargs["message_id"],
            "virtual_path": kwargs["virtual_path"],
            "original_filename": kwargs["original_filename"],
        },
    )
    monkeypatch.setattr(
        server,
        "get_user_threads",
        lambda user_id: [{"thread_id": "chat_001", "title": "chat_001", "updated_at": "now"}],
    )

    original_startup = list(server.app.router.on_startup)
    server.app.router.on_startup.clear()

    with TestClient(server.app) as test_client:
        yield test_client, workspace_root

    server.app.router.on_startup[:] = original_startup


def test_upload_workspace_file_stores_relative_path_under_user_workspace(client):
    test_client, workspace_root = client

    response = test_client.post(
        "/workspace/upload",
        data={
            "user_id": "alice",
            "thread_id": "chat_001",
            "message_id": "12",
        },
        files={"file": ("report.csv", b"a,b\n1,2\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["path"] == "/temp/chat_001/12_report.csv"
    assert response.json()["original_filename"] == "report.csv"
    assert response.json()["user_id"] == "alice"

    assert (workspace_root / "users" / "alice" / "temp" / "chat_001" / "12_report.csv").read_text(
        encoding="utf-8"
    ) == "a,b\n1,2\n"


def test_download_workspace_file_supports_user_relative_and_prefixed_paths(client):
    test_client, workspace_root = client
    download_file = workspace_root / "users" / "alice" / "outputs" / "result.csv"
    download_file.parent.mkdir(parents=True, exist_ok=True)
    download_file.write_text("id,value\n1,ok\n", encoding="utf-8")

    relative_response = test_client.get(
        "/workspace/download",
        params={"user_id": "alice", "path": "/outputs/result.csv"},
    )
    assert relative_response.status_code == 200
    assert relative_response.content == b"id,value\n1,ok\n"

    prefixed_response = test_client.get(
        "/workspace/download",
        params={"user_id": "alice", "path": "/users/alice/outputs/result.csv"},
    )
    assert prefixed_response.status_code == 200
    assert prefixed_response.content == b"id,value\n1,ok\n"


def test_attach_message_files_stores_relative_path_and_validates_user_workspace(client):
    test_client, workspace_root = client
    attach_file = workspace_root / "users" / "alice" / "temp" / "chat_001" / "12_report.csv"
    attach_file.parent.mkdir(parents=True, exist_ok=True)
    attach_file.write_text("a,b\n1,2\n", encoding="utf-8")

    response = test_client.post(
        "/message/attach",
        json={
            "user_id": "alice",
            "thread_id": "chat_001",
            "message_id": 12,
            "attachments": [
                {
                    "path": "/users/alice/temp/chat_001/12_report.csv",
                    "name": "report.csv",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["attachments"] == [
        {
            "file_id": 1,
            "path": "/temp/chat_001/12_report.csv",
            "name": "report.csv",
        }
    ]
