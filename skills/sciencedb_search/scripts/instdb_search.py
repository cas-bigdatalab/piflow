import requests
import json

from langchain_core.tools import tool

from skills.sciencedb_search.scripts.search_main import scidb_search_main


def _split_keywords(raw: str) -> list[str]:
    # Split on any whitespace and drop empties.
    return [k for k in raw.split() if k]

url = "https://www.casdc.cn/api/query/list"
downloadUrl = "https://www.casdc.cn/api/query/download"

def getFtpInfo(downloadId: str) -> str:
    params = {
        "id": downloadId
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    response = requests.get(downloadUrl, params=params, headers = headers)
    return response.json().get("data")


def instDB_search_main(keyword: str) -> str:
    """
    搜索 InstDB 数据集。

    用于：
    - 查找科学数据集
    - 获取数据下载链接
    - 数据资源检索

    参数：
    - keyword: 检索关键词
    - size: 返回数量
    """
    print(f"使用关键词 {keyword} 在InstDB 中搜索相关数据集")
    params = {
        "keyword": keyword  # 搜索关键词
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    response = requests.get(url, params=params, headers=headers)

    lines = []
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get("data", []):
            results.append({
                "title": item.get("name"),
                "descriptionZh": item.get("description"),
                "下载链接": item.get("ftpUrl") ,
                "source": 'InstDB'
            })
            title = item.get("name")
            downloadUrl = getFtpInfo(item.get("_id"))
            descriptionZh = item.get("description")
            size = item.get("storageNum")
            source = item.get("publisher").get("nameZh")
            lines.append(
                f" **{title}**,description:{descriptionZh}, 下载链接: {downloadUrl}, 来源: {source}, size: {size} KB"
            )
    scidb_search_result = scidb_search_main(keyword, 10)
    return "\n".join(lines) + "\n"  + scidb_search_result
