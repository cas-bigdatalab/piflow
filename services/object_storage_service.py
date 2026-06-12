from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from minio import Minio

from infra.config_loader import get_settings
from runtime.workspace_manager import WorkspaceManager


def resolve_bucket_name(user_id: str) -> str:
    normalized = (user_id or "").strip()
    if not normalized:
        raise ValueError("user_id is required")

    if "_" not in normalized:
        return "admin"

    _, bucket = normalized.rsplit("_", 1)
    bucket = bucket.strip()
    if not bucket:
        raise ValueError("bucket suffix is empty")
    return bucket


def normalize_bucket_relative_path(path: str) -> str:
    raw = (path or "").strip().strip("/")
    if not raw:
        raise ValueError("target path is required")

    parts = Path(raw).parts
    if any(part in ("..", "") for part in parts):
        raise ValueError("target path is invalid")

    return "/".join(parts)


def join_object_key(base_prefix: str, relative_path: str) -> str:
    prefix = (base_prefix or "").strip().strip("/")
    rel = normalize_bucket_relative_path(relative_path)
    return f"{prefix}/{rel}" if prefix else rel


def _to_relative_display_path(base_prefix: str, full_key: str) -> str:
    prefix = (base_prefix or "").strip().strip("/")
    normalized = (full_key or "").strip().strip("/")
    if prefix:
        prefix_with_sep = prefix + "/"
        if normalized.startswith(prefix_with_sep):
            return normalized[len(prefix_with_sep):]
        if normalized == prefix:
            return ""
    return normalized


@dataclass
class StorageListItem:
    name: str
    path: str
    type: str
    size: int | None = None
    last_modified: datetime | None = None


class ObjectStorageService:

    def __init__(self, client: Any | None = None, workspace: WorkspaceManager | None = None):
        settings = get_settings()
        self.config = settings.minio
        self.workspace = workspace or WorkspaceManager()
        self.client = client or Minio(
            self.config.endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            secure=self.config.secure,
        )

    def resolve_local_file(self, local_path: str) -> Path:
        raw = (local_path or "").strip()
        if not raw:
            raise ValueError("local_path is required")

        return self.workspace.resolve_virtual_path(raw)

    def save_local_file(self, user_id: str, target_path: str, local_path: str) -> dict[str, Any]:
        bucket_name = resolve_bucket_name(user_id)
        source = self.resolve_local_file(local_path)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError("local file not found")

        object_key = join_object_key(self.config.base_prefix, target_path)
        self.client.fput_object(bucket_name, object_key, str(source))

        stat = source.stat()
        return {
            "bucket": bucket_name,
            "path": normalize_bucket_relative_path(target_path),
            "object_key": object_key,
            "source_path": str(source),
            "size": stat.st_size,
        }

    def list_directory(self, user_id: str, dir_path: str) -> dict[str, Any]:
        bucket_name = resolve_bucket_name(user_id)
        relative_dir = self._normalize_directory_path(dir_path)
        prefix = self._build_list_prefix(relative_dir)

        objects = self.client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=False,
        )

        items: list[StorageListItem] = []
        for entry in objects:
            object_name = (getattr(entry, "object_name", "") or "").strip("/")
            is_dir = bool(getattr(entry, "is_dir", False))
            display_path = _to_relative_display_path(self.config.base_prefix, object_name)
            display_path = display_path.rstrip("/") if is_dir else display_path
            name = Path(display_path).name if display_path else ""
            if not name:
                continue

            items.append(
                StorageListItem(
                    name=name,
                    path=display_path,
                    type="directory" if is_dir else "file",
                    size=None if is_dir else getattr(entry, "size", None),
                    last_modified=getattr(entry, "last_modified", None),
                )
            )

        items.sort(key=lambda item: (item.type != "directory", item.name))
        return {
            "bucket": bucket_name,
            "dir_path": relative_dir,
            "items": [
                {
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "last_modified": item.last_modified.isoformat() if item.last_modified else None,
                }
                for item in items
            ],
        }

    def _build_list_prefix(self, relative_dir: str) -> str:
        prefix = (self.config.base_prefix or "").strip().strip("/")
        if not relative_dir:
            return f"{prefix}/" if prefix else ""
        return f"{prefix}/{relative_dir}/" if prefix else f"{relative_dir}/"

    @staticmethod
    def _normalize_directory_path(dir_path: str) -> str:
        raw = (dir_path or "").strip().strip("/")
        if not raw:
            return ""

        parts = Path(raw).parts
        if any(part in ("..", "") for part in parts):
            raise ValueError("dir_path is invalid")

        return "/".join(parts)
