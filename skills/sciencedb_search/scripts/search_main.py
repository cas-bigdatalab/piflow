"""
ScienceDB dataset search skill.
Return stable text that always contains dataset name + download link.
"""

from __future__ import annotations

import re
import time
from typing import Any

import requests


BASE_SEARCH_URL = "https://www.scidb.cn/api/sdb-query-service/query?q="
BASE_FILETREE_URL = "https://www.scidb.cn/api/gin-sdb-filetree/public/file/childrenFileListByPath"
BASE_DOWNLOAD = "https://china.scidb.cn/download?fileId="


def _post_json_with_retry(url: str, body: dict[str, Any], retries: int = 2) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, json=body, timeout=10)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise RuntimeError(f"Invalid JSON payload type: {type(payload).__name__}")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(0.2)
                continue
            break
    raise RuntimeError(str(last_error) if last_error else "unknown request error")


def _search_scidb_keyword(keyword: str, page: int = 1, size: int = 5) -> list[dict[str, Any]]:
    url = f"{BASE_SEARCH_URL}{keyword}"
    body = {"pub": True, "page": page, "size": size}
    payload = _post_json_with_retry(url, body, retries=1)
    return payload.get("data", {}).get("data", []) or []


def _get_file_id(dataset_id: str, version: str) -> str:
    if not dataset_id or not version:
        return ""

    body = {
        "dataSetId": dataset_id,
        "version": version,
        "path": f"/{version}",
        "lastIndex": 0,
        "pageSize": 200,
    }
    payload = _post_json_with_retry(BASE_FILETREE_URL, body, retries=2)
    files = payload.get("data") or []
    if not isinstance(files, list):
        return ""

    for node in files:
        if not isinstance(node, dict):
            continue
        file_id = str(node.get("id", "")).strip()
        if file_id:
            return file_id
    return ""


def _construct_download_link(file_id: str) -> str:
    file_id = (file_id or "").strip()
    if not file_id:
        return ""
    return f"{BASE_DOWNLOAD}{file_id}"


def _fetch_datasets(keyword: str, size: int) -> tuple[list[dict[str, str]], list[str]]:
    datasets = _search_scidb_keyword(keyword, page=1, size=size)
    with_link: list[dict[str, str]] = []
    missing_link_titles: list[str] = []

    for ds in datasets:
        if not isinstance(ds, dict):
            continue

        title = re.sub(r"<.*?>", "", str(ds.get("titleZh") or ds.get("titleEn") or "未命名数据集"))
        dataset_id = str(ds.get("dataSetId") or "").strip()
        version = str(ds.get("version") or "").strip()

        file_id = _get_file_id(dataset_id, version)
        download_link = _construct_download_link(file_id)
        if not download_link:
            missing_link_titles.append(title)
            continue

        with_link.append({"dataset_name": title, "download_link": download_link})

    return with_link, missing_link_titles


def process(keyword: str, size: int = 5) -> str:
    """
    Search ScienceDB and return text with mandatory dataset name + download link.
    """
    try:
        results, missing = _fetch_datasets(keyword, size)
        if not results:
            return f"没有找到与“{keyword}”相关且可直接下载的数据集。"

        lines: list[str] = [f"共找到 {len(results)} 个可下载数据集："]
        for idx, item in enumerate(results, start=1):
            lines.append(
                f"{idx}. 数据集名称: {item['dataset_name']}\n"
                f"   下载链接: {item['download_link']}"
            )

        if missing:
            lines.append("以下条目未拿到下载链接，已自动过滤：")
            for title in missing:
                lines.append(f"- {title}")

        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return f"数据集搜索失败: {exc}"

