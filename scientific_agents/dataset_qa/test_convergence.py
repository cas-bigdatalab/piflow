"""State-driven closure, actual waiting and cumulative turn deadlines."""
import asyncio
import json
import time

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest

from .contracts import Limits, Options, Server
from .execution import Execution
from .mcp import MCPGateway
from .service import DatasetQA
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_delivery import deliver
from .test_operations import batch, goal, saved
from .test_runtime import RawDialogue


@pytest.mark.parametrize("warm", [False, True])
def test_direct_artifact_uses_no_selection_round_and_preserves_replay(engine, warm):
    async def run():
        backend, gateway = Backend(), None
        gateway = backend.gateway()
        if warm:
            async with gateway.session() as tools:
                await tools.load("data")
        responses = [] if warm else [load()]
        dialogue = RawDialogue(*responses, batch(["find"], remote("search"), operations=[goal("find", direct=True)]),
            AIMessageChunk(content="已找到，请查看结果。"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid)
            assert values[-1]["status"]=="COMPLETED" and len(result_cards(values))==1
            assert len(dialogue.inputs)==(2 if warm else 3) and dialogue.inputs[-1][1]==[]
            assert len(backend.calls)==1 and not any(isinstance(m, ToolMessage) and m.name=="deliver_results"
                for m in dialogue.inputs[-1][0])
            refs = json.loads(service.store.session("alice", sid)["context"])["references"]
            assert refs["candidates"]["result_id"]==result_cards(values)[0]["result_id"]
            assert values==await collect(service, sid) and len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_direct_target_keeps_focus_and_explicit_selection(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]),
            AIMessageChunk(content="已找到。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            card = result_cards(await collect(service, sid))[0]
            target = {"result_id": card["result_id"], "path": "/items/1", "kind": "object"}
            dialogue.responses = [batch(["sample"], remote("sample", reference="b", count=1),
                operations=[goal("sample", target=target, direct=True)], references={"current": target, "selected": [target]}),
                AIMessageChunk(content="采样已完成。")]
            before = len(dialogue.inputs)
            values = await collect(service, sid, rid="sample")
            assert values[-1]["status"]=="COMPLETED" and len(dialogue.inputs)-before==2
            refs = json.loads(service.store.session("alice", sid)["context"])["references"]
            assert refs["current"]==target and refs["selected"]==[target]
            assert backend.calls[-1][2]["reference"]=="b"
        finally:
            await service.close()
    asyncio.run(run())


def test_non_direct_pagination_and_pending_operations_keep_needed_tools(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].inputSchema["properties"]["offset"] = {"type": "integer"}
        dialogue = RawDialogue(load(), batch(["pages"], remote("search", offset=0), operations=[goal("pages"), goal("sample", output="answer")]),
            batch(["pages", "sample"], remote("search", offset=2), remote("sample", reference="b", count=1)),
            deliver([0, 1], merge_path="/items"), AIMessageChunk(content="已完成。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service))
            assert values[-1]["status"]=="COMPLETED" and [call[1] for call in backend.calls]==["search", "search", "sample"]
            assert len(result_cards(values))==1
        finally:
            await service.close()
    asyncio.run(run())


def test_direct_delivery_waits_for_the_entire_native_batch(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["find", None], remote("search"), remote("inspect", reference="a"),
            operations=[goal("find", direct=True)]), deliver([0]), AIMessageChunk(content="已完成。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service))
            assert values[-1]["status"]=="COMPLETED" and [call[1] for call in backend.calls]==["search", "inspect"]
            assert result_cards(values)[0]["result_id"].endswith(":0")
        finally:
            await service.close()
    asyncio.run(run())


def test_wait_notice_does_not_terminate_or_repeat_a_slow_call(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        dialogue = RawDialogue(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]),
            AIMessageChunk(content="已完成。"))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(wait_notice=0.03, turn_timeout=1)))
        sid, values = session(service), []
        try:
            async with asyncio.timeout(2):
                async for value in service.stream("alice", sid, "查找", "turn", Options()):
                    if value is None:
                        continue
                    values.append(value)
                    if "尚未取得" in value.get("summary", ""):
                        assert service.store.task("alice", sid, value["task_id"])["status"]=="RUNNING"
                        assert len(backend.calls)==1
                        backend.gate.set()
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert sum("尚未取得" in value.get("summary", "") for value in values)==1
            assert len(dialogue.inputs)==3
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("queued", [False, True])
def test_turn_deadline_stops_waiting_with_an_accurate_reason(engine, queued):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        dialogue = RawDialogue(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(turn_timeout=0.25, wait_notice=0.03)))
        if queued:
            service.slots = asyncio.Semaphore(0)
        sid = session(service)
        try:
            values = await asyncio.wait_for(collect(service, sid), 2)
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="task_timeout"
            text = "".join(value["text"] for value in values if value["type"]=="message")
            assert "等待" in text and not result_cards(values)
            if queued:
                assert not backend.calls and not dialogue.inputs and "尚未开始执行" in text
            else:
                assert len(backend.calls)==1 and "尚未确认" in text
                assert saved(service, sid, values[-1]["task_id"])["operations"][0]["state"]=="unknown"
                assert service.slots._value==8
            assert values==await collect(service, sid)
        finally:
            await service.close()
    asyncio.run(run())


def test_final_generation_deadline_keeps_completed_artifact(engine):
    async def run():
        backend = Backend()

        class StalledFinal(RawDialogue):
            async def respond(self, messages, definitions):
                if not definitions:
                    self.inputs.append((messages, definitions))
                    await asyncio.Event().wait()
                async for chunk in super().respond(messages, definitions):
                    yield chunk

        dialogue = StalledFinal(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(turn_timeout=0.3, wait_notice=0.03)))
        try:
            values = await asyncio.wait_for(collect(service, session(service)), 2)
            assert values[-1]["status"]=="COMPLETED" and len(result_cards(values))==1 and len(backend.calls)==1
            assert any("已完成的操作及结果已保留" in value.get("text", "") for value in values)
        finally:
            await service.close()
    asyncio.run(run())


def test_progress_ignores_query_changes_and_new_result_ids():
    execution = Execution()
    assert execution.observe("first", {"items": [{"name": "server"}]}, "list_mcp_servers")
    assert not execution.observe("another-query", {"items": [{"name": "server"}]}, "list_mcp_servers")
    assert execution.observe("same-operation", {"result_id": "a", "data": {"rows": [1]}})
    assert not execution.observe("same-operation", {"result_id": "b", "data": {"rows": [1]}})
    assert execution.observe("read", {"data": [1]}, "read_result", {"result_id": "a", "offset": 0})
    assert execution.observe("read", {"data": [1]}, "read_result", {"result_id": "a", "offset": 1})
    assert execution.observe("remember-1", {"saved": True}, "remember", context={"memory": {"counter": 1}})
    assert not execution.observe("remember-2", {"saved": True}, "remember", context={"memory": {"counter": 2}})


def test_direct_flag_does_not_bypass_single_object_reference_grounding(engine):
    async def run():
        backend = Backend()
        backend.items = backend.items[:1]

        def choose(messages, definitions):
            names = {item["function"]["name"] for item in definitions}
            assert "read_result" in names and "remember" in names
            assert "load_mcp_tools" not in names and not any(name.startswith("mcp_") for name in names)
            rid = next(json.loads(m.content)["result_id"] for m in messages if isinstance(m, ToolMessage)
                and "result_id" in json.loads(m.content))
            return action("deliver_results", result_ids=[rid], references={"current": {"result_id": rid, "path": "/items/0"}})

        dialogue = RawDialogue(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]),
            choose, AIMessageChunk(content="已找到。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid)
            assert values[-1]["status"]=="COMPLETED" and len(dialogue.inputs)==4 and len(backend.calls)==1
            assert json.loads(service.store.session("alice", sid)["context"])["references"]["current"]["path"]=="/items/0"
        finally:
            await service.close()
    asyncio.run(run())


def test_deadline_preserves_success_and_reports_the_unconfirmed_operation(engine):
    async def run():
        backend = Backend()
        original = backend.client

        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            execute = client.call_tool

            async def call(name, arguments, **options):
                if name=="sample":
                    backend.gate = asyncio.Event()
                return await execute(name, arguments, **options)
            client.call_tool = call
            return client

        gateway = backend.gateway(limits=Limits(turn_timeout=0.4, wait_notice=0.03))
        gateway.client_factory = factory
        dialogue = RawDialogue(load(), batch(["find"], remote("search"),
            operations=[goal("find", direct=True), goal("sample")]), batch(["sample"], remote("sample", reference="a", count=1)))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await asyncio.wait_for(collect(service, sid), 2)
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="task_timeout"
            assert len(result_cards(values))==1 and [call[1] for call in backend.calls]==["search", "sample"]
            assert [item["state"] for item in saved(service, sid, values[-1]["task_id"])["operations"]]==["succeeded", "unknown"]
            text = "".join(value["text"] for value in values if value["type"]=="message")
            assert "已为您完成：操作 find" in text and "暂时还无法提供：操作 sample" in text
        finally:
            await service.close()
    asyncio.run(run())


def test_turn_deadline_is_not_reset_by_model_or_mcp_calls(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()

        class Delayed(RawDialogue):
            async def respond(self, messages, definitions):
                await asyncio.sleep(0.14)
                async for chunk in super().respond(messages, definitions):
                    yield chunk

        dialogue = Delayed(load(), batch(["find"], remote("search"), operations=[goal("find", direct=True)]))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(turn_timeout=0.8)))
        try:
            started = time.monotonic()
            values = await asyncio.wait_for(collect(service, session(service)), 2)
            assert values[-1]["code"]=="task_timeout" and len(dialogue.inputs)==2 and len(backend.calls)==1
            assert time.monotonic()-started<1
        finally:
            await service.close()
    asyncio.run(run())


def test_real_mcp_cancellation_respects_the_turn_deadline(engine):
    from fastmcp import FastMCP
    mcp, started = FastMCP("deadline-test"), []

    @mcp.tool
    async def slow_task() -> dict:
        started.append(True)
        await asyncio.Event().wait()
        return {}

    async def run():
        dialogue = RawDialogue(load("local"), batch(["work"], remote("slow_task"), operations=[goal("work", direct=True)]))
        service = DatasetQA(engine, dialogue, MCPGateway({"local": Server(mcp)}, limits=Limits(turn_timeout=0.6)))
        try:
            values = await asyncio.wait_for(collect(service, session(service)), 2)
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="task_timeout" and started==[True]
        finally:
            await service.close()
    asyncio.run(run())
