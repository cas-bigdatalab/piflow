"""Client for the BDBE metadata and GenBank public APIs.

The service owns upstream authentication and transport details. Callers should
never pass an AccessKey; it is read from the configured environment variable
and added as the ``X-AK`` header for upstream requests.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator
from urllib.parse import urlencode

import requests

from infra.config_loader import get_settings

log = logging.getLogger("flow.bdbe")


class BdbeUpstreamError(RuntimeError):
    """An upstream BDBE request failed or returned an invalid response."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _base_url() -> str:
    value = str(get_settings().bdbe.base_url or "").strip().rstrip("/")
    if not value:
        raise ValueError("settings.bdbe.base_url must not be empty")
    if not value.startswith(("http://", "https://")):
        raise ValueError("settings.bdbe.base_url must include http:// or https://")
    return value


def _access_key() -> str:
    config = get_settings().bdbe
    configured_value = str(config.access_key or "").strip()
    if configured_value:
        return configured_value

    env_name = str(config.access_key_env or "").strip()
    if not env_name:
        raise ValueError("settings.bdbe.access_key_env must not be empty")
    value = os.getenv(env_name, "").strip()
    if not value:
        raise ValueError(f"environment variable {env_name} must contain the BDBE AccessKey")
    return value


def _headers(*, accept: str = "application/json") -> dict[str, str]:
    config = get_settings().bdbe
    headers = {
        "Accept": accept,
        "X-AK": _access_key(),
    }
    host_header = str(config.host_header or "").strip()
    if host_header:
        headers["Host"] = host_header
    return headers


def _cookies(sessionid: str | None = None) -> dict[str, str] | None:
    normalized = str(sessionid or "").strip()
    return {"sessionid": normalized} if normalized else None


def _timeout(*, download: bool = False) -> int:
    config = get_settings().bdbe
    value = config.download_timeout_seconds if download else config.timeout_seconds
    if value <= 0:
        raise ValueError("BDBE timeout must be positive")
    return value


def _request_error(response: requests.Response, operation: str) -> BdbeUpstreamError:
    detail = ""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail_value = payload.get("detail") or payload.get("message")
            if isinstance(detail_value, str):
                detail = detail_value[:300]
    except (ValueError, json.JSONDecodeError):
        pass
    suffix = f": {detail}" if detail else ""
    return BdbeUpstreamError(
        f"BDBE {operation} failed with status {response.status_code}{suffix}",
        status_code=response.status_code,
    )


def _get_json(
    path: str,
    *,
    params: dict[str, Any],
    sessionid: str | None = None,
) -> Any:
    url = f"{_base_url()}{path}"
    try:
        response = requests.get(
            url,
            params=params,
            headers=_headers(),
            cookies=_cookies(sessionid),
            timeout=_timeout(),
        )
    except requests.RequestException as exc:
        log.warning("BDBE request failed operation=%s error=%s", path, exc)
        raise BdbeUpstreamError(f"BDBE request failed for {path}") from exc

    if not response.ok:
        raise _request_error(response, path)
    try:
        return response.json()
    except ValueError as exc:
        raise BdbeUpstreamError(f"BDBE {path} returned invalid JSON") from exc


def query_metadata(
    *,
    term: str,
    db: str | None = None,
    page: int = 1,
    pagesize: int = 100,
    genome_next: str | None = None,
    sessionid: str | None = None,
) -> Any:
    normalized_term = str(term or "").strip()
    if not normalized_term:
        raise ValueError("term is required")
    if page < 1:
        raise ValueError("page must be greater than or equal to 1")
    if pagesize < 1:
        raise ValueError("pagesize must be greater than or equal to 1")

    params: dict[str, Any] = {
        "term": normalized_term,
        "page": page,
        "pagesize": pagesize,
    }
    if db:
        params["db"] = db
    if genome_next:
        params["genomeNext"] = genome_next
    return _get_json("/bioservice/meta/query", params=params, sessionid=sessionid)


def get_metadata_detail(
    *,
    db: str,
    sdi: str,
    fmt: str | None = None,
    itype: str | None = None,
    sessionid: str | None = None,
) -> Any:
    normalized_db = str(db or "").strip()
    normalized_sdi = str(sdi or "").strip()
    if not normalized_db:
        raise ValueError("db is required")
    if not normalized_sdi:
        raise ValueError("sdi is required")

    params: dict[str, Any] = {"db": normalized_db, "sdi": normalized_sdi}
    if fmt:
        params["fmt"] = fmt
    if itype:
        params["itype"] = itype
    return _get_json("/bioservice/meta/detail", params=params, sessionid=sessionid)


def _normalize_dataids(dataids: str | list[str]) -> str:
    if isinstance(dataids, str):
        values = [item.strip() for item in dataids.split(",")]
    else:
        values = [str(item).strip() for item in dataids]
    values = [item for item in values if item]
    max_ids = get_settings().bdbe.max_download_ids
    if not values:
        raise ValueError("dataids is required")
    if max_ids <= 0:
        raise ValueError("settings.bdbe.max_download_ids must be positive")
    if len(values) > max_ids:
        raise ValueError(f"dataids cannot contain more than {max_ids} accessions")
    return ",".join(values)


@contextmanager
def stream_genbank(
    *,
    dataids: str | list[str],
    sessionid: str | None = None,
    chunk_size: int = 64 * 1024,
) -> Iterator[tuple[requests.Response, Iterator[bytes]]]:
    """Open a streaming GenBank response and close it after iteration.

    The response object is returned so the API layer can copy safe download
    headers such as Content-Type and Content-Disposition.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    normalized_dataids = _normalize_dataids(dataids)
    params = {"dataids": normalized_dataids}
    url = f"{_base_url()}/bioservice/nuc/genbank"
    try:
        response = requests.get(
            url,
            params=params,
            headers=_headers(accept="application/octet-stream, application/json"),
            cookies=_cookies(sessionid),
            timeout=_timeout(download=True),
            stream=True,
        )
    except requests.RequestException as exc:
        log.warning("BDBE GenBank request failed error=%s", exc)
        raise BdbeUpstreamError("BDBE GenBank request failed") from exc

    try:
        if not response.ok:
            raise _request_error(response, "/bioservice/nuc/genbank")
        yield response, response.iter_content(chunk_size=chunk_size)
    finally:
        response.close()


def build_genbank_url(*, dataids: str | list[str]) -> str:
    """Build a diagnostic upstream URL without embedding authentication."""

    return f"{_base_url()}/bioservice/nuc/genbank?{urlencode({'dataids': _normalize_dataids(dataids)})}"
