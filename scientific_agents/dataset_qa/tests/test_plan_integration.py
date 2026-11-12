"""Real SDK streaming and MCP transport; the model provider is deterministic."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from fastmcp import FastMCP
import httpx
from jsonschema import Draft202012Validator
from langchain_openai import ChatOpenAI
import pytest

from ..contracts import Server
from ..dialogue import Dialogue
from ..mcp import MCPGateway
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, load, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_planning import approve, specimen


@pytest.mark.parametrize("available", [True, False])
def test_real_protocol_plan_parallel_reads_acceptance_and_final_evidence(engine, available):
    mcp = FastMCP("Generic file data")
    calls, requests, activity = [], [], {"active": 0, "peak": 0}
    url = "https://example.invalid/observations.jsonl"
    annotations = {"readOnlyHint": True, "idempotentHint": True}

    @mcp.tool(annotations=annotations, meta={"piflow": {"qa": {"collection": "/items"}}})
    async def locate() -> dict:
        calls.append("locate")
        return {"items": [{"url": url}]}

    async def read(kind, location):
        assert location == url
        calls.append(kind)
        activity["active"] += 1
        activity["peak"] = max(activity["peak"], activity["active"])
        try:
            await asyncio.sleep(0.02)
            return {"schema": {"value": "number"}} if kind == "schema" else {
                "available": available, "rows": [{"value": 1}, {"value": 2}] if available else []}
        finally:
            activity["active"] -= 1

    @mcp.tool(annotations=annotations, meta={"piflow": {"qa": {
        "bind": {"location": ["/url"]}, "result": {"kind": "schema", "requires": [{"path": "/schema"}]}}}})
    async def describe_file(location: str) -> dict:
        return await read("schema", location)

    @mcp.tool(annotations=annotations, meta={"piflow": {"qa": {
        "bind": {"location": ["/url"]}, "result": {"kind": "records", "requires": [{"path": "/rows"}],
            "unavailable_when": [{"path": "/available", "test": "equals", "value": False}]}}}})
    async def read_records(location: str, size: int) -> dict:
        assert size == 2
        return await read("records", location)

    spec = {"outcomes": [{"key": "schema", "description": "文件字段结构", "kind": "schema"},
        {"key": "records", "description": "两条样例记录", "kind": "records", "constraints": ["最多两条"]}],
        "steps": [{"key": "locate", "tool": "locate"},
            {"key": "describe", "tool": "describe_file", "object": {"step": "locate", "path": "/items/0"}, "produces": ["schema"]},
            {"key": "read", "tool": "read_records", "arguments": {"size": 2},
                "object": {"step": "locate", "path": "/items/0"}, "produces": ["records"]}]}

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        schemas = {tool["function"]["name"]: tool["function"]["parameters"] for tool in body.get("tools", [])}
        if len(requests) == 1:
            assert "plan" not in schemas["remember"]["properties"]
            decisions = [("load_mcp_tools", {"server": "files"}), ("remember", {"planning": True})]
        elif len(requests) == 2:
            decisions = [("remember", {"plan": spec})]
        elif len(requests) == 3:
            assert not calls  # No business operation before coverage review.
            decisions = [("review_plan", {"revision": 1, "covered": ["schema", "records"]})]
        else:
            assert len(requests) == 4 and not schemas
            context = json.loads(body["messages"][1]["content"])
            statuses = {item["description"]: item["state"] for item in context["outcome_status"]}
            assert statuses == {"文件字段结构": "accepted", "两条样例记录": "accepted" if available else "unavailable"}
            decisions = []
        if decisions:
            for name, args in decisions:
                Draft202012Validator(schemas[name]).validate(args)
            delta = {"role": "assistant", "tool_calls": [{"index": index, "id": f"request-{len(requests)}-{index}",
                "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
                for index, (name, args) in enumerate(decisions)]}
        else:
            delta = {"role": "assistant", "content": "已提供字段结构和两条样例。" if available else "已提供字段结构；这个文件当前没有可展示的样例记录。"}
        chunk = {"id": f"request-{len(requests)}", "created": 0, "model": "qwen3.5-plus",
            "object": "chat.completion.chunk", "choices": [{"index": 0, "delta": delta,
                "finish_reason": "tool_calls" if decisions else "stop"}]}
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
            text="data: "+json.dumps(chunk)+"\n\ndata: [DONE]\n\n")

    class Conversation(Dialogue):
        async def summarize(self, summary, messages):
            return summary

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            model = ChatOpenAI(model="qwen3.5-plus", api_key="test", base_url="https://example.invalid/v1",
                http_async_client=client, max_retries=0, extra_body={"enable_thinking": False})
            service = DatasetQA(engine, Conversation(model=model), MCPGateway({"files": Server(mcp)}))
            try:
                values = await collect(service, session(service), "找到文件后，查看字段结构和两条样例")
                assert_completed(service, None, values[-1])
                assert calls[0] == "locate" and sorted(calls[1:]) == ["records", "schema"]
                assert activity["peak"] == 2 and activity["active"] == 0
                assert len(requests) == 4 and len(result_cards(values)) == 2
                assert all(set(card) == {"result_id", "view_type", "title", "data"} for card in result_cards(values))
                assert not any(value["type"] == "interaction" for value in values)
            finally:
                await service.close()
    asyncio.run(run())


def test_missing_pointer_replanning_reuses_finished_prerequisite(engine):
    async def run():
        backend = configured()
        incorrect = specimen()
        incorrect["steps"][2]["object"]["path"] = "/absent"
        def correct(messages, definitions):
            assert [call[1] for call in backend.calls] == ["search", "inspect"]
            return action("remember", plan=specimen())
        dialogue = BareDialogue(load(), action("remember", plan=incorrect), approve, correct, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找资源，查看第一个的详情，并采样三条")
            assert_completed(service, None, values[-1])
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample"]
            saved = payload(service, sid, values)
            assert saved["plan"]["revision"] == 2
            assert all(len(item["attempts"]) == 1 for item in saved["operations"])
        finally:
            await service.close()
    asyncio.run(run())


def test_plan_continuation_preserves_receipts_and_requires_new_review(engine):
    async def run():
        backend = configured()
        incorrect = specimen()
        incorrect["steps"][2]["object"]["path"] = "/absent"
        dialogue = BareDialogue(load(), action("remember", plan=incorrect), approve,
            action("request_input", missing="样例的操作对象", question="样例也使用第一个结果吗？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "找资源，查看第一个详情，再给我样例", "first")
            assert first[-1]["status"] == "WAITING_INPUT"
            dialogue.responses = [action("remember", continuation="continue", plan=specimen()), approve, text()]
            second = await collect(service, sid, "是，第一个结果，采样三条", "second")
            assert_completed(service, None, second[-1])
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample"]
            saved = payload(service, sid, second)
            assert saved["resume"] is True and saved["plan"]["reviewed"] == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_safe_failed_read_can_be_corrected_without_repeating_successes(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][3].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original_client, rejected = backend.client, [True]
        def client(*args, **kwargs):
            instance = original_client(*args, **kwargs)
            original_call = instance.call_tool
            async def call(name, arguments, **options):
                result = await original_call(name, arguments, **options)
                if name == "sample" and rejected[0]:
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="private-backend-trace")])
                return result
            instance.call_tool = call
            return instance
        backend.client = client
        def repair(messages, definitions):
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample"]
            rejected[0] = False
            revised = specimen()
            revised["steps"][2]["arguments"]["count"] = 2
            revised["outcomes"][1]["description"] = "private-backend-trace"
            return action("remember", plan=revised)
        def final(messages, definitions):
            assert not definitions
            assert "private-backend-trace" not in json.dumps([m.content for m in messages])
            return text("已提供详情与两条样例。")
        dialogue = BareDialogue(load(), action("remember", plan=specimen()), approve, repair, approve, final)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找资源，查看第一个详情，再给最多三条样例")
            assert_completed(service, None, values[-1])
            assert [call[1] for call in backend.calls] == ["search", "inspect", "sample", "sample"]
            saved = payload(service, sid, values)
            assert [len(item["attempts"]) for item in saved["operations"]] == [1, 1, 2]
            assert saved["operations"][-1]["state"] == "succeeded"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("revise_blocked_child", [False, True])
def test_corrected_prerequisite_resumes_dependent_plan_steps(engine, revise_blocked_child):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original_client = backend.client
        def client(*args, **kwargs):
            instance = original_client(*args, **kwargs)
            original_call = instance.call_tool
            async def call(name, arguments, **options):
                result = await original_call(name, arguments, **options)
                if name == "search" and len(backend.calls) == 1:
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="invalid upstream query")])
                return result
            instance.call_tool = call
            return instance
        backend.client = client
        def repair(messages, definitions):
            assert [call[1] for call in backend.calls] == ["search"]
            revised = specimen()
            revised["steps"][0]["arguments"]["query"] = "corrected query"
            if revise_blocked_child:
                revised["steps"][2]["arguments"]["count"] = 2
            return action("remember", plan=revised)
        dialogue = BareDialogue(load(), action("remember", plan=specimen()), approve, repair, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            values = await collect(service, sid, "查找资源，获取详情和最多三条样例")
            assert_completed(service, None, values[-1])
            assert [call[1] for call in backend.calls] == ["search", "search", "inspect", "sample"]
            assert backend.calls[-1][2] == {"reference": "a", "count": 2 if revise_blocked_child else 3}
            saved = payload(service, sid, values)
            assert [len(operation["attempts"]) for operation in saved["operations"]] == [2, 1, 1]
            assert all(operation["state"] == "succeeded" for operation in saved["operations"])
            assert all("unavailable_dependency" not in operation for operation in saved["operations"])
            assert {value["state"] for value in saved["plan"]["acceptance"].values()} == {"accepted"}
            assert len(result_cards(values)) == 2 and len(dialogue.inputs) == 6
        finally:
            await service.close()
    asyncio.run(run())


def test_incomplete_content_cannot_be_promoted_by_transport_success_or_delivery_retry(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][3].meta["piflow"]["qa"]["result"] = {
            "kind": "sample", "requires": [{"path": "/artifact_url"}]}
        dialogue = BareDialogue(load(), action("remember", plan=specimen()), approve,
            action("deliver_results"), action("deliver_results"), action("deliver_results"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "查看详情并生成样例文件")
            assert values[-1]["status"] == "COMPLETED" and values[-1]["outcome"] == "partial"
            assert len(backend.calls) == 3
            saved = payload(service, sid, values)
            assert saved["plan"]["acceptance"]["records"]["state"] == "incomplete"
            message = "".join(value["text"] for value in values if value["type"] == "message")
            assert message and "invalid_delivery" not in message and "op1" not in message
        finally:
            await service.close()
    asyncio.run(run())


def test_revising_one_shared_read_does_not_retarget_its_other_consumer(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][1].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original = specimen()
        original["outcomes"][1].update(kind="inspect", description="第二个对象详情", constraints=[])
        original["steps"][2] = {**original["steps"][1], "key": "other", "produces": ["records"]}
        corrected = deepcopy(original)
        corrected["steps"][2]["object"] = {"step": "find", "path": "/items/1"}
        dialogue = BareDialogue(load(), action("remember", plan=original), action("remember", plan=corrected), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "查找资源，再查看第一和第二个的详情")
            assert_completed(service, None, values[-1])
            assert backend.calls == [("data", "search", {"query": "资源"}),
                ("data", "inspect", {"reference": "a"}), ("data", "inspect", {"reference": "b"})]
        finally:
            await service.close()
    asyncio.run(run())
