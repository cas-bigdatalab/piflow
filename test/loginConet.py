import requests

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import uuid as uuid_lib
from typing import Any


DATA_CENTER_NAME_TO_URL = {
    "国家对地观测科学数据中心": "http://124.16.184.77:7801",
    "国家冰川冻土沙漠科学数据中心": "http://210.77.77.148:7001",
}


def _resolve_data_center_url(item: dict[str, Any]) -> str:
    data_center_name = str(item.get("dataCenterName") or "").strip()
    data_center = str(item.get("dataCenter") or item.get("datacenter") or "").strip()
    web_address = str(item.get("webAddress") or "").strip()

    if data_center_name in DATA_CENTER_NAME_TO_URL:
        return DATA_CENTER_NAME_TO_URL[data_center_name]

    # dataCenterName 有时可能直接返回 URL
    if data_center_name.startswith("http://") or data_center_name.startswith("https://"):
        return data_center_name

    return data_center or web_address


def _ensure_uuid(raw_value: Any) -> str:
    raw = str(raw_value or "").strip()
    if raw:
        try:
            return str(uuid_lib.UUID(raw))
        except ValueError:
            pass
    return str(uuid_lib.uuid4())


def aes_encrypt(plain_text):

    KEY = "ABCDEFGHIJKL_key"
    # IV偏移量 (需与前端/后端一致)
    IV = "ABCDEFGHIJKLM_iv"

    if not plain_text:
        return None

    # 创建cipher对象
    cipher = AES.new(
        key=KEY.encode('utf-8'),
        mode=AES.MODE_CBC,
        iv=IV.encode('utf-8')
    )

    # 加密并添加填充
    encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))

    # Base64编码
    return base64.b64encode(encrypted).decode('utf-8')


def loginIn(username, password):
    url = "http://conet.rdcn.link/piflow-web/jwtLogin"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": "Bearer false",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "http://conet.rdcn.link",
        "Referer": "http://conet.rdcn.link/login",
        "User-Agent": "Mozilla/5.0"
    }

    data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)

        if response.status_code != 200:
            raise Exception(f"登录失败，HTTP状态码: {response.status_code}")

        result = response.json()

        # 判断业务是否成功
        if result.get("code") == 200:
            token = result.get("token")
            if not token:
                raise Exception("登录成功但未返回token")
            return token
        else:
            raise Exception(f"登录失败: {result.get('errorMsg')}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求异常: {e}")


def run_flow(token, flow_id):
    url = "http://conet.rdcn.link/piflow-web/flow/runFlow"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "http://conet.rdcn.link",
        "Referer": "http://conet.rdcn.link/flowTask",
        "User-Agent": "Mozilla/5.0"
    }

    data = {
        "flowId": flow_id
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            verify=False,
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"调用 runFlow 失败，HTTP状态码: {response.status_code}")

        result = response.json()

        # 根据实际接口返回判断（有的接口没有 code，需要你确认）
        if result.get("code") == 200 or "success" in str(result).lower():
            return result
        else:
            raise Exception(f"运行 flow 失败: {result}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求异常: {e}")


def search_and_analyze_datasets(
    token: str,
    fuzzy_search: str,
    page: int = 1,
    limit: int = 10,
    datacenter_id: str = "",
) -> dict[str, Any]:
    """
    检索协同数据源，并返回统一化分析结果。
    对应接口：/piflow-vue-web/datasource/v2/getSynergyByPage
    """
    url = "http://conet.rdcn.link/piflow-web/datasource/v2/getSynergyByPage"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "http://conet.rdcn.link",
        "Referer": "http://conet.rdcn.link/data",
        "User-Agent": "Mozilla/5.0",
    }

    data = {
        "page": str(page),
        "limit": str(limit),
        "fuzzySearch": fuzzy_search,
        "datacenterId": datacenter_id,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            verify=False,
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"数据集检索请求异常: {e}")

    if response.status_code != 200:
        raise Exception(f"数据集检索失败，HTTP状态码: {response.status_code}")

    result = response.json()

    records: list[dict[str, Any]] = []
    total = None

    if isinstance(result, list):
        # 接口直接返回数组
        records = [x for x in result if isinstance(x, dict)]
    elif isinstance(result, dict):
        if "code" in result and result.get("code") != 200:
            raise Exception(f"数据集检索失败: {result.get('errorMsg') or result}")

        payload = result.get("data", result)

        if isinstance(payload, list):
            records = [x for x in payload if isinstance(x, dict)]
        elif isinstance(payload, dict):
            for key in ("records", "list", "rows", "data"):
                value = payload.get(key)
                if isinstance(value, list):
                    records = [x for x in value if isinstance(x, dict)]
                    break
            # 兼容 data 本身就是单条对象的情况
            if not records and "name" in payload:
                records = [payload]

            for key in ("total", "count", "totalCount"):
                value = payload.get(key)
                if value is not None:
                    total = int(value)
                    break

        if total is None:
            for key in ("total", "count", "totalCount"):
                value = result.get(key)
                if value is not None:
                    total = int(value)
                    break
    else:
        raise Exception(f"数据集检索返回格式不支持: {type(result)}")

    if total is None:
        total = len(records)

    dataset_stops = []
    for item in records:
        if not isinstance(item, dict):
            continue
        data_center_url = _resolve_data_center_url(item)
        dataset_stops.append(
            {
                "customizedProperties": item.get("customizedProperties") or {},
                "dataSourceId": item.get("dataSourceId") or item.get("id") or "",
                "dataCenter": data_center_url,
                "registerId": item.get("registerId") or item.get("registerID") or "",
                "sourceType": item.get("sourceType") or "",
                "webAddress": data_center_url,
                "name": item.get("nameZh")
                or item.get("datasetName")
                or item.get("dataSetName")
                or item.get("title")
                or "",
                "uuid": _ensure_uuid(item.get("uuid")),
                "bundle": item.get("stopBundle") or "",
                "properties": item.get("properties") or {},
                "keywordsZh": item.get("keywordsZh") or {},
                "descriptionZh": item.get("descriptionZh") or {},
            }
        )

    return {
        "query": {
            "fuzzy_search": fuzzy_search,
            "page": page,
            "limit": limit,
            "datacenter_id": datacenter_id,
        },
        "total": total,
        "returned": len(dataset_stops),
        "dataset_stops": dataset_stops,
    }


if __name__ == "__main__":

    username = "netuser1"
    password = "cnic$@Nzlh1"

    try:
        result = aes_encrypt(password)
        print(f"加密结果: {result}")
    except Exception as e:
        print(f"加密失败: {e}")

    token = loginIn(username,result)

    print(token)

    # print(run_flow(token,"c82b36ab3b60420aa8985a03821f3e92"))
    print(search_and_analyze_datasets(token, "榆林市卫星遥感数据集图像分割文件", page=1, limit=10))
