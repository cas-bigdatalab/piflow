"""Public replies stay useful while private failure receipts remain truthful."""
import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest

from ..contracts import Limits, QAError, Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from .assertions import assert_handled
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_operations import batch, goal, saved
from .test_runtime import RawDialogue


DIAGNOSTIC = (
    "PRIVATE_UPSTREAM_DIAGNOSTIC_73: unsupported partition; "
    "Traceback at /srv/private/catalogue.py:91; "
    "endpoint=https://internal.invalid/query?authorization=secret-test-token"
)


def with_fault(backend, rejects):
    """Keep real dispatch counts, then supply a protocol-level tool rejection."""
    original = backend.client

    def client(*args, **kwargs):
        connection = original(*args, **kwargs)
        execute = connection.call_tool

        async def call(name, arguments, **options):
            result = await execute(name, arguments, **options)
            if rejects(name, arguments):
                return SimpleNamespace(is_error=True,
                    content=[SimpleNamespace(type="text", text=DIAGNOSTIC)])
            return result

        connection.call_tool = call
        return connection

    gateway = backend.gateway()
    gateway.client_factory = client
    return gateway


def assert_no_diagnostics(value):
    text = json.dumps(value, ensure_ascii=False, default=str)
    for private in ("PRIVATE_UPSTREAM_DIAGNOSTIC_73", "/srv/private/catalogue.py",
                    "internal.invalid", "secret-test-token", "Traceback"):
        assert private not in text


async def assert_public_history_and_replay(service, sid, events, request):
    text = "".join(event.get("text", "") for event in events if event["type"]=="message")
    assert text.strip()
    assert_no_diagnostics(events)
    history = await service.get_session("alice", sid)
    assert_no_diagnostics(history)
    assistant = [item["payload"]["text"] for item in history["items"]
        if item["item_type"]=="ASSISTANT_MESSAGE"]
    assert assistant==[text]
    assert await collect(service, sid, request)==events
    return history


@pytest.mark.parametrize("partial", [False, True])
def test_tool_rejection_has_friendly_content_without_an_extra_model_or_mcp_call(engine, partial):
    async def run():
        backend = Backend()
        gateway = with_fault(backend, lambda name, args: name=="sample")
        calls = [remote("search"), remote("sample", reference="a", count=1)] if partial else [
            remote("sample", reference="a", count=1)]
        names = ["find", "sample"] if partial else ["sample"]
        dialogue = RawDialogue(load(), batch(names, *calls, operations=[goal(name) for name in names]))
        service = DatasetQA(engine, dialogue, gateway)
        sid, request = session(service), "请获取数据集 A 的样本，并保留已取得的信息。"
        try:
            events = await collect(service, sid, request)
            task = assert_handled(service, sid, events[-1], "tool_failed")
            assert events[-1]["outcome"]==("partial" if partial else "unavailable")
            assert len(dialogue.inputs)==2 and all(definitions for _, definitions in dialogue.inputs)
            assert len(backend.calls)==len(calls)
            assert len(result_cards(events))==int(partial)
            payload = json.loads(task["payload"])
            assert payload["operations"][-1]["state"]=="failed"
            assert payload["operations"][-1]["attempts"][-1]["error"]["detail"]==[DIAGNOSTIC]
            history = await assert_public_history_and_replay(service, sid, events, request)
            assert history["tasks"][0]["status"]=="COMPLETED"
            assert history["tasks"][0]["outcome"]==events[-1]["outcome"]
            assert len(dialogue.inputs)==2 and len(backend.calls)==len(calls)
        finally:
            await service.close()

    asyncio.run(run())


@pytest.mark.parametrize("limited", [False, True])
def test_final_model_sees_verified_evidence_without_past_rejection_diagnostics(engine, limited):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        gateway = with_fault(backend, lambda name, args: args.get("query")=="first")
        if limited:
            gateway.limits = Limits(max_rounds=3)
        inspected = []

        def corrected(messages, definitions):
            # Internal correction still receives actionable error information.
            assert any(DIAGNOSTIC in message.content for message in messages if isinstance(message, ToolMessage))
            return remote("search", query="corrected")(messages, definitions)

        def final(messages, definitions):
            assert definitions==[]
            assert_no_diagnostics([message.model_dump(mode="json") for message in messages])
            assert not any(isinstance(message, ToolMessage) or getattr(message, "tool_calls", None) for message in messages)
            context = json.loads(messages[1].content)
            assert all("error" not in row and "capability" not in row
                for row in context["operations"]["items"])
            envelope = json.loads(messages[-1].content)
            assert envelope["delivery_manifest"] and envelope["final_delivery"]
            assert "气象观测" in json.dumps(envelope, ensure_ascii=False)
            inspected.append(envelope)
            return AIMessageChunk(content="已取得候选数据集，请查看下方结果。")

        responses = [load(), remote("search", query="first"), corrected]
        if not limited:
            responses.append(action("deliver_results"))
        dialogue = RawDialogue(*responses, final)
        service = DatasetQA(engine, dialogue, gateway)
        sid, request = session(service), "请查找可用的数据集候选。"
        try:
            events = await collect(service, sid, request)
            if limited:
                assert_handled(service, sid, events[-1], "step_limit")
                assert events[-1]["outcome"]=="partial"
            else:
                assert events[-1]["status"]=="COMPLETED" and "outcome" not in events[-1]
                assert service.store.task("alice", sid, events[-1]["task_id"])["status"]=="COMPLETED"
            assert len(inspected)==1 and len(backend.calls)==2
            assert len(dialogue.inputs)==(4 if limited else 5)
            payload = saved(service, sid, events[-1]["task_id"])
            assert [attempt["state"] for attempt in payload["operations"][0]["attempts"]]==["failed", "succeeded"]
            assert payload["operations"][0]["attempts"][0]["error"]["detail"]==[DIAGNOSTIC]
            await assert_public_history_and_replay(service, sid, events, request)
            assert len(backend.calls)==2
        finally:
            await service.close()

    asyncio.run(run())


def test_real_mcp_tool_error_is_private_and_closes_with_a_reply(engine):
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError

    async def run():
        mcp, calls = FastMCP("private-diagnostic-regression"), []

        @mcp.tool()
        async def query_records() -> dict:
            calls.append("query_records")
            raise ToolError(DIAGNOSTIC)

        dialogue = RawDialogue(load("local"), remote("query_records"))
        service = DatasetQA(engine, dialogue, MCPGateway({"local": Server(mcp)}))
        sid, request = session(service), "请查询可用的记录。"
        try:
            events = await collect(service, sid, request)
            task = assert_handled(service, sid, events[-1], "tool_failed")
            assert events[-1]["outcome"]=="unavailable" and not result_cards(events)
            assert calls==["query_records"] and len(dialogue.inputs)==2
            payload = json.loads(task["payload"])
            assert DIAGNOSTIC in json.dumps(payload["operations"], ensure_ascii=False)
            await assert_public_history_and_replay(service, sid, events, request)
            assert calls==["query_records"] and len(dialogue.inputs)==2
        finally:
            await service.close()

    asyncio.run(run())


@pytest.mark.parametrize("paged", [False, True])
def test_final_writer_keeps_focused_evidence_beyond_default_preview_and_drops_read_errors(engine, paged):
    async def run():
        backend = Backend()
        backend.items = [{"id": str(index), "title": "Candidate "+str(index),
            "description": "Record description. "*90} for index in range(200)]
        fact = "DISTANT_VERIFIED_FACT_9288"
        backend.items[-1]["provenance_code"] = fact
        selected_path = "/items" if paged else "/items/199/provenance_code"
        private_path = "/PRIVATE_READ_SELECTOR_008"
        verified = []

        def read_at(path):
            def request(messages, definitions):
                rid = next(json.loads(message.content)["result_id"] for message in reversed(messages)
                    if isinstance(message, ToolMessage) and "result_id" in json.loads(message.content))
                return action("read_result", result_id=rid, path=path,
                    offset=199 if paged and path==selected_path else 0, limit=1)
            return request

        def deliver(messages, definitions):
            assert any(fact in str(message.content) for message in messages)
            assert any("PRIVATE_READ_ERROR_008" in str(message.content) for message in messages)
            return action("deliver_results")

        def final(messages, definitions):
            assert definitions==[]
            encoded = json.dumps([message.model_dump(mode="json") for message in messages], ensure_ascii=False)
            assert fact in encoded
            assert "PRIVATE_READ_ERROR_008" not in encoded and private_path not in encoded
            assert_no_diagnostics(encoded)
            assert not any(isinstance(message, ToolMessage) or getattr(message, "tool_calls", None)
                for message in messages)
            # The generic preview really omits this fact: the targeted read,
            # rather than a larger default preview, must reach the answer writer.
            envelope = json.loads(messages[-1].content)
            assert fact not in json.dumps(envelope, ensure_ascii=False)
            focused = [json.loads(message.content)["focused_evidence"] for message in messages
                if isinstance(message.content, str) and message.content.startswith('{"focused_evidence":')]
            assert focused and any(item["path"]==selected_path and fact in json.dumps(item, ensure_ascii=False)
                for item in focused)
            verified.append(True)
            return AIMessageChunk(content="最后一条记录的 provenance_code 是 "+fact+"。")

        dialogue = RawDialogue(load(), batch(["find"], remote("search"),
            operations=[goal("find", output="answer")]), read_at(private_path), read_at(selected_path), deliver, final)
        service = DatasetQA(engine, dialogue, backend.gateway())
        builtin = service._builtin

        async def checked_builtin(user, sid, tid, name, arguments, tools, context, payload):
            if name=="read_result" and arguments.get("path")==private_path:
                raise QAError("invalid_pointer", "PRIVATE_READ_ERROR_008", detail=[DIAGNOSTIC])
            return await builtin(user, sid, tid, name, arguments, tools, context, payload)

        service._builtin = checked_builtin
        sid, request = session(service), "请查询记录，告诉我最后一条记录的 provenance_code。"
        try:
            events = await collect(service, sid, request)
            assert events[-1]["status"]=="COMPLETED" and "outcome" not in events[-1]
            assert verified==[True] and len(backend.calls)==1
            assert len(dialogue.inputs)==6
            await assert_public_history_and_replay(service, sid, events, request)
        finally:
            await service.close()

    asyncio.run(run())


def test_recovery_clarification_does_not_publish_planner_diagnostics_or_store_them_as_memory(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        gateway = with_fault(backend, lambda name, args: args.get("query")=="first")

        def clarify(messages, definitions):
            assert any(DIAGNOSTIC in message.content for message in messages if isinstance(message, ToolMessage))
            memory = action("remember", operations=[goal("find"), goal("next", description=DIAGNOSTIC)],
                calls=[], values={"private_notes": DIAGNOSTIC, "preferred_format": DIAGNOSTIC})
            question = action("request_input", missing="请选择后续处理的数据集和所需内容。",
                question=DIAGNOSTIC, options=[{"label": DIAGNOSTIC, "value": DIAGNOSTIC}])
            return AIMessageChunk(content="", tool_calls=[*memory.tool_calls, *question.tool_calls])

        dialogue = RawDialogue(load(), batch(["find"], remote("search", query="first"),
            operations=[goal("find")], values={"preferred_format": "csv"}), clarify)
        service = DatasetQA(engine, dialogue, gateway)
        sid, request = session(service), "请检索数据集，再确认后续处理对象。"
        try:
            events = await collect(service, sid, request)
            assert events[-1]["status"]=="WAITING_INPUT"
            assert_no_diagnostics(events)
            interaction, = [event for event in events if event["type"]=="interaction"]
            assert interaction["question"].strip() and not interaction.get("options")
            history = await service.get_session("alice", sid)
            assert_no_diagnostics(history)
            context = json.loads(service.store.session("alice", sid)["context"])
            assert context["memory"]["preferred_format"]=="csv" and "private_notes" not in context["memory"]
            assert_no_diagnostics(context)
            payload = saved(service, sid, events[-1]["task_id"])
            assert payload["operations"][0]["attempts"][0]["error"]["detail"]==[DIAGNOSTIC]
            assert payload["diagnostics_exposed"] is True
            assert await collect(service, sid, request)==events
            assert len(backend.calls)==1 and len(dialogue.inputs)==3
        finally:
            await service.close()

    asyncio.run(run())


def test_recovery_goal_labels_and_memory_cannot_reintroduce_private_details_into_final_reply(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        gateway = with_fault(backend, lambda name, args: args.get("query")=="first")
        gateway.limits = Limits(max_rounds=3)
        checked = []

        def recover(messages, definitions):
            assert any(DIAGNOSTIC in message.content for message in messages if isinstance(message, ToolMessage))
            return batch(["find"], remote("search", query="corrected"),
                operations=[goal("find"), goal("next", description=DIAGNOSTIC, output="answer")],
                values={"private_notes": DIAGNOSTIC, "preferred_format": DIAGNOSTIC})(messages, definitions)

        def final(messages, definitions):
            assert definitions==[]
            assert_no_diagnostics([message.model_dump(mode="json") for message in messages])
            context = json.loads(messages[1].content)
            assert context["memory"]["preferred_format"]=="csv" and "private_notes" not in context["memory"]
            rows = context["operations"]["items"]
            assert rows[0]["description"]=="操作 find" and rows[1]["description"]!=DIAGNOSTIC
            assert [row["state"] for row in rows]==["succeeded", "pending"]
            checked.append(True)
            return AIMessageChunk(content="候选数据集已保留，可继续选择后续处理内容。")

        dialogue = RawDialogue(load(), batch(["find"], remote("search", query="first"),
            operations=[goal("find")], values={"preferred_format": "csv"}), recover, final)
        service = DatasetQA(engine, dialogue, gateway)
        sid, request = session(service), "请查找候选数据集，并准备后续处理。"
        try:
            events = await collect(service, sid, request)
            assert_handled(service, sid, events[-1], "step_limit")
            assert checked==[True] and len(result_cards(events))==1
            await assert_public_history_and_replay(service, sid, events, request)
            context = json.loads(service.store.session("alice", sid)["context"])
            assert_no_diagnostics(context)
            assert context["memory"]["preferred_format"]=="csv"
            payload = saved(service, sid, events[-1]["task_id"])
            assert payload["operations"][0]["attempts"][0]["error"]["detail"]==[DIAGNOSTIC]
            assert len(backend.calls)==2 and len(dialogue.inputs)==4
        finally:
            await service.close()

    asyncio.run(run())


def test_final_context_answer_excludes_the_recovery_planners_free_text_reason(engine):
    async def run():
        backend = Backend()
        backend.catalog["offline"] = []
        gateway = backend.gateway()
        original = backend.client

        def unavailable_catalogue(target, **kwargs):
            connection = original(target, **kwargs)
            if target=="offline":
                async def list_tools():
                    raise RuntimeError(DIAGNOSTIC)
                connection.list_tools = list_tools
            return connection

        gateway.client_factory = unavailable_catalogue
        checked = []

        def final(messages, definitions):
            assert definitions==[]
            assert_no_diagnostics([message.model_dump(mode="json") for message in messages])
            context = json.loads(messages[1].content)
            assert context["response_basis"]["executed"] is False
            assert "reason" not in context["response_basis"]
            checked.append(True)
            return AIMessageChunk(content="您可以说明要查找的数据集主题。")

        dialogue = RawDialogue(load("offline"),
            action("respond_from_context", mode="conversation", reason=DIAGNOSTIC), final)
        service = DatasetQA(engine, dialogue, gateway)
        sid, request = session(service), "接下来我可以提供什么信息？"
        try:
            events = await collect(service, sid, request)
            assert events[-1]["status"]=="COMPLETED" and "outcome" not in events[-1]
            assert checked==[True] and not backend.calls
            assert saved(service, sid, events[-1]["task_id"])["diagnostics_exposed"] is True
            await assert_public_history_and_replay(service, sid, events, request)
        finally:
            await service.close()

    asyncio.run(run())
