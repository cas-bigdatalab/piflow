from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from skills.sciencedb_search.scripts.search_main import (
    MAX_SIZE_PER_KEYWORD,
    _format_records,
    _matches_keyword,
    _normalize_keywords,
    _record_key,
)


INSTDB_LIST_URL = "https://www.casdc.cn/api/query/list"
INSTDB_DOWNLOAD_URL = "https://www.casdc.cn/api/query/download"
REQUEST_TIMEOUT = 30
MAX_INSTDB_FTP_WORKERS = 6


def get_ftp_info(download_id: str) -> dict[str, Any]:
    if not download_id:
        return {}

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    try:
        response = requests.get(
            INSTDB_DOWNLOAD_URL,
            params={"id": download_id},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        return {}

    data = response.json().get("data", {})
    if isinstance(data, dict):
        return data
    return {}


def _format_instdb_download_link(ftp_info: dict[str, Any]) -> str:
    ftp_url = str(ftp_info.get("ftpUrl", "")).strip()
    username = str(ftp_info.get("username", "")).strip()
    password = str(ftp_info.get("password", "")).strip()

    if ftp_url and username and password:
        return f"{ftp_url} (username: {username}, password: {password})"
    if ftp_url:
        return ftp_url
    return ""


def _fetch_download_link_map(items: list[dict[str, Any]]) -> dict[str, str]:
    ids = [str(item.get("_id", "")).strip() for item in items if item.get("_id")]
    if not ids:
        return {}

    max_workers = min(MAX_INSTDB_FTP_WORKERS, len(ids))
    result: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(get_ftp_info, item_id): item_id for item_id in ids}
        for future in as_completed(future_map):
            item_id = future_map[future]
            try:
                ftp_info = future.result()
            except Exception:
                ftp_info = {}
            result[item_id] = _format_instdb_download_link(ftp_info)
    return result


def search_instdb_records(
    keywords: str | list[str] | tuple[str, ...],
    size: int = 5,
    max_records: int | None = None,
) -> list[dict[str, Any]]:
    keyword_list = _normalize_keywords(keywords)
    if not keyword_list:
        return []
    effective_size = max(1, min(size, MAX_SIZE_PER_KEYWORD))

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    dedup: dict[str, dict[str, Any]] = {}

    for keyword in keyword_list:
        try:
            response = requests.get(
                INSTDB_LIST_URL,
                params={"keyword": keyword},
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        data = response.json()
        items = data.get("data", [])
        if not isinstance(items, list):
            continue

        sliced_items = items[:effective_size]
        download_link_map = _fetch_download_link_map(sliced_items)

        for item in sliced_items:
            item_id = str(item.get("_id", "")).strip()
            download_link = download_link_map.get(item_id, "")

            publisher = (item.get("publisher") or {}).get("nameZh") or "国家基础学科公共科学数据中心"
            record = {
                "title": item.get("name") or "未命名数据集",
                "description": item.get("description") or "",
                "download_link": download_link,
                "size": item.get("storageNum", ""),
                "source": "InstDB",
                "provider": publisher,
                "matched_keyword": keyword,
            }
            if not _matches_keyword(record, keyword):
                continue
            key = _record_key(record)
            if key not in dedup:
                dedup[key] = record
                if max_records is not None and max_records > 0 and len(dedup) >= max_records:
                    return list(dedup.values())

    return list(dedup.values())


def instDB_search_main(keyword: str | list[str], size: int = 5) -> str:
    """
    在 InstDB 检索数据集，支持一次传入多个关键词并自动合并去重。

    参数:
    - keyword: 关键词字符串或关键词列表
    - size: 每个关键词的检索条数上限
    """
    records = search_instdb_records(keyword, size=size)
    if not records:
        return f"抱歉，没有在 InstDB 找到与 '{keyword}' 相关的数据集。"
    return _format_records(records)
