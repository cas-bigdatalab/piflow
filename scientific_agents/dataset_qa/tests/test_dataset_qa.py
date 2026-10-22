"""Generic tool discovery, durable dialogue and unified API regression checks."""
import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import replace
import json
import sys
import threading
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
import httpx
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.pool import StaticPool

from ..context import encode, project, slice_result
from ..contracts import Limits, Options, QAError, Server
from ..dialogue import BUILTINS, SYSTEM, Dialogue as SemanticDialogue
from ..mcp import MCPGateway, Tool
from ..service import DatasetQA
from ...unified.adapters.dataset_qa import DatasetQAAdapter
from ...unified.api import Native, install_unified


def definition(name, properties=None, required=None, annotations=None):
    return SimpleNamespace(name=name, description="Tool "+name,
        inputSchema={"type": "object", "properties": properties or {},
                     "required": required or [], "additionalProperties": False},
        annotations=annotations or {}, meta={})


class Backend:
    def __init__(self):
        self.calls, self.connections, self.lists = [], [], []
        self.gate, self.failure, self.protocol_error = None, None, False
        self.catalog = {
            "data": [
                definition("search", {"query": {"type": "string"}, "count": {"type": "integer", "minimum": 1, "maximum": 50}}),
                definition("inspect", {"reference": {"type": "string"}}, ["reference"]),
                definition("preview", {"reference": {"type": "string"}}, ["reference"]),
                definition("sample", {"reference": {"type": "string"}, "count": {"type": "integer", "minimum": 1, "maximum": 100}}, ["reference", "count"]),
            ],
            "compute": [definition("multiply", {"x": {"type": "number"}, "y": {"type": "number"}}, ["x", "y"])],
        }
        self.items = [{"id": "a", "title": "气象观测"}, {"id": "b", "title": "气象模拟"}]

    def client(self, target, **kwargs):
        backend = self

        class Client:
            async def __aenter__(self):
                backend.connections.append(target)
                return self

            async def __aexit__(self, *args):
                return False

            async def list_tools(self):
                backend.lists.append(target)
                return backend.catalog[target]

            async def call_tool(self, name, arguments, **kwargs):
                backend.calls.append((target, name, deepcopy(arguments)))
                if backend.gate:
                    await backend.gate.wait()
                if backend.failure and name==backend.failure[0]:
                    raise backend.failure[1]
                if backend.protocol_error:
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="Invalid operation")])
                if name=="search":
                    data = {"items": backend.items, "pagination": {"total": len(backend.items)}}
                elif name=="sample":
                    data = {"code": 200, "data": [{"row": i, "batch": len(backend.calls)} for i in range(arguments["count"])]}
                elif name=="multiply":
                    data = arguments["x"]*arguments["y"]
                else:
                    data = {"reference": arguments.get("reference"), "size": 0, "format": "JSON"}
                return SimpleNamespace(structured_content=data, is_error=False)
        return Client()

    def gateway(self, **kwargs):
        return MCPGateway({name: Server(name, name+" service") for name in self.catalog},
            client_factory=self.client, **kwargs)


def action(name, **arguments):
    return AIMessageChunk(content="", tool_calls=[{"name": name, "args": arguments, "id": "call-"+name}])


def remote(name, **arguments):
    def respond(messages, definitions):
        alias = next(v["function"]["name"] for v in definitions if v["function"]["name"].endswith("_"+name))
        return action(alias, **arguments)
    return respond


def load(server="data", **kwargs):
    return action("load_mcp_tools", server=server, **kwargs)


def with_operations(response, messages, definitions, *, output="result", resume=None):
    """Scripted models co-emit the new private bookkeeping with native calls."""
    names = {value["function"]["name"] for value in definitions if value["function"]["name"].startswith("mcp_")}
    native = [call for call in response.tool_calls if call["name"] in names]
    if not native or response.invalid_tool_calls or any(call["name"]=="remember" and any(
            key in call["args"] for key in ("operations", "calls", "resume")) for call in response.tool_calls):
        return response
    context = json.loads(messages[1].content)
    previous = context.get("operations", {}).get("items", []) or (context.get("pending") or {}).get("operations", {}).get("items", [])
    if resume is False:
        previous = []
    operation_id = previous[0]["id"] if previous else "task"
    arguments = {"calls": [operation_id]*len(native)}
    if not context.get("operations", {}).get("items"):
        arguments["operations"] = [{key: item[key] for key in ("id", "description", "target", "output", "direct") if key in item} for item in previous] if previous else [
            {"id": operation_id, "description": "完成当前请求", "output": output}]
    if context.get("pending"):
        arguments["resume"] = True if resume is None else resume
    registration = {"name": "remember", "args": arguments, "id": "operation-bookkeeping"}
    return response.model_copy(update={"tool_calls": [registration, *response.tool_calls]})


class Dialogue(SemanticDialogue):
    def __init__(self, *responses):
        super().__init__(model=object())
        self.responses, self.contexts, self.summaries, self.inputs = list(responses), [], [], []

    def messages(self, message, context):
        self.contexts.append(deepcopy(context))
        return super().messages(message, context)

    async def respond(self, messages, definitions):
        self.inputs.append((deepcopy(messages), deepcopy(definitions)))
        response = self.responses.pop(0) if self.responses else AIMessageChunk(content="已处理。")
        if callable(response):
            response = response(messages, definitions)
        if isinstance(response, Exception):
            raise response
        if definitions and not response.tool_calls and not response.invalid_tool_calls:
            result_ids = []
            for message in messages:
                if isinstance(message, ToolMessage):
                    result_id = json.loads(message.content).get("result_id")
                    if result_id and result_id not in result_ids:
                        result_ids.append(result_id)
            self.responses.insert(0, response)
            # Default mock delivery selects one artifact; explicit calls test merging.
            response = action("deliver_results", result_ids=result_ids[:1])
        yield with_operations(response, messages, definitions)

    async def summarize(self, summary, messages):
        self.summaries.append(messages)
        return "已讨论的选择与约束。"


@pytest.fixture
def engine():
    value = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    yield value
    value.dispose()


def session(service, user="alice", request="create"):
    return service.store.create(user, "", request)["id"]


async def collect(service, sid, message="继续", rid="turn", **params):
    return [v async for v in service.stream("alice", sid, message, rid, Options(**params)) if v is not None]


def result_cards(values):
    return [card for value in values if value["type"]=="result" for card in value["items"]]


def test_search_detail_sample_use_raw_results_and_generic_memory(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(action("list_mcp_servers"), load(), remote("search", query="气象", count=2),
            AIMessageChunk(content="找到两个数据集。"),
            load(), remote("inspect", reference="b"), action("remember", values={"selected_dataset_id": "b"}),
            AIMessageChunk(content="已展示。"), load(), remote("sample", reference="b", count=3))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        first = await collect(service, sid, "找气象数据", "search")
        search = result_cards(first)[0]
        await collect(service, sid, "看看第二个", "detail", result_id=search["result_id"])
        values = await collect(service, sid, "采样三条", "sample")
        card = result_cards(values)[0]
        assert backend.calls == [("data", "search", {"query": "气象", "count": 2}),
            ("data", "inspect", {"reference": "b"}), ("data", "sample", {"reference": "b", "count": 3})]
        assert backend.lists==["data"]
        assert "compute" not in backend.connections
        assert card["data"]["items"]==[{"code": 200, "data": [{"row": i, "batch": 3} for i in range(3)]}]
        view = await service.get_session("alice", sid)
        assert view["context"]=={"selected_dataset_id": "b"}
        restored = next(i["payload"] for i in view["items"] if i["item_type"]=="RESULT_CARD" and i["payload"]["result_id"]==card["result_id"])
        assert restored["data"]==card["data"]
        assert search["data"]["items"]==backend.items
        assert set(restored)=={"result_id", "view_type", "title", "data"}
    asyncio.run(run())


def test_discovery_is_lazy_cached_and_accepts_new_tools():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        async with gateway.session() as tools:
            assert tools.list_servers()["items"]
            assert not tools.definitions() and not backend.connections
            page = await tools.load("compute")
            alias = page["items"][0]["name"]
            assert (await tools.call(alias, {"x": 2, "y": 3}))[1].data==6
        async with gateway.session() as tools:
            await tools.load("compute")
        assert backend.lists==["compute"]
        assert backend.connections==["compute"]  # A cached schema needs no new connection.
        backend.catalog["compute"].append(definition("future_operation", {"value": {"type": "string"}}))
        gateway.limits = replace(gateway.limits, cache_seconds=0)
        async with gateway.session() as tools:
            page = await tools.load("compute", query="future_operation", limit=1)
            assert page["items"][0]["tool"]=="future_operation"
        assert backend.lists==["compute", "compute"]
    asyncio.run(run())


def test_same_tool_name_on_different_servers_is_unambiguous():
    async def run():
        backend = Backend()
        backend.catalog["other"] = [definition("multiply", {"x": {"type": "number"}, "y": {"type": "number"}}, ["x", "y"])]
        async with backend.gateway().session() as tools:
            one = (await tools.load("compute"))["items"][0]["name"]
            two = (await tools.load("other"))["items"][0]["name"]
            assert one!=two and len(one)<=64
            await tools.call(two, {"x": 4, "y": 2})
        assert backend.calls==[("other", "multiply", {"x": 4, "y": 2})]
    asyncio.run(run())


def test_configuration_refresh_disabled_servers_and_no_credential_exposure(tmp_path):
    async def run():
        path = tmp_path/"mcp.yaml"
        path.write_text('mcpServers:\n  remote:\n    url: https://example.invalid/mcp\n    headers: {Authorization: secret-value}\n    description: remote service\n  data:\n    enabled: false\n', encoding="utf-8")
        gateway = Backend().gateway(config_path=path)
        async with gateway.session() as tools:
            public = tools.list_servers()
            assert "data" not in [v["name"] for v in public["items"]]
            assert "secret-value" not in encode(public) and "https://" not in encode(public)
            assert tools.servers["remote"].target["mcpServers"]["remote"]["headers"]
        path.write_text('servers:\n- name: new\n  command: python\n  args: [server.py]\n', encoding="utf-8")
        async with gateway.session() as tools:
            assert "new" in tools.servers and "remote" not in tools.servers
    asyncio.run(run())


@pytest.mark.parametrize("raw", ["[]", "servers: 1", "servers: [bad]", "servers: [{name: a, url: x}, {name: a, url: y}]", "mcpServers: {bad: 1}", "mcpServers: {bad: {timeout: 0, url: x}}"])
def test_invalid_config_is_reported_without_connecting(tmp_path, raw):
    path = tmp_path/"bad.yaml"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(QAError, match="配置"):
        MCPGateway(config_path=path).configured_servers()


def test_schema_and_tool_budgets_evict_definitions_consistently():
    async def run():
        backend = Backend()
        async with backend.gateway(limits=Limits(max_tools=2)).session() as tools:
            page = await tools.load("data")
            aliases = {v["function"]["name"] for v in tools.definitions()}
            assert len(aliases)==2
            assert {v["name"] for v in page["items"]}==aliases
            assert {tool.name for tool in tools.loaded.values()}=={"search", "inspect"}
            assert {row["tool"] for row in page["not_loaded"]}=={"preview", "sample"}
            evicted = Tool("data", "sample", "", {}, {}, {}).alias
            with pytest.raises(QAError, match="未加载"):
                await tools.call(evicted, {})
        backend.catalog["compute"][0].description = "x"*20000
        async with backend.gateway().session() as tools:
            assert (await tools.load("compute"))["items"][0]["error"]=="schema_too_large"
            assert not tools.definitions()
    asyncio.run(run())


def test_full_schema_validation_and_remote_refs_fail_before_dispatch():
    async def run():
        backend = Backend()
        backend.catalog["compute"] = [definition("nested", {"rows": {"type": "array", "items": {"type": "integer", "minimum": 1}, "maxItems": 2}}, ["rows"])]
        async with backend.gateway().session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            for args in ({"rows": [0]}, {"rows": [1, 2, 3]}, {"rows": [1], "extra": True}):
                with pytest.raises(QAError) as caught:
                    await tools.call(alias, args)
                assert caught.value.code=="invalid_parameters" and caught.value.detail["constraint"]
            tools.loaded[alias].schema["properties"]["rows"] = {"$ref": "https://example.invalid/schema"}
            with pytest.raises(QAError) as caught:
                await tools.call(alias, {"rows": []})
            assert caught.value.code=="invalid_schema"
        assert not backend.calls
    asyncio.run(run())


def test_business_envelopes_preserved_protocol_errors_reported():
    async def run():
        backend = Backend()
        backend.items = {"code": 17, "data": []}
        async with backend.gateway().session() as tools:
            alias = (await tools.load("data", query="search", limit=1))["items"][0]["name"]
            assert (await tools.call(alias, {}))[1].data["items"]=={"code": 17, "data": []}
            backend.protocol_error = True
            with pytest.raises(QAError) as caught:
                await tools.call(alias, {})
            assert caught.value.code=="tool_failed"
            assert caught.value.detail==["Invalid operation"]
    asyncio.run(run())


def test_saved_result_is_paged_without_repeating_sample(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(load(), remote("sample", reference="a", count=4), AIMessageChunk(content="已采样。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        card = result_cards(values)[0]
        dialogue.responses = [action("read_result", result_id=card["result_id"], path="/data", offset=2, limit=1)]*2
        read = await collect(service, sid, rid="read")
        pages = [json.loads(m.content) for m in dialogue.inputs[-1][0]
            if isinstance(m, ToolMessage) and m.name=="read_result"]
        assert len(pages)==2 and all(pages[1][key]==value for key, value in pages[0].items())
        assert pages[0]=={"result_id": card["result_id"], "data": [{"row": 2, "batch": 1}], "next_offset": 3,
            "objects": [{"handle": "object:1", "path": "/data/2"}]}
        saved = json.loads(service.store.task("alice", sid, read[-1]["task_id"])["payload"])
        assert saved["objects"]["object:1"]=={"result_id": card["result_id"], "path": "/data/2", "kind": "object"}
        assert len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_clarification_resume_and_cancel_keep_one_active_interaction(engine):
    async def run():
        dialogue = Dialogue(action("request_input", missing="待操作的对象", question="请选择对象", options=[{"label": "甲", "value": "a"}, "乙"]))
        service = DatasetQA(engine, dialogue, Backend().gateway())
        sid = session(service)
        waiting = await collect(service, sid)
        tid = waiting[-1]["task_id"]
        assert waiting[-1]["status"]=="WAITING_INPUT"
        view = await service.get_session("alice", sid)
        assert view["interaction"]["question"]=="请选择对象"
        assert not any(i["item_type"]=="INTERACTION" for i in view["items"])
        dialogue.responses = [load(), remote("inspect", reference="a")]
        await collect(service, sid, "甲", "reply")
        assert dialogue.contexts[-1]["pending"]["task_id"]==tid
        assert service.store.task("alice", sid, tid)["status"]=="COMPLETED"
        assert (await service.get_session("alice", sid))["interaction"] is None
        dialogue.responses = [action("request_input", missing="下一项操作所需的参数", question="请补充执行参数")]
        waiting = await collect(service, sid, rid="wait-again")
        await service.cancel("alice", sid, waiting[-1]["task_id"])
        assert (await service.get_session("alice", sid))["interaction"] is None
        dialogue.responses = [load(), remote("search")]
        assert (await collect(service, sid, rid="next"))[-1]["status"]=="COMPLETED"
    asyncio.run(run())


def test_replay_versions_and_cursors_never_repeat_upstream(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("sample", reference="a", count=2)), backend.gateway())
        sid = session(service)
        first = await collect(service, sid, rid="sample", expected_version=0)
        # Simulate a restart after background reads release SQLite's single test connection.
        await asyncio.gather(*list(service.summaries.values()))
        await service.close()
        recovered = DatasetQA(engine, Dialogue(), backend.gateway())
        assert first==await collect(recovered, sid, rid="sample", expected_version=0)
        assert len(backend.calls)==1
        resumed = await collect(recovered, sid, rid="sample", after_event_seq=first[-2]["event_seq"])
        assert len(resumed)==1 and resumed[0]["type"]=="done"
        for message, rid, opts in [("changed", "sample", {}), ("new", "new", {"expected_version": 0}),
                                  ("继续", "sample", {"after_event_seq": 99999}), ("new", "missing", {"after_event_seq": 1})]:
            with pytest.raises(QAError):
                await collect(recovered, sid, message, rid, **opts)
        assert len(backend.calls)==1
        await recovered.close()
    asyncio.run(run())


def test_disconnect_keeps_task_cancel_fences_late_result(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        service = DatasetQA(engine, Dialogue(load(), remote("search")), backend.gateway())
        sid = session(service)
        stream = service.stream("alice", sid, "查找", "running", Options())
        first = await anext(stream)
        assert first["type"]=="stage" and first["stage"]=="prepare"
        await stream.aclose()
        with pytest.raises(QAError, match="正在处理"):
            await collect(service, sid, rid="busy")
        await service.cancel("alice", sid, first["task_id"])
        backend.gate.set()
        await asyncio.gather(*list(service.jobs.values()), return_exceptions=True)
        assert service.store.session("alice", sid)["active_task_id"] is None
        assert not service.store.results("alice", sid, first["task_id"])
        service.dialogue.responses = [load(), remote("search"), AIMessageChunk(content="继续处理新问题。")]
        assert (await collect(service, sid, rid="next"))[-1]["status"]=="COMPLETED"
    asyncio.run(run())


def test_unknown_execution_not_retried_and_partial_results_retained(engine):
    async def run():
        backend = Backend()
        backend.failure = ("sample", TimeoutError())
        service = DatasetQA(engine, Dialogue(load(), remote("search"), remote("sample", reference="a", count=1)), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert len(result_cards(values))==1  # Retained evidence never implies sampling succeeded.
        assert len(service.store.results("alice", sid))==1
        assert values[-1]["code"]=="execution_unknown"
        assert all(v["type"] in {"stage", "message", "result", "done"} for v in values)
        assert values[-1]["status"]=="FAILED" and len(backend.calls)==2
        assert values==await collect(service, sid)
        assert len(backend.calls)==2
    asyncio.run(run())


def test_invalid_tool_arguments_can_be_corrected_without_bad_dispatch(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load("compute"), remote("multiply", x="bad", y=2),
            remote("multiply", x=3, y=2)), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED"
        assert backend.calls==[("compute", "multiply", {"x": 3, "y": 2})]
        assert all("status" not in v for v in values if v["type"]=="stage")
    asyncio.run(run())


@pytest.mark.parametrize("idempotent", [False, True])
def test_protocol_business_error_is_not_retried_even_if_idempotent(engine, idempotent):
    async def run():
        backend = Backend()
        backend.protocol_error = True
        backend.catalog["compute"][0].annotations = {"idempotentHint": idempotent}
        dialogue = Dialogue(load("compute"), remote("multiply", x=2, y=3))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="tool_failed"
        assert len(backend.calls)==1
        assert not service.store.results("alice", sid)
        assert len(dialogue.inputs)==2
        assert "Invalid operation" in "".join(v["text"] for v in values if v["type"]=="message")
    asyncio.run(run())


def test_model_failure_after_tool_preserves_card_without_claiming_completion(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("search"), RuntimeError("model offline")), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="FAILED"
        assert len(result_cards(values))==1  # Unique goal-bound evidence survives model failure.
        assert values[-1]["code"]=="service_unavailable"
        assert len(service.store.results("alice", sid))==1
    asyncio.run(run())


def test_foreign_results_and_user_isolation_never_dispatch(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("search")), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        card = result_cards(values)[0]
        other = session(service, request="other")
        for params in ({"result_id": card["result_id"]}, {"selected_dataset_id": "a"}):
            values = await collect(service, other, rid=next(iter(params)), **params)
            assert values[-1]["status"]=="FAILED"
        with pytest.raises(QAError):
            service.store.session("bob", sid)
        assert len(backend.calls)==1
    asyncio.run(run())


def test_long_dialogue_summary_pagination_and_minimal_views(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        for i in range(15):
            dialogue.responses = [load(), remote("search")]
            await collect(service, sid, "继续解释"+str(i), str(i))
            await asyncio.gather(*list(service.summaries.values()))
        assert dialogue.summaries and dialogue.contexts[-1]["summary"]
        assert all(len(c["history"])<=12 for c in dialogue.contexts)
        assert len(backend.calls)==15
        listed = await service.list_sessions("alice", 1, 20)
        assert set(listed)=={"items", "pagination"}
        view = await service.get_session("alice", sid, limit=4, tail=True)
        assert len(view["items"])==4 and view["has_more"]
        assert "next_after_item_id" not in view and "context" not in view
        older = await service.get_session("alice", sid, limit=4, before=view["before_item_id"])
        assert older["items"][-1]["item_id"]<view["items"][0]["item_id"]
        assert set(view["tasks"][0])=={"task_id", "status", "current_stage"}
        assert set(view["items"][0])=={"item_id", "task_id", "item_type", "create_time", "payload"}
    asyncio.run(run())


def test_delete_and_worker_expiry_fence_writes_without_reexecution(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(), backend.gateway())
        sid = session(service)
        task, _ = service.store.submit("alice", sid, "lost", {"message": "操作", "params": {}, "parent_task_id": None}, None, "old")
        with service.store.transaction() as conn:
            conn.execute(update(service.store.tasks).where(service.store.tasks.c.id==task["id"]).values(expires=0))
        await service.start()
        assert service.store.task("alice", sid, task["id"])["status"]=="FAILED"
        assert service.store.session("alice", sid)["active_task_id"] is None
        assert not backend.calls
        assert session(service)==sid
        await service.delete_session("alice", sid)
        with pytest.raises(QAError):
            service.store.write("alice", sid, task["id"], card={"result_id": "late"})
        with pytest.raises(QAError, match="已删除"):
            session(service)
        await service.close()
    asyncio.run(run())


def test_partial_stream_survives_cancel(engine):
    async def run():
        gate = asyncio.Event()

        class Streaming(Dialogue):
            async def respond(self, messages, definitions):
                if definitions:
                    async for chunk in super().respond(messages, definitions):
                        yield chunk
                    return
                yield AIMessageChunk(content="取消以后仍需保留的回答。"*5)
                await gate.wait()

        service = DatasetQA(engine, Streaming(load(), remote("search")), Backend().gateway())
        sid = session(service)
        stream = service.stream("alice", sid, "解释一下", "stream", Options())
        while True:
            value = await anext(stream)
            if value and value["type"]=="message":
                break
        await service.cancel("alice", sid, value["task_id"])
        await stream.aclose()
        await asyncio.gather(*list(service.jobs.values()), return_exceptions=True)
        view = await service.get_session("alice", sid)
        reply = next(i for i in view["items"] if i["item_type"]=="ASSISTANT_MESSAGE")
        assert reply["payload"]["text"]==value["text"]
        events = service.store.replay("alice", sid, value["task_id"], 0)
        assert events[-1]["type"]=="done" and events[-1]["status"]=="CANCELLED"
    asyncio.run(run())


def test_first_text_is_streamed_before_model_finishes_and_reasoning_blocks_hidden(engine):
    async def run():
        gate = asyncio.Event()

        class Streaming(Dialogue):
            async def respond(self, messages, definitions):
                if definitions:
                    async for chunk in super().respond(messages, definitions):
                        yield chunk
                    return
                yield AIMessageChunk(content=[{"type": "reasoning", "reasoning": "internal"}, {"type": "text", "text": "首"}])
                await gate.wait()
                yield AIMessageChunk(content="尾")

        service = DatasetQA(engine, Streaming(load(), remote("search")), Backend().gateway())
        sid = session(service)
        stream = service.stream("alice", sid, "解释一下", "stream", Options())

        async def first_text():
            async for value in stream:
                if value and value["type"]=="message":
                    return value

        first = await asyncio.wait_for(first_text(), 2)
        assert first["text"]=="首" and not gate.is_set()
        assert service.store.task("alice", sid, first["task_id"])["status"]=="RUNNING"
        gate.set()
        rest = [v async for v in stream if v is not None]
        assert first["text"]+"".join(v["text"] for v in rest if v["type"]=="message")=="首尾"
        assert rest[-1]["status"]=="COMPLETED"
    asyncio.run(run())


def test_fragmented_tool_arguments_never_create_empty_messages(engine, monkeypatch):
    from .. import service as runtime

    async def run():
        clock = [0.0]
        monkeypatch.setattr(runtime, "time", SimpleNamespace(monotonic=lambda: clock[0]))

        class Fragments(Dialogue):
            round = 0

            async def respond(self, *args):
                self.round += 1
                if self.round==1:
                    for index, text in enumerate(['{', '"query":', '""}']):
                        clock[0] += 0.2
                        yield AIMessageChunk(content="", tool_call_chunks=[{
                            "name": "list_mcp_servers" if index==0 else None, "args": text,
                            "id": "call" if index==0 else None, "index": 0}])
                else:
                    yield AIMessageChunk(content="已处理。")

        service = DatasetQA(engine, Fragments(), Backend().gateway())
        sid = session(service)
        values = await collect(service, sid)
        persisted = service.store.replay("alice", sid, values[-1]["task_id"], 0)
        for events in (values, persisted):
            assert all(v["text"] for v in events if v["type"]=="message")
            assert not any(v.get("stage")=="list_mcp_servers" for v in events)
            assert all(v.get("stage") in {None, "prepare", "answer"} for v in events)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="mcp_required"
    asyncio.run(run())


def test_heartbeat_uses_idle_interval_and_progress_resets_it(engine, monkeypatch):
    from .. import service as runtime

    async def run():
        clock, gate = [0.0], asyncio.Event()
        monkeypatch.setattr(runtime, "time", SimpleNamespace(monotonic=lambda: clock[0]))

        class Waiting(Dialogue):
            async def respond(self, *args):
                await gate.wait()
                yield action("request_input", missing="待操作的对象", question="需要处理哪个对象？")

        service = DatasetQA(engine, Waiting(), Backend().gateway())
        sid = session(service)
        stream = service.stream("alice", sid, "等待", "stream", Options())
        async for value in stream:
            if value and value.get("stage")=="prepare":
                tid = value["task_id"]
                break
        pending = asyncio.create_task(anext(stream))
        clock[0] = 14
        await service._notify()
        assert not (await asyncio.wait({pending}, timeout=0.05))[0]
        clock[0] = 15
        await service._notify()
        assert await asyncio.wait_for(pending, 1) is None
        clock[0] = 20
        await service._write("alice", sid, tid, {"type": "stage", "stage": "execute", "summary": "实际进度"})
        assert (await anext(stream))["summary"]=="实际进度"
        pending = asyncio.create_task(anext(stream))
        clock[0] = 34
        await service._notify()
        assert not (await asyncio.wait({pending}, timeout=0.05))[0]
        clock[0] = 35
        await service._notify()
        assert await asyncio.wait_for(pending, 1) is None
        gate.set()
        values = [v async for v in stream if v is not None]
        assert values[-1]["status"]=="WAITING_INPUT"
    asyncio.run(run())


def test_stages_explain_model_loading_and_arbitrary_mcp_execution(engine):
    async def run():
        backend = Backend()
        backend.catalog["compute"][0].annotations = {"title": "自定义计算"}
        service = DatasetQA(engine, Dialogue(load("compute"), remote("multiply", x=2, y=3)), backend.gateway())
        values = await collect(service, session(service))
        stages = [v for v in values if v["type"]=="stage"]
        assert all(v.get("summary") for v in stages)
        phases = [v["stage"] for v in stages]
        assert phases==["prepare", "execute", "answer"]
        assert not any(v["stage"] in {"model", "context", "load_mcp_tools", "list_mcp_servers"} for v in stages)
        tool = [v for v in stages if v["stage"]=="execute"]
        assert len(tool)==1 and "status" not in tool[0]
        assert all("自定义计算" in v["summary"] for v in tool)
        assert values==await collect(service, session(service))
    asyncio.run(run())


def test_old_empty_events_are_skipped_without_stalling_replay(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        payload = {"message": "继续", "params": Options().model_dump(exclude={"after_event_seq", "expected_version"}), "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "old", payload, None, service.owner)
        for _ in range(105):
            service.store.write("alice", sid, task["id"], {"type": "message", "text": "", "mode": "append"})
        service.store.finish("alice", sid, task["id"], "COMPLETED", message="已有回答")
        values = await asyncio.wait_for(collect(service, sid, rid="old"), 2)
        assert not any(v["type"]=="message" for v in values)
        assert values[-1]["status"]=="COMPLETED"
    asyncio.run(run())


@pytest.mark.parametrize("provider,model,url,expected", [
    ("dashscope", "qwen3.5-plus", "https://dashscope.aliyuncs.com/compatible-mode/v1", {"enable_thinking": False}),
    ("deepseek", "deepseek-v4-flash", "https://api.deepseek.com/v1", {"thinking": {"type": "disabled"}}),
    ("openai", "glm-4.7", "https://open.bigmodel.cn/api/paas/v4", {"thinking": {"type": "disabled"}}),
    ("custom", "qwen/qwen3-32b", "https://openrouter.ai/api/v1", {"reasoning": {"enabled": False}}),
])
def test_real_sdk_disables_thinking_in_stream_and_summary_requests(monkeypatch, provider, model, url, expected):
    from langchain_openai import ChatOpenAI
    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        base = {"id": "test", "created": 0, "model": model}
        if body.get("stream"):
            chunk = {**base, "object": "chat.completion.chunk", "choices": [{"index": 0,
                "delta": {"role": "assistant", "content": "实际回答"}, "finish_reason": "stop"}]}
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
                text="data: "+encode(chunk)+"\n\ndata: [DONE]\n\n")
        return httpx.Response(200, json={**base, "object": "chat.completion", "choices": [{"index": 0,
            "message": {"role": "assistant", "content": "对话摘要"}, "finish_reason": "stop"}]})

    async def run():
        monkeypatch.setenv("QA_TEST_LLM_KEY", "test-key")
        settings = SimpleNamespace(llm=SimpleNamespace(provider=provider, model=model),
            providers={provider: SimpleNamespace(base_url=url, api_key_env="QA_TEST_LLM_KEY")})
        monkeypatch.setattr("infra.config_loader.get_settings", lambda: settings)
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            monkeypatch.setattr("langchain_openai.ChatOpenAI", lambda **kwargs: ChatOpenAI(http_async_client=client, **kwargs))
            dialogue = SemanticDialogue()
            chunks = [chunk async for chunk in dialogue.respond(dialogue.messages("问题", {}), BUILTINS)]
            assert "".join(chunk.text for chunk in chunks)=="实际回答"
            final = [chunk async for chunk in dialogue.respond(dialogue.messages("整理结果", {}), [])]
            assert "".join(chunk.text for chunk in final)=="实际回答"
            assert await dialogue.summarize("", [{"role": "user", "text": "问题"}])=="对话摘要"
            await dialogue.close()

    asyncio.run(run())
    assert len(requests)==3 and requests[0]["stream"] and requests[0]["tools"]
    assert requests[0]["tool_choice"]=="required"
    assert len(requests[0]["tools"])==len(BUILTINS)
    assert requests[1]["stream"] and "tools" not in requests[1]
    assert "tool_choice" not in requests[1] and "tool_choice" not in requests[2]
    assert all({k: body[k] for k in ("enable_thinking", "thinking", "reasoning", "extra_body") if k in body}==expected for body in requests)


def test_all_task_results_returned_even_when_more_than_recent_evidence(engine):
    async def run():
        backend = Backend()
        responses = [load("compute"), *[remote("multiply", x=i, y=2) for i in range(10)]]
        service = DatasetQA(engine, Dialogue(*responses), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        cards = service.store.results("alice", sid, values[-1]["task_id"])
        assert values[-1]["status"]=="COMPLETED" and len(result_cards(values))==1
        assert len(cards)==10 and [c["data"] for c in cards]==list(range(0, 20, 2))
    asyncio.run(run())


def test_old_result_references_remain_discoverable_without_upstream(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(load("compute"), *[remote("multiply", x=i, y=2) for i in range(10)])
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        first = result_cards(values)[0]
        assert first["result_id"] not in {c["result_id"] for c in service.store.results("alice", sid)}
        dialogue.responses = [action("read_result", offset=0, limit=2)]
        await collect(service, sid, rid="browse-old")
        page = next(json.loads(m.content) for m in dialogue.inputs[-1][0]
            if isinstance(m, ToolMessage) and m.name=="read_result")
        assert page["items"][0]["result_id"]==first["result_id"]
        assert page["next_offset"]==2
        dialogue.responses = [action("read_result", result_id=first["result_id"])]
        await collect(service, sid, rid="read-old")
        assert next(json.loads(m.content) for m in dialogue.inputs[-1][0]
            if isinstance(m, ToolMessage) and m.name=="read_result")["data"]==0
        assert len(backend.calls)==10
    asyncio.run(run())


def test_generic_projection_and_pointer_keep_valid_json():
    value = {"items": [{"id": "ABC-012345", "description": "x"*1000} for _ in range(20)], "total": 20, "token": "private"}
    data, cut = project(value, 1500)
    assert cut and len(encode(data))<=1500 and "token" not in data
    assert data["items"][0]["id"]=="ABC-012345"
    assert slice_result({"a/b": {"~key": [1, 2, 3]}}, "/a~1b/~0key", 1, 1)==([2], True)
    with pytest.raises(QAError):
        slice_result(value, "/missing")


def test_context_budget_retains_complete_call_result_groups():
    # Keep history space fixed as instructions/schemas evolve; still prune it.
    dialogue = SemanticDialogue(model=object(), limits=Limits(
        context_chars=len(encode(BUILTINS))+len(SYSTEM)+2500, result_chars=800))
    messages = dialogue.messages("请继续", {"history": [{"role": "user", "text": "x"*10000}], "memory": {"chosen": "a"}})
    for i in range(6):
        messages.extend([AIMessage(content="", tool_calls=[{"name": "any", "args": {"i": i}, "id": str(i)}]),
            ToolMessage(content=encode({"result_id": str(i), "data": {"rows": ["x"*1000]*10}}), tool_call_id=str(i))])
    budgeted = dialogue.budget(messages, BUILTINS)
    assert len(budgeted)<len(messages)
    assert len(encode([m.model_dump(mode="json") for m in budgeted]))+len(encode(BUILTINS))<dialogue.limits.context_chars+500
    for i in range(3, len(budgeted), 2):
        assert budgeted[i].tool_calls[0]["id"]==budgeted[i+1].tool_call_id
        json.loads(budgeted[i+1].content)
    assert budgeted[-1].tool_call_id=="5"


def test_context_budget_keeps_result_pagination_metadata():
    dialogue = SemanticDialogue(model=object())
    messages = dialogue.messages("继续读取", {})
    messages.extend([AIMessage(content="", tool_calls=[{"name": "read_result", "args": {}, "id": "page"}]),
        ToolMessage(content=encode({"result_id": "saved", "data": [1], "next_offset": 20}), tool_call_id="page")])
    assert json.loads(dialogue.budget(messages, BUILTINS)[-1].content)["next_offset"]==20


def test_malformed_model_call_is_failed_without_dispatch(engine):
    async def run():
        backend = Backend()
        chunk = AIMessageChunk(content="", invalid_tool_calls=[{"name": "anything", "args": "{bad", "id": "bad", "error": "invalid JSON"}])
        service = DatasetQA(engine, Dialogue(chunk, chunk, chunk), backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED"
        assert values[-1]["code"]=="invalid_tool_call"
        assert not backend.calls
    asyncio.run(run())


def test_unloaded_tools_and_loop_budget_cannot_dispatch(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(action(Tool("data", "search", "", {}, {}, {}).alias),
            action("list_mcp_servers"), action("list_mcp_servers"))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=2)))
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED"
        assert values[-1]["code"]=="step_limit"
        assert not backend.calls and not backend.connections
    asyncio.run(run())


def test_real_fastmcp_discovers_arbitrary_tool_and_calls_schema():
    pytest.importorskip("fastmcp")
    from fastmcp import FastMCP
    mcp = FastMCP("runtime-test")

    @mcp.tool
    def power(base: int, exponent: int=2) -> dict:
        """Compute a power."""
        return {"value": base**exponent}

    async def run():
        gateway = MCPGateway({"local": Server(mcp)})
        async with gateway.session() as tools:
            alias = (await tools.load("local"))["items"][0]["name"]
            tool, value = await tools.call(alias, {"base": 3})
            assert tool.schema["properties"]["base"]["type"]=="integer"
            assert value.data=={"value": 9} and not value.content
        @mcp.tool
        def greeting(name: str) -> str:
            """Return a greeting."""
            return "hello "+name
        gateway.limits = replace(gateway.limits, cache_seconds=0)
        async with gateway.session() as tools:
            alias = (await tools.load("local", query="greeting", limit=1))["items"][0]["name"]
            assert (await tools.call(alias, {"name": "world"}))[1].data in ("hello world", {"result": "hello world"})
    asyncio.run(run())


def test_real_mcp_transport_uses_existing_mounted_tools(monkeypatch):
    pytest.importorskip("fastmcp")
    from mcp_servers.corpus_mcp import mcp
    seen = []
    monkeypatch.setattr("mcp_servers.corpus_mcp.get_dataset_detail_by_cstr",
        lambda cstr: seen.append(cstr) or {"cstr": cstr, "size": 0})

    async def run():
        async with MCPGateway({"corpus": Server(mcp)}).session() as tools:
            page = await tools.load("corpus", query="get_corpus_dataset_detail", limit=1)
            assert page["items"][0]["tool"]=="get_corpus_dataset_detail"
            value = (await tools.call(page["items"][0]["name"], {"cstr": "CSTR-A"}))[1]
            assert value.data["size"]==0
        assert seen==["CSTR-A"]
    asyncio.run(run())


def test_unified_routes_minimal_contract_and_authorization(engine, monkeypatch):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("search")), backend.gateway())
        app, bindings = FastAPI(), {}

        def binding(user, sid, agent=None):
            if agent:
                bindings[user, sid] = agent
            return bindings.get((user, sid))

        def identity(self, request):
            self.request = request
            auth = request.headers.get("authorization", "")
            if not auth.startswith("Bearer "):
                raise HTTPException(401, "请登录")
            self.user = auth[7:]

        monkeypatch.setattr(Native, "__init__", identity)
        app.state.scientific_agents = SimpleNamespace(session_services={"dataset_qa": service},
            store=SimpleNamespace(_lock=threading.RLock(), binding=binding))
        install_unified(app, adapters={"dataset_qa": DatasetQAAdapter})
        prefix = "/api/piflow/v1/agents"
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test",
                headers={"Authorization": "Bearer alice"}) as client:
            created = await client.post(prefix+"/sessions", json={"agent_id": "dataset_qa", "request_id": "create"})
            assert set(created.json())=={"code", "message", "result"}
            sid = created.json()["result"]["session_id"]
            response = await client.post(prefix+f"/sessions/{sid}/chat/stream", json={"message": "找气象数据", "request_id": "search"})
            values = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
            assert all(v["session_id"]==sid and v["request_id"]=="search" for v in values)
            card = result_cards(values)[0]
            assert "error" not in values[-1] and values[-1]["status"]=="COMPLETED"
            result = (await client.get(prefix+f"/sessions/{sid}/tasks/{values[-1]['task_id']}/results")).json()["result"]
            assert set(result)=={"items"}
            assert result["items"][0]["data"]==card["data"]
            view = (await client.get(prefix+f"/sessions/{sid}?tail=true&item_limit=2")).json()["result"]
            assert len(view["items"])==2 and view["has_more"]
            listed = (await client.get(prefix+"/sessions?agent_id=dataset_qa&keyword=气象")).json()["result"]
            assert set(listed)=={"items", "pagination"} and listed["pagination"]["total"]==1
            assert (await client.get(prefix+f"/sessions/{sid}", headers={"Authorization": "Bearer bob"})).status_code==404
            for params in ({"unknown": True}, {"top_k": 10}):
                bad = await client.post(prefix+f"/sessions/{sid}/chat/stream", json={"message": "你好", "params": params})
                assert '"code": "invalid_parameters"' in bad.text and '"status": "FAILED"' in bad.text
    asyncio.run(run())


def test_default_registry_only_exposes_enabled_dataset_qa():
    app = FastAPI()
    install_unified(app)
    assert "dataset_qa" not in app.state.unified_adapters
    app = FastAPI()
    app.state.dataset_qa_enabled = True
    install_unified(app)
    assert app.state.unified_adapters=={"dataset_qa": DatasetQAAdapter}


def test_host_lifecycle_registers_and_closes_dataset_qa(engine, monkeypatch):
    from ...integration import install_scientific_agents

    async def run():
        events = []

        @asynccontextmanager
        async def host_lifespan(app):
            events.append("host.start")
            yield
            events.append("host.close")

        @asynccontextmanager
        async def forecast_lifespan(app):
            app.state.store, app.state.sessions = SimpleNamespace(engine=engine), object()
            events.append("forecast.start")
            yield
            events.append("forecast.close")

        class Service:
            async def start(self):
                events.append("qa.start")

            async def close(self):
                events.append("qa.close")

        extension = FastAPI(lifespan=forecast_lifespan)
        monkeypatch.setitem(sys.modules, "scientific_agents.forecast.api",
            SimpleNamespace(PREFIX="/api/piflow/v1", create_app=lambda **kwargs: extension))
        app, qa = FastAPI(lifespan=host_lifespan), Service()
        install_scientific_agents(app, resources=lambda: None, dataset_qa=qa)
        async with app.router.lifespan_context(app):
            assert app.state.scientific_agents.session_services["dataset_qa"] is qa
        assert not hasattr(app.state, "scientific_agents")
        assert events==["host.start", "forecast.start", "qa.start", "qa.close", "forecast.close", "host.close"]
    asyncio.run(run())
