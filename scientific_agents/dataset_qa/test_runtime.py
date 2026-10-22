"""Execution guarantees and latency regressions, without live model requests."""
import asyncio
from dataclasses import replace
import json

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest
from sqlalchemy import update

from .contracts import Limits, Server
from .dialogue import Dialogue as NativeDialogue
from .mcp import MCPGateway
from .persistence import dumps
from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session, with_operations
from .test_delivery import deliver


class RawDialogue(Dialogue):
    async def respond(self, messages, definitions):
        self.inputs.append((messages, definitions))
        response = self.responses.pop(0)
        response = response(messages, definitions) if callable(response) else response
        yield with_operations(response, messages, definitions)


@pytest.mark.parametrize("responses", [
    [AIMessageChunk(content="Invented dataset result")],
    [action("list_mcp_servers"), AIMessageChunk(content="Discovery is enough")],
    [action("remember", values={"choice": "a"}), AIMessageChunk(content="Memory is enough")],
])
def test_no_success_without_actual_mcp_execution(engine, responses):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(*responses, AIMessageChunk(content="Still no action"), AIMessageChunk(content="Still no action"),
            AIMessageChunk(content="The task was not executed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="mcp_required"
        assert not backend.calls and not result_cards(values)
        shown = "".join(v["text"] for v in values if v["type"]=="message")
        assert "Invented dataset result" not in shown and "还没有取得新的服务结果" in shown
        planning = [v for v in dialogue.inputs if v[1]]
        assert len(planning)==len(responses)+2 and len(dialogue.inputs)==len(planning)
        assert all(d["function"]["name"]!="deliver_results" for d in dialogue.inputs[0][1])
        await service.close()
    asyncio.run(run())


def test_cached_tools_reduce_model_rounds_but_execute_each_new_request(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue(load(), remote("search"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        assert (await collect(service, sid))[-1]["status"]=="COMPLETED"
        assert len(dialogue.inputs)==4
        assert {v["name"] for v in dialogue.contexts[0]["mcp_servers"]["items"]}=={"data", "compute"}
        dialogue.responses = [remote("search"), AIMessageChunk(content="Fresh result")]
        before = len(dialogue.inputs)
        values = await collect(service, sid, rid="fresh")
        assert values[-1]["status"]=="COMPLETED" and len(dialogue.inputs)-before==3
        assert len(backend.calls)==2 and backend.lists==["data"]
        assert len(backend.connections)==2 and "compute" not in backend.connections
        assert sum(d["function"]["name"].startswith("mcp_") for d in dialogue.inputs[before][1])==4
        assert dialogue.inputs[-1][1]==[]
        await service.close()
    asyncio.run(run())


def test_single_result_fallback_needs_no_selection_request(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), remote("search"), AIMessageChunk(content="INTERNAL"),
            AIMessageChunk(content="Final reply"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="COMPLETED" and len(result_cards(values))==1
        assert len(dialogue.inputs)==4 and dialogue.inputs[-1][1]==[]
        assert "".join(v["text"] for v in values if v["type"]=="message")=="Final reply"
        # Selected evidence occurs once; its previous tool message is just a reference.
        history = [json.loads(m.content) for m in dialogue.inputs[-1][0] if isinstance(m, ToolMessage)]
        assert any(set(value)=={"result_id"} for value in history)
        await service.close()
    asyncio.run(run())


def test_multiple_results_are_not_arbitrarily_selected_or_reexecuted(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), remote("search"), remote("preview", reference="a"),
            *[AIMessageChunk(content="INTERNAL") for _ in range(3)], AIMessageChunk(content="Delivery was not completed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="invalid_delivery"
        assert not result_cards(values) and len(backend.calls)==2 and len(dialogue.inputs)==6
        assert len(service.store.results("alice", sid, values[-1]["task_id"]))==2
        await service.close()
    asyncio.run(run())


def test_saved_evidence_is_not_a_new_mcp_execution(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue(load(), remote("search"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        card = result_cards(await collect(service, sid))[0]
        dialogue.responses = [action("read_result", result_id=card["result_id"])]
        values = await collect(service, sid, rid="read")
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="mcp_required"
        assert len(backend.calls)==1 and not result_cards(values)
        await service.close()
    asyncio.run(run())


def test_partial_mcp_failure_cannot_be_delivered_as_success(engine):
    async def run():
        backend = Backend()
        backend.catalog["compute"][0].annotations = {"idempotentHint": True}
        original = backend.client

        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            execute = client.call_tool

            async def call(name, arguments, **options):
                backend.protocol_error = name=="multiply"
                return await execute(name, arguments, **options)
            client.call_tool = call
            return client

        gateway = backend.gateway()
        gateway.client_factory = factory
        service = DatasetQA(engine, Dialogue(load(), remote("search"), load("compute"),
            remote("multiply", x=2, y=3), deliver()), gateway)
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="tool_failed"
        assert len(backend.calls)==2 and len(result_cards(values))==1
        assert len(service.store.results("alice", sid))==1
        await service.close()
    asyncio.run(run())


def test_priming_respects_config_identity_and_expiry():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        async with gateway.session() as tools:
            await tools.load("data")
        async with gateway.session() as tools:
            tools.prime("search")
            assert len(tools.definitions())==4 and not tools.clients
        gateway.servers["data"] = Server("different-target")
        async with gateway.session() as tools:
            tools.prime("search", [{"server": "data", "name": "search"}])
            assert not tools.definitions()
        gateway.servers["data"] = Server("data", "data service")
        gateway.limits = replace(gateway.limits, cache_seconds=0)
        async with gateway.session() as tools:
            tools.prime("search")
            assert not tools.definitions() and not tools.clients
    asyncio.run(run())


def test_summary_does_not_block_done_or_overwrite_new_memory(engine):
    async def run():
        entered, gate = asyncio.Event(), asyncio.Event()

        class Summarizing(Dialogue):
            async def summarize(self, previous, messages):
                entered.set()
                await gate.wait()
                return "Saved summary"

        dialogue = Summarizing(load(), remote("search"))
        service = DatasetQA(engine, dialogue, Backend().gateway())
        sid = session(service)
        for i in range(10):
            task, _ = service.store.submit("alice", sid, "seed"+str(i), {"message": "History"}, None, service.owner)
            service.store.finish("alice", sid, task["id"], "COMPLETED", message="Answer")
        values = await asyncio.wait_for(collect(service, sid), 2)
        assert values[-1]["status"]=="COMPLETED" and not gate.is_set()
        await asyncio.wait_for(entered.wait(), 2)
        dialogue.responses = [action("remember", values={"choice": "latest"}), remote("search")]
        newer = await collect(service, sid, rid="newer")
        version = newer[-1]["version"]
        gate.set()
        await asyncio.gather(*list(service.summaries.values()))
        saved = service.store.session("alice", sid)
        context = json.loads(saved["context"])
        assert context["memory"]["choice"]=="latest" and context["summary"]=="Saved summary"
        assert saved["version"]==version
        await service.close()
    asyncio.run(run())


def test_summary_commit_is_fenced_while_active_and_after_cursor_changes(engine):
    service = DatasetQA(engine, Dialogue(), Backend().gateway())
    sid = session(service)
    task, _ = service.store.submit("alice", sid, "active", {"message": "History"}, None, service.owner)
    assert not service.store.save_summary("alice", sid, 0, "Stale", 8)
    service.store.finish("alice", sid, task["id"], "COMPLETED")
    with service.store.transaction() as conn:
        conn.execute(update(service.store.sessions).where(service.store.sessions.c.id==sid).values(
            context=dumps({"memory": {"keep": True}, "summary_after": 9})))
    assert not service.store.save_summary("alice", sid, 0, "Stale", 8)
    assert service.store.save_summary("alice", sid, 9, "Current", 12)
    assert json.loads(service.store.session("alice", sid)["context"])["memory"]=={"keep": True}


def test_model_timeout_ends_the_request_without_dispatch_or_retry(engine):
    async def run():
        class Waiting(Dialogue):
            async def respond(self, *args):
                await asyncio.Event().wait()
                yield AIMessageChunk(content="Never")

        backend = Backend()
        service = DatasetQA(engine, Waiting(), backend.gateway(limits=Limits(model_timeout=0.03)))
        values = await asyncio.wait_for(collect(service, session(service)), 2)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="model_timeout"
        assert not backend.calls and not service.slots.locked()
        await service.close()
    asyncio.run(run())


def test_action_schema_preserves_local_refs_without_mutating_tool_schema():
    from jsonschema import Draft202012Validator, ValidationError
    schema = {"type": "object", "$defs": {"Row": {"type": "integer"}},
        "properties": {"row": {"$ref": "#/$defs/Row"}}, "required": ["row"]}
    tools = [{"type": "function", "function": {"name": "future_tool", "parameters": schema}}]
    definitions = []

    class Model:
        def bind_tools(self, values, **options):
            assert options=={"tool_choice": "required"}
            definitions.extend(values)
            return self

        async def astream(self, messages):
            yield AIMessageChunk(content="", tool_calls=[{"id": "ref", "name": "future_tool", "args": {"row": 1}}])

    async def run():
        dialogue = NativeDialogue(model=Model())
        return [chunk async for chunk in dialogue.respond(dialogue.messages("use the tool", {}), tools)]

    asyncio.run(run())
    definition, = definitions
    validator = Draft202012Validator(definition["function"]["parameters"])
    validator.validate({"row": 1})
    with pytest.raises(ValidationError):
        validator.validate({"row": "invalid"})
    assert schema["properties"]["row"]["$ref"]=="#/$defs/Row"


@pytest.mark.parametrize("premature,empty,malformed", [(False, False, False), (True, False, False),
    (False, True, False), (False, False, True)])
def test_real_sdk_and_mcp_complete_search_with_bounded_correction(engine, monkeypatch, premature, empty, malformed):
    import httpx
    from langchain_openai import ChatOpenAI
    from mcp_servers.corpus_mcp import mcp

    requests, upstream = [], []
    rows = [] if empty else [{"id": str(i), "title": "Dataset "+str(i)} for i in range(5)]

    def search(**arguments):
        upstream.append(arguments)
        return {"items": rows, "pagination": {"total": len(rows)}}

    monkeypatch.setattr("mcp_servers.corpus_mcp.list_dataset_details", search)

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        base = {"id": "request-"+str(len(requests)), "created": 0, "model": "qwen3.5-plus",
            "object": "chat.completion.chunk"}
        if body.get("tools"):
            assert body["tool_choice"]=="required"
            choices = {tool["function"]["name"]: tool["function"]["parameters"] for tool in body["tools"]}
            if malformed and len(requests)==1:
                action_args = {"name": "load_mcp_tools", "arguments": {}}
            elif premature and len(requests)==1:
                assert "deliver_results" not in choices
                action_args = {"name": "deliver_results", "arguments": {"result_ids": []}}
            elif len(requests)==1+int(premature)+int(malformed):
                if premature:
                    rejected = json.loads(body["messages"][-1]["content"])
                    assert rejected["error"]=="mcp_required" and rejected["executed"] is False
                if malformed:
                    feedback = json.loads(body["messages"][-1]["content"])["runtime_feedback"]
                    assert feedback["error"]=="invalid_tool_call"
                    assert all(not message.get("tool_calls") for message in body["messages"])
                name = next(name for name in choices if name.endswith("_search_corpus_datasets"))
                action_args = {"name": name, "arguments": {"query": "Chemistry"}}
            elif empty and len(requests)==2:
                ask = choices["request_input"]
                assert "missing" in ask["required"]
                action_args = {"name": "request_input", "arguments": {"question": "没有结果，是否更换领域？"}}
            else:
                saved = next(json.loads(m["content"]) for m in reversed(body["messages"])
                    if m["role"]=="tool" and "result_id" in json.loads(m["content"]))
                action_args = {"name": "deliver_results", "arguments": {"result_ids": [saved["result_id"]]}}
            deltas = [{"role": "assistant", "tool_calls": [{"index": 0, "id": base["id"],
                "type": "function", "function": {"name": action_args["name"],
                    "arguments": '{"server":' if malformed and len(requests)==1 else json.dumps(action_args["arguments"])}}]}]
            if action_args["name"].startswith("mcp_"):
                deltas[0]["tool_calls"][0]["index"] = 1
                deltas[0]["tool_calls"].insert(0, {"index": 0, "id": base["id"]+"-operations", "type": "function", "function": {
                    "name": "remember", "arguments": json.dumps({"operations": [{"id": "search", "description": "Find chemistry datasets", "direct": True}], "calls": ["search"]})}})
        else:
            deltas = [{"role": "assistant", "content": "No matching records."}] if empty else [
                {"role": "assistant", "content": "Retrieved "}, {"content": "five records."}]
        chunks = [{**base, "choices": [{"index": 0, "delta": delta,
            "finish_reason": ("tool_calls" if body.get("tools") else "stop") if i==len(deltas)-1 else None}]}
            for i, delta in enumerate(deltas)]
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
            text="".join("data: "+json.dumps(chunk)+"\n\n" for chunk in chunks)+"data: [DONE]\n\n")

    async def run():
        gateway = MCPGateway({"corpus": Server(mcp)})
        async with gateway.session() as tools:
            await tools.load("corpus")
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            model = ChatOpenAI(model="qwen3.5-plus", api_key="test", base_url="https://example.invalid/v1",
                http_async_client=client, max_retries=0, extra_body={"enable_thinking": False})
            service = DatasetQA(engine, NativeDialogue(model=model), gateway)
            values = await collect(service, session(service), message="Find chemistry datasets")
            assert values[-1]["status"]=="COMPLETED" and result_cards(values)[0]["data"]["items"]==rows
            assert "".join(v["text"] for v in values if v["type"]=="message")==(
                "No matching records." if empty else "Retrieved five records.")
            assert not any(v["type"]=="interaction" for v in values)
            assert upstream==[{"page_num": 1, "page_size": 5, "filters": {"keywords": "Chemistry"}}]
            assert len(requests)==2+int(premature)+int(malformed) and "tools" not in requests[-1] and "tool_choice" not in requests[-1]
            assert all(body["enable_thinking"] is False for body in requests)
            await service.close()
    asyncio.run(run())
