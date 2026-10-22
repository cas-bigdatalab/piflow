"""One frontend list path, with unchanged MCP evidence and saved-result pointers."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from langchain_core.messages import ToolMessage
import pytest

from .assertions import assert_completed
from ..service import DatasetQA
from ..contracts import Server
from ..mcp import MCPGateway
from .test_dataset_qa import Backend, Dialogue, collect, engine, load, remote, result_cards, session
from ...unified.adapters.dataset_qa import DatasetQAAdapter


@pytest.mark.parametrize("server,operation,arguments,payload,expected", [
    ("data", "search", {}, {"items": [{"cstr": "a"}], "pagination": {"total": 7}}, [{"cstr": "a"}]),
    ("data", "search", {}, {"items": [], "pagination": {"total": 0}}, []),
    ("data", "inspect", {"reference": "a"}, {"cstr": "a", "title": "Dataset"}, [{"cstr": "a", "title": "Dataset"}]),
    ("data", "preview", {"reference": "a"}, {"code": 200, "data": {"imageUrl": "https://example.invalid/a.png"}},
        [{"code": 200, "data": {"imageUrl": "https://example.invalid/a.png"}}]),
    ("data", "sample", {"reference": "a", "count": 1}, {"code": 200, "data": [{"row": 1}]},
        [{"code": 200, "data": [{"row": 1}]}]),
    ("data", "sample", {"reference": "a", "count": 1}, [{"row": 1}], [{"row": 1}]),
    ("compute", "multiply", {"x": 0, "y": 2}, 0, [0]),
])
def test_sse_history_results_and_replay_share_one_list_path(engine, server, operation, arguments, payload, expected):
    async def run():
        backend = Backend()
        original = backend.client

        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            execute = client.call_tool

            async def call(*args, **kwargs):
                await execute(*args, **kwargs)
                return SimpleNamespace(structured_content=deepcopy(payload), is_error=False)
            client.call_tool = call
            return client

        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = Dialogue(load(server), remote(operation, **arguments))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        values = await collect(service, sid)
        card, = result_cards(values)
        tid = values[-1]["task_id"]
        assert_completed(service, None, values[-1])
        assert card["data"]["items"]==expected
        assert set(card)=={"result_id", "view_type", "title", "data"} and card["view_type"]=="tool_result"
        if operation=="search":
            assert card["data"]["pagination"]==payload["pagination"]

        saved, = service.store.results("alice", sid, tid)
        assert saved["data"]==payload
        evidence = next(json.loads(m.content) for m in dialogue.inputs[2][0]
            if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content))
        assert evidence["data"]==payload

        adapter = DatasetQAAdapter(SimpleNamespace(user="alice",
            extension=SimpleNamespace(session_services={"dataset_qa": service})))
        assert (await adapter.get_results(sid, tid))["items"]==[card]
        history = await service.get_session("alice", sid)
        assert [i["payload"] for i in history["items"] if i["item_type"]=="RESULT_CARD"]==[card]
        assert await collect(service, sid)==values and len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_media_only_result_has_empty_items_and_preserves_resource(engine):
    async def run():
        backend = Backend()
        original = backend.client
        url = "https://example.invalid/preview.png?signature=complete"

        def factory(*args, **kwargs):
            client = original(*args, **kwargs)

            async def call(*args, **kwargs):
                return SimpleNamespace(structured_content=None, is_error=False, content=[
                    {"type": "resource_link", "uri": url, "mimeType": "image/png"}])
            client.call_tool = call
            return client

        gateway = backend.gateway()
        gateway.client_factory = factory
        service = DatasetQA(engine, Dialogue(load(), remote("preview", reference="a")), gateway)
        values = await collect(service, session(service))
        card, = result_cards(values)
        assert_completed(service, None, values[-1])
        assert card["data"]=={"items": []}
        assert card["content"][0]["url"]==url and card["content"][0]["type"]=="image"
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("operation,helper,arguments,payload,view,title", [
    ("search_corpus_datasets", "list_dataset_details", {"query": "science"},
        {"items": [{"cstr": "a"}], "pagination": {"total": 7}}, "detail", "数据集检索"),
    ("get_corpus_dataset_detail", "get_dataset_detail_by_cstr", {"cstr": "a"},
        {"cstr": "a", "title": "Dataset"}, "data", "数据集详情"),
    ("get_corpus_dataset_directory", "get_dataset_directory", {"cstr": "a", "file_id": "folder-1"},
        {"code": 200, "data": [{"fileId": "file-1", "fileName": "observations.csv", "isFile": True}]},
        "directory", "查看数据内容"),
    ("sample_corpus_dataset", "get_dataset_sampler", {"cstr": "a", "size": 5},
        {"code": 200, "data": {"url": "https://example.invalid/sample.json", "size": 5}}, "url", "数据集随机采样"),
])
def test_real_mcp_view_type_survives_sse_history_results_and_replay(engine, monkeypatch, operation, helper,
        arguments, payload, view, title):
    from mcp_servers import corpus_mcp

    calls = []

    def upstream(*args, **kwargs):
        calls.append((args, kwargs))
        return deepcopy(payload)

    monkeypatch.setattr(corpus_mcp, "get_dataset_detail_by_cstr", lambda cstr: {"source": "corpus"})
    monkeypatch.setattr(corpus_mcp, helper, upstream)

    async def run():
        dialogue = Dialogue(load("corpus"), remote(operation, **arguments))
        service = DatasetQA(engine, dialogue, MCPGateway({"corpus": Server(corpus_mcp.mcp)}))
        sid = session(service)
        values = await collect(service, sid)
        card, = result_cards(values)
        tid = values[-1]["task_id"]
        assert_completed(service, None, values[-1])
        assert card=={"result_id": tid+":0", "view_type": view, "title": "corpus · "+title,
            "data": payload if "items" in payload else {"items": [payload]}}
        saved, = service.store.results("alice", sid, tid)
        assert saved=={"result_id": card["result_id"], "view_type": view, "title": card["title"], "data": payload}
        evidence = next(json.loads(m.content) for m in dialogue.inputs[2][0]
            if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content))
        assert evidence["view_type"]==view and evidence["data"]==payload
        adapter = DatasetQAAdapter(SimpleNamespace(user="alice",
            extension=SimpleNamespace(session_services={"dataset_qa": service})))
        assert (await adapter.get_results(sid, tid))["items"]==[card]
        history = await service.get_session("alice", sid)
        assert [i["payload"] for i in history["items"] if i["item_type"]=="RESULT_CARD"]==[card]
        assert await collect(service, sid)==values and len(calls)==1
        await service.close()
    asyncio.run(run())
