"""Service-local discovery faults must not invalidate usable tools or artifacts."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest

from ..contracts import QAError, Server
from ..execution import Execution
from ..mcp import MCPGateway
from ..service import DatasetQA
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_operations import batch, goal, saved
from .test_runtime import RawDialogue


def loading(*servers):
    return AIMessageChunk(content="", tool_calls=[
        {**load(server).tool_calls[0], "id": "load-"+str(index)} for index, server in enumerate(servers)])


def faulty_gateway(backend, *, directory=False):
    attempts = []
    backend.catalog["offline"] = backend.catalog["data"]
    gateway = backend.gateway()

    def factory(target, **kwargs):
        client = backend.client(target, **kwargs)
        connect, list_tools = client.__aenter__, client.list_tools

        async def enter(self):
            attempts.append((target, "connect"))
            if target=="offline" and not directory:
                raise ValueError("isolated unavailable service")
            return await connect()

        async def tools():
            attempts.append((target, "directory"))
            if target=="offline" and directory:
                raise RuntimeError("isolated unavailable directory")
            return await list_tools()

        client.__class__.__aenter__, client.list_tools = enter, tools
        return client

    gateway.client_factory = factory
    return gateway, attempts


@pytest.mark.parametrize("order", [("offline", "data"), ("data", "offline")])
@pytest.mark.parametrize("directory", [False, True])
def test_mixed_discovery_batch_continues_without_extra_model_round(engine, order, directory):
    async def run():
        backend = Backend()
        gateway, attempts = faulty_gateway(backend, directory=directory)
        dialogue = RawDialogue(loading(*order), remote("search", query="demo"),
            action("deliver_results"), AIMessageChunk(content="已找到相关记录。"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid)
            assert events[-1]["status"]=="COMPLETED" and "code" not in events[-1]
            assert len(dialogue.inputs)==4 and len(backend.calls)==1
            assert len(result_cards(events))==1
            text = "".join(v.get("text", "") for v in events)
            assert text=="已找到相关记录。"
            messages = [m for m in dialogue.inputs[1][0] if isinstance(m, ToolMessage) and m.name=="load_mcp_tools"]
            assert [m.tool_call_id for m in messages]==["load-0", "load-1"]
            failure = next(json.loads(m.content) for m in messages if "error" in json.loads(m.content))
            assert failure["server"]=="offline" and failure["executed"] is False
            assert {target for target, phase in attempts if phase=="connect"}=={"data", "offline"}
            assert events==await collect(service, sid) and len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_discovery_after_success_does_not_override_goal_or_published_card(engine):
    async def run():
        backend = Backend()
        gateway, _ = faulty_gateway(backend)
        dialogue = RawDialogue(load(), remote("search"), load("offline"),
            action("deliver_results"), AIMessageChunk(content="请查看查询结果。"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid)
            assert events[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert len(result_cards(events))==1 and len(dialogue.inputs)==5
            assert "".join(v.get("text", "") for v in events)=="请查看查询结果。"
            payload = saved(service, sid, events[-1]["task_id"])
            assert "error" not in payload and payload["operations"][0]["state"]=="succeeded"
            history = await service.get_session("alice", sid)
            assert next(i["payload"]["text"] for i in history["items"] if i["item_type"]=="ASSISTANT_MESSAGE")=="请查看查询结果。"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("directory", [False, True])
def test_discovery_failure_cached_only_for_current_turn(directory, caplog):
    async def run():
        backend = Backend()
        gateway, attempts = faulty_gateway(backend, directory=directory)
        async with gateway.session() as tools:
            for _ in range(3):
                with pytest.raises(QAError) as exc:
                    await tools.load("offline")
                assert exc.value.code=="mcp_unavailable"
            assert attempts.count(("offline", "connect"))==1
            assert attempts.count(("offline", "directory"))==int(directory)
            assert (await tools.load("data"))["items"]
        gateway.client_factory = backend.client
        async with gateway.session() as tools:
            assert (await tools.load("offline"))["items"]
        records = [r for r in caplog.records if r.name=="flow.dataset_qa.mcp" and r.exc_info]
        assert len(records)==1 and "offline" in records[0].getMessage()
        assert str(records[0].exc_info[1]).startswith("isolated unavailable")
    asyncio.run(run())


def test_distinct_unavailable_services_are_progress_until_usable_service_found(engine):
    async def run():
        backend = Backend()
        backend.catalog["offline-two"] = []
        gateway, attempts = faulty_gateway(backend)
        factory = gateway.client_factory
        gateway.client_factory = lambda target, **kwargs: factory("offline" if target=="offline-two" else target, **kwargs)
        dialogue = RawDialogue(load("offline"), load("offline-two"), load(), remote("search"),
            action("deliver_results"), AIMessageChunk(content="已找到记录。"))
        service = DatasetQA(engine, dialogue, gateway)
        try:
            events = await collect(service, session(service))
            assert events[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert len(dialogue.inputs)==6 and attempts.count(("offline", "connect"))==2
        finally:
            await service.close()
    asyncio.run(run())


def test_all_services_unavailable_end_with_specific_friendly_reason(engine):
    async def run():
        backend = Backend()
        gateway, _ = faulty_gateway(backend)
        gateway.servers = {"offline": gateway.servers["offline"]}
        dialogue = RawDialogue(load("offline"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid)
            assert events[-1]["status"]=="FAILED" and events[-1]["code"]=="mcp_unavailable"
            assert len(dialogue.inputs)==1 and not backend.calls and not result_cards(events)
            text = "".join(v.get("text", "") for v in events)
            assert text==events[-1]["message"] and "暂时无法访问" in text
            assert "MCP" not in text and "未执行" not in text
        finally:
            await service.close()
    asyncio.run(run())


def test_real_partial_failure_keeps_artifact_and_one_coherent_explanation(engine):
    async def run():
        backend = Backend()

        def sample(messages, definitions):
            backend.protocol_error = True
            return batch(["sample"], remote("sample", reference="a", count=1))(messages, definitions)

        dialogue = RawDialogue(load(), batch(["find"], remote("search"),
            operations=[goal("find"), goal("sample")]), sample)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid)
            assert events[-1]["status"]=="FAILED" and events[-1]["code"]=="tool_failed"
            assert len(result_cards(events))==1 and len(backend.calls)==2
            messages = [v["text"] for v in events if v["type"]=="message"]
            assert len(messages)==1 and messages[0].count("Invalid operation")==1
            assert "已为您完成：操作 find" in messages[0] and "暂时还无法提供：操作 sample" in messages[0]
            assert "MCP" not in messages[0] and "未完成" not in messages[0]
            assert events[-1]["message"]==Execution.notice(QAError("tool_failed", "technical message", detail=["Invalid operation"]))
            assert saved(service, sid, events[-1]["task_id"])["operations"][1]["state"]=="failed"
        finally:
            await service.close()
    asyncio.run(run())


def test_isolation_with_real_mcp_client_and_fresh_sampling(engine):
    from fastmcp import FastMCP
    async def run():
        mcp, calls = FastMCP("generic-records"), []

        @mcp.tool()
        def sample():
            calls.append("sample")
            return {"batch": len(calls)}

        def unavailable():
            raise ValueError("isolated unavailable service")

        gateway = MCPGateway({"working": Server(mcp), "offline": Server(unavailable)})
        dialogue = RawDialogue(loading("working", "offline"), remote("sample"),
            action("deliver_results"), AIMessageChunk(content="样本已就绪。"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid, rid="first")
            assert events[-1]["status"]=="COMPLETED" and len(calls)==1
            assert events==await collect(service, sid, rid="first") and len(calls)==1
            dialogue.responses = [remote("sample"), action("deliver_results"), AIMessageChunk(content="新样本已就绪。")]
            fresh = await collect(service, sid, rid="next")
            assert fresh[-1]["status"]=="COMPLETED" and len(calls)==2
            assert result_cards(events)[0]["data"]!=result_cards(fresh)[0]["data"]
        finally:
            await service.close()
    asyncio.run(run())
