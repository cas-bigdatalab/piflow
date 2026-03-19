import uuid

from skills.synergy_datasource_search.scripts import synergy_datasource_search as skill


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_synergy_datasource_search_process(monkeypatch):
    calls = {"count": 0}

    def fake_post(url, headers=None, data=None, verify=None, timeout=None):  # noqa: ANN001
        calls["count"] += 1
        payload = {
            "code": 200,
            "data": {
                "records": [
                    {
                        "dataSourceId": "eeddd7533316dbe26146565c18c95505",
                        "dataCenterName": "国家对地观测科学数据中心",
                        "registerId": "CSTR:33113.11.ZYlk4iEw9sxvKs",
                        "sourceType": "COLLABORATIVE_NETWORK",
                        "name": "榆林市卫星遥感数据集图像分割文件",
                        "uuid": "not-a-uuid",
                        "bundle": "cn.piflow.bundle.hdfs.HdfsPathToDf",
                        "properties": {},
                    }
                ]
            },
        }
        return _FakeResponse(200, payload)

    monkeypatch.setattr(skill.requests, "post", fake_post)

    result = skill.process(
        analysis_name="山洪敏感度识别",
        required_data_source_keywords=["沟道", "高程", "地貌信息熵"],
        required_data_source_full_names=[],
        token="mock-token",
        size=10,
    )

    assert result["analysis_name"] == "山洪敏感度识别"
    assert len(result["required_data_source_keywords"]) == 3
    assert result["required_data_source_full_names"] == []
    assert result["dataset_count"] == 1
    assert calls["count"] == len(result["required_data_source_keywords"])
    assert result["exact_full_name_matched_count"] == 0
    assert result["keyword_related_count"] == 1

    stop = result["dataset_stops"][0]
    assert stop["dataCenter"] == "http://124.16.184.77:7801"
    assert stop["webAddress"] == "http://124.16.184.77:7801"
    assert stop["name"] == "榆林市卫星遥感数据集图像分割文件"
    assert stop["bundle"] == "cn.piflow.bundle.hdfs.HdfsPathToDf"

    uuid.UUID(stop["uuid"])


def test_dam_intent_adds_full_name_search(monkeypatch):
    calls: list[str] = []

    def fake_post(url, headers=None, data=None, verify=None, timeout=None):  # noqa: ANN001
        query = str((data or {}).get("fuzzySearch", "")).strip()
        calls.append(query)

        if query == "榆林市卫星遥感数据集图像分割文件":
            payload = {
                "code": 200,
                "data": {
                    "records": [
                        {
                            "dataSourceId": "eeddd7533316dbe26146565c18c95505",
                            "dataCenterName": "国家对地观测科学数据中心",
                            "registerId": "CSTR:33113.11.ZYlk4iEw9sxvKs",
                            "sourceType": "COLLABORATIVE_NETWORK",
                            "name": "榆林市卫星遥感数据集图像分割文件",
                            "bundle": "cn.piflow.bundle.hdfs.HdfsPathToDf",
                            "properties": {},
                        }
                    ]
                },
            }
            return _FakeResponse(200, payload)

        return _FakeResponse(200, {"code": 200, "data": {"records": []}})

    monkeypatch.setattr(skill.requests, "post", fake_post)

    result = skill.process(
        analysis_name="淤地坝识别筛选",
        required_data_source_keywords=["沟道", "高程", "地貌信息熵", "卫星遥感分割", "地理坐标"],
        required_data_source_full_names=[
            "2019年中国榆林市30m数字高程数据集",
            "2019年中国榆林市沟道信息",
            "地貌信息熵",
            "榆林市卫星遥感数据集图像分割文件",
            "榆林市地理坐标信息文件",
        ],
        token="mock-token",
        size=10,
    )

    assert "榆林市卫星遥感数据集图像分割文件" in result["required_data_source_full_names"]
    assert "榆林市卫星遥感数据集图像分割文件" in calls
    assert result["dataset_count"] == 1
    assert result["exact_full_name_matched_count"] == 1
    assert result["exact_full_name_matched_dataset_stops"][0]["name"] == "榆林市卫星遥感数据集图像分割文件"
    assert result["keyword_related_count"] == 0
    assert "地貌信息熵" in result["missing_required_full_names"]
