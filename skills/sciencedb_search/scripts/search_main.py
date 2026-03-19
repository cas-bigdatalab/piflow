from langchain_core.tools import tool

import requests
from typing import List, Dict

BASE_SEARCH_URL = "https://www.scidb.cn/api/sdb-query-service/query?q="
BASE_FILETREE_URL = "https://www.scidb.cn/api/gin-sdb-filetree/public/file/childrenFileListByPath"
BASE_DOWNLOAD = "https://china.scidb.cn/download?fileId="


def search_scidb_keyword(keyword: str, page: int = 1, size: int = 5) -> List[Dict]:
    url = f"{BASE_SEARCH_URL}{keyword}"
    body = {"pub": True, "page": page, "size": size}
    r = requests.post(url, json=body)
    r.raise_for_status()
    data = r.json()
    return data.get('data', {}).get('data', [])


def get_file_ids(dataset_id: str, version: str) -> str:
    body = {
        "dataSetId": dataset_id,
        "version": version,
        "path": f"/{version}",
        "lastIndex": 0,
        "pageSize": 200
    }
    r = requests.post(BASE_FILETREE_URL, json=body)
    r.raise_for_status()
    data = r.json()
    if data.get('data'):
        return data['data'][0]['id']
    return ""


def construct_download_link(download_id: str) -> str:
    return f"{BASE_DOWNLOAD}{download_id}" if download_id else ""


def fetch_datasets_with_links(keyword: str, page: int = 1, size: int = 5) -> List[Dict]:
    datasets = search_scidb_keyword(keyword, page=page, size=size)
    results = []
    for ds in datasets:
        dataSetId = ds.get('dataSetId')
        version = ds.get('version')
        introductionZh = ds.get('introductionZh')
        download_id = get_file_ids(dataSetId, version)
        download_link = construct_download_link(download_id)
        results.append({
            "titleZh": ds.get("titleZh"),
            # "keywordZh": ds.get("keywordZh"),
            # "author": ds.get("author"),
            "download_link": download_link,
            "introductionZh": introductionZh,
            "size": ds.get("size")
        })
    return results


def scidb_search_main(keyword: str, size: int) -> str:
    """
    搜索 scienceDB 数据集。

    用于：
    - 查找科学数据集
    - 获取数据下载链接
    - 数据资源检索

    参数：
    - keyword: 检索关键词
    - size: 返回数量
    """
    print(f"使用关键词 {keyword} 在scienceDB 中搜索相关数据集")
    info_list = fetch_datasets_with_links(keyword, 1, size)
    if not info_list:
        return f"抱歉，没有找到与 '{keyword}' 相关的数据集。"

    lines = []
    for i, item in enumerate(info_list, start=1):
        title = item.get("titleZh", "未命名")
        desc = item.get("introductionZh", "")
        # author = item.get("author", "")
        size = item.get("size")
        link = item.get("download_link", "")
        # introductionZh = item.get("introductionZh", "")
        lines.append(
            f"{i}. **{title}**, desc{desc},下载链接: {link}, 来源: ScienceDB, size: {size} KB"
        )
    return "\n".join(lines)
