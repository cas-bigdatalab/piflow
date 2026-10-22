"""Goal-backed aggregation, bounded evidence and delivery recovery."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
import pytest

from .assertions import assert_completed, assert_handled
from ..context import encode
from ..contracts import Limits, QAError, Server
from ..dialogue import Dialogue
from ..mcp import MCPGateway
from ..operations import Operation, Operations
from ..references import at_path
from ..results import collection_paths, evidence_group
from ..service import DatasetQA
from .test_dataset_qa import Backend, action, collect, definition, engine, load, remote, result_cards, session
from .test_operations import batch, goal, saved
from .test_runtime import RawDialogue


def source():
    backend = Backend()
    backend.catalog["data"] = [definition("lookup_records", {"query": {"type": "string"}},
        annotations={"readOnlyHint": True, "idempotentHint": True})]
    rows = {
        "first": [{"id": "a", "title": "Alpha"}, {"id": "b", "title": "Beta"}],
        "second": [{"id": "b", "title": "Beta"}, {"id": "c", "title": "Gamma"}],
    }
    connect = backend.client

    def client(*args, **kwargs):
        connection = connect(*args, **kwargs)
        call = connection.call_tool

        async def execute(name, arguments, **options):
            await call(name, arguments, **options)
            return SimpleNamespace(is_error=False, structured_content={
                "items": deepcopy(rows.get(arguments.get("query"), [])), "pagination": {"total": 100}})
        connection.call_tool = execute
        return connection

    gateway = backend.gateway()
    gateway.client_factory = client
    return backend, gateway


@pytest.mark.parametrize("separate_goals", [False, True])
@pytest.mark.parametrize("selection", ["explicit", "default", "no_call"])
def test_multiple_retrievals_deliver_one_source_backed_list_without_merge_parameters(engine, separate_goals, selection):
    async def run():
        backend, gateway = source()
        goals = [goal("find"), *([goal("related")] if separate_goals else [])]
        second = "related" if separate_goals else "find"

        def finish(messages, definitions):
            pool = json.loads(messages[1].content)["evidence"]
            assert pool["total"]==2 and len(encode(pool))<=gateway.limits.result_chars
            assert [item["operations"] for item in pool["items"]]==[["find"], [second]]
            if selection=="no_call":
                return AIMessageChunk(content="Internal draft")
            return action("deliver_results", **({"result_ids": [item["result_id"] for item in pool["items"]]}
                if selection=="explicit" else {}))

        dialogue = RawDialogue(load(), batch(["find"], remote("lookup_records", query="first"), operations=goals),
            batch([second], remote("lookup_records", query="second")), finish, AIMessageChunk(content="Verified candidates."))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid, "Find usable resources")
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==2
            assert len(dialogue.inputs)==5  # No classifier, per-result summary or extra selection request.
            final = json.loads(dialogue.inputs[-1][0][-1].content)
            assert len(final["answer_evidence"])==2 and len(encode(final))<=gateway.limits.result_chars
            assert [item["operations"] for item in final["answer_evidence"]]==[["find"], [second]]
            card, = result_cards(events)
            assert set(card)=={"result_id", "view_type", "title", "data"}
            assert card["data"]=={"items": [{"id": "a", "title": "Alpha"},
                {"id": "b", "title": "Beta"}, {"id": "c", "title": "Gamma"}]}
            assert "pagination" not in card["data"]
            payload = saved(service, sid, events[-1]["task_id"])
            assert len(payload["delivery_sources"])==2
            assert len(service.store.results("alice", sid))==3
            refs = json.loads(service.store.session("alice", sid)["context"])["references"]
            assert refs["candidates"]["result_id"]==card["result_id"]
            raw = service.store.results("alice", sid, result_id=card["result_id"])[0]
            assert at_path(raw["data"], refs["candidates"]["path"])[1]["id"]=="b"
            assert await collect(service, sid, "Find usable resources")==events and len(backend.calls)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_delivery_parameter_exhaustion_recovers_without_repeating_execution(engine):
    async def run():
        backend, gateway = source()
        dialogue = RawDialogue(load(), batch(["find"], remote("lookup_records", query="first"), operations=[goal("find")]),
            batch(["find"], remote("lookup_records", query="second")),
            *[action("deliver_results", result_ids="invalid") for _ in range(3)], AIMessageChunk(content="Saved results."))
        service = DatasetQA(engine, dialogue, gateway)
        try:
            events = await collect(service, session(service))
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==2
            assert len(result_cards(events))==1
            assert "操作尚未完成" not in "".join(event.get("text", "") for event in events)
        finally:
            await service.close()
    asyncio.run(run())


def test_real_mcp_collection_results_are_combined_without_an_extra_model_round(engine):
    from fastmcp import FastMCP

    async def run():
        mcp, calls = FastMCP("collection-test"), []

        @mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
        async def lookup_records(query: str) -> dict:
            calls.append(query)
            return {"items": [{"id": query, "title": "Object "+query}]}

        dialogue = RawDialogue(load("records"),
            batch(["find"], remote("lookup_records", query="a"), operations=[goal("find")]),
            batch(["find"], remote("lookup_records", query="b")), action("deliver_results"), AIMessageChunk(content="Found both."))
        service = DatasetQA(engine, dialogue, MCPGateway({"records": Server(mcp)}))
        try:
            events = await collect(service, session(service))
            assert_completed(service, None, events[-1])
            assert calls==["a", "b"]
            assert len(dialogue.inputs)==5
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==["a", "b"]
        finally:
            await service.close()
    asyncio.run(run())


def test_auxiliary_result_informs_final_answer_without_becoming_a_display_card(engine):
    async def run():
        backend = Backend()

        def answer(messages, definitions):
            delivery = json.loads(messages[-1].content)
            assert len(delivery["final_delivery"])==1
            evidence, = delivery["answer_evidence"]
            assert evidence["operations"]==[] and evidence["data"]["size"]==0
            assert len(encode(delivery))<=8000
            return AIMessageChunk(content="The lookup also confirmed the size.")

        dialogue = RawDialogue(load(), batch([None], remote("inspect", reference="a"), operations=[goal("find")]),
            batch(["find"], remote("search")), action("deliver_results"), answer)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            events = await collect(service, session(service))
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==2
            card, = result_cards(events)
            assert card["data"]["items"]==backend.items
        finally:
            await service.close()
    asyncio.run(run())


def test_empty_collections_are_valid_results_and_do_not_erase_other_candidates(engine):
    async def run():
        backend, gateway = source()
        dialogue = RawDialogue(load(), batch(["find"], remote("lookup_records", query="empty"), operations=[goal("find")]),
            batch(["find"], remote("lookup_records", query="second")), action("deliver_results"), AIMessageChunk(content="Found candidates."))
        service = DatasetQA(engine, dialogue, gateway)
        try:
            events = await collect(service, session(service))
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==2
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==["b", "c"]
        finally:
            await service.close()
    asyncio.run(run())


def test_precise_saved_result_read_remains_available_in_final_synthesis(engine):
    async def run():
        backend, gateway = source()
        connect = gateway.client_factory

        def client(*args, **kwargs):
            connection = connect(*args, **kwargs)
            call = connection.call_tool

            async def execute(*args, **kwargs):
                result = await call(*args, **kwargs)
                result.structured_content["analysis"] = {"rare_fact": "Precisely read evidence", "body": "x"*12000}
                return result
            connection.call_tool = execute
            return connection

        def read(messages, definitions):
            result_id = json.loads(messages[1].content)["evidence"]["items"][0]["result_id"]
            return action("read_result", result_id=result_id, path="/analysis/rare_fact")

        def answer(messages, definitions):
            read = next(json.loads(message.content) for message in messages
                if isinstance(message, ToolMessage) and message.name=="read_result")
            assert read["data"]=="Precisely read evidence"
            return AIMessageChunk(content="Verified the requested fact.")

        gateway.client_factory = client
        dialogue = RawDialogue(load(), batch(["find"], remote("lookup_records", query="first"), operations=[goal("find")]),
            read, action("deliver_results"), answer)
        service = DatasetQA(engine, dialogue, gateway)
        try:
            events = await collect(service, session(service))
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_aggregation_does_not_complete_an_unexecuted_required_operation(engine):
    async def run():
        backend, gateway = source()
        dialogue = RawDialogue(load(), batch(["find"], remote("lookup_records", query="first"),
            operations=[goal("find"), goal("export")]), *[action("deliver_results") for _ in range(3)])
        service = DatasetQA(engine, dialogue, gateway)
        try:
            events = await collect(service, session(service))
            assert_handled(service, None, events[-1])
            assert len(backend.calls)==1
            assert len(result_cards(events))==1  # Only qualified partial evidence is retained.
            assert "export" in "".join(event.get("text", "") for event in events)
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("difference", ["tool", "server", "target", "unsafe", "view", "structure", "nested", "scalar"])
def test_automatic_merge_rejects_unproven_or_incompatible_collections(difference):
    operations = Operations()
    operations.declare([Operation(id="a", description="First"), Operation(id="b", description="Second")])
    cards = [{"result_id": key, "view_type": "data", "title": "Collection", "data": {"items": [{"id": key}]}}
        for key in ("a", "b")]
    for key in ("a", "b"):
        operations.start(key, key, {"server": "service", "name": "lookup"}, retry_safe=True)
        operations.finish(key, key, result_id=key)
    attempt = operations.items[1]["attempts"][0]
    if difference in {"tool", "server"}:
        attempt["tool"]["name" if difference=="tool" else "server"] = "other"
    elif difference=="target":
        operations.items[1]["target"] = {"result_id": "parent", "path": "/items/1"}
    elif difference=="unsafe":
        attempt["retry_safe"] = False
    elif difference=="view":
        cards[1]["view_type"] = "directory"
    elif difference=="structure":
        cards[1]["data"] = {"items": [{"url": "https://example.invalid/file"}]}
    elif difference=="nested":
        cards[1]["data"] = {"code": 200, "data": [{"id": "b"}]}
    else:
        cards[1]["data"] = {"items": ["b"]}
    with pytest.raises(QAError, match="合并|列表|幂等|汇总"):
        collection_paths(cards, operations)


@pytest.mark.parametrize("limit", [4, 64, 800, 8000])
def test_evidence_pool_is_bounded_and_keeps_source_identifiers_whole(limit):
    cards = [{"result_id": "task-"+str(index)+"x"*100, "view_type": "data", "title": "Records",
        "data": {"items": [{"id": str(index), "title": "Object "+str(index), "body": "large "*2000,
            "token": "secret", "blob": "binary"}]}} for index in range(24)]
    original = deepcopy(cards)
    view = evidence_group(cards, Operations(), limit)
    assert len(encode(view))<=limit and cards==original
    assert all(item["result_id"]==cards[index]["result_id"] for index, item in enumerate(view.get("items", [])))
    assert "secret" not in encode(view) and "binary" not in encode(view)


def test_grouped_evidence_replaces_duplicate_bodies_without_breaking_tool_pairs():
    dialogue = Dialogue(model=object(), limits=Limits(context_chars=14000))
    cards = [{"result_id": "result-"+str(i), "view_type": "data", "title": "Records",
        "data": {"items": [{"id": str(i), "title": "Object "+str(i), "body": "x"*9000}]}} for i in range(3)]
    pool = evidence_group(cards, Operations(), 2500)
    messages = dialogue.messages("Find resources", {"evidence": pool})
    for card in cards:
        call_id = card["result_id"]
        messages.extend([AIMessage(content="", tool_calls=[{"name": "lookup", "args": {}, "id": call_id}]),
            ToolMessage(content=encode(card), tool_call_id=call_id, name="mcp_lookup")])
    messages.extend([AIMessage(content="", tool_calls=[{"name": "read_result", "args": {}, "id": "read"}]),
        ToolMessage(content=encode({"result_id": cards[0]["result_id"], "data": {"requested_fact": "precise evidence"}}),
            tool_call_id="read", name="read_result")])
    bounded = dialogue.budget(messages, [])
    assert json.loads(bounded[1].content)["evidence"]==pool
    tools = [message for message in bounded if isinstance(message, ToolMessage)]
    assert len(tools)==4 and all("data" not in json.loads(message.content) for message in tools[:3])
    assert [message.tool_call_id for message in tools[:3]]==[card["result_id"] for card in cards]
    assert json.loads(tools[-1].content)["data"]=={"requested_fact": "precise evidence"}
    assert len(encode([message.model_dump(mode="json", exclude_none=True) for message in bounded]))<14000
