"""Actual HTTP ingress, MCP and file downloads with separate internal addresses."""
import asyncio
from contextlib import asynccontextmanager
import csv
import hashlib
import io
import socket
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import httpx
from starlette.responses import StreamingResponse
import uvicorn

from ..artifact_storage import download_base_context
from ..artifacts import execution_metadata
from .test_artifact_download_origin import http_mcp
from .test_file_pipeline import files, query_args


@asynccontextmanager
async def ingress(backend, prefix="/edge"):
    """Model a sanitizing ingress that strips a prefix and rewrites Host.

    Both endpoints use real sockets. Only upstream scientific data is stubbed;
    MCP streaming, signing, persistence and downloaded bytes are real.
    """
    origin = urlsplit(backend)._replace(path="", query="", fragment="").geturl()
    app = FastAPI()
    seen = []
    async with httpx.AsyncClient(timeout=None, trust_env=False) as upstream:
        @app.api_route(prefix+"/{path:path}", methods=["GET", "POST", "DELETE"])
        async def forward(request: Request, path: str):
            headers = {key: value for key, value in request.headers.items()
                if key.lower() not in {"host", "content-length", "connection", "forwarded"}
                and not key.lower().startswith("x-forwarded-")}
            headers.update({"host": "mcp.internal:8086",
                "forwarded": f'host="{request.url.netloc}";proto={request.url.scheme}',
                "x-forwarded-prefix": prefix})
            target = origin+"/"+path
            if request.url.query:
                target += "?"+request.url.query
            seen.append((request.method, path))
            outgoing = upstream.build_request(request.method, target,
                headers=headers, content=await request.body())
            response = await upstream.send(outgoing, stream=True)

            async def content():
                try:
                    async for chunk in response.aiter_raw():
                        yield chunk
                finally:
                    await response.aclose()

            return StreamingResponse(content(), status_code=response.status_code,
                headers={key: value for key, value in response.headers.items()
                    if key.lower() not in {"connection", "transfer-encoding"}})

        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        address = f"http://127.0.0.1:{sock.getsockname()[1]}{prefix}"
        server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False,
            proxy_headers=False, timeout_graceful_shutdown=2))
        task = asyncio.create_task(server.serve(sockets=[sock]))
        try:
            async with asyncio.timeout(10):
                while not server.started:
                    if task.done():
                        await task
                    await asyncio.sleep(0.01)
            yield address, seen
        finally:
            server.should_exit = True
            await asyncio.wait_for(task, 10)
            sock.close()


def test_remote_mcp_and_download_use_ingress_not_container_or_qa_origin(files, monkeypatch):
    from infra.config_loader import get_settings

    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.setenv("DATASET_QA_ARTIFACT_URL_MODE", "legacy")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_TRUST_PROXY_HEADERS", "true")
    monkeypatch.setattr(get_settings().app, "port", 8086)

    async def run():
        mount = "/api/piflow/v1/mcp"
        async with asyncio.timeout(30), http_mcp(mount) as backend:
            async with ingress(backend) as (external, seen):
                public = external+mount
                assert urlsplit(public).port != urlsplit(backend).port
                transport = StreamableHttpTransport(public+"/", headers={
                    "Forwarded": "host=untrusted.invalid;proto=https",
                    "X-Forwarded-Prefix": "/untrusted"},
                    httpx_client_factory=lambda **kwargs: httpx.AsyncClient(**kwargs, trust_env=False))
                # A separate QA service's local context must never replace the
                # remote MCP service's publicly reachable download endpoint.
                with download_base_context("https://qa-only.invalid/unrelated/mcp"):
                    async with Client(transport) as client:
                        args = query_args()
                        query = await client.call_tool("query_pubchem_compounds", args,
                            meta=execution_metadata("owner", "proxy-query", args, 60))
                        original = query.structured_content
                        args = {"source_ref": original["resource"]["source_ref"], "format": "csv"}
                        result = await client.call_tool("export_dataset", args,
                            meta=execution_metadata("owner", "proxy-export", args, 60))
                        exported = result.structured_content

                assert original["downloadUrl"].startswith(public+"/artifacts/")
                assert exported["downloadUrl"].startswith(public+"/artifacts/")
                assert exported["record_count"] == original["record_count"] == 2
                async with httpx.AsyncClient(trust_env=False) as client:
                    response = await client.get(exported["downloadUrl"])
                    partial = await client.get(exported["downloadUrl"], headers={"Range": "bytes=0-15"})
                assert response.status_code == 200 and partial.status_code == 206
                assert "attachment" in response.headers["content-disposition"]
                assert partial.content == response.content[:16]
                assert [row["CID"] for row in csv.DictReader(io.StringIO(response.text))] == ["1", "2"]
                assert hashlib.sha256(response.content).hexdigest() == exported["resource"]["sha256"]
                assert len(files.requests) == 2
                assert any(method == "POST" and path == mount.lstrip("/")+"/" for method, path in seen)
                assert sum(method == "GET" and "/artifacts/" in path for method, path in seen) == 2
    asyncio.run(run())
