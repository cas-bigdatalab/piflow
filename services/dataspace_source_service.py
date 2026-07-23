from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from piflow_engine.cn.piflow.engine.datasource import DataspaceClient, DataspaceError
from piflow_engine.cn.piflow.engine.datasource.dataspace_source import DataspaceSource
from repositories.dataspace_source_repository import (
    get_dataspace_source_by_id,
    insert_dataspace_source,
    list_dataspace_sources,
)


def create_dataspace_source(
    *,
    base_url: str,
    app_id: str,
    auth_code: str,
    space_name: str,
    ftp_user: str,
    ftp_password: str,
    logo: str | None = None,
) -> DataspaceSource:
    resolved = validate_dataspace_source_connection(
        base_url=base_url,
        app_id=app_id,
        auth_code=auth_code,
        space_name=space_name,
        ftp_user=ftp_user,
        ftp_password=ftp_password,
        logo=logo,
    )

    record = insert_dataspace_source(
        base_url=base_url,
        app_id=app_id,
        auth_code=auth_code,
        space_name=space_name,
        space_id=resolved["space_id"],
        ftp_user=ftp_user,
        ftp_password=ftp_password,
        ftp_link=resolved["ftp_link"],
        webdav_link=resolved["webdav_link"],
        root_path=resolved["root_path"],
        logo=resolved["logo"],
    )
    return _build_dataspace_source(record)


def validate_dataspace_source_connection(
    *,
    base_url: str,
    app_id: str,
    auth_code: str,
    space_name: str,
    ftp_user: str,
    ftp_password: str,
    logo: str | None = None,
) -> dict[str, Any]:
    client = DataspaceClient(
        base_url=base_url,
        app_id=app_id,
        auth_code=auth_code,
    )
    space_id = client.get_space_id_by_name(space_name)
    space_info = client.get_space_info(space_id)
    space_data = space_info.get("data") or {}
    upload_link = space_data.get("uploadLink") or {}

    ftp_link = str(upload_link.get("ftpLink", "")).strip()
    webdav_link = str(upload_link.get("webDavLink", "")).strip()
    root_path = _resolve_root_path(
        ftp_link=ftp_link,
        space_path=str(upload_link.get("spacePath", "")).strip(),
    )
    resolved_logo = str(logo or "").strip() or str(space_data.get("spaceLogo", "") or "")
    _ = client.list_ftp_directory(
        ftp_link,
        ftp_user,
        ftp_password,
        ftp_subpath="",
    )
    return {
        "base_url": base_url,
        "app_id": app_id,
        "auth_code": auth_code,
        "space_name": space_name,
        "space_id": space_id,
        "ftp_user": ftp_user,
        "ftp_password": ftp_password,
        "ftp_link": ftp_link,
        "webdav_link": webdav_link,
        "root_path": root_path,
        "logo": resolved_logo,
    }


def get_dataspace_source(source_id: str) -> DataspaceSource:
    record = get_dataspace_source_by_id(source_id)
    if not record:
        raise DataspaceError(f"dataspace source not found: {source_id}")
    return _build_dataspace_source(record)


def list_dataspace_source_directory(
    source_id: str,
    *,
    relative_path: str = "",
) -> dict[str, Any]:
    source = get_dataspace_source(source_id)
    client = source.to_client()
    entries = client.list_ftp_directory(
        source.ftp_link,
        source.ftp_user,
        source.ftp_password,
        ftp_subpath=relative_path,
    )
    remote_path = _join_root_relative(source.root_path, relative_path)
    return {
        "sourceId": source.source_id,
        "spaceName": source.space_name,
        "spaceId": source.space_id,
        "remotePath": remote_path,
        "entries": entries,
    }


def download_dataspace_source_file(
    source_id: str,
    *,
    relative_path: str,
    target_dir: str | Path | None = None,
) -> dict[str, Any]:
    source = get_dataspace_source(source_id)
    if not relative_path.strip():
        raise DataspaceError("relative_path is required")

    client = source.to_client()
    target_root = Path(target_dir or Path.cwd()).expanduser().resolve()
    local_path = target_root / Path(relative_path.strip().lstrip("/"))
    downloaded = client.download_ftp_file(
        source.ftp_link,
        source.ftp_user,
        source.ftp_password,
        relative_path=relative_path,
        local_path=local_path,
    )
    return {
        "sourceId": source.source_id,
        "spaceName": source.space_name,
        "spaceId": source.space_id,
        "remotePath": _join_root_relative(source.root_path, relative_path),
        "localPath": str(downloaded),
    }


def upload_dataspace_source_file(
    source_id: str,
    *,
    relative_path: str,
    local_path: str | Path,
) -> dict[str, Any]:
    source = get_dataspace_source(source_id)
    if not relative_path.strip():
        raise DataspaceError("relative_path is required")

    client = source.to_client()
    uploaded = client.upload_ftp_file(
        source.ftp_link,
        source.ftp_user,
        source.ftp_password,
        relative_path=relative_path,
        local_path=local_path,
    )
    return {
        "sourceId": source.source_id,
        "spaceName": source.space_name,
        "spaceId": source.space_id,
        "remotePath": _join_root_relative(source.root_path, relative_path),
        "localPath": str(uploaded),
    }


def upload_dataspace_source_directory(
    source_id: str,
    *,
    remote_relative_path: str,
    local_dir: str | Path,
) -> dict[str, Any]:
    source = get_dataspace_source(source_id)
    if not remote_relative_path.strip():
        raise DataspaceError("remote_relative_path is required")

    client = source.to_client()
    uploaded = client.upload_ftp_directory(
        source.ftp_link,
        source.ftp_user,
        source.ftp_password,
        local_dir=local_dir,
        remote_subpath=remote_relative_path,
    )
    return {
        "sourceId": source.source_id,
        "spaceName": source.space_name,
        "spaceId": source.space_id,
        "remotePath": _join_root_relative(source.root_path, remote_relative_path),
        "localDir": str(uploaded),
    }


def list_registered_dataspace_sources() -> list[DataspaceSource]:
    return [_build_dataspace_source(record) for record in list_dataspace_sources()]


def _build_dataspace_source(record: dict[str, Any]) -> DataspaceSource:
    return DataspaceSource(
        source_id=str(record["source_id"]),
        base_url=str(record["base_url"]),
        app_id=str(record["app_id"]),
        auth_code=str(record["auth_code"]),
        space_name=str(record["space_name"]),
        space_id=str(record["space_id"]),
        ftp_user=str(record["ftp_user"]),
        ftp_password=str(record["ftp_password"]),
        ftp_link=str(record.get("ftp_link", "") or ""),
        webdav_link=str(record.get("webdav_link", "") or ""),
        root_path=str(record.get("root_path", "") or ""),
        logo=str(record.get("logo", "") or ""),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )


def _resolve_root_path(*, ftp_link: str, space_path: str) -> str:
    if ftp_link:
        parsed = urlparse(ftp_link)
        path = parsed.path.strip()
        if path:
            return path

    if space_path:
        normalized = space_path.rstrip("/")
        if normalized:
            tail = normalized.rsplit("/", 1)[-1]
            return f"/{tail}"

    raise DataspaceError("unable to resolve dataspace root path from space info")


def _join_root_relative(root_path: str, relative_path: str) -> str:
    normalized_root = root_path or "/"
    normalized_relative = relative_path.strip()
    if not normalized_relative or normalized_relative == ".":
        return normalized_root
    if normalized_relative.startswith("/"):
        return normalized_relative
    return f"{normalized_root.rstrip('/')}/{normalized_relative.lstrip('/')}"
