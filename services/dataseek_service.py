from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

import requests

from services.corpus_connector_service import (
    get_dataset_detail_by_cstr,
    get_dataset_directory,
    get_dataset_preview,
    should_query_dataset_directory,
)


DATASEEK_SUBMISSION_URL = "http://172.31.3.81:7000/api/v1/datasets/submissions"
DATASEEK_DATASET_URL = "http://172.31.3.81:7000/dataset/seek"
DATASEEK_TIMEOUT = 30
log = logging.getLogger("flow.dataseek")


def submit_dataset_to_dataseek(*, cstr: str, token: str) -> dict[str, Any]:
    normalized_cstr = str(cstr or "").strip()
    normalized_token = str(token or "").strip()
    if not normalized_cstr:
        raise ValueError("cstr is required")
    if not normalized_token:
        raise ValueError("current user token is required")

    dataset = get_dataset_detail_by_cstr(normalized_cstr)
    # get_dataset_detail_by_cstr returns the upstream raw object directly.
    # Keep compatibility with the normalized shape used by other callers too.
    raw = dataset.get("raw")
    source = raw if isinstance(raw, dict) else dataset

    name = str(dataset.get("title") or "").strip()
    if not name:
        name = str(source.get("title") or source.get("name") or "").strip()
    summary = str(source.get("description") or "").strip()
    if not name:
        raise ValueError("dataset title is empty")
    if not summary:
        raise ValueError("dataset description is empty")

    keywords = _normalize_values(source.get("keywords"))
    if not keywords:
        keywords = _normalize_values(source.get("field"))
    if not keywords:
        raise ValueError("dataset keywords and field are both empty")

    preview = (
        get_dataset_directory(normalized_cstr)
        if should_query_dataset_directory(normalized_cstr)
        else get_dataset_preview(normalized_cstr)
    )
    storage_directory = _first_parent_id(preview)
    if not storage_directory:
        raise ValueError("dataset preview has no first-level parentId")

    submission = {
        "external_id": normalized_cstr,
        "name": name,
        "summary": summary,
        "keywords": keywords,
        "storage_directory": storage_directory,
        "token": normalized_token,
    }
    log.info(
        "Dataseek submission payload url=%s payload=%s",
        DATASEEK_SUBMISSION_URL,
        json.dumps(
            {**submission, "token": "[REDACTED_SECRET]"},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )

    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            DATASEEK_SUBMISSION_URL,
            headers={
                "Accept": "*/*",
                "Content-Type": "application/json",
                "User-Agent": "curl/8.5.0",
            },
            json=submission,
            timeout=DATASEEK_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"failed to submit dataset to Dataseek: {exc}") from exc

    if response.status_code >= 400:
        # Keep the upstream diagnostic, but never log or expose the submitted token.
        response_body = str(response.text or "").strip()
        log.error(
            "Dataseek rejected submission status=%s headers=%r body=%r",
            response.status_code,
            {
                key: value
                for key, value in response.headers.items()
                if key.lower() in {"server", "www-authenticate", "content-type", "location"}
            },
            response_body,
        )
        raise RuntimeError(
            f"Dataseek submission failed with HTTP {response.status_code}: {response_body}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Dataseek returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Dataseek response must be a JSON object")
    if str(payload.get("code")) != "0":
        raise RuntimeError(f"Dataseek submission failed: {payload.get('msg') or payload.get('code')}")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Dataseek response data is missing")
    external_id = str(data.get("external_id") or "").strip()
    if not external_id:
        raise RuntimeError("Dataseek response external_id is missing")

    return {
        "external_id": external_id,
        "url": f"{DATASEEK_DATASET_URL}/{external_id}?{urlencode({'token': normalized_token})}",
    }


def _normalize_values(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [item for item in (str(item or "").strip() for item in value) if item]
    normalized = str(value or "").strip()
    return [normalized] if normalized else []


def _first_parent_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    nodes = payload.get("data")
    if not isinstance(nodes, list):
        return ""
    for node in nodes:
        if isinstance(node, dict):
            parent_id = str(node.get("parentId") or "").strip()
            if parent_id:
                return parent_id
    return ""
