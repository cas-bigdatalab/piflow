from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests


BASE_SEARCH_URL = "https://www.scidb.cn/api/sdb-query-service/query?q="
BASE_FILETREE_URL = "https://www.scidb.cn/api/gin-sdb-filetree/public/file/childrenFileListByPath"
BASE_DOWNLOAD = "https://china.scidb.cn/download?fileId="
REQUEST_TIMEOUT = 30
MAX_KEYWORDS = 6
MAX_SIZE_PER_KEYWORD = 5
MAX_OUTPUT_RECORDS = 40
MAX_SCIDB_FILE_ID_WORKERS = 8
DESCRIPTION_LIMIT = 120

_KEYWORD_SPLITTER = re.compile(r"[\s,，;；、|/]+")


def _normalize_keywords(
    keywords: str | list[str] | tuple[str, ...] | None,
    limit: int | None = None,
) -> list[str]:
    """将关键词统一为去重后的列表，支持字符串或数组输入。"""
    if keywords is None:
        return []

    raw_items: list[str]
    if isinstance(keywords, str):
        raw_items = [keywords]
    else:
        raw_items = [str(k) for k in keywords]

    merged: list[str] = []
    for item in raw_items:
        text = item.strip()
        if not text:
            continue
        for part in _KEYWORD_SPLITTER.split(text):
            token = part.strip()
            if token:
                merged.append(token)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in merged:
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(token)
        if limit is not None and limit > 0 and len(deduped) >= limit:
            break
    return deduped


def _safe_text(text: Any, limit: int = DESCRIPTION_LIMIT) -> str:
    if text is None:
        return ""
    value = str(text).replace("\n", " ").replace("\r", " ").strip()
    value = re.sub(r"<[^>]+>", "", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _record_key(record: dict[str, Any]) -> str:
    link = str(record.get("download_link", "")).strip().lower()
    source = str(record.get("source", "")).strip().lower()
    title = str(record.get("title", "")).strip().lower()
    if link:
        return f"{source}|{link}"
    return f"{source}|{title}"


def _matches_keyword(record: dict[str, Any], keyword: str) -> bool:
    token = keyword.strip().lower()
    if len(token) < 2:
        return True
    haystack = f"{record.get('title', '')} {record.get('description', '')}".lower()
    return token in haystack


def _format_dataset_line(index: int, item: dict[str, Any]) -> str:
    title = item.get("title") or "未命名数据集"
    description = _safe_text(item.get("description", ""))
    source = item.get("source", "未知来源")
    provider = item.get("provider", "")
    link = item.get("download_link", "")
    size = item.get("size", "")
    hit_keyword = item.get("matched_keyword", "")

    source_text = str(source)
    if provider and provider != source:
        source_text = f"{source} / {provider}"

    return (
        f"{index}. 数据集名: {title} | 下载链接: {link} | 关键词: {hit_keyword} | "
        f"描述: {description} | 文件大小: {size} KB | 来源: {source_text}"
    )


def _format_records(records: list[dict[str, Any]]) -> str:
    if not records:
        return "未检索到相关数据集。"
    return "\n".join(_format_dataset_line(index, item) for index, item in enumerate(records, start=1))


def _format_process_output(
    scidb_records: list[dict[str, Any]],
    instdb_records: list[dict[str, Any]],
    max_results: int,
) -> str:
    merged: dict[str, dict[str, Any]] = {}
    for record in scidb_records + instdb_records:
        key = _record_key(record)
        if key not in merged:
            merged[key] = record

    merged_records = list(merged.values())
    if max_results > 0:
        merged_records = merged_records[:max_results]

    if not merged_records:
        return "未检索到相关数据集。"

    lines: list[str] = []
    if not scidb_records:
        lines.append("ScienceDB: 无结果")
    if not instdb_records:
        lines.append("InstDB: 无结果")

    lines.extend(
        _format_dataset_line(index, item)
        for index, item in enumerate(merged_records, start=1)
    )
    return "\n".join(lines)


def search_scidb_keyword(keyword: str, page: int = 1, size: int = 5) -> list[dict[str, Any]]:
    url = f"{BASE_SEARCH_URL}{keyword}"
    body = {"pub": True, "page": page, "size": size}
    try:
        response = requests.post(url, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return []

    data = response.json()
    return data.get("data", {}).get("data", [])


def get_file_id(dataset_id: str, version: str) -> str:
    if not dataset_id or not version:
        return ""

    body = {
        "dataSetId": dataset_id,
        "version": version,
        "path": f"/{version}",
        "lastIndex": 0,
        "pageSize": 200,
    }
    try:
        response = requests.post(BASE_FILETREE_URL, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return ""

    data = response.json()
    files = data.get("data") or []
    if not files:
        return ""
    return files[0].get("id", "")


def construct_download_link(download_id: str) -> str:
    return f"{BASE_DOWNLOAD}{download_id}" if download_id else ""


def _fetch_scidb_file_id_map(datasets: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    if not datasets:
        return {}

    keys = {
        (str(item.get("dataSetId", "")), str(item.get("version", "")))
        for item in datasets
        if item.get("dataSetId") and item.get("version")
    }
    if not keys:
        return {}

    max_workers = min(MAX_SCIDB_FILE_ID_WORKERS, len(keys))
    result: dict[tuple[str, str], str] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(get_file_id, dataset_id, version): (dataset_id, version)
            for dataset_id, version in keys
        }
        for future in as_completed(future_map):
            dataset_key = future_map[future]
            try:
                result[dataset_key] = future.result()
            except Exception:
                result[dataset_key] = ""
    return result


def fetch_datasets_with_links(keyword: str, page: int = 1, size: int = 5) -> list[dict[str, Any]]:
    effective_size = max(1, min(size, MAX_SIZE_PER_KEYWORD))
    datasets = search_scidb_keyword(keyword, page=page, size=effective_size)
    if not datasets:
        return []

    file_id_map = _fetch_scidb_file_id_map(datasets)
    results: list[dict[str, Any]] = []

    for dataset in datasets:
        dataset_id = str(dataset.get("dataSetId", ""))
        version = str(dataset.get("version", ""))
        download_id = file_id_map.get((dataset_id, version), "")
        download_link = construct_download_link(download_id)
        results.append(
            {
                "title": dataset.get("titleZh") or dataset.get("titleEn") or "未命名数据集",
                "description": dataset.get("introductionZh") or dataset.get("introductionEn") or "",
                "download_link": download_link,
                "size": dataset.get("size", ""),
                "source": "ScienceDB",
                "provider": "ScienceDB",
                "matched_keyword": keyword,
            }
        )
    return results


def search_scidb_records(
    keywords: str | list[str] | tuple[str, ...],
    size: int = 5,
    keyword_limit: int = MAX_KEYWORDS,
) -> list[dict[str, Any]]:
    keyword_list = _normalize_keywords(keywords, limit=keyword_limit)
    if not keyword_list:
        return []

    effective_size = max(1, min(size, MAX_SIZE_PER_KEYWORD))
    dedup: dict[str, dict[str, Any]] = {}

    for current_keyword in keyword_list:
        records = fetch_datasets_with_links(keyword=current_keyword, page=1, size=effective_size)
        for record in records:
            if not _matches_keyword(record, current_keyword):
                continue
            key = _record_key(record)
            if key not in dedup:
                dedup[key] = record
            if len(dedup) >= MAX_OUTPUT_RECORDS:
                return list(dedup.values())

    return list(dedup.values())


def scidb_search_main(keyword: str | list[str], size: int = 5) -> str:
    """
    在 scienceDB 检索数据集，支持一次传入多个关键词并自动合并去重。

    参数:
    - keyword: 关键词字符串或关键词列表
    - size: 每个关键词的检索条数上限
    """
    records = search_scidb_records(keyword, size=size, keyword_limit=MAX_KEYWORDS)
    if not records:
        return f"抱歉，没有找到与 '{keyword}' 相关的数据集。"
    return _format_records(records)


def process(
    keywords: str | list[str] | None = None,
    size: int = 5,
    sources: str | list[str] = "all",
    keyword: str | list[str] | None = None,
    max_keywords: int = MAX_KEYWORDS,
    max_results: int = MAX_OUTPUT_RECORDS,
) -> str:
    """
    普通检索统一入口：一次接收多个关键词，单次调用聚合 ScienceDB 和 InstDB 结果并去重返回。

    参数:
    - keywords: 关键词字符串或关键词列表（推荐）
    - size: 每个关键词在每个来源中的检索条数上限
    - sources: 数据来源，支持 all / scienceDB / InstDB 或其列表
    - keyword: 兼容旧调用的单参数写法
    - max_keywords: 本次检索最多使用的关键词数量
    - max_results: 返回给用户的最大结果数量
    """
    effective_keywords = keywords if keywords is not None else keyword
    if effective_keywords is None:
        return "请提供检索关键词。"

    limit = max_keywords if max_keywords > 0 else MAX_KEYWORDS
    normalized_keywords = _normalize_keywords(effective_keywords, limit=limit)
    if not normalized_keywords:
        return "请提供有效的检索关键词。"

    source_tokens = {item.lower() for item in _normalize_keywords(sources)}
    use_all = not source_tokens or "all" in source_tokens
    use_scidb = use_all or any(s in source_tokens for s in ("scidb", "sciencedb", "science"))
    use_instdb = use_all or any(s in source_tokens for s in ("instdb", "inst"))

    effective_size = max(1, min(size, MAX_SIZE_PER_KEYWORD))
    result_limit = max_results if max_results > 0 else MAX_OUTPUT_RECORDS

    scidb_records: list[dict[str, Any]] = []
    instdb_records: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures: dict[str, Any] = {}
        if use_scidb:
            futures["scidb"] = executor.submit(
                search_scidb_records,
                normalized_keywords,
                effective_size,
                limit,
            )
        if use_instdb:
            from skills.sciencedb_search.scripts.instdb_search import search_instdb_records

            futures["instdb"] = executor.submit(
                search_instdb_records,
                normalized_keywords,
                effective_size,
            )

        for source_name, future in futures.items():
            try:
                records = future.result()
            except Exception:
                records = []
            if source_name == "scidb":
                scidb_records = records
            else:
                instdb_records = records

    if not scidb_records and not instdb_records:
        return f"抱歉，没有找到与 '{normalized_keywords}' 相关的数据集。"

    return _format_process_output(scidb_records, instdb_records, result_limit)
