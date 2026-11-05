from __future__ import annotations

from typing import Any

from services.corpus_connector_service import (
    get_dataset_detail_by_cstr,
    get_dataset_directory,
    should_query_dataset_directory,
)


def build_dataseek_submission(*, cstr: str, token: str) -> dict[str, Any]:
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

    if not should_query_dataset_directory(normalized_cstr):
        raise ValueError(
            f"dataset cstr={normalized_cstr} is preview-only and has no directory to use as storage_directory"
        )

    directory = get_dataset_directory(normalized_cstr)
    storage_directory = _first_parent_id(directory)
    if not storage_directory:
        raise ValueError(
            f"dataset cstr={normalized_cstr} directory listing has no first-level parentId"
        )

    submission = {
        "external_id": normalized_cstr,
        "name": name,
        "summary": summary,
        "keywords": keywords,
        "storage_directory": storage_directory,
        "token": normalized_token,
    }
    return submission


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
