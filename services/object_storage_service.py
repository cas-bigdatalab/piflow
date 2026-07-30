from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
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
        self.juicefs_config = settings.juicefs
        self.workspace = workspace or WorkspaceManager()
        self.client = client or Minio(
            self.config.endpoint,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            secure=self.config.secure,
        )
        self.juicefs_client = client or Minio(
            self.juicefs_config.endpoint,
            access_key=self.juicefs_config.access_key,
            secret_key=self.juicefs_config.secret_key,
            secure=self.juicefs_config.secure,
        )

    def resolve_local_file(self, local_path: str) -> Path:
        raw = (local_path or "").strip()
        if not raw:
            raise ValueError("local_path is required")

        return self.workspace.resolve_virtual_path(raw)

    def resolve_user_local_file(self, user_id: str, local_path: str) -> Path:
        raw = (local_path or "").strip()
        if not raw:
            raise ValueError("local_path is required")

        return self.workspace.resolve_user_virtual_path(user_id, raw)

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

    def save_local_file_juicefs(self, user_id: str, target_path: str, local_path: str) -> dict[str, Any]:
        bucket_name = resolve_bucket_name(user_id)
        self._ensure_juicefs_bucket(bucket_name)
        source = self.resolve_user_local_file(user_id, local_path)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError("local file not found")

        object_key = self._build_juicefs_object_key(bucket_name, target_path)
        self.juicefs_client.fput_object(bucket_name, object_key, str(source))

        stat = source.stat()
        return {
            "user_id": user_id,
            "desktop_id": user_id,
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

    def list_directory_juicefs(self, user_id: str, dir_path: str) -> dict[str, Any]:
        bucket_name = resolve_bucket_name(user_id)
        self._ensure_juicefs_bucket(bucket_name)
        relative_dir = self._normalize_directory_path(dir_path)
        prefix = self._build_juicefs_prefix(bucket_name, relative_dir)

        objects = self.juicefs_client.list_objects(
            bucket_name,
            prefix=prefix,
            recursive=False,
        )

        items = self._collect_juicefs_list_items(
            objects,
            root_prefix=self._build_juicefs_root_prefix(bucket_name),
            current_prefix=prefix,
        )
        return {
            "user_id": user_id,
            "desktop_id": user_id,
            "dir_path": relative_dir,
            "prefix": prefix,
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

    def mkdir_juicefs(self, user_id: str, dir_path: str) -> dict[str, Any]:
        bucket_name = resolve_bucket_name(user_id)
        self._ensure_juicefs_bucket(bucket_name)
        relative_dir = self._normalize_directory_path(dir_path)
        if not relative_dir:
            raise ValueError("dir_path is required")

        object_key = self._build_juicefs_directory_key(bucket_name, relative_dir)
        self.juicefs_client.put_object(bucket_name, object_key, data=BytesIO(b""), length=0)

        return {
            "user_id": user_id,
            "desktop_id": user_id,
            "dir_path": relative_dir,
            "object_key": object_key,
            "created": True,
        }

    def _build_list_prefix(self, relative_dir: str) -> str:
        prefix = (self.config.base_prefix or "").strip().strip("/")
        if not relative_dir:
            return f"{prefix}/" if prefix else ""
        return f"{prefix}/{relative_dir}/" if prefix else f"{relative_dir}/"

    def _build_juicefs_prefix(self, bucket_name: str, relative_dir: str) -> str:
        root_prefix = self._build_juicefs_root_prefix(bucket_name)
        if not relative_dir:
            return f"{root_prefix}/"
        return f"{root_prefix}/{relative_dir}/"

    def _build_juicefs_root_prefix(self, bucket_name: str) -> str:
        prefix = (self.juicefs_config.base_prefix or "").strip().strip("/")
        return f"corpus/{bucket_name}/{prefix}" if prefix else f"corpus/{bucket_name}"

    def _ensure_juicefs_bucket(self, bucket_name: str) -> None:
        if not self.juicefs_client.bucket_exists(bucket_name):
            self.juicefs_client.make_bucket(bucket_name)

    def _build_juicefs_object_key(self, bucket_name: str, relative_path: str) -> str:
        return f"{self._build_juicefs_prefix(bucket_name, '')}{normalize_bucket_relative_path(relative_path)}"

    def _build_juicefs_directory_key(self, bucket_name: str, relative_dir: str) -> str:
        prefix = self._build_juicefs_prefix(bucket_name, relative_dir)
        return prefix if prefix.endswith("/") else f"{prefix}/"

    @staticmethod
    def _collect_juicefs_list_items(
        objects: Any,
        root_prefix: str,
        current_prefix: str,
    ) -> list[StorageListItem]:
        items: list[StorageListItem] = []
        normalized_root_prefix = root_prefix.strip().strip("/")
        normalized_current_prefix = current_prefix.strip().strip("/")
        for entry in objects:
            object_name = (getattr(entry, "object_name", "") or "").strip("/")
            is_dir = bool(getattr(entry, "is_dir", False))

            # Skip the current directory's own placeholder object.
            if normalized_current_prefix and object_name == normalized_current_prefix:
                continue

            full_display_path = object_name
            if normalized_root_prefix and full_display_path.startswith(normalized_root_prefix + "/"):
                full_display_path = full_display_path[len(normalized_root_prefix) + 1 :]
            full_display_path = full_display_path.rstrip("/") if is_dir else full_display_path
            if not full_display_path:
                continue

            current_display_path = object_name
            if normalized_current_prefix and current_display_path.startswith(normalized_current_prefix + "/"):
                current_display_path = current_display_path[len(normalized_current_prefix) + 1 :]
            current_display_path = current_display_path.rstrip("/") if is_dir else current_display_path
            name = Path(current_display_path).name if current_display_path else ""
            if not name:
                continue

            items.append(
                StorageListItem(
                    name=name,
                    path=full_display_path,
                    type="directory" if is_dir else "file",
                    size=None if is_dir else getattr(entry, "size", None),
                    last_modified=getattr(entry, "last_modified", None),
                )
            )

        items.sort(key=lambda item: (item.type != "directory", item.name))
        return items

    @staticmethod
    def _normalize_directory_path(dir_path: str) -> str:
        raw = (dir_path or "").strip().strip("/")
        if not raw:
            return ""

        parts = Path(raw).parts
        if any(part in ("..", "") for part in parts):
            raise ValueError("dir_path is invalid")

        return "/".join(parts)
