from __future__ import annotations

import io
import tarfile

from services.corpus_connector_service import (
    build_rustfs_mount_info,
    create_rustfs_temporary_credentials,
    create_corpus_connector,
    delete_corpus_connector,
    disable_corpus_connector,
    get_dataset_detail,
    get_dataset_detail_by_cstr,
    get_dataset_file_jsonl,
    get_corpus_connector_detail,
    get_corpus_connector_tree,
    enable_corpus_connector,
    list_connector_details,
    get_dataset_connector_detail_with_resource,
    get_dataset_connector_resource,
    update_corpus_connector,
    list_connector_details_with_resources,
    list_dataset_details,
    list_dataset_details_v2,
    list_connector_resources,
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.content = payload if isinstance(payload, bytes) else b""

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_create_rustfs_temporary_credentials_signs_and_returns_credentials(monkeypatch):
    seen = {}

    def fake_request(method, url, data=None, headers=None, timeout=None):
        seen["method"] = method
        seen["url"] = url
        seen["data"] = data
        seen["headers"] = headers
        seen["timeout"] = timeout
        return _FakeResponse(
            {
                "credentials": {
                    "accessKey": "temp-ak",
                    "secretKey": "temp-sk",
                    "expiration": "2026-08-26T09:09:00Z",
                }
            }
        )

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "rustfs_admin": type(
                    "RustFSAdmin",
                    (),
                    {
                        "base_url": "http://10.0.85.201:9001",
                        "access_key": "rustfsadmin",
                        "secret_key": "rustfsadmin",
                        "session_token": "jwt-token",
                        "service": "s3",
                        "region": "us-east-1",
                        "timeout_seconds": 12,
                    },
                )(),
            },
        )(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.request", fake_request)

    result = create_rustfs_temporary_credentials("30s", name="mount-test", description="temporary")

    assert result == {
        "credentials": {
            "accessKey": "temp-ak",
            "secretKey": "temp-sk",
            "expiration": "2026-08-26T09:09:00Z",
        }
    }
    assert seen["method"] == "PUT"
    assert seen["url"] == "http://10.0.85.201:9001/rustfs/admin/v3/add-service-accounts"
    assert seen["timeout"] == 12
    assert "\"accessKey\":\"" in seen["data"]
    assert "\"secretKey\":\"" in seen["data"]
    assert "\"name\":\"mount-test\"" in seen["data"]
    assert "\"description\":\"temporary\"" in seen["data"]
    assert "\"expiration\":\"" in seen["data"]
    assert "Authorization" in seen["headers"]
    normalized_headers = {str(key).lower(): value for key, value in seen["headers"].items()}
    assert "x-amz-content-sha256" in normalized_headers
    assert normalized_headers["x-amz-security-token"] == "jwt-token"


def test_create_rustfs_temporary_credentials_rejects_invalid_ttl(monkeypatch):
    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "rustfs_admin": type(
                    "RustFSAdmin",
                    (),
                    {
                        "base_url": "http://10.0.85.201:9001",
                        "access_key": "rustfsadmin",
                        "secret_key": "rustfsadmin",
                        "service": "s3",
                        "region": "us-east-1",
                        "timeout_seconds": 30,
                    },
                )(),
            },
        )(),
    )

    try:
        create_rustfs_temporary_credentials("abc")
        raised = False
    except ValueError as exc:
        raised = True
        assert str(exc) == "ttl must look like '30s', '5m', '1h', or '1d'"

    assert raised is True


def test_build_rustfs_mount_info_uses_generated_credentials(monkeypatch):
    monkeypatch.setattr(
        "services.corpus_connector_service.create_rustfs_temporary_credentials",
        lambda ttl, name=None, description=None: {
            "credentials": {
                "accessKey": "temp-ak",
                "secretKey": "temp-sk",
                "expiration": "2026-08-26T09:09:00Z",
            }
        },
    )

    result = build_rustfs_mount_info("chem-corpus-k037")

    assert result["fileName"] == "chem-corpus-k037.tar"
    assert result["mountDirName"] == "CHEM-CORPUS-K037"
    assert result["mountPath"] == "/mnt/corpus/CHEM-CORPUS-K037"
    assert result["ttl"] == "5m"
    assert result["env"]["RCLONE_CONFIG_MOUNTTMP_ACCESS_KEY_ID"] == "temp-ak"
    assert result["env"]["RCLONE_CONFIG_MOUNTTMP_SECRET_ACCESS_KEY"] == "temp-sk"
    assert "--include '/chem-corpus-k037.tar'" in result["commands"]["mount"]
    assert "/mnt/corpus/CHEM-CORPUS-K037" in result["script"]


def test_build_rustfs_mount_info_keeps_suffix_for_mount_file_name(monkeypatch):
    monkeypatch.setattr(
        "services.corpus_connector_service.create_rustfs_temporary_credentials",
        lambda ttl, name=None, description=None: {
            "credentials": {
                "accessKey": "temp-ak",
                "secretKey": "temp-sk",
                "expiration": "2026-08-26T09:09:00Z",
            }
        },
    )

    result = build_rustfs_mount_info("chem-corpus-k037.tar.gz")

    assert result["fileName"] == "chem-corpus-k037.tar.gz"
    assert result["mountDirName"] == "CHEM-CORPUS-K037.TAR"


class _FakeRemoteResource:
    cpu_cores = 8.0
    memory_gb = 16.0
    free_disk_gb = 128.0
    hostname = "node-1"


class _FakeRemoteExecutionClient:
    last_target = None
    closed = False

    def __init__(self, target: str):
        type(self).last_target = target
        type(self).closed = False

    def get_server_resource(self):
        return _FakeRemoteResource()

    def close(self) -> None:
        type(self).closed = True


class _FailingRemoteExecutionClient:
    closed = False

    def __init__(self, target: str):
        self.target = target
        type(self).closed = False

    def get_server_resource(self):
        raise RuntimeError(f"unavailable: {self.target}")

    def close(self) -> None:
        type(self).closed = True


def _fake_dataset_resolve_remote_resource(connector, *, grpc_port):
    connector_id = str(connector.get("connectorId", "") or "").strip()
    latency_map = {
        "DS-NODE-1": 20.0,
        "DS-NODE-2": 10.0,
        "DS-NODE-3": 30.0,
    }
    if connector_id not in latency_map:
        return "", {
            "cpu_cores": None,
            "memory_gb": None,
            "free_disk_gb": None,
            "hostname": None,
            "latency_ms": None,
        }
    return f"{connector_id.lower()}:50061", {
        "cpu_cores": 8.0,
        "memory_gb": 16.0,
        "free_disk_gb": 128.0,
        "hostname": connector_id.lower(),
        "latency_ms": latency_map[connector_id],
    }


def test_get_dataset_file_jsonl_downloads_and_parses_jsonl(monkeypatch):
    seen_urls = []

    class _FakeDownloadResponse(_FakeResponse):
        encoding = None

        @property
        def text(self):
            return '{"id": 1}\n{"id": 2}\n'

    def fake_get(url, params=None, timeout=None):
        seen_urls.append(url)
        if url.endswith("/dataset/downloadDatasetFileUrls/ES-CORPUS-B138"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": [
                        {
                            "downloadUrls": ["http://10.0.82.213:7004/files/sample.jsonl"],
                            "name": "连接器节点1",
                        }
                    ],
                }
            )
        if url.endswith("/files/sample.jsonl"):
            return _FakeDownloadResponse(b'{"id": 1}\n{"id": 2}\n')
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)

    result = get_dataset_file_jsonl("ES-CORPUS-B138")

    assert result["fileName"] == "sample.jsonl"
    assert result["json"] == [{"id": 1}, {"id": 2}]
    assert seen_urls == [
        "http://10.0.82.213:7003/dataset/downloadDatasetFileUrls/ES-CORPUS-B138",
        "http://10.0.82.213:7004/files/sample.jsonl",
    ]


def test_get_dataset_file_jsonl_parses_jsonl_from_tar(monkeypatch):
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w") as archive:
        content = b'{"id": 1}\n{"id": 2}\n'
        info = tarfile.TarInfo("records.jsonl")
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    archive_bytes = archive_buffer.getvalue()

    class _ArchiveResponse(_FakeResponse):
        def __init__(self):
            super().__init__(archive_bytes)

    def fake_get(url, params=None, timeout=None):
        if url.endswith("/dataset/downloadDatasetFileUrls/ES-CORPUS-F018"):
            return _FakeResponse(
                {
                    "code": 200,
                    "data": [
                        {
                            "downloadUrls": ["http://10.0.82.213:7004/files/f018.tar"],
                            "name": "连接器节点1",
                        }
                    ],
                }
            )
        if url.endswith("/files/f018.tar"):
            return _ArchiveResponse()
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)

    result = get_dataset_file_jsonl("ES-CORPUS-F018")

    assert result["fileName"] == "f018.tar"
    assert result["contentFileName"] == "records.jsonl"
    assert result["json"] == [{"id": 1}, {"id": 2}]


def test_list_connector_resources_uses_service_url_host(monkeypatch):
    payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                }
            ]
        },
    }

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        lambda url, params, timeout: _FakeResponse(payload),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = list_connector_resources()

    assert result["DS-NODE-1"]["connector"]["connectorId"] == "DS-NODE-1"
    assert result["DS-NODE-1"]["remote_grpc_target"] == "10.0.82.213:50061"
    assert result["DS-NODE-1"]["resource"]["cpu_cores"] == 8.0
    assert _FakeRemoteExecutionClient.last_target == "10.0.82.213:50061"
    assert _FakeRemoteExecutionClient.closed is True


def test_get_dataset_connector_detail_with_resource_joins_by_connector_id(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "id": "6a744595d38ea034d388c7b4",
            "cstr": "ES-CORPUS-B138",
            "title": "dataset title",
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                }
            ]
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.queryDataset"):
            return _FakeResponse(dataset_payload)
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        fake_get,
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = get_dataset_connector_detail_with_resource("6a744595d38ea034d388c7b4")

    assert result["dataset"]["cstr"] == "ES-CORPUS-B138"
    assert result["connector"]["connectorId"] == "DS-NODE-1"
    assert result["remote_grpc_target"] == "10.0.82.213:50061"
    assert result["resource"]["cpu_cores"] == 8.0
    assert _FakeRemoteExecutionClient.last_target == "10.0.82.213:50061"
    assert _FakeRemoteExecutionClient.closed is True


def test_get_dataset_connector_resource_prefers_explicit_grpc_target(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "id": "dataset-2",
            "cstr": "ABC",
            "connectorId": "DS-NODE-2",
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                "connectorId": "DS-NODE-2",
                "remoteGrpcTarget": "10.0.0.2:50062",
                }
            ]
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.queryDataset"):
            return _FakeResponse(dataset_payload)
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        fake_get,
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = get_dataset_connector_resource("dataset-2", grpc_port=60000)

    assert result["remote_grpc_target"] == "10.0.0.2:50062"


def test_list_connector_details_with_resources_returns_pagination(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        lambda url, params, timeout: _FakeResponse(connector_payload),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = list_connector_details_with_resources(page_num=1, page_size=10)

    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 1}
    assert result["items"][0]["connector"]["connectorId"] == "DS-NODE-1"
    assert result["items"][0]["resource"]["hostname"] == "node-1"
    assert result["items"][0]["resource_display"] == {
        "hostname": "node-1",
        "cpu": "8 核",
        "memory": "16.00 GB",
        "free_disk": "128.00 GB",
        "summary": "node-1 · CPU 8 核 · 内存 16.00 GB · 剩余磁盘 128.00 GB",
    }


def test_list_connector_details_returns_basic_items_only(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    called = {"resource": False}

    def fake_get(url, params, timeout):
        assert url.endswith("/dataset.connector.page")
        return _FakeResponse(connector_payload)

    def fake_remote_client(*args, **kwargs):
        called["resource"] = True
        raise AssertionError("resource lookup should not be called")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.create_remote_execution_client", fake_remote_client)

    result = list_connector_details(page_num=1, page_size=10)

    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 1}
    assert result["items"] == [
        {
            "connector": {
                "connectorId": "DS-NODE-1",
                "name": "连接器节点1",
                "enabled": None,
                "serviceUrl": "10.0.82.213:7004",
                "protocol": "",
                "institution": "",
                "host": "",
                "remoteGrpcTarget": "",
                "grpcPort": "",
                "sync": "",
                "recommended": False,
                "raw": {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                },
            }
        }
    ]
    assert called["resource"] is False


def test_list_connector_details_with_resources_forwards_keyword(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {"connectorId": "DS-NODE-1", "name": "连接器节点1"},
                {"connectorId": "DS-NODE-2", "name": "连接器节点2"},
                {"connectorId": "DS-NODE-3", "name": "连接器节点3"},
            ],
            "total": 3,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    seen = {}

    def fake_get(url, params, timeout):
        seen["url"] = url
        seen["params"] = params
        return _FakeResponse(connector_payload)

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)

    result = list_connector_details_with_resources(
        page_num=1,
        page_size=10,
        keyword=" DS-NODE-1 ",
    )

    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.page"
    assert seen["params"] == {"pageNum": 1, "pageSize": 10, "keyword": "DS-NODE-1"}
    assert len(result["items"]) == 1
    assert result["items"][0]["connector"]["connectorId"] == "DS-NODE-1"


def test_list_connector_details_with_resources_filters_connector_id_keyword(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "serviceUrl": "10.0.90.174:7004",
                },
                {
                    "connectorId": "DS-NODE-3",
                    "name": "连接器节点3",
                    "serviceUrl": "10.0.90.94:7004",
                },
            ],
            "total": 3,
            "pageNum": 1,
            "pageSize": 10,
        },
    }

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        lambda url, params, timeout: _FakeResponse(connector_payload),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = list_connector_details_with_resources(
        page_num=1,
        page_size=10,
        keyword="DS-NODE-1",
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["connector"]["connectorId"] == "DS-NODE-1"


def test_list_connector_details_with_resources_returns_null_resource_when_grpc_fails(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "10.0.82.213:7004",
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        lambda url, params, timeout: _FakeResponse(connector_payload),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.create_remote_execution_client",
        _FailingRemoteExecutionClient,
    )

    result = list_connector_details_with_resources(page_num=1, page_size=10)

    assert result["items"][0]["remote_grpc_target"] == "10.0.82.213:50061"
    assert result["items"][0]["resource"] == {
        "cpu_cores": None,
        "memory_gb": None,
        "free_disk_gb": None,
        "hostname": None,
    }
    assert result["items"][0]["resource_display"] == {
        "hostname": None,
        "cpu": None,
        "memory": None,
        "free_disk": None,
        "summary": "",
    }
    assert _FailingRemoteExecutionClient.closed is True


def test_list_connector_details_with_resources_returns_null_resource_when_host_missing(monkeypatch):
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "serviceUrl": "-",
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.get",
        lambda url, params, timeout: _FakeResponse(connector_payload),
    )

    result = list_connector_details_with_resources(page_num=1, page_size=10)

    assert result["items"][0]["remote_grpc_target"] == ""
    assert result["items"][0]["resource"] == {
        "cpu_cores": None,
        "memory_gb": None,
        "free_disk_gb": None,
        "hostname": None,
    }


def test_list_dataset_details_returns_dataset_page(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点1",
                    "fromList": [{"connectorId": "DS-NODE-1", "name": "连接器节点1"}],
                },
                {
                    "id": "dataset-2",
                    "title": "disabled dataset",
                    "cstr": "ES-CORPUS-B139",
                    "source": "连接器节点2",
                    "fromList": [{"connectorId": "DS-NODE-2", "name": "连接器节点2"}],
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "organization": "不可用机构",
                    "status": 0,
                    "sync": "2026-08-08 09:15",
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    def fake_post(url, params, json, timeout):
        if url.endswith("/dataset.page"):
            return _FakeResponse(dataset_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = list_dataset_details(page_num=1, page_size=10)

    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 2}
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == "dataset-1"
    assert result["items"][0]["connectorId"] == "DS-NODE-1"
    assert result["items"][0]["title"] == "dataset title"
    assert result["items"][0]["name"] == "连接器节点1"
    assert result["items"][0]["replicaCount"] == 1
    assert result["items"][0]["connectors"] == [
        {
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
            "connectorOrganization": "中国地震台网中心",
            "name": "连接器节点1",
            "status": "可用",
            "sync": "2026-08-07 11:52",
            "recommended": True,
            "latency_ms": 20.0,
        }
    ]
    assert result["items"][1]["connectors"] == [
        {
            "connectorId": "DS-NODE-2",
            "fromName": "连接器节点2",
            "connectorOrganization": "不可用机构",
            "name": "连接器节点2",
            "status": "不可用",
            "sync": "2026-08-08 09:15",
            "recommended": True,
            "latency_ms": 10.0,
        }
    ]


def test_list_dataset_details_uses_top_level_total_when_data_is_a_list(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": [
            {
                "id": f"dataset-{index}",
                "title": f"dataset title {index}",
                "cstr": f"ES-CORPUS-{index:03d}",
                "source": f"连接器节点{index}",
                "fromList": [{"name": f"连接器节点{index}"}],
            }
            for index in range(10)
        ],
        "total": 18,
        "pageNum": 1,
        "pageSize": 10,
    }

    def fake_post(url, params, json, timeout):
        assert url.endswith("/dataset.page")
        assert params == {"pageNum": 1, "pageSize": 10}
        return _FakeResponse(dataset_payload)

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "corpus_route": type(
                    "CorpusRoute",
                    (),
                    {"base_url": "http://10.0.82.213:7003"},
                )()
            },
        )(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)

    result = list_dataset_details(page_num=1, page_size=10)

    assert len(result["items"]) == 10
    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 18}


def test_list_dataset_details_returns_multiple_connectors(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点1",
                    "fromList": [
                        {"connectorId": "DS-NODE-1", "name": "连接器节点1"},
                        {"connectorId": "DS-NODE-2", "name": "连接器节点2"},
                    ],
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "institutionName": "国家地球系统科学数据中心",
                    "status": 1,
                    "sync": "2026-08-07 12:10",
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    def fake_post(url, params, json, timeout):
        if url.endswith("/dataset.page"):
            return _FakeResponse(dataset_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = list_dataset_details(page_num=1, page_size=10)

    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 1}
    assert len(result["items"]) == 1
    assert result["items"][0]["connectorId"] == "DS-NODE-1"
    assert result["items"][0]["fromName"] == "连接器节点1"
    assert result["items"][0]["replicaCount"] == 2
    assert result["items"][0]["connectors"] == [
        {
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
            "connectorOrganization": "中国地震台网中心",
            "name": "连接器节点1",
            "status": "可用",
            "sync": "2026-08-07 11:52",
            "recommended": False,
            "latency_ms": 20.0,
        },
        {
            "connectorId": "DS-NODE-2",
            "fromName": "连接器节点2",
            "connectorOrganization": "国家地球系统科学数据中心",
            "name": "连接器节点2",
            "status": "可用",
            "sync": "2026-08-07 12:10",
            "recommended": True,
            "latency_ms": 10.0,
        },
    ]
    assert result["items"][0]["name"] == "连接器节点1"


def test_list_dataset_details_keeps_unavailable_connectors(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点1",
                    "fromList": [
                        {"connectorId": "DS-NODE-1", "name": "连接器节点1"},
                        {"connectorId": "DS-NODE-2", "name": "连接器节点2"},
                    ],
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "institutionName": "不可用机构",
                    "status": 0,
                    "sync": "2026-08-08 09:15",
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    def fake_post(url, params, json, timeout):
        if url.endswith("/dataset.page"):
            return _FakeResponse(dataset_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = list_dataset_details(page_num=1, page_size=10)

    assert len(result["items"]) == 1
    assert result["items"][0]["replicaCount"] == 2
    assert result["items"][0]["connectors"][1] == {
        "connectorId": "DS-NODE-2",
        "fromName": "连接器节点2",
        "connectorOrganization": "不可用机构",
        "name": "连接器节点2",
        "status": "不可用",
        "sync": "2026-08-08 09:15",
        "recommended": True,
        "latency_ms": 10.0,
    }


def test_list_dataset_details_merges_duplicate_dataset_rows_from_multiple_connectors(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点1",
                    "fromList": [{"connectorId": "DS-NODE-1", "name": "连接器节点1"}],
                },
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点2",
                    "fromList": [{"connectorId": "DS-NODE-2", "name": "连接器节点2"}],
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "institutionName": "国家地球系统科学数据中心",
                    "status": 1,
                    "sync": "2026-08-07 12:10",
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    def fake_post(url, params, json, timeout):
        if url.endswith("/dataset.page"):
            return _FakeResponse(dataset_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = list_dataset_details(page_num=1, page_size=10)

    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == "dataset-1"
    assert result["items"][0]["replicaCount"] == 2
    assert [item["name"] for item in result["items"][0]["connectors"]] == ["连接器节点1", "连接器节点2"]


def test_list_dataset_details_forwards_filters(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [],
            "total": 0,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    seen = {}

    def fake_post(url, params, json, timeout):
        seen["url"] = url
        seen["params"] = params
        seen["json"] = json
        return _FakeResponse(dataset_payload)

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr(
        "services.corpus_connector_service.requests.post",
        fake_post,
    )

    list_dataset_details(
        page_num=2,
        page_size=20,
        filters={
            "title": "  地震  ",
            "fileNumber": 10,
            "publishAt": __import__("datetime").datetime(2026, 8, 20, 3, 29, 22, 345000),
            "from": " connector-1 ",
            "empty": "",
            "none": None,
        },
    )

    assert seen["url"].endswith("/dataset.page")
    assert seen["params"] == {"pageNum": 2, "pageSize": 20}
    assert seen["json"] == {
        "title": "地震",
        "fileNumber": 10,
        "publishAt": "2026-08-20T03:29:22.345000",
        "from": "connector-1",
    }


def test_list_dataset_details_v2_proxies_dataset_page_and_adds_replica_count(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "id": "dataset-1",
                    "title": "dataset title",
                    "cstr": "ES-CORPUS-B138",
                    "source": "连接器节点1",
                    "fromList": [{"connectorId": "DS-NODE-1", "name": "连接器节点1"}],
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 10,
        },
    }
    seen = {}

    def fake_post(url, params, json, timeout):
        seen["url"] = url
        seen["params"] = params
        seen["json"] = json
        return _FakeResponse(dataset_payload)

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)

    result = list_dataset_details_v2(
        page_num=1,
        page_size=10,
        filters={"title": "  地震  ", "from": " connector-1 "},
    )

    assert seen["url"].endswith("/dataset.page")
    assert seen["params"] == {"pageNum": 1, "pageSize": 10}
    assert seen["json"] == {"title": "地震", "from": "connector-1"}
    assert result["pagination"] == {"pageNum": 1, "pageSize": 10, "total": 1}
    assert result["items"] == [
        {
            "id": "dataset-1",
            "title": "dataset title",
            "cstr": "ES-CORPUS-B138",
            "source": "连接器节点1",
            "fromList": [{"connectorId": "DS-NODE-1", "name": "连接器节点1"}],
            "replicaCount": 1,
        }
    ]


def test_get_dataset_detail_returns_single_dataset(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "id": "6a744595d38ea034d388c7b4",
            "title": "dataset title",
            "cstr": "ES-CORPUS-B138",
            "source": "连接器节点1",
            "fromList": [{"connectorId": "DS-NODE-1", "name": "连接器节点1"}],
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                }
            ],
            "total": 1,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset/queryDataset"):
            return _FakeResponse(dataset_payload)
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = get_dataset_detail("6a744595d38ea034d388c7b4")

    assert result["id"] == "6a744595d38ea034d388c7b4"
    assert result["cstr"] == "ES-CORPUS-B138"
    assert result["connectorId"] == "DS-NODE-1"
    assert result["replicaCount"] == 1
    assert result["connectors"] == [
        {
            "connectorId": "DS-NODE-1",
            "fromName": "连接器节点1",
            "connectorOrganization": "中国地震台网中心",
            "name": "连接器节点1",
            "status": "可用",
            "sync": "2026-08-07 11:52",
            "recommended": True,
            "latency_ms": 20.0,
        }
    ]


def test_get_dataset_detail_keeps_unavailable_connectors(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "id": "6a744595d38ea034d388c7b4",
            "title": "dataset title",
            "cstr": "ES-CORPUS-B138",
            "source": "连接器节点1",
            "fromList": [
                {"connectorId": "DS-NODE-1", "name": "连接器节点1"},
                {"connectorId": "DS-NODE-2", "name": "连接器节点2"},
            ],
        },
    }
    connector_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "content": [
                {
                    "connectorId": "DS-NODE-1",
                    "name": "连接器节点1",
                    "institutionName": "中国地震台网中心",
                    "status": 1,
                    "sync": "2026-08-07 11:52",
                },
                {
                    "connectorId": "DS-NODE-2",
                    "name": "连接器节点2",
                    "institutionName": "不可用机构",
                    "status": 0,
                    "sync": "2026-08-08 09:15",
                },
            ],
            "total": 2,
            "pageNum": 1,
            "pageSize": 100,
        },
    }

    def fake_get(url, params, timeout):
        if url.endswith("/dataset/queryDataset"):
            return _FakeResponse(dataset_payload)
        if url.endswith("/dataset.connector.page"):
            return _FakeResponse(connector_payload)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr(
        "services.corpus_connector_service._resolve_remote_resource",
        _fake_dataset_resolve_remote_resource,
    )

    result = get_dataset_detail("6a744595d38ea034d388c7b4")

    assert result["replicaCount"] == 2
    assert result["connectors"][1] == {
        "connectorId": "DS-NODE-2",
        "fromName": "连接器节点2",
        "connectorOrganization": "不可用机构",
        "name": "连接器节点2",
        "status": "不可用",
        "sync": "2026-08-08 09:15",
        "recommended": True,
        "latency_ms": 10.0,
    }


def test_get_dataset_detail_by_cstr_returns_upstream_data(monkeypatch):
    dataset_payload = {
        "code": 200,
        "message": "OK",
        "data": {
            "id": "6aa7b5fcd73768d1650bd7d1",
            "cstr": "ST001-CAMPBELL-B001",
            "title": "共和县光伏观测站campbell仪器观测数据集",
            "source": "西宁共和县光伏观测站",
        },
    }
    seen = {}

    def fake_get(url, timeout):
        seen["url"] = url
        seen["timeout"] = timeout
        return _FakeResponse(dataset_payload)

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)

    result = get_dataset_detail_by_cstr(" ST001-CAMPBELL-B001 ")

    assert seen["url"].endswith("/dataset/ST001-CAMPBELL-B001")
    assert result == {
        "id": "6aa7b5fcd73768d1650bd7d1",
        "cstr": "ST001-CAMPBELL-B001",
        "title": "共和县光伏观测站campbell仪器观测数据集",
        "source": "西宁共和县光伏观测站",
    }


def test_get_dataset_detail_rejects_empty_data(monkeypatch):
    def fake_get(url, params, timeout):
        if url.endswith("/dataset.queryDataset"):
            return _FakeResponse({"code": 200, "message": "OK", "data": {}})
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)

    try:
        get_dataset_detail("dataset-empty")
        raised = False
    except ValueError as exc:
        raised = True
        assert str(exc) == "dataset detail response data is empty for dataset_id=dataset-empty"

    assert raised is True


def test_corpus_connector_proxy_requests(monkeypatch):
    seen = {}

    def fake_get(url, params, timeout):
        seen["method"] = "GET"
        seen["url"] = url
        seen["params"] = params
        return _FakeResponse({"code": 200, "message": "OK", "data": {"ok": True}})

    def fake_post(url, params, json, timeout):
        seen["method"] = "POST"
        seen["url"] = url
        seen["params"] = params
        seen["json"] = json
        return _FakeResponse({"code": 200, "message": "OK", "data": {"ok": True}})

    monkeypatch.setattr(
        "services.corpus_connector_service.get_settings",
        lambda: type("Settings", (), {"corpus_route": type("CorpusRoute", (), {"base_url": "http://10.0.82.213:7003"})()})(),
    )
    monkeypatch.setattr("services.corpus_connector_service.requests.get", fake_get)
    monkeypatch.setattr("services.corpus_connector_service.requests.post", fake_post)

    assert create_corpus_connector({"name": "demo"})["data"]["ok"] is True
    assert seen["method"] == "POST"
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.save"
    assert seen["json"] == {"name": "demo"}

    assert update_corpus_connector({"id": "c-1"})["data"]["ok"] is True
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.update"

    assert delete_corpus_connector("c-1")["data"]["ok"] is True
    assert seen["method"] == "GET"
    assert seen["params"] == {"id": "c-1"}
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.delete"

    assert disable_corpus_connector("c-1")["data"]["ok"] is True
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.disable"

    assert get_corpus_connector_detail("c-1")["data"]["ok"] is True
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.detail"

    assert enable_corpus_connector("c-1")["data"]["ok"] is True
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.enable"

    assert get_corpus_connector_tree()["data"]["ok"] is True
    assert seen["url"] == "http://10.0.82.213:7003/dataset.connector.tree"
