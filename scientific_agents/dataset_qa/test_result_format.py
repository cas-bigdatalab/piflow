"""One frontend list path, with unchanged MCP evidence and saved-result pointers."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from langchain_core.messages import ToolMessage
import pytest

from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, collect, engine, load, remote, result_cards, session
from ..unified.adapters.dataset_qa import DatasetQAAdapter


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
        assert values[-1]["status"]=="COMPLETED"
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
        assert values[-1]["status"]=="COMPLETED" and card["data"]=={"items": []}
        assert card["content"][0]["url"]==url and card["content"][0]["type"]=="image"
        await service.close()
    asyncio.run(run())
