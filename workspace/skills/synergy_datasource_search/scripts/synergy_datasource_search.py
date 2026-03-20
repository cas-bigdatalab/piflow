"""
Pure Conet synergy datasource search executor.
No semantic parsing is done in this script.
"""

from __future__ import annotations

import base64
import os
import re
import uuid as uuid_lib
from typing import Any

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


JWT_LOGIN_PATH = "/piflow-web/jwtLogin"
SYNERGY_SEARCH_PATH = "/piflow-web/datasource/v2/getSynergyByPage"

DATA_CENTER_NAME_TO_URL = {
    "\u56fd\u5bb6\u5bf9\u5730\u89c2\u6d4b\u79d1\u5b66\u6570\u636e\u4e2d\u5fc3": "http://124.16.184.77:7801",
    "\u56fd\u5bb6\u51b0\u5ddd\u51bb\u571f\u6c99\u6f20\u79d1\u5b66\u6570\u636e\u4e2d\u5fc3": "http://210.77.77.148:7001",
}

ROUTING_INTENTS_ANALYSIS = {
    "analysis",
    "workflow_source_recommendation",
}
ROUTING_INTENTS_GENERIC_SEARCH = {
    "generic_search",
    "dataset_search",
    "download_search",
    "search",
}


def _ensure_uuid(raw_value: Any) -> str:
    raw = str(raw_value or "").strip()
    if raw:
        try:
            return str(uuid_lib.UUID(raw))
        except ValueError:
            pass
    return str(uuid_lib.uuid4())


def _resolve_data_center_url(item: dict[str, Any]) -> str:
    data_center_name = str(item.get("dataCenterName") or "").strip()
    data_center = str(item.get("dataCenter") or item.get("datacenter") or "").strip()
    web_address = str(item.get("webAddress") or "").strip()

    if data_center_name in DATA_CENTER_NAME_TO_URL:
        return DATA_CENTER_NAME_TO_URL[data_center_name]
    if data_center_name.startswith("http://") or data_center_name.startswith("https://"):
        return data_center_name
    return data_center or web_address


def _aes_encrypt(plain_text: str) -> str:
    if not plain_text:
        raise ValueError("password is empty")

    key = "ABCDEFGHIJKL_key".encode("utf-8")
    iv = "ABCDEFGHIJKLM_iv".encode("utf-8")
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def _login_conet(base_url: str, username: str, password: str) -> str:
    url = f"{base_url.rstrip('/')}{JWT_LOGIN_PATH}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": "Bearer false",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base_url.rstrip("/"),
        "Referer": f"{base_url.rstrip('/')}/login",
        "User-Agent": "Mozilla/5.0",
    }
    data = {"username": username, "password": _aes_encrypt(password)}

    response = requests.post(url, headers=headers, data=data, verify=False, timeout=12)
    if response.status_code != 200:
        raise RuntimeError(f"Conet login failed, HTTP {response.status_code}")

    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(f"Conet login failed: {payload.get('errorMsg') or payload}")

    token = payload.get("token")
    if not token:
        raise RuntimeError("Conet login succeeded but token is missing")
    return str(token)


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("records", "list", "rows", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    if isinstance(payload.get("name"), str):
        return [payload]

    return []


def _normalize_stop(item: dict[str, Any]) -> dict[str, Any]:
    data_center_url = _resolve_data_center_url(item)
    return {
        "customizedProperties": item.get("customizedProperties") or {},
        "dataSourceId": item.get("dataSourceId") or item.get("id") or "",
        "dataCenter": data_center_url,
        "registerId": item.get("registerId") or item.get("registerID") or "",
        "sourceType": item.get("sourceType") or "",
        "webAddress": data_center_url,
        "name": item.get("name")
        or item.get("nameZh")
        or item.get("datasetName")
        or item.get("dataSetName")
        or item.get("title")
        or "",
        "uuid": _ensure_uuid(item.get("uuid")),
        "bundle": item.get("bundle") or item.get("stopBundle") or "",
        "properties": item.get("properties") or {},
    }


def _search_synergy_by_keyword(
    token: str,
    query: str,
    base_url: str,
    page: int,
    size: int,
    datacenter_id: str,
) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}{SYNERGY_SEARCH_PATH}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base_url.rstrip("/"),
        "Referer": f"{base_url.rstrip('/')}/data",
        "User-Agent": "Mozilla/5.0",
    }
    data = {
        "page": str(page),
        "limit": str(size),
        "fuzzySearch": query,
        "datacenterId": datacenter_id,
    }

    response = requests.post(url, headers=headers, data=data, verify=False, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"Synergy search failed, HTTP {response.status_code}")

    result = response.json()
    if isinstance(result, dict) and "code" in result and result.get("code") != 200:
        raise RuntimeError(f"Synergy search failed: {result.get('errorMsg') or result}")

    payload = result.get("data", result) if isinstance(result, dict) else result
    return _extract_records(payload)


def _normalize_queries(values: list[str] | str | None) -> list[str]:
    if values is None:
        return []

    if isinstance(values, str):
        raw_items = [x.strip() for x in values.split(",")]
    else:
        raw_items = [str(x).strip() for x in values]

    seen = set()
    normalized: list[str] = []
    for item in raw_items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _derive_fallback_keywords(
    user_query: str,
    analysis_name: str,
    full_names: list[str],
) -> list[str]:
    """
    Build lexical fallback keywords when callers omit `required_data_source_keywords`.
    The fallback is deterministic and domain-agnostic.
    """
    corpus = [user_query, analysis_name, *full_names]
    raw_tokens: list[str] = []

    for text in corpus:
        normalized = str(text or "").strip()
        if not normalized:
            continue

        parts = re.split(r"[^\w\u4e00-\u9fff]+", normalized)
        for part in parts:
            token = part.strip()
            if not token:
                continue
            if re.fullmatch(r"\d{4}(?:\u5e74)?", token):
                continue
            raw_tokens.append(token)

    compact_tokens: list[str] = []
    for token in raw_tokens:
        if token.isdigit():
            continue
        if len(token) <= 1:
            continue
        compact_tokens.append(token)

    return _normalize_queries(compact_tokens)[:8]


def _normalize_routing_intent(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized.replace("-", "_").replace(" ", "_")


def _dedupe_dataset_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for stop in stops:
        key = (str(stop.get("dataSourceId", "")).strip(), str(stop.get("name", "")).strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(stop)
    return deduped


def _find_missing_required_names(stops: list[dict[str, Any]], required_names: list[str]) -> list[str]:
    if not required_names:
        return []
    matched = {str(stop.get("name", "")).strip() for stop in stops}
    return [name for name in required_names if name not in matched]


def _filter_exact_full_name_stops(
    stops: list[dict[str, Any]],
    required_names: list[str],
) -> list[dict[str, Any]]:
    if not required_names:
        return []
    required_set = {str(name).strip() for name in required_names if str(name).strip()}
    return [stop for stop in stops if str(stop.get("name", "")).strip() in required_set]


def process(
    user_query: str = "",
    analysis_name: str = "",
    required_data_source_keywords: list[str] | str | None = None,
    required_data_source_full_names: list[str] | str | None = None,
    size: int = 10,
    page: int = 1,
    datacenter_id: str = "",
    token: str = "",
    conet_username: str = "",
    conet_password: str = "",
    conet_base_url: str = "http://conet.rdcn.link",
    routing_intent: str = "",
) -> dict[str, Any]:
    """
    Execute synergy datasource retrieval by explicit keywords/full names.
    Semantic understanding should be done by the model via SKILL.md instructions.
    """
    analysis_label = analysis_name.strip() or user_query.strip() or "\u672a\u6307\u5b9a\u5206\u6790\u7c7b\u578b"

    keywords = _normalize_queries(required_data_source_keywords)
    full_names = _normalize_queries(required_data_source_full_names)
    if not keywords and full_names:
        keywords = _derive_fallback_keywords(
            user_query=user_query,
            analysis_name=analysis_name,
            full_names=full_names,
        )

    normalized_intent = _normalize_routing_intent(routing_intent)
    if not normalized_intent:
        return {
            "analysis_name": analysis_label,
            "required_data_source_keywords": keywords,
            "required_data_source_full_names": full_names,
            "dataset_stops": [],
            "dataset_count": 0,
            "exact_full_name_matched_dataset_stops": [],
            "exact_full_name_matched_count": 0,
            "keyword_related_dataset_stops": [],
            "keyword_related_count": 0,
            "missing_required_full_names": full_names,
            "blocked_by_intent_guard": True,
            "routing_recommendation": "set routing_intent to analysis or generic_search",
            "message": (
                "routing_intent is required. "
                "Use routing_intent='analysis' for workflow source recommendation "
                "or routing_intent='generic_search' for ordinary dataset retrieval."
            ),
        }

    if normalized_intent in ROUTING_INTENTS_GENERIC_SEARCH:
        return {
            "analysis_name": analysis_label,
            "required_data_source_keywords": keywords,
            "required_data_source_full_names": full_names,
            "dataset_stops": [],
            "dataset_count": 0,
            "exact_full_name_matched_dataset_stops": [],
            "exact_full_name_matched_count": 0,
            "keyword_related_dataset_stops": [],
            "keyword_related_count": 0,
            "missing_required_full_names": full_names,
            "blocked_by_intent_guard": True,
            "routing_recommendation": "sciencedb_search.process",
            "message": (
                "routing_intent indicates generic dataset search. "
                "Please use sciencedb_search.process."
            ),
        }
    if normalized_intent not in ROUTING_INTENTS_ANALYSIS:
        return {
            "analysis_name": analysis_label,
            "required_data_source_keywords": keywords,
            "required_data_source_full_names": full_names,
            "dataset_stops": [],
            "dataset_count": 0,
            "exact_full_name_matched_dataset_stops": [],
            "exact_full_name_matched_count": 0,
            "keyword_related_dataset_stops": [],
            "keyword_related_count": 0,
            "missing_required_full_names": full_names,
            "blocked_by_intent_guard": True,
            "routing_recommendation": "set routing_intent to analysis or generic_search",
            "message": (
                f"Unsupported routing_intent='{normalized_intent}'. "
                "Use routing_intent='analysis' or routing_intent='generic_search'."
            ),
        }

    if not full_names:
        return {
            "analysis_name": analysis_label,
            "required_data_source_keywords": keywords,
            "required_data_source_full_names": full_names,
            "dataset_stops": [],
            "dataset_count": 0,
            "exact_full_name_matched_dataset_stops": [],
            "exact_full_name_matched_count": 0,
            "keyword_related_dataset_stops": [],
            "keyword_related_count": 0,
            "missing_required_full_names": [],
            "blocked_by_intent_guard": True,
            "routing_recommendation": "sciencedb_search.process",
            "message": (
                "analysis routing requires required_data_source_full_names from "
                "explicit workflow planning context. "
                "Without required_data_source_full_names, use sciencedb_search.process."
            ),
        }

    if not keywords and not full_names:
        return {
            "analysis_name": analysis_label,
            "required_data_source_keywords": [],
            "required_data_source_full_names": [],
            "dataset_stops": [],
            "dataset_count": 0,
            "exact_full_name_matched_dataset_stops": [],
            "exact_full_name_matched_count": 0,
            "keyword_related_dataset_stops": [],
            "keyword_related_count": 0,
            "missing_required_full_names": [],
            "message": "No search keywords/full names provided.",
        }

    resolved_token = token.strip()
    if not resolved_token:
        resolved_username = conet_username.strip() or os.getenv("CONET_USERNAME", "netuser1")
        resolved_password = conet_password.strip() or os.getenv("CONET_PASSWORD", "cnic$@Nzlh1")
        resolved_token = _login_conet(conet_base_url, resolved_username, resolved_password)

    raw_keyword_records: list[dict[str, Any]] = []
    for keyword in keywords:
        raw_keyword_records.extend(
            _search_synergy_by_keyword(
                token=resolved_token,
                query=keyword,
                base_url=conet_base_url,
                page=page,
                size=size,
                datacenter_id=datacenter_id,
            )
        )

    raw_full_name_records: list[dict[str, Any]] = []
    for full_name in full_names:
        raw_full_name_records.extend(
            _search_synergy_by_keyword(
                token=resolved_token,
                query=full_name,
                base_url=conet_base_url,
                page=page,
                size=max(size, 50),
                datacenter_id=datacenter_id,
            )
        )

    keyword_stops = _dedupe_dataset_stops([_normalize_stop(item) for item in raw_keyword_records])
    full_name_query_stops = _dedupe_dataset_stops([_normalize_stop(item) for item in raw_full_name_records])
    all_stops = _dedupe_dataset_stops(full_name_query_stops + keyword_stops)

    exact_full_name_matched_stops = _filter_exact_full_name_stops(all_stops, full_names)
    exact_pairs = {
        (str(stop.get("dataSourceId", "")).strip(), str(stop.get("name", "")).strip())
        for stop in exact_full_name_matched_stops
    }
    keyword_related_stops = [
        stop
        for stop in all_stops
        if (str(stop.get("dataSourceId", "")).strip(), str(stop.get("name", "")).strip()) not in exact_pairs
    ]

    missing_required_full_names = _find_missing_required_names(exact_full_name_matched_stops, full_names)

    response = {
        "analysis_name": analysis_label,
        "required_data_source_keywords": keywords,
        "required_data_source_full_names": full_names,
        "dataset_stops": all_stops,
        "dataset_count": len(all_stops),
        "exact_full_name_matched_dataset_stops": exact_full_name_matched_stops,
        "exact_full_name_matched_count": len(exact_full_name_matched_stops),
        "keyword_related_dataset_stops": keyword_related_stops,
        "keyword_related_count": len(keyword_related_stops),
        "missing_required_full_names": missing_required_full_names,
    }
    if normalized_intent in ROUTING_INTENTS_ANALYSIS:
        response["resolved_routing_intent"] = "analysis"
    return response
