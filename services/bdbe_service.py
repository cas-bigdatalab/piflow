"""Client for the BDBE metadata and GenBank public APIs.

The service owns upstream authentication and transport details. Callers should
never pass an AccessKey; it is read from the configured environment variable
and added as the ``X-AK`` header for upstream requests.
"""

from __future__ import annotations

import json
import logging
import os
import re
from email.message import Message
from contextlib import contextmanager
from typing import Any, Iterator
from urllib.parse import urlencode
from pathlib import PurePosixPath

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

    try:
        if not response.ok:
            raise _request_error(response, path)
        try:
            payload = response.json()
        except ValueError as exc:
            raise BdbeUpstreamError(f"BDBE {path} returned invalid JSON") from exc
        _checked_payload(payload)
        return payload
    finally:
        response.close()


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
    if not 1 <= pagesize <= 1000:
        raise ValueError("pagesize must be between 1 and 1000")

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
    elif isinstance(dataids, list) and all(isinstance(item, str) for item in dataids):
        values = [item.strip() for item in dataids]
    else:
        raise ValueError("dataids must contain Accession strings")
    values = list(dict.fromkeys(item for item in values if item))
    if any(len(item)>500 or "," in item or any(c.isspace() for c in item) for item in values):
        raise ValueError("dataids must contain separate Accession identifiers")
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
        try:
            yield response, response.iter_content(chunk_size=chunk_size)
        except requests.RequestException as exc:
            raise BdbeUpstreamError("BDBE GenBank stream interrupted") from exc
    finally:
        response.close()


def build_genbank_url(*, dataids: str | list[str]) -> str:
    """Build a diagnostic upstream URL without embedding authentication."""

    return f"{_base_url()}/bioservice/nuc/genbank?{urlencode({'dataids': _normalize_dataids(dataids)})}"


def _checked_payload(value):
    """Interpret service envelopes here, never in the agent runtime."""
    if isinstance(value, dict) and (value.get("success") is False or value.get("error")
            or "code" in value and str(value["code"]) not in {"0", "200"}):
        raise BdbeUpstreamError("BDBE returned an unsuccessful response")
    return value


def _scalar(row, *keys):
    values = [str(row[key]).strip() for key in keys
        if type(row.get(key)) in (str, int) and str(row[key]).strip()]
    if len(set(values))>1:
        raise BdbeUpstreamError("BDBE returned conflicting record identifiers")
    return values[0] if values else None


def _record(row, db=None):
    if not isinstance(row, dict) or not row:
        raise BdbeUpstreamError("BDBE returned an invalid metadata record")
    _checked_payload(row)
    database, identifier = _scalar(row, "db", "DB"), _scalar(row, "SDI", "sdi")
    uid = _scalar(row, "UID", "uid")
    # Accessions are never inferred from SDI, UID, CSTR or a project identifier.
    accessions = []
    for key in ("Accession", "accession", "accessions", "Accession Version"):
        value = row.get(key)
        if isinstance(value, str):
            accessions.extend(item.strip() for item in value.split(",") if item.strip())
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            accessions.extend(item.strip() for item in value if item.strip())
    name = next((row[key] for key in ("Name", "name", "Title", "title") if isinstance(row.get(key), str) and row[key].strip()), None)
    if not (identifier or uid or name or accessions):
        raise BdbeUpstreamError("BDBE response lacks metadata record identifiers or a title")
    database = database or db
    if name:
        name = re.sub(r"</?high-light>", "", name, flags=re.I)
    item = {"source": "BDBE", "db": database, "sdi": identifier,
        "id": identifier or uid, "title": name,
        "description": row.get("Description", row.get("description")), "raw": row}
    if accessions:
        item["accessions"] = list(dict.fromkeys(accessions))
    return item


def metadata_page(payload, *, db=None, page=1, pagesize=20):
    """Normalize documented results lists; reject unknown shapes, not as empty."""
    value = _checked_payload(payload)
    if isinstance(value, dict) and "results" not in value and "data" in value:
        value = _checked_payload(value["data"])
    rows = value.get("results") if isinstance(value, dict) else value
    if not isinstance(rows, list):
        raise BdbeUpstreamError("BDBE metadata response lacks a results list")
    items = [_record(row, db=db) for row in rows]
    total = value.get("total") if isinstance(value, dict) else None
    if isinstance(value, dict) and isinstance(value.get("pagination"), dict):
        total = value["pagination"].get("total", total)
    if isinstance(total, str) and total.isascii() and total.isdecimal():
        total = int(total)
    if type(total) is not int or total<0:
        total = None
    result = {"items": items, "pagination": {"page": page, "page_size": pagesize, "total": total}}
    # Preserve upstream continuation information. Do not claim a cursor can be
    # incremented as a page number until that API contract has been verified.
    if isinstance(value, dict):
        result["metadata"] = {k: v for k, v in value.items() if k not in {"results", "pagination"}}
    return result


def metadata_detail(payload, *, db, sdi):
    value = _checked_payload(payload)
    if isinstance(value, dict) and not any(key in value for key in ("SDI", "sdi", "UID", "uid", "Title", "title", "Name", "name")):
        if "data" in value:
            value = _checked_payload(value["data"])
        elif "results" in value:
            value = value["results"]
        else:
            raise BdbeUpstreamError("BDBE detail response lacks a metadata record")
    if isinstance(value, list):
        if len(value)>1:
            raise BdbeUpstreamError("BDBE detail returned multiple records")
        value = value[0] if value else None
    if value in (None, {}):
        return {"status": "unavailable", "item": None}
    item = _record(value, db=db)
    if item["db"] != db or item["sdi"] not in (None, sdi):
        raise BdbeUpstreamError("BDBE returned a different requested record")
    item["sdi"] = item["id"] = sdi
    return {"status": "ready", "item": item}


def download_genbank_file(dataids, sessionid=None, *, execution=None):
    """Publish only a complete GBFF stream, without loading it into memory."""
    from scientific_agents.dataset_qa.file_publication import publish_file

    normalized = _normalize_dataids(dataids)
    arguments = {"dataids": dataids, "sessionid": sessionid}
    def produce(path, checkpoint, max_bytes):
        size, records, in_record, pending = 0, 0, False, b""
        def consume(line):
            nonlocal in_record, records
            if not line.strip():
                return
            locus = line.startswith((b"LOCUS ", b"LOCUS\t"))
            if not in_record:
                if not locus:
                    raise BdbeUpstreamError("BDBE returned non-GBFF content outside a record")
                in_record = True
            elif locus:
                raise BdbeUpstreamError("BDBE returned an unterminated GBFF record")
            elif line.strip() == b"//":
                records += 1
                in_record = False
        with stream_genbank(dataids=normalized, sessionid=sessionid) as (response, chunks):
            media = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0].strip().lower()
            if media in {"application/json", "text/html"}:
                raise BdbeUpstreamError("BDBE did not return a GBFF file")
            header = Message()
            header["Content-Disposition"] = response.headers.get("content-disposition", "")
            name = PurePosixPath((header.get_filename() or "genbank.gbff").replace("\\", "/")).name
            with path.open("wb") as output:
                for chunk in chunks:
                    checkpoint()
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("文件超过本次下载大小预算")
                    output.write(chunk)
                    lines = (pending+chunk).split(b"\n")
                    pending = lines.pop()
                    if len(pending)>1024*1024:
                        raise BdbeUpstreamError("BDBE returned an invalid GBFF line")
                    for line in lines:
                        consume(line)
                consume(pending)
        if not records or in_record:
            raise BdbeUpstreamError("BDBE did not return a complete GBFF file")
        return {"name": name, "format": "gbff", "media_type": media,
            "record_count": records, "query": {"dataids": normalized.split(",")}}
    return publish_file(execution, arguments, "bdbe.genbank", produce)
