from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from minio import Minio
from minio.error import S3Error

from repositories.s3_source_repository import (
    delete_s3_source as delete_s3_source_record,
    get_s3_source_by_id,
    insert_s3_source,
    list_s3_sources,
    update_s3_source as update_s3_source_record,
)


class S3SourceError(Exception):
    pass


@dataclass
class S3Source:
    source_id: str
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    bucket: str
    base_prefix: str
    logo: str
    created_at: Any = None
    updated_at: Any = None

    def to_client(self) -> Minio:
        return _create_minio_client(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )


def create_s3_source(
    *,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
    base_prefix: str,
    logo: str | None = None,
) -> S3Source:
    resolved = validate_s3_source_connection(
        name=name,
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        bucket=bucket,
        base_prefix=base_prefix,
        logo=logo,
    )

    record = insert_s3_source(
        name=resolved["name"],
        endpoint=resolved["endpoint"],
        access_key=resolved["access_key"],
        secret_key=resolved["secret_key"],
        secure=resolved["secure"],
        bucket=resolved["bucket"],
        base_prefix=resolved["base_prefix"],
        logo=resolved["logo"],
    )
    return _build_s3_source(record)


def update_s3_source(
    *,
    source_id: str,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
    base_prefix: str,
    logo: str | None = None,
) -> S3Source:
    resolved = validate_s3_source_connection(
        name=name,
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
        bucket=bucket,
        base_prefix=base_prefix,
        logo=logo,
    )

    record = update_s3_source_record(
        source_id=source_id,
        name=resolved["name"],
        endpoint=resolved["endpoint"],
        access_key=resolved["access_key"],
        secret_key=resolved["secret_key"],
        secure=resolved["secure"],
        bucket=resolved["bucket"],
        base_prefix=resolved["base_prefix"],
        logo=resolved["logo"],
    )
    if not record:
        raise S3SourceError(f"s3 source not found: {source_id}")
    return _build_s3_source(record)


def delete_s3_source(source_id: str) -> None:
    if not delete_s3_source_record(source_id):
        raise S3SourceError(f"s3 source not found: {source_id}")


def validate_s3_source_connection(
    *,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
    base_prefix: str,
    logo: str | None = None,
) -> dict[str, Any]:
    normalized_name = _require_non_empty(name, "name")
    normalized_endpoint = _normalize_endpoint(endpoint)
    normalized_access_key = _require_non_empty(access_key, "access_key")
    normalized_secret_key = _require_non_empty(secret_key, "secret_key")
    normalized_bucket = _normalize_bucket_name(bucket)
    normalized_base_prefix = _normalize_base_prefix(base_prefix)
    resolved_logo = str(logo or "").strip()

    try:
        client = _create_minio_client(
            endpoint=normalized_endpoint,
            access_key=normalized_access_key,
            secret_key=normalized_secret_key,
            secure=secure,
        )
    except Exception as exc:
        raise S3SourceError(f"s3 client initialization failed: {exc}") from exc

    try:
        exists = client.bucket_exists(normalized_bucket)
    except S3Error as exc:
        raise S3SourceError(f"failed to access bucket={normalized_bucket}: {exc}") from exc
    except Exception as exc:
        raise S3SourceError(f"failed to access bucket={normalized_bucket}: {exc}") from exc
    if not exists:
        raise S3SourceError(f"s3 bucket not found: {normalized_bucket}")

    probe_prefix = f"{normalized_base_prefix}/" if normalized_base_prefix else ""
    try:
        iterator = client.list_objects(
            normalized_bucket,
            prefix=probe_prefix,
            recursive=False,
        )
        next(iter(iterator), None)
    except S3Error as exc:
        raise S3SourceError(f"failed to list s3 prefix '{probe_prefix}': {exc}") from exc
    except Exception as exc:
        raise S3SourceError(f"failed to list s3 prefix '{probe_prefix}': {exc}") from exc

    return {
        "name": normalized_name,
        "endpoint": normalized_endpoint,
        "access_key": normalized_access_key,
        "secret_key": normalized_secret_key,
        "secure": bool(secure),
        "bucket": normalized_bucket,
        "base_prefix": normalized_base_prefix,
        "logo": resolved_logo,
    }


def validate_registered_s3_source(source_id: str) -> dict[str, Any]:
    source = get_s3_source(source_id)
    resolved = validate_s3_source_connection(
        name=source.name,
        endpoint=source.endpoint,
        access_key=source.access_key,
        secret_key=source.secret_key,
        secure=source.secure,
        bucket=source.bucket,
        base_prefix=source.base_prefix,
        logo=source.logo,
    )
    return {
        "source_id": source.source_id,
        **resolved,
    }


def get_s3_source(source_id: str) -> S3Source:
    record = get_s3_source_by_id(source_id)
    if not record:
        raise S3SourceError(f"s3 source not found: {source_id}")
    return _build_s3_source(record)


def list_s3_source_directory(
    source_id: str,
    *,
    relative_path: str = "",
) -> dict[str, Any]:
    source = get_s3_source(source_id)
    client = source.to_client()
    normalized_relative = _normalize_optional_relative_path(relative_path)
    prefix = _build_list_prefix(source.base_prefix, normalized_relative)

    try:
        objects = client.list_objects(
            source.bucket,
            prefix=prefix,
            recursive=False,
        )
        entries = _collect_directory_entries(
            objects=objects,
            base_prefix=source.base_prefix,
            current_relative=normalized_relative,
        )
    except S3Error as exc:
        raise S3SourceError(f"failed to list s3 directory: {exc}") from exc
    except Exception as exc:
        raise S3SourceError(f"failed to list s3 directory: {exc}") from exc

    return {
        "sourceId": source.source_id,
        "name": source.name,
        "bucket": source.bucket,
        "basePrefix": source.base_prefix,
        "path": normalized_relative,
        "entries": entries,
    }


def download_s3_source_file(
    source_id: str,
    *,
    relative_path: str,
    target_dir: str | Path | None = None,
) -> dict[str, Any]:
    source = get_s3_source(source_id)
    normalized_relative = _normalize_required_relative_path(relative_path)
    object_key = _join_object_key(source.base_prefix, normalized_relative)
    target_root = Path(target_dir or Path.cwd()).expanduser().resolve()
    local_path = target_root / Path(normalized_relative)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        stat = client_stat = source.to_client().stat_object(source.bucket, object_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
            raise S3SourceError(f"s3 file not found: {normalized_relative}") from exc
        raise S3SourceError(f"failed to stat s3 file '{normalized_relative}': {exc}") from exc
    except Exception as exc:
        raise S3SourceError(f"failed to stat s3 file '{normalized_relative}': {exc}") from exc

    if object_key.endswith("/") or getattr(stat, "size", None) == 0 and normalized_relative.endswith("/"):
        raise S3SourceError(f"s3 path is a directory: {normalized_relative}")

    try:
        source.to_client().fget_object(source.bucket, object_key, str(local_path))
    except S3Error as exc:
        raise S3SourceError(f"failed to download s3 file '{normalized_relative}': {exc}") from exc
    except Exception as exc:
        raise S3SourceError(f"failed to download s3 file '{normalized_relative}': {exc}") from exc

    return {
        "sourceId": source.source_id,
        "name": source.name,
        "bucket": source.bucket,
        "basePrefix": source.base_prefix,
        "path": normalized_relative,
        "objectKey": object_key,
        "localPath": str(local_path),
    }


def list_registered_s3_sources() -> list[S3Source]:
    return [_build_s3_source(record) for record in list_s3_sources()]


def _build_s3_source(record: dict[str, Any]) -> S3Source:
    return S3Source(
        source_id=str(record["source_id"]),
        name=str(record.get("name", "") or ""),
        endpoint=str(record["endpoint"]),
        access_key=str(record["access_key"]),
        secret_key=str(record["secret_key"]),
        secure=bool(record.get("secure", False)),
        bucket=str(record["bucket"]),
        base_prefix=_normalize_base_prefix(str(record.get("base_prefix", "") or "")),
        logo=str(record.get("logo", "") or ""),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _create_minio_client(
    *,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
) -> Minio:
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_endpoint(endpoint: str) -> str:
    normalized = _require_non_empty(endpoint, "endpoint")
    normalized = normalized.removeprefix("http://").removeprefix("https://").strip().rstrip("/")
    if not normalized:
        raise ValueError("endpoint is required")
    return normalized


def _normalize_bucket_name(bucket: str) -> str:
    normalized = _require_non_empty(bucket, "bucket")
    if "/" in normalized:
        raise ValueError("bucket is invalid")
    return normalized


def _normalize_base_prefix(base_prefix: str) -> str:
    raw = str(base_prefix or "").strip().strip("/")
    if not raw:
        return ""
    parts = Path(raw).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("base_prefix is invalid")
    return "/".join(parts)


def _normalize_required_relative_path(relative_path: str) -> str:
    normalized = _normalize_optional_relative_path(relative_path)
    if not normalized:
        raise ValueError("relative_path is required")
    return normalized


def _normalize_optional_relative_path(relative_path: str) -> str:
    raw = str(relative_path or "").strip().strip("/")
    if not raw:
        return ""
    parts = Path(raw).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("relative_path is invalid")
    return "/".join(parts)


def _join_object_key(base_prefix: str, relative_path: str) -> str:
    normalized_prefix = _normalize_base_prefix(base_prefix)
    normalized_relative = _normalize_required_relative_path(relative_path)
    return f"{normalized_prefix}/{normalized_relative}" if normalized_prefix else normalized_relative


def _build_list_prefix(base_prefix: str, relative_path: str) -> str:
    normalized_prefix = _normalize_base_prefix(base_prefix)
    normalized_relative = _normalize_optional_relative_path(relative_path)
    if normalized_prefix and normalized_relative:
        return f"{normalized_prefix}/{normalized_relative}/"
    if normalized_prefix:
        return f"{normalized_prefix}/"
    if normalized_relative:
        return f"{normalized_relative}/"
    return ""


def _collect_directory_entries(
    *,
    objects: Any,
    base_prefix: str,
    current_relative: str,
) -> list[dict[str, Any]]:
    normalized_base_prefix = _normalize_base_prefix(base_prefix)
    normalized_current = _normalize_optional_relative_path(current_relative)
    current_prefix = _build_list_prefix(normalized_base_prefix, normalized_current).strip("/")

    items: list[dict[str, Any]] = []
    for entry in objects:
        object_name = str(getattr(entry, "object_name", "") or "").strip("/")
        if not object_name:
            continue
        if current_prefix and object_name == current_prefix:
            continue

        relative = object_name
        if normalized_base_prefix:
            prefix_with_sep = normalized_base_prefix + "/"
            if relative == normalized_base_prefix:
                continue
            if relative.startswith(prefix_with_sep):
                relative = relative[len(prefix_with_sep) :]

        if normalized_current:
            current_with_sep = normalized_current + "/"
            if relative == normalized_current:
                continue
            if relative.startswith(current_with_sep):
                relative = relative[len(current_with_sep) :]

        relative = relative.strip("/")
        if not relative:
            continue

        is_dir = bool(getattr(entry, "is_dir", False))
        path_value = relative.rstrip("/") if is_dir else relative
        name = Path(path_value).name
        if not name:
            continue

        items.append(
            {
                "name": name,
                "path": path_value,
                "type": "directory" if is_dir else "file",
                "size": None if is_dir else getattr(entry, "size", None),
                "last_modified": getattr(entry, "last_modified", None).isoformat()
                if getattr(entry, "last_modified", None)
                else None,
            }
        )

    items.sort(key=lambda item: (item["type"] != "directory", item["name"]))
    return items
