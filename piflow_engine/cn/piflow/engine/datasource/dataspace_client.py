from __future__ import annotations

from ftplib import FTP, error_perm
import hashlib
import logging
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


DEFAULT_VERSION = "1.0"
DEFAULT_TIMEOUT_SECONDS = 30
logger = logging.getLogger(__name__)


class DataspaceError(RuntimeError):
    """Raised when the Dataspace OpenAPI request fails."""


@dataclass(frozen=True)
class DataspaceClient:
    base_url: str
    app_id: str
    auth_code: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    version: str = DEFAULT_VERSION

    def list_spaces(
        self,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        return self._get("/api/ds.open/space/listAll", params)

    def get_space_id_by_name(
        self,
        space_name: str,
        *,
        timestamp: str | None = None,
    ) -> str:
        payload = self.list_spaces(timestamp=timestamp)
        spaces = payload.get("data") or []
        matched_ids: list[str] = []
        for item in spaces:
            if not isinstance(item, dict):
                continue
            if str(item.get("spaceName", "")).strip() == space_name:
                space_id = str(
                    item.get("spaceId", "") or item.get("id", "")
                ).strip()
                if space_id:
                    matched_ids.append(space_id)

        if not matched_ids:
            raise DataspaceError(f"space not found by name: {space_name}")
        if len(matched_ids) > 1:
            raise DataspaceError(
                f"multiple spaces found by name: {space_name}, ids={matched_ids}"
            )
        return matched_ids[0]

    def get_space_info(
        self,
        space_id: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "spaceId": str(space_id),
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        return self._get("/api/ds.open/space/info", params)

    def list_space_directory_by_name(
        self,
        space_name: str,
        ftp_user: str,
        ftp_password: str,
        *,
        ftp_subpath: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        space_id = self.get_space_id_by_name(space_name, timestamp=timestamp)
        space_info = self.get_space_info(space_id, timestamp=timestamp)
        space_data = space_info.get("data") or {}
        upload_link = space_data.get("uploadLink") or {}
        ftp_link = str(upload_link.get("ftpLink", "")).strip()
        if not ftp_link:
            raise DataspaceError(
                f"space info does not contain ftpLink for space={space_name}"
            )

        ftp_config = self._parse_ftp_link(ftp_link)
        remote_path = self._resolve_ftp_remote_path(
            ftp_config["path"],
            ftp_subpath,
        )
        entries = self._list_ftp_directory(
            host=ftp_config["host"],
            port=ftp_config["port"],
            username=ftp_user,
            password=ftp_password,
            remote_path=remote_path,
        )
        return {
            "spaceName": space_name,
            "spaceId": space_id,
            "ftpLink": ftp_link,
            "remotePath": remote_path,
            "spaceInfo": space_info,
            "entries": entries,
        }

    def list_ftp_directory(
        self,
        ftp_link: str,
        ftp_user: str,
        ftp_password: str,
        *,
        ftp_subpath: str | None = None,
    ) -> list[dict[str, Any]]:
        ftp_config = self._parse_ftp_link(ftp_link)
        remote_path = self._resolve_ftp_remote_path(
            ftp_config["path"],
            ftp_subpath,
        )
        return self._list_ftp_directory(
            host=ftp_config["host"],
            port=ftp_config["port"],
            username=ftp_user,
            password=ftp_password,
            remote_path=remote_path,
            timeout_seconds=self.timeout_seconds,
        )

    def download_ftp_file(
        self,
        ftp_link: str,
        ftp_user: str,
        ftp_password: str,
        *,
        relative_path: str,
        local_path: str | Path,
    ) -> Path:
        ftp_config = self._parse_ftp_link(ftp_link)
        remote_path = self._resolve_ftp_remote_path(
            ftp_config["path"],
            relative_path,
        )
        target_path = Path(local_path).expanduser().resolve()
        self._download_ftp_file(
            host=ftp_config["host"],
            port=ftp_config["port"],
            username=ftp_user,
            password=ftp_password,
            remote_path=remote_path,
            local_path=target_path,
            timeout_seconds=self.timeout_seconds,
        )
        return target_path

    def upload_ftp_file(
        self,
        ftp_link: str,
        ftp_user: str,
        ftp_password: str,
        *,
        space_id: str | None = None,
        relative_path: str,
        local_path: str | Path,
    ) -> Path:
        ftp_config = self._parse_ftp_link(ftp_link)
        remote_path = self._resolve_ftp_remote_path(
            ftp_config["path"],
            relative_path,
        )
        source_path = Path(local_path).expanduser().resolve()
        self._upload_ftp_file(
            host=ftp_config["host"],
            port=ftp_config["port"],
            username=ftp_user,
            password=ftp_password,
            remote_path=remote_path,
            local_path=source_path,
            timeout_seconds=self.timeout_seconds,
        )
        if space_id:
            self._refresh_space_file_index_or_warn(space_id)
        return source_path

    def upload_ftp_directory(
        self,
        ftp_link: str,
        ftp_user: str,
        ftp_password: str,
        *,
        space_id: str | None = None,
        local_dir: str | Path,
        remote_subpath: str | None = None,
    ) -> Path:
        ftp_config = self._parse_ftp_link(ftp_link)
        remote_path = self._resolve_ftp_remote_path(
            ftp_config["path"],
            remote_subpath,
        )
        source_dir = Path(local_dir).expanduser().resolve()
        self._upload_ftp_directory(
            host=ftp_config["host"],
            port=ftp_config["port"],
            username=ftp_user,
            password=ftp_password,
            remote_path=remote_path,
            local_dir=source_dir,
            timeout_seconds=self.timeout_seconds,
        )
        if space_id:
            self._refresh_space_file_index_or_warn(space_id)
        return source_dir

    def refresh_space_file_index(
        self,
        space_id: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "spaceId": str(space_id).strip(),
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        if not params["spaceId"]:
            raise DataspaceError("space_id is required for space file refresh")
        return self._get("/api/ds.open/space/fl.syn", params)

    def _refresh_space_file_index_or_warn(self, space_id: str) -> None:
        try:
            self.refresh_space_file_index(space_id)
        except DataspaceError as exc:
            logger.warning(
                "refresh space file index failed for space_id=%s: %s",
                space_id,
                exc,
            )

    def get_user_info(
        self,
        email: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "email": email,
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        return self._get("/api/ds.open/userInfo", params)

    def list_user_spaces(
        self,
        user_id: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "userId": str(user_id),
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        return self._get("/api/ds.open/space/list", params)

    def list_user_spaces_by_email(
        self,
        email: str,
        *,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        request_timestamp = timestamp or self._timestamp()
        user_info = self.get_user_info(email, timestamp=request_timestamp)
        user_data = user_info.get("data") or {}
        user_id = str(user_data.get("id", "")).strip()
        if not user_id:
            raise DataspaceError(
                f"Dataspace user lookup returned no user id for email={email}"
            )

        spaces = self.list_user_spaces(user_id, timestamp=request_timestamp)
        return {
            "email": email,
            "userId": user_id,
            "userInfo": user_info,
            "spaceList": spaces,
        }

    def list_space_files(
        self,
        space_id: str,
        *,
        hash_value: str | None = None,
        page: int | None = None,
        size: int | None = None,
        direction: str | None = None,
        sort: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "spaceId": str(space_id),
            "hash": hash_value,
            "page": page,
            "size": size,
            "direction": direction,
            "sort": sort,
            "timestamp": timestamp or self._timestamp(),
            "version": self.version,
        }
        return self._get("/api/ds.open/space/fileList", params)

    def build_sign(self, params: dict[str, Any]) -> str:
        filtered: dict[str, str] = {}
        for key, value in params.items():
            if key == "sign" or value is None or value == "":
                continue
            if isinstance(value, (bytes, bytearray, memoryview)):
                continue
            filtered[str(key)] = str(value)

        canonical = "&".join(
            f"{key}={filtered[key]}"
            for key in sorted(filtered.keys())
        )
        return hashlib.md5(f"{canonical}{self.auth_code}".encode("utf-8")).hexdigest()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {
            key: value
            for key, value in params.items()
            if value is not None and value != ""
        }
        request_params["sign"] = self.build_sign(request_params)
        response = requests.get(
            self._url(path),
            params=request_params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != 200:
            raise DataspaceError(
                f"Dataspace request failed: code={payload.get('code')} "
                f"message={payload.get('message')}"
            )
        return payload

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    @staticmethod
    def _parse_ftp_link(ftp_link: str) -> dict[str, Any]:
        parsed = urlparse(ftp_link)
        if parsed.scheme.lower() != "ftp":
            raise DataspaceError(f"unsupported ftp link: {ftp_link}")
        host = parsed.hostname
        if not host:
            raise DataspaceError(f"ftp host is missing in link: {ftp_link}")
        return {
            "host": host,
            "port": parsed.port or 21,
            "path": parsed.path or "/",
        }

    @staticmethod
    def _resolve_ftp_remote_path(
        base_path: str,
        ftp_subpath: str | None,
    ) -> str:
        normalized_base = base_path or "/"
        if not ftp_subpath:
            return normalized_base

        normalized_subpath = ftp_subpath.strip()
        if not normalized_subpath or normalized_subpath == ".":
            return normalized_base

        if normalized_subpath.startswith("/"):
            return normalized_subpath

        return f"{normalized_base.rstrip('/')}/{normalized_subpath.lstrip('/')}"

    @staticmethod
    def _list_ftp_directory(
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> list[dict[str, Any]]:
        ftp = FTP()
        try:
            ftp.connect(host=host, port=port, timeout=timeout_seconds)
            ftp.login(user=username, passwd=password)
            ftp.cwd(remote_path)

            entries: list[dict[str, Any]] = []
            try:
                for name, facts in ftp.mlsd():
                    entries.append(
                        {
                            "name": name,
                            "type": facts.get("type", "unknown"),
                            "size": facts.get("size"),
                            "modify": facts.get("modify"),
                            "raw": facts,
                        }
                    )
                return entries
            except (error_perm, AttributeError):
                names = ftp.nlst()
                return [
                    {
                        "name": name.rsplit("/", 1)[-1],
                        "type": "unknown",
                        "size": None,
                        "modify": None,
                        "raw": None,
                    }
                    for name in names
                ]
        except Exception as exc:
            raise DataspaceError(
                f"failed to list ftp directory host={host} path={remote_path}: {exc}"
            ) from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    @staticmethod
    def _download_ftp_file(
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        local_path: Path,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        ftp = FTP()
        try:
            ftp.connect(host=host, port=port, timeout=timeout_seconds)
            ftp.login(user=username, passwd=password)
            normalized_remote = remote_path.rstrip("/")
            if not normalized_remote:
                raise DataspaceError("remote ftp file path is empty")

            remote_dir, _, filename = normalized_remote.rpartition("/")
            if not filename:
                raise DataspaceError(f"remote ftp file path is invalid: {remote_path}")
            ftp.cwd(remote_dir or "/")

            local_path.parent.mkdir(parents=True, exist_ok=True)
            with local_path.open("wb") as handle:
                ftp.retrbinary(f"RETR {filename}", handle.write)
        except Exception as exc:
            raise DataspaceError(
                f"failed to download ftp file host={host} path={remote_path}: {exc}"
            ) from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    @staticmethod
    def _upload_ftp_file(
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        local_path: Path,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not local_path.exists():
            raise DataspaceError(f"local upload file not found: {local_path}")
        if not local_path.is_file():
            raise DataspaceError(f"local upload path is not a file: {local_path}")

        ftp = FTP()
        try:
            ftp.connect(host=host, port=port, timeout=timeout_seconds)
            ftp.login(user=username, passwd=password)

            normalized_remote = remote_path.rstrip("/")
            if not normalized_remote:
                raise DataspaceError("remote ftp upload path is empty")

            remote_dir, _, filename = normalized_remote.rpartition("/")
            if not filename:
                raise DataspaceError(f"remote ftp upload path is invalid: {remote_path}")

            DataspaceClient._ensure_ftp_directory(ftp, remote_dir or "/")
            with local_path.open("rb") as handle:
                ftp.storbinary(f"STOR {filename}", handle)
        except Exception as exc:
            raise DataspaceError(
                f"failed to upload ftp file host={host} path={remote_path}: {exc}"
            ) from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    @staticmethod
    def _upload_ftp_directory(
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        local_dir: Path,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not local_dir.exists():
            raise DataspaceError(f"local upload directory not found: {local_dir}")
        if not local_dir.is_dir():
            raise DataspaceError(f"local upload path is not a directory: {local_dir}")

        ftp = FTP()
        try:
            ftp.connect(host=host, port=port, timeout=timeout_seconds)
            ftp.login(user=username, passwd=password)

            normalized_remote = remote_path.rstrip("/")
            if not normalized_remote:
                raise DataspaceError("remote ftp upload path is empty")

            DataspaceClient._ensure_ftp_directory(ftp, normalized_remote)
            for file_path in sorted(local_dir.rglob("*")):
                if not file_path.is_file():
                    continue
                relative_file = file_path.relative_to(local_dir).as_posix()
                remote_file_path = f"{normalized_remote.rstrip('/')}/{relative_file}"
                remote_parent, _, filename = remote_file_path.rpartition("/")
                DataspaceClient._ensure_ftp_directory(ftp, remote_parent or "/")
                with file_path.open("rb") as handle:
                    ftp.storbinary(f"STOR {filename}", handle)
        except Exception as exc:
            raise DataspaceError(
                f"failed to upload ftp directory host={host} path={remote_path}: {exc}"
            ) from exc
        finally:
            try:
                ftp.quit()
            except Exception:
                pass

    @staticmethod
    def _ensure_ftp_directory(ftp: FTP, remote_dir: str) -> None:
        normalized = remote_dir.strip() or "/"
        if normalized in {"/", "."}:
            return

        try:
            ftp.cwd(normalized)
            return
        except error_perm:
            pass

        if normalized.startswith("/"):
            parts = [part for part in normalized.split("/") if part]
        else:
            parts = [part for part in normalized.split("/") if part and part != "."]

        if not parts:
            return

        for segment in parts:
            try:
                ftp.cwd(segment)
            except error_perm:
                ftp.mkd(segment)
                ftp.cwd(segment)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
