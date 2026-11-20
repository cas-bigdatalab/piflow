"""Real MCP and HTTP delivery with bounded, deterministic upstream streams."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from types import SimpleNamespace

from fastmcp import Client
import pytest
import requests

from mcp_servers.corpus_mcp import mcp
from services import bdbe_service as backend
from ..artifacts import Artifacts, ArtifactSpec, execution_metadata
from ..capabilities import inputs
from ..contracts import QAError, Server
from ..file_publication import publish_file
from ..mcp import MCPGateway
from ..persistence import Store
from ..responses import delivery_links
from .test_dataset_qa import engine
from .test_file_pipeline import files, SECRET
from .test_local_artifacts import download_client


GBFF = b'LOCUS       EXAMPLE       4 bp    DNA\nACCESSION   NC_000001\nORIGIN\n        1 acgt\n//\n'


@pytest.fixture
def upstream(monkeypatch):
    state = SimpleNamespace(calls=[], body=GBFF, media="application/octet-stream", error=None)
    @contextmanager
    def stream(**kw):
        state.calls.append(kw)
        def chunks():
            for offset in range(0, len(state.body), 7):
                yield state.body[offset:offset+7]
            if state.error:
                raise state.error
        response = SimpleNamespace(headers={"content-type": state.media,
            "content-disposition": "attachment; filename*=UTF-8''observations.gbff"})
        yield response, chunks()
    monkeypatch.setattr(backend, "stream_genbank", stream)
    return state


def args():
    return {"dataids": ["NC_000001"], "sessionid": None}


def download(*, user="alice", request="one"):
    return backend.download_genbank_file(**args(), execution=execution_metadata(
        user, request, args(), 120, secret=SECRET)["piflow_execution"])


def test_genbank_download_replay_range_and_links(files, upstream, download_client):
    first = download()
    assert first["resource"]["kind"] == "file"
    assert first["resource"]["record_count"] == 1
    assert first["resource"]["size_bytes"] == len(GBFF)
    assert "file_path" not in first
    response = download_client.get(first["downloadUrl"])
    assert response.status_code == 200 and response.content == GBFF
    assert "attachment" in response.headers["content-disposition"]
    assert response.headers["content-type"] == "application/octet-stream"
    assert hashlib.sha256(response.content).hexdigest() == first["resource"]["sha256"]
    assert download_client.get(first["downloadUrl"], headers={"Range": "bytes=0-9"}).content == GBFF[:10]
    second = download()
    assert second["resource"]["source_ref"] == first["resource"]["source_ref"] and len(upstream.calls) == 1
    assert delivery_links([{"result_id": "r", "view_type": "url", "data": first}])[0]["url"] == first["downloadUrl"]
    assert not list(files.root.rglob(".pending-*"))


def test_concurrent_same_operation_is_downloaded_once_and_users_are_isolated(files, upstream):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: download(), range(2)))
    assert len(upstream.calls) == 1
    assert results[0]["resource"]["source_ref"] == results[1]["resource"]["source_ref"]
    assert download(user="bob")["resource"]["source_ref"] != results[0]["resource"]["source_ref"]
    assert len(upstream.calls) == 2


@pytest.mark.parametrize("body,media", [(b"", "text/plain"), (b"<html>login</html>", "text/html"),
    (b'{"error":"not available"}', "application/json"), (GBFF[:-4], "text/plain"),
    (GBFF+b"LOCUS next", "application/octet-stream"),
    (b"invalid header\n"+GBFF, "application/octet-stream")])
def test_incomplete_or_non_file_results_are_not_published(files, upstream, body, media):
    upstream.body, upstream.media = body, media
    with pytest.raises(backend.BdbeUpstreamError):
        download()
    assert not list(files.root.glob("*/*/manifest.json"))
    assert not list(files.root.rglob(".pending-*"))


def test_record_count_is_measured_not_number_requested(files, upstream):
    upstream.body = GBFF+GBFF.replace(b"EXAMPLE", b"SECOND").replace(b"ORIGIN", b"            LOCUS in a description\nORIGIN")
    assert download()["resource"]["record_count"] == 2


def test_untrusted_execution_cannot_download_or_publish(files, upstream):
    meta = execution_metadata("alice", "one", args(), 120, secret=SECRET)["piflow_execution"]
    meta["user"] = "bob"
    with pytest.raises(ValueError):
        backend.download_genbank_file(**args(), execution=meta)
    assert upstream.calls == []


def test_worker_thread_keeps_event_loop_responsive(files, upstream, monkeypatch):
    import threading
    from mcp_servers import bdbe_mcp
    entered, release = threading.Event(), threading.Event()
    original = bdbe_mcp.download_genbank_file
    def delayed(*a, **kw):
        entered.set()
        assert release.wait(3)
        return original(*a, **kw)
    monkeypatch.setattr(bdbe_mcp, "download_genbank_file", delayed)
    async def run():
        async with Client(mcp) as client:
            task = asyncio.create_task(client.call_tool("download_bdbe_genbank", args(),
                meta=execution_metadata("alice", "threaded", args(), 120, secret=SECRET)))
            try:
                for _ in range(100):
                    if entered.is_set():
                        break
                    await asyncio.sleep(0.01)
                assert entered.is_set()
                assert len(await client.list_tools()) >= 11
            finally:
                release.set()
            result = await task
            assert result.data["resource"]["format"] == "gbff"
    asyncio.run(run())


def test_generic_file_without_record_count_is_registered_but_not_a_record_export_source(files, engine):
    def producer(path, checkpoint, limit):
        path.write_bytes(b"plain document")
        return {"name": "document.txt", "format": "txt"}
    meta = execution_metadata("alice", "doc", {}, 120, secret=SECRET)["piflow_execution"]
    value = publish_file(meta, {}, "document-source", producer)
    registry = Artifacts(Store(engine))
    resource = value["resource"]
    assert "record_count" not in resource
    aid = registry.register("alice", "s", {"result_id": "r", "data": value},
        SimpleNamespace(server="piflow-corpus", name="document"), ArtifactSpec(kind="file"))
    assert registry.get("alice", aid)["resource"] == resource
    assert registry.recent("alice")[0]["kind"] == "file"
    async def check():
        async with MCPGateway({"piflow-corpus": Server(mcp)}).session() as tools:
            await tools.load("piflow-corpus", query="export_dataset", group="artifact")
            # Group name is discovered from the real catalogue, not inferred from file extension.
            catalogue = await tools.tools("piflow-corpus")
            export = next(tool for tool in catalogue if tool.name == "export_dataset")
            with pytest.raises(QAError):
                inputs(export, {"format": "csv"}, resource)
    asyncio.run(check())


def test_transfer_interruption_cleans_temporary_file(files, upstream):
    upstream.error = requests.ConnectionError("disconnected")
    with pytest.raises(requests.ConnectionError):
        download()
    assert not list(files.root.glob("*/*/manifest.json"))
    assert not list(files.root.rglob(".pending-*"))
