"""Public download origins across direct, container and reverse-proxy deployments."""
import asyncio
import csv
import io
import json
import threading
from types import SimpleNamespace

from fastapi import FastAPI
import httpx
import pytest
from starlette.requests import Request

from infra.config_loader import get_settings
from mcp_servers import corpus_mcp
from .. import artifact_storage as storage
from ..contracts import Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from ...unified.adapters.dataset_qa import DatasetQAAdapter
from ...unified.api import Native, install_unified
from .test_dataset_qa import action, engine
from .test_decisions import BareDialogue, text
from .test_file_pipeline import files
from .test_local_artifacts import file_plan
from .test_planning import approve


@pytest.fixture(autouse=True)
def origin_settings(monkeypatch, tmp_path):
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_URL_MODE", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", raising=False)
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", "test-only-deployment-key")
    monkeypatch.setattr(get_settings().app, "port", 8090)


def request(headers=None, *, root_path=""):
    return Request({"type": "http", "scheme": "http", "path": root_path + "/",
        "root_path": root_path, "query_string": b"", "server": ("0.0.0.0", 8086),
        "client": ("203.0.113.5", 50123),
        "headers": [(key.lower().encode(), value.encode()) for key, value in {
            "Host": "container.internal:8086", **(headers or {})}.items()]})


@pytest.mark.parametrize("base", [
    "http://public.example:18086/api/piflow/v1/mcp",
    "https://public.example:9443/gateway/tools",
    "http://[2001:db8::1]:18086/api/piflow/v1/mcp",
])
def test_explicit_external_ports_survive_internal_listen_port_changes(base, monkeypatch):
    assert storage.request_download_base(base, request=request()) == base
    monkeypatch.setattr(get_settings().app, "port", 7081)
    assert storage.request_download_base(base, request=request()) == base


@pytest.mark.parametrize("base", ["http://public.example/mcp", "https://public.example/mcp",
    "https://public.example:443/mcp", "http://public.example:80/mcp", "https://[2001:db8::1]/mcp"])
def test_request_mode_keeps_standard_public_ports(base, monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_URL_MODE", "request")
    assert storage.request_download_base(base, request=request()) == base


def test_default_mode_preserves_legacy_fallback_without_changing_explicit_ports(monkeypatch):
    assert storage.request_download_base("http://public.example/mcp") == "http://public.example:8090/mcp"
    monkeypatch.setattr(get_settings().app, "port", 8086)
    assert storage.request_download_base("http://public.example/mcp", request=request()) == "http://public.example:8086/mcp"
    assert storage.request_download_base("http://public.example:80/mcp") == "http://public.example:80/mcp"


@pytest.mark.parametrize("headers,expected", [
    ({"X-Forwarded-Host": "api.public.example", "X-Forwarded-Proto": "https"},
        "https://api.public.example/api/mcp"),
    ({"X-Forwarded-Host": "api.public.example", "X-Forwarded-Proto": "http", "X-Forwarded-Port": "18086"},
        "http://api.public.example:18086/api/mcp"),
    ({"X-Forwarded-Host": "api.public.example:9443", "X-Forwarded-Proto": "https", "X-Forwarded-Port": "443"},
        "https://api.public.example:443/api/mcp"),
    ({"X-Forwarded-Host": "[2001:db8::2]", "X-Forwarded-Proto": "https", "X-Forwarded-Port": "9443"},
        "https://[2001:db8::2]:9443/api/mcp"),
    ({"X-Forwarded-Host": "earlier.invalid, public.example:9443", "X-Forwarded-Proto": "http, https",
        "X-Forwarded-Port": "8086, 9443"}, "https://public.example:9443/api/mcp"),
    ({"Forwarded": 'for=198.51.100.1;host="public.example:443";proto=https'},
        "https://public.example:443/api/mcp"),
    ({"Forwarded": 'for=198.51.100.1;host="[2001:db8::3]:9443";proto=https'},
        "https://[2001:db8::3]:9443/api/mcp"),
    ({"Forwarded": 'host=earlier.invalid;proto=http, host=public.example;proto=https',
        "X-Forwarded-Host": "other.invalid", "X-Forwarded-Proto": "http", "X-Forwarded-Port": "1234"},
        "https://public.example/api/mcp"),
    ({"X-Forwarded-Proto": "https"}, "https://public.example/api/mcp"),
    ({"X-Forwarded-Prefix": "/research"}, "http://public.example/research/api/mcp"),
])
def test_trusted_proxy_origins_are_independent_of_internal_ports(headers, expected, monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")
    actual = storage.request_download_base("http://public.example/api/mcp", request=request(headers))
    assert actual == expected


@pytest.mark.parametrize("path,prefix,expected", [
    ("/api/mcp", "/gateway", "/gateway/api/mcp"),
    ("/gateway/api/mcp", "/gateway", "/gateway/api/mcp"),
    ("/gateway/api/mcp", "/gateway/", "/gateway/api/mcp"),
    ("/gateway-other/api/mcp", "/gateway", "/gateway/gateway-other/api/mcp"),
    ("/api/mcp", "/", "/api/mcp"),
])
def test_proxy_prefix_merging_respects_path_boundaries(path, prefix, expected, monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")
    value = storage.request_download_base("https://public.example" + path,
        request=request({"X-Forwarded-Prefix": prefix}))
    assert value == "https://public.example" + expected


@pytest.mark.parametrize("headers", [
    {"X-Forwarded-Host": "attacker.invalid", "X-Forwarded-Proto": "https", "X-Forwarded-Prefix": "/wrong"},
    {"Forwarded": "host=attacker.invalid;proto=https"},
    {"Origin": "https://frontend.example:3000", "Referer": "https://frontend.example/page"},
])
def test_untrusted_headers_and_frontend_origin_do_not_change_download_authority(headers):
    assert storage.request_download_base("http://public.example/api/mcp", request=request(headers)) == (
        "http://public.example:8090/api/mcp")


@pytest.mark.parametrize("headers", [
    {"X-Forwarded-Host": "user:pass@evil.example", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "https://evil.example", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public.example:", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public%2f.example", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Port": "0", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Port": "65536", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Port": "bad", "X-Forwarded-Proto": "https"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Proto": "javascript"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Prefix": "//evil.example"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Prefix": "/prefix?token=bad"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Prefix": "/prefix#bad"},
    {"X-Forwarded-Host": "public.example", "X-Forwarded-Prefix": "/prefix/%2e%2e/other"},
    {"Forwarded": 'host="public.example;proto=https', "X-Forwarded-Host": "other.example"},
    {"Forwarded": "host=first.example;host=second.example;proto=https"},
])
def test_malformed_trusted_bundle_does_not_partially_override_origin(headers, monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")
    assert storage.request_download_base("http://public.example/api/mcp", request=request(headers)) == (
        "http://public.example:8090/api/mcp")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_URL_MODE", "request")
    assert storage.request_download_base("http://public.example/api/mcp", request=request(headers)) == (
        "http://public.example/api/mcp")


def test_explicit_public_base_wins_over_container_origin_and_forwarding(monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "https://downloads.public.example/replaced/path")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_URL_MODE", "unused-when-base-is-explicit")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")
    supplied = storage.request_download_base("http://mcp:8086/internal/tools", request=request({
        "Forwarded": "host=proxy.example;proto=https", "X-Forwarded-Prefix": "/gateway"}))
    with storage.download_base_context(supplied):
        assert storage.StorageConfig.load().download_base() == "https://downloads.public.example/replaced/path"


def test_invalid_mode_is_checked_only_when_artifacts_are_used(monkeypatch):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_URL_MODE", "typo")
    base = storage.request_download_base("http://public.example/mcp", request=request())
    with storage.download_base_context(base):
        with pytest.raises(storage.ArtifactStorageError) as error:
            storage.StorageConfig.load()
    assert error.value.phase == "configuration"


@pytest.mark.parametrize("prefix", ["", "/gateway"])
def test_qa_adapter_uses_trusted_public_origin_and_preserves_mount(engine, files, monkeypatch, prefix):
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")

    async def run():
        service = DatasetQA(engine, BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
            action("remember", plan=file_plan()), approve, text()),
            MCPGateway({"piflow-corpus": Server(corpus_mcp.mcp)}))
        mcp_app = corpus_mcp.create_mcp_app()
        app = FastAPI(lifespan=mcp_app.lifespan)
        app.mount("/api/piflow/v1/mcp", mcp_app)
        bindings = {}
        def binding(user, sid, agent=None):
            if agent:
                bindings[user, sid] = agent
            return bindings.get((user, sid))
        def identity(native, incoming):
            native.request, native.user = incoming, "alice"
        monkeypatch.setattr(Native, "__init__", identity)
        app.state.scientific_agents = SimpleNamespace(session_services={"dataset_qa": service},
            store=SimpleNamespace(_lock=threading.RLock(), binding=binding))
        install_unified(app, adapters={"dataset_qa": DatasetQAAdapter})
        api = "/api/piflow/v1/agents"
        headers = {"X-Forwarded-Host": "api.public.example", "X-Forwarded-Proto": "https",
            "Origin": "https://frontend.example:3000"}
        if prefix:
            headers["X-Forwarded-Prefix"] = prefix
        try:
            async with mcp_app.lifespan(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, root_path=prefix),
                        base_url="http://container.internal:8086", headers=headers) as client:
                    response = await client.post(api + "/sessions", json={"agent_id": "dataset_qa", "request_id": "create"})
                    sid = response.json()["result"]["session_id"]
                    response = await client.post(api + f"/sessions/{sid}/tasks/plan/pre-bind/stream",
                        json={"user_request": "按给定条件检索并保存 CSV", "request_id": "query-export"})
                    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
                    assert events[-1]["type"] == "done" and events[-1]["status"] == "COMPLETED"
                    handle = next(row["handle"] for row in service.artifacts.recent("alice") if row["format"] == "csv")
                    resource = service.artifacts.get("alice", handle)["resource"]
                    assert resource["downloadUrl"].startswith("https://api.public.example" + prefix + "/api/piflow/v1/mcp/artifacts/")
                    downloaded = await client.get(resource["downloadUrl"])
                    assert downloaded.status_code == 200
                    assert [row["CID"] for row in csv.DictReader(io.StringIO(downloaded.text))] == ["1", "2"]
        finally:
            await service.close()
    asyncio.run(run())
