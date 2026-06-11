from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

import server


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

        root_resolved = self.root.resolve()
        input_path = Path(raw)
        if raw.startswith("/"):
            first_part = Path(raw.lstrip("/")).parts[:1]
            if first_part and first_part[0] in self.ALLOWED_DIRS:
                candidate = self.root / raw.lstrip("/")
            elif input_path.is_absolute() and str(input_path.resolve()).startswith(str(root_resolved)):
                candidate = input_path
            else:
                candidate = input_path
        elif input_path.is_absolute():
            candidate = input_path
        else:
            candidate = self.root / raw.lstrip("/")

        resolved = candidate.resolve()
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


class FakeMinioObject:

    def __init__(
        self,
        object_name: str,
        is_dir: bool = False,
        size: int | None = None,
        last_modified: datetime | None = None,
    ):
        self.object_name = object_name
        self.is_dir = is_dir
        self.size = size
        self.last_modified = last_modified


class FakeObjectStorageService:

    def __init__(self, workspace_root: Path):
        self.workspace = FakeWorkspaceManager(workspace_root)
        self.workspace.ensure_workspace()
        self.saved_calls: list[tuple[str, str, str]] = []

    def save_local_file(self, user_id: str, target_path: str, local_path: str):
        self.saved_calls.append((user_id, target_path, local_path))
        source = self.workspace.resolve_virtual_path(local_path)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError("local file not found")

        bucket = "bbb" if "_" in user_id else "admin"
        return {
            "bucket": bucket,
            "path": target_path,
            "object_key": f"corpus/output/piflow/{target_path}",
            "source_path": str(source),
            "size": source.stat().st_size,
        }

    def list_directory(self, user_id: str, dir_path: str):
        if ".." in dir_path:
            raise ValueError("dir_path is invalid")

        bucket = "bbb" if "_" in user_id else "admin"
        if dir_path == "":
            items = [
                {
                    "name": "task1",
                    "path": "task1",
                    "type": "directory",
                    "size": None,
                    "last_modified": None,
                },
                {
                    "name": "result.json",
                    "path": "result.json",
                    "type": "file",
                    "size": 12,
                    "last_modified": datetime(2026, 6, 11, 8, 0, tzinfo=timezone.utc).isoformat(),
                },
            ]
        else:
            items = [
                {
                    "name": "nested.json",
                    "path": f"{dir_path}/nested.json",
                    "type": "file",
                    "size": 24,
                    "last_modified": datetime(2026, 6, 11, 9, 0, tzinfo=timezone.utc).isoformat(),
                }
            ]

        return {
            "bucket": bucket,
            "dir_path": dir_path,
            "items": items,
        }


def _setup_client(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    fake_service = FakeObjectStorageService(workspace_root)

    monkeypatch.setattr(server, "ObjectStorageService", lambda: fake_service)

    original_startup = list(server.app.router.on_startup)
    server.app.router.on_startup.clear()

    client = TestClient(server.app)
    return client, workspace_root, fake_service, original_startup


def _teardown_client(client, original_startup):
    client.close()
    server.app.router.on_startup[:] = original_startup


def test_save_storage_file_uses_workspace_relative_path_and_bucket_rule(tmp_path, monkeypatch):
    client, workspace_root, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        source = workspace_root / "outputs" / "result.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('{"ok":true}', encoding="utf-8")

        response = client.post(
            "/storage/save",
            json={
                "user_id": "admin",
                "target_path": "task1/result.json",
                "local_path": "/outputs/result.json",
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "bucket": "admin",
            "path": "task1/result.json",
            "object_key": "corpus/output/piflow/task1/result.json",
            "source_path": str(source),
            "size": len('{"ok":true}'),
        }
    finally:
        _teardown_client(client, original_startup)


def test_save_storage_file_supports_absolute_workspace_path_and_admin_fallback(tmp_path, monkeypatch):
    client, workspace_root, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        source = workspace_root / "outputs" / "absolute.json"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('{"absolute":1}', encoding="utf-8")

        response = client.post(
            "/storage/save",
            json={
                "user_id": "admin",
                "target_path": "task2/absolute.json",
                "local_path": str(source),
            },
        )

        assert response.status_code == 200
        assert response.json()["bucket"] == "admin"
        assert response.json()["object_key"] == "corpus/output/piflow/task2/absolute.json"
        assert response.json()["source_path"] == str(source)
    finally:
        _teardown_client(client, original_startup)


def test_save_storage_file_rejects_missing_local_file(tmp_path, monkeypatch):
    client, _, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/storage/save",
            json={
                "user_id": "admin",
                "target_path": "task1/missing.json",
                "local_path": "/outputs/missing.json",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "local file not found"
    finally:
        _teardown_client(client, original_startup)


def test_list_storage_files_returns_current_level_entries(tmp_path, monkeypatch):
    client, _, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/storage/list",
            json={
                "user_id": "aaa_bbb",
                "dir_path": "",
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "bucket": "bbb",
            "dir_path": "",
            "items": [
                {
                    "name": "task1",
                    "path": "task1",
                    "type": "directory",
                    "size": None,
                    "last_modified": None,
                },
                {
                    "name": "result.json",
                    "path": "result.json",
                    "type": "file",
                    "size": 12,
                    "last_modified": "2026-06-11T08:00:00+00:00",
                },
            ],
        }
    finally:
        _teardown_client(client, original_startup)


def test_list_storage_files_supports_nested_directory_iteration(tmp_path, monkeypatch):
    client, _, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/storage/list",
            json={
                "user_id": "admin",
                "dir_path": "task1",
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "bucket": "admin",
            "dir_path": "task1",
            "items": [
                {
                    "name": "nested.json",
                    "path": "task1/nested.json",
                    "type": "file",
                    "size": 24,
                    "last_modified": "2026-06-11T09:00:00+00:00",
                }
            ],
        }
    finally:
        _teardown_client(client, original_startup)


def test_list_storage_files_rejects_invalid_directory_path(tmp_path, monkeypatch):
    client, _, _, original_startup = _setup_client(tmp_path, monkeypatch)
    try:
        response = client.post(
            "/storage/list",
            json={
                "user_id": "admin",
                "dir_path": "../secret",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "dir_path is invalid"
    finally:
        _teardown_client(client, original_startup)
