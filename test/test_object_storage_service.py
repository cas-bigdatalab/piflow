from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.object_storage_service import (
    ObjectStorageService,
    join_object_key,
    normalize_bucket_relative_path,
    resolve_bucket_name,
)


class DummyWorkspace:

    def __init__(self, root: Path):
        self.root = root

    def resolve_virtual_path(self, virtual_path: str) -> Path:
        raw = (virtual_path or "").strip()
        if not raw:
            raise ValueError("workspace path is empty")

        input_path = Path(raw)
        if input_path.is_absolute():
            candidate = input_path
        else:
            candidate = self.root / raw.lstrip("/")

        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root.resolve())
        except ValueError as exc:
            raise ValueError(f"path escapes workspace: {virtual_path}") from exc
        return resolved


class DummyMinioObject:

    def __init__(self, object_name, is_dir=False, size=None, last_modified=None):
        self.object_name = object_name
        self.is_dir = is_dir
        self.size = size
        self.last_modified = last_modified


class DummyMinioClient:

    def __init__(self):
        self.saved = []
        self.list_calls = []
        self.entries = []

    def fput_object(self, bucket_name, object_key, file_path):
        self.saved.append((bucket_name, object_key, file_path))

    def list_objects(self, bucket_name, prefix, recursive=False):
        self.list_calls.append((bucket_name, prefix, recursive))
        return list(self.entries)


def test_resolve_bucket_name_uses_suffix_or_admin_fallback():
    assert resolve_bucket_name("aaa_bbb") == "bbb"
    assert resolve_bucket_name("admin") == "admin"


def test_resolve_bucket_name_rejects_empty_suffix():
    with pytest.raises(ValueError, match="bucket suffix is empty"):
        resolve_bucket_name("aaa_")


def test_normalize_bucket_relative_path_and_join_key():
    assert normalize_bucket_relative_path("/task1/result.json") == "task1/result.json"
    assert join_object_key("corpus/output/piflow", "task1/result.json") == (
        "corpus/output/piflow/task1/result.json"
    )


def test_normalize_bucket_relative_path_rejects_parent_escape():
    with pytest.raises(ValueError, match="target path is invalid"):
        normalize_bucket_relative_path("../secret.json")


def test_save_local_file_uploads_to_expected_bucket_and_object_key(tmp_path, monkeypatch):
    source = tmp_path / "outputs" / "result.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('{"ok":true}', encoding="utf-8")

    fake_client = DummyMinioClient()
    workspace = DummyWorkspace(tmp_path)
    service = ObjectStorageService(client=fake_client, workspace=workspace)
    monkeypatch.setattr(service.config, "base_prefix", "corpus/output/piflow")

    result = service.save_local_file("aaa_bbb", "task1/result.json", str(source))

    assert fake_client.saved == [
        ("bbb", "corpus/output/piflow/task1/result.json", str(source))
    ]
    assert result["bucket"] == "bbb"
    assert result["path"] == "task1/result.json"


def test_list_directory_lists_current_prefix_only(tmp_path, monkeypatch):
    fake_client = DummyMinioClient()
    fake_client.entries = [
        DummyMinioObject("corpus/output/piflow/task1/", is_dir=True),
        DummyMinioObject(
            "corpus/output/piflow/result.json",
            is_dir=False,
            size=12,
            last_modified=datetime(2026, 6, 11, 8, 0, tzinfo=timezone.utc),
        ),
    ]
    workspace = DummyWorkspace(tmp_path)
    service = ObjectStorageService(client=fake_client, workspace=workspace)
    monkeypatch.setattr(service.config, "base_prefix", "corpus/output/piflow")

    result = service.list_directory("admin", "")

    assert fake_client.list_calls == [("admin", "corpus/output/piflow/", False)]
    assert result == {
        "bucket": "admin",
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


def test_list_directory_rejects_invalid_dir_path(tmp_path):
    service = ObjectStorageService(client=DummyMinioClient(), workspace=DummyWorkspace(tmp_path))

    with pytest.raises(ValueError, match="dir_path is invalid"):
        service.list_directory("admin", "../secret")
