"""Download delivery uses the actual HTTP mount without extra deployment settings."""
import asyncio
from contextlib import asynccontextmanager
import csv
import hashlib
import io
import json
import socket
import threading
from types import SimpleNamespace

import anyio
from fastapi import FastAPI
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import httpx
import pytest
import uvicorn
from starlette.requests import Request

from mcp_servers import corpus_mcp
from mcp_servers.corpus_mcp import create_mcp_app
from .. import artifact_storage as storage
from ..artifacts import execution_metadata
from ..contracts import Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from ...unified.adapters.dataset_qa import DatasetQAAdapter
from ...unified.api import Native, install_unified
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import files, query_args
from .test_local_artifacts import file_plan
from .test_planning import approve


@asynccontextmanager
async def http_mcp(mount):
    mcp_app = create_mcp_app()
    app = FastAPI(lifespan=mcp_app.lifespan)
    app.mount(mount, mcp_app)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    base = f"http://127.0.0.1:{sock.getsockname()[1]}{mount}"
    server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    await task
                await asyncio.sleep(0.01)
        yield base
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, 10)
        sock.close()


@pytest.mark.parametrize("mount", ["/api/piflow/v1/mcp", "/gateway/research/tools"])
def test_http_query_export_download_without_base_or_secret(files, monkeypatch, mount):
    if mount == "/api/piflow/v1/mcp":
        monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "  ")
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)

    async def run():
        async with http_mcp(mount) as base:
            async with Client(base+"/") as client:
                args = query_args()
                query = await client.call_tool("query_pubchem_compounds", args,
                    meta=execution_metadata("owner", "query", args, 60), raise_on_error=False)
                assert not query.is_error
                original = query.structured_content
                args = {"source_ref": original["resource"]["source_ref"], "format": "csv"}
                result = await client.call_tool("export_dataset", args,
                    meta=execution_metadata("owner", "export", args, 60))
                exported = result.structured_content
                assert exported["downloadUrl"].startswith(base+"/artifacts/")
                assert exported["record_count"] == original["record_count"] == 2
            async with Client(base+"/") as client:
                repeated = await client.call_tool("export_dataset", args,
                    meta=execution_metadata("owner", "new-session", args, 60))
                assert repeated.structured_content["resource"]["source_ref"] == exported["resource"]["source_ref"]
            async with httpx.AsyncClient() as client:
                response = await client.get(exported["downloadUrl"])
                partial = await client.get(exported["downloadUrl"], headers={"Range": "bytes=0-15"})
            assert response.status_code == 200 and partial.status_code == 206
            rows = list(csv.DictReader(io.StringIO(response.text)))
            assert [row["CID"] for row in rows] == ["1", "2"]
            assert hashlib.sha256(response.content).hexdigest() == exported["resource"]["sha256"]
            assert len(files.requests) == 2
    asyncio.run(run())


def test_qa_plan_uses_http_defaults_through_to_download(engine, files, monkeypatch):
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)

    async def run():
        async with http_mcp("/api/piflow/v1/mcp") as base:
            dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
                action("remember", plan=file_plan()), approve, text())
            service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(base+"/")}))
            try:
                sid = session(service)
                events = await collect(service, sid, "按给定条件检索并导出 CSV")
                assert payload(service, sid, events).get("error") is None
                assert len(dialogue.inputs) == 4 and len(files.requests) == 2
                items = service.artifacts.recent("alice")
                assert {item["format"] for item in items} == {"jsonl", "csv"}
                item = next(item for item in items if item["format"] == "csv")
                resource = service.artifacts.get("alice", item["handle"])["resource"]
                assert resource["downloadUrl"].startswith(base+"/artifacts/")
                async with httpx.AsyncClient() as client:
                    response = await client.get(resource["downloadUrl"])
                assert response.status_code == 200
                assert len(list(csv.DictReader(io.StringIO(response.text)))) == 2
            finally:
                await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("prefix,mount", [("", "/api/piflow/v1/mcp"), ("/gateway", "/research/downloads")])
@pytest.mark.parametrize("authority,port,expected", [
    ("api.example:8443", 8086, "api.example:8443"),
    ("api.example", 8086, "api.example:8086"),
    ("api.example", 8090, "api.example:8090"),
])
def test_split_frontend_uses_api_origin_with_default_in_process_mcp(engine, files, monkeypatch, prefix, mount, authority, port, expected):
    from infra.config_loader import get_settings
    monkeypatch.setattr(get_settings().app, "port", port)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)

    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
            action("remember", plan=file_plan()), approve, text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(corpus_mcp.mcp)}))
        mcp_app = create_mcp_app()
        app = FastAPI(lifespan=mcp_app.lifespan)
        app.mount(mount, mcp_app)
        bindings = {}
        def binding(user, sid, agent=None):
            if agent:
                bindings[user, sid] = agent
            return bindings.get((user, sid))
        def identity(native, request):
            native.request, native.user = request, "alice"
        monkeypatch.setattr(Native, "__init__", identity)
        app.state.scientific_agents = SimpleNamespace(session_services={"dataset_qa": service},
            store=SimpleNamespace(_lock=threading.RLock(), binding=binding))
        install_unified(app, adapters={"dataset_qa": DatasetQAAdapter})
        api = "/api/piflow/v1/agents"
        try:
            async with mcp_app.lifespan(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, root_path=prefix),
                        base_url="https://"+authority, headers={"Origin": "https://frontend.example:3000"}) as client:
                    response = await client.post(api+"/sessions", json={"agent_id": "dataset_qa", "request_id": "create"})
                    assert response.status_code == 200
                    sid = response.json()["result"]["session_id"]
                    response = await client.post(api+f"/sessions/{sid}/tasks/plan/pre-bind/stream",
                        json={"user_request": "按给定条件检索并生成 CSV", "request_id": "query-export"})
                    assert response.status_code == 200
                    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
                    assert events and events[-1]["type"] == "done" and events[-1]["status"] == "COMPLETED", events[-1:]
                    assert len(dialogue.inputs) == 4 and len(files.requests) == 2
                    item = next(item for item in service.artifacts.recent("alice") if item["format"] == "csv")
                    resource = service.artifacts.get("alice", item["handle"])["resource"]
                    assert resource["downloadUrl"].startswith("https://"+expected+prefix+mount+"/artifacts/")
                    response = await client.get(resource["downloadUrl"])
                    assert response.status_code == 200
                    assert len(list(csv.DictReader(io.StringIO(response.text)))) == 2
        finally:
            await service.close()
        # A finished API task must not turn a later background job's origin into
        # this user's request host. The explicit override remains available there.
        with pytest.raises(storage.ArtifactStorageError):
            storage.StorageConfig.load().download_base()
    asyncio.run(run())


def test_explicit_public_address_wins_and_replay_refreshes_origin(files, monkeypatch):
    async def run():
        async with http_mcp("/tools") as base:
            async with Client(base+"/") as client:
                args = query_args()
                meta = execution_metadata("owner", "same-query", args, 60)
                original = (await client.call_tool("query_pubchem_compounds", args, meta=meta)).structured_content
                assert original["downloadUrl"].startswith("https://testserver/api/piflow/v1/mcp/artifacts/")
                monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL")
                refreshed = (await client.call_tool("query_pubchem_compounds", args, meta=meta)).structured_content
                assert refreshed["downloadUrl"].startswith(base+"/artifacts/")
                assert refreshed["resource"]["source_ref"] == original["resource"]["source_ref"]
                assert len(files.requests) == 2
                monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "https://secret:password@host/mcp")
                rejected = await client.call_tool("query_pubchem_compounds", args, meta=meta, raise_on_error=False)
                assert rejected.is_error and rejected.meta["piflow"]["phase"] == "configuration"
                assert "password" not in str(rejected.content) and len(files.requests) == 2
    asyncio.run(run())


@pytest.mark.parametrize("host,prefix", [("download.example", "/proxy/research/mcp"), ("[::1]:8123", "")])
def test_origin_preserves_asgi_mount_and_ignores_untrusted_forwarding(files, monkeypatch, host, prefix):
    from infra.config_loader import get_settings
    monkeypatch.setattr(get_settings().app, "port", 8090)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    request = Request({"type": "http", "scheme": "https", "path": prefix+"/", "root_path": prefix,
        "query_string": b"access_token=private", "headers": [(b"host", host.encode()),
            (b"x-forwarded-host", b"attacker.invalid"), (b"x-forwarded-prefix", b"/wrong"),
            (b"x-forwarded-proto", b"http")]})
    monkeypatch.setattr(corpus_mcp, "get_http_request", lambda: request)
    with corpus_mcp._artifact_download_context():
        assert storage.StorageConfig.load().download_base() == "https://"+(host if ":" in host else host+":8090")+prefix
    with pytest.raises(storage.ArtifactStorageError):
        storage.StorageConfig.load().download_base()


def test_origins_are_task_local_in_workers_and_reset_after_error(files, monkeypatch):
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)

    async def run():
        entered = 0
        gate = asyncio.Event()
        async def one(index):
            nonlocal entered
            base = f"https://worker-{index}.example/mcp"
            try:
                with storage.download_base_context(base):
                    entered += 1
                    if entered == 8:
                        gate.set()
                    await asyncio.wait_for(gate.wait(), 2)
                    assert await anyio.to_thread.run_sync(lambda: storage.StorageConfig.load().download_base()) == base
                    raise RuntimeError("end of request")
            except RuntimeError:
                pass
            with pytest.raises(storage.ArtifactStorageError):
                storage.StorageConfig.load().download_base()
        await asyncio.gather(*(one(i) for i in range(8)))
    asyncio.run(run())


def test_download_over_tcp_when_proxy_host_loses_port(files, monkeypatch):
    from infra.config_loader import get_settings
    from urllib.parse import urlsplit
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)

    async def run():
        async with http_mcp("/api/piflow/v1/mcp") as base:
            monkeypatch.setattr(get_settings().app, "port", urlsplit(base).port)
            transport = StreamableHttpTransport(base+"/", headers={"Host": "127.0.0.1"},
                httpx_client_factory=lambda **kwargs: httpx.AsyncClient(**kwargs, trust_env=False))
            async with Client(transport) as client:
                args = query_args()
                result = await client.call_tool("query_pubchem_compounds", args,
                    meta=execution_metadata("owner", "query", args, 60))
                args = {"source_ref": result.structured_content["resource"]["source_ref"], "format": "csv"}
                result = await client.call_tool("export_dataset", args,
                    meta=execution_metadata("owner", "export", args, 60))
                output = result.structured_content
            assert output["downloadUrl"].startswith(base+"/artifacts/")
            async with httpx.AsyncClient() as client:
                response = await client.get(output["downloadUrl"])
            assert response.status_code == 200
            assert "attachment;" in response.headers["content-disposition"]
            assert len(list(csv.DictReader(io.StringIO(response.text)))) == 2
    asyncio.run(run())


@pytest.mark.parametrize("base,expected", [
    ("http://api.example/mcp", "http://api.example:8090/mcp"),
    ("http://api.example:80/mcp", "http://api.example:80/mcp"),
    ("https://api.example:443/mcp", "https://api.example:443/mcp"),
    ("http://[::1]/gateway/mcp", "http://[::1]:8090/gateway/mcp"),
])
def test_port_fallback_keeps_explicit_ports_and_public_override(files, monkeypatch, base, expected):
    from infra.config_loader import get_settings
    monkeypatch.setattr(get_settings().app, "port", 8090)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    assert storage.request_download_base(base) == expected
    monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "https://public.example/downloads")
    with storage.download_base_context(storage.request_download_base(base)):
        assert storage.StorageConfig.load().download_base() == "https://public.example/downloads"
