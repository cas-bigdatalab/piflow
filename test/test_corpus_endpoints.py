from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.corpus_router import router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_list_corpus_connectors_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.list_connector_details",
        lambda page_num, page_size, keyword=None: {
            "items": [
                {
                    "connector": {"connectorId": "DS-NODE-1", "name": "连接器节点1"},
                }
            ],
            "pagination": {"pageNum": page_num, "pageSize": page_size, "total": 1},
        },
    )

    with _build_client() as client:
        response = client.post("/corpus/connector/list", json={"pageNum": 1, "pageSize": 10})

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["items"][0]["connector"]["connectorId"] == "DS-NODE-1"


def test_list_corpus_datasets_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.list_dataset_details",
        lambda page_num, page_size, filters=None: {
            "items": [
                {
                    "id": "dataset-1",
                    "cstr": "ES-CORPUS-B138",
                    "title": "dataset title",
                    "connectorId": "DS-NODE-1",
                    "fromName": "连接器节点1",
                    "connectors": [
                        {
                            "connectorId": "DS-NODE-1",
                            "fromName": "连接器节点1",
                            "connectorOrganization": "中国地震台网中心",
                            "name": "中国地震台网中心",
                            "status": "可用",
                            "sync": "2026-08-07 11:52",
                            "recommended": True,
                        }
                    ],
                    "replicaCount": 1,
                    "name": "中国地震台网中心",
                }
            ],
            "pagination": {"pageNum": page_num, "pageSize": page_size, "total": 1},
        },
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/dataset/list",
            json={"pageNum": 1, "pageSize": 10, "title": "地震", "from": "connector-1"},
        )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["items"][0]["id"] == "dataset-1"
    assert response.json()["result"]["items"][0]["connectors"][0]["connectorId"] == "DS-NODE-1"
    assert response.json()["result"]["items"][0]["replicaCount"] == 1


def test_list_corpus_connectors_endpoint_passes_keyword(monkeypatch):
    seen = {}

    def fake_list_connector_details_with_resources(page_num, page_size, keyword=None):
        seen["page_num"] = page_num
        seen["page_size"] = page_size
        seen["keyword"] = keyword
        return {"items": [], "pagination": {"pageNum": page_num, "pageSize": page_size, "total": 0}}

    monkeypatch.setattr(
        "routers.corpus_router.list_connector_details",
        fake_list_connector_details_with_resources,
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/connector/list",
            json={"pageNum": 2, "pageSize": 20, "keyword": "地球"},
        )

    assert response.status_code == 200
    assert seen == {"page_num": 2, "page_size": 20, "keyword": "地球"}


def test_list_corpus_datasets_endpoint_passes_filters(monkeypatch):
    seen = {}

    def fake_list_dataset_details(page_num, page_size, filters=None):
        seen["page_num"] = page_num
        seen["page_size"] = page_size
        seen["filters"] = filters
        return {"items": [], "pagination": {"pageNum": page_num, "pageSize": page_size, "total": 0}}

    monkeypatch.setattr("routers.corpus_router.list_dataset_details", fake_list_dataset_details)

    with _build_client() as client:
        response = client.post(
            "/corpus/dataset/list",
            json={
                "pageNum": 2,
                "pageSize": 20,
                "id": "dataset-1",
                "title": "地震",
                "from": "connector-1",
            },
        )

    assert response.status_code == 200
    assert seen["page_num"] == 2
    assert seen["page_size"] == 20
    assert seen["filters"]["id"] == "dataset-1"
    assert seen["filters"]["title"] == "地震"
    assert seen["filters"]["from"] == "connector-1"


def test_get_corpus_dataset_detail_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.get_dataset_detail",
        lambda dataset_id: {
            "id": dataset_id,
            "cstr": "ES-CORPUS-B138",
            "title": "dataset title",
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
            "connectors": [
                {
                    "connectorId": "DS-NODE-1",
                    "fromName": "连接器节点1",
                    "connectorOrganization": "中国地震台网中心",
                    "name": "中国地震台网中心",
                    "status": "可用",
                    "sync": "2026-08-07 11:52",
                    "recommended": True,
                }
            ],
            "replicaCount": 1,
            "name": "中国地震台网中心",
        },
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/dataset/detail",
            json={"datasetId": "6a744595d38ea034d388c7b4"},
        )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["dataset"]["id"] == "6a744595d38ea034d388c7b4"
    assert response.json()["result"]["dataset"]["connectors"][0]["connectorId"] == "DS-NODE-1"


def test_create_rustfs_service_account_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.create_rustfs_temporary_credentials",
        lambda ttl, name=None, description=None: {
            "credentials": {
                "accessKey": "temp-ak",
                "secretKey": "temp-sk",
                "expiration": "2026-08-26T09:09:00Z",
            }
        },
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/rustfs/service-account",
            json={"ttl": "30s", "name": "mount-test", "description": "temporary"},
        )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["credentials"]["accessKey"] == "temp-ak"


def test_create_rustfs_service_account_endpoint_rejects_invalid_ttl(monkeypatch):
    def fake_create(ttl, name=None, description=None):
        raise ValueError("ttl must look like '30s', '5m', '1h', or '1d'")

    monkeypatch.setattr(
        "routers.corpus_router.create_rustfs_temporary_credentials",
        fake_create,
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/rustfs/service-account",
            json={"ttl": "abc"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "ttl must look like '30s', '5m', '1h', or '1d'"


def test_get_rustfs_mount_info_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.build_rustfs_mount_info",
        lambda file_name: {
            "fileName": "chem-corpus-k037.tar",
            "mountDirName": "CHEM-CORPUS-K037",
            "mountPath": "/mnt/corpus/CHEM-CORPUS-K037",
            "ttl": "5m",
            "credentials": {
                "accessKey": "temp-ak",
                "secretKey": "temp-sk",
                "expiration": "2026-08-26T09:09:00Z",
            },
            "script": "rclone script",
        },
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/rustfs/mount-info",
            json={"fileName": "chem-corpus-k037"},
        )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["fileName"] == "chem-corpus-k037.tar"
    assert response.json()["result"]["mountDirName"] == "CHEM-CORPUS-K037"


def test_get_rustfs_mount_info_endpoint_rejects_invalid_input(monkeypatch):
    def fake_build(file_name):
        raise ValueError("fileName is required")

    monkeypatch.setattr(
        "routers.corpus_router.build_rustfs_mount_info",
        fake_build,
    )

    with _build_client() as client:
        response = client.post(
            "/corpus/rustfs/mount-info",
            json={"fileName": "   "},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "fileName is required"


def test_get_corpus_dataset_file_jsonl_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.get_dataset_file_jsonl",
        lambda cstr: {
            "cstr": cstr,
            "fileName": "sample.jsonl",
            "downloadUrl": "http://example.com/sample.jsonl",
            "json": [{"id": 1}, {"id": 2}],
        },
    )

    with _build_client() as client:
        response = client.get("/dataset/downloadDatasetFileAsJsonl/ES-CORPUS-B138")

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["json"][0]["id"] == 1


def test_get_corpus_connector_latency_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.get_corpus_connector_latency",
        lambda connector_id: {
            "connectorId": connector_id,
            "remote_grpc_target": "10.0.82.213:50061",
            "latency_ms": 12.345,
        },
    )

    with _build_client() as client:
        response = client.get("/corpus/connector/latency?id=DS-NODE-1")

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["result"]["connectorId"] == "DS-NODE-1"
    assert response.json()["result"]["latency_ms"] == 12.345


def test_list_corpus_connectors_endpoint_rejects_invalid_page(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.list_connector_details_with_resources",
        lambda page_num, page_size, keyword=None: (_ for _ in ()).throw(ValueError("page_num must be positive")),
    )

    with _build_client() as client:
        response = client.post("/corpus/connector/list", json={"pageNum": 0, "pageSize": 10})

    assert response.status_code == 400
    assert response.json()["detail"] == "page_num must be positive"


def test_corpus_connector_proxy_endpoints(monkeypatch):
    monkeypatch.setattr(
        "routers.corpus_router.create_corpus_connector",
        lambda payload: {"op": "save", "payload": payload},
    )
    monkeypatch.setattr(
        "routers.corpus_router.update_corpus_connector",
        lambda payload: {"op": "update", "payload": payload},
    )
    monkeypatch.setattr(
        "routers.corpus_router.delete_corpus_connector",
        lambda connector_id: {"op": "delete", "id": connector_id},
    )
    monkeypatch.setattr(
        "routers.corpus_router.disable_corpus_connector",
        lambda connector_id: {"op": "disable", "id": connector_id},
    )
    monkeypatch.setattr(
        "routers.corpus_router.get_corpus_connector_detail",
        lambda connector_id: {"op": "detail", "id": connector_id},
    )
    monkeypatch.setattr(
        "routers.corpus_router.enable_corpus_connector",
        lambda connector_id: {"op": "enable", "id": connector_id},
    )
    monkeypatch.setattr(
        "routers.corpus_router.get_corpus_connector_tree",
        lambda: {"op": "tree"},
    )

    with _build_client() as client:
        save_res = client.post("/corpus/connector/save", json={"name": "demo"})
        update_res = client.post("/corpus/connector/update", json={"id": "c-1"})
        detail_res = client.get("/corpus/connector/detail", params={"id": "c-1"})
        delete_res = client.get("/corpus/connector/delete", params={"id": "c-1"})
        disable_res = client.get("/corpus/connector/disable", params={"id": "c-1"})
        enable_res = client.get("/corpus/connector/enable", params={"id": "c-1"})
        tree_res = client.get("/corpus/connector/tree")

    assert save_res.status_code == 200
    assert save_res.json()["result"]["op"] == "save"
    assert update_res.json()["result"]["op"] == "update"
    assert detail_res.json()["result"]["op"] == "detail"
    assert delete_res.json()["result"]["op"] == "delete"
    assert disable_res.json()["result"]["op"] == "disable"
    assert enable_res.json()["result"]["op"] == "enable"
    assert tree_res.json()["result"]["op"] == "tree"
