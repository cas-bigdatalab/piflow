"""Terminal failures close only affected work; bookkeeping cannot hide their cause."""
import asyncio
from types import SimpleNamespace

import pytest

from ..contracts import QAError
from ..operations import Operations
from ..responses import notice
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload
from .test_planning import approve, specimen
from .test_operations import batch, goal
from .test_runtime import RawDialogue


def blocked_gateway(backend):
    backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
    original = backend.client
    def client(*args, **kwargs):
        connection = original(*args, **kwargs)
        execute = connection.call_tool
        async def call(name, arguments, **options):
            result = await execute(name, arguments, **options)
            if name == "search" and arguments.get("query") == "资源":
                return SimpleNamespace(is_error=True, content=[], meta={"piflow": {
                    "error_code": "artifact_unavailable", "phase": "prepare"}})
            return result
        connection.call_tool = call
        return connection
    gateway = backend.gateway()
    gateway.client_factory = client
    return gateway


@pytest.mark.parametrize("independent", [False, True])
def test_plan_blocked_prerequisite_closes_without_model_replanning(engine, independent):
    async def run():
        backend = configured()
        spec = specimen()
        if independent:
            spec["outcomes"].append({"key": "other", "description": "另一项查询", "kind": "search"})
            spec["steps"].append({"key": "other", "tool": "search", "arguments": {"query": "独立请求"}, "produces": ["other"]})
        dialogue = BareDialogue(load(), action("remember", plan=spec), approve)
        service = DatasetQA(engine, dialogue, blocked_gateway(backend))
        try:
            sid = session(service)
            events = await collect(service, sid, "查询后查看详情和样例，并处理独立请求")
            saved = payload(service, sid, events)
            assert len(dialogue.inputs) == 3
            assert len(backend.calls) == 1 + int(independent)
            assert not any(name in {"inspect", "sample"} for _, name, _ in backend.calls)
            assert saved["error"]["error_code"] == "artifact_unavailable"
            assert saved["operations"][1]["unavailable_dependency"] == saved["operations"][0]["id"]
            assert saved["operations"][1]["attempts"] == []
            assert len(result_cards(events)) == int(independent)
            assert events[-1]["outcome"] == ("partial" if independent else "unavailable")
            text = "".join(e.get("text", "") for e in events if e["type"] == "message")
            assert "文件尚未准备好" in text and "确认操作对象" not in text
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("decision", ["malformed", "repeat", "plan", "goals"])
def test_unplanned_failure_gets_one_scope_decision_not_repeated_replanning(engine, decision):
    async def run():
        backend = configured()
        followup = (action("remember", invalid_field=True) if decision == "malformed" else
            action("remember", plan=specimen()) if decision == "plan" else
            action("remember", goals=[{"description": "查询结果", "tool": "search"}]) if decision == "goals" else
            remote("search", query="资源"))
        dialogue = BareDialogue(load(), remote("search", query="资源"), followup)
        service = DatasetQA(engine, dialogue, blocked_gateway(backend))
        try:
            sid = session(service)
            events = await collect(service, sid, "查询资源后查看详情和样例")
            saved = payload(service, sid, events)
            assert len(backend.calls) == 1 and len(dialogue.inputs) == 3
            assert saved["error"]["error_code"] == "artifact_unavailable"
            assert not result_cards(events)
            text = "".join(e.get("text", "") for e in events if e["type"] == "message")
            assert "文件尚未准备好" in text
            assert "查询资源后查看详情和样例" not in text and "。。" not in text
        finally:
            await service.close()
    asyncio.run(run())


def test_react_independent_call_can_complete_after_an_unplanned_blocker(engine):
    async def run():
        backend = configured()
        discover = load()
        discover.tool_calls.append({"name": "load_mcp_tools", "args": {"server": "compute"}, "id": "load-compute"})
        dialogue = BareDialogue(discover, remote("search", query="资源"), remote("multiply", x=2, y=3))
        service = DatasetQA(engine, dialogue, blocked_gateway(backend))
        try:
            sid = session(service)
            events = await collect(service, sid, "执行两项独立查询")
            assert len(backend.calls) == 2 and len(dialogue.inputs) == 3
            assert len(result_cards(events)) == 1
            assert payload(service, sid, events)["error"]["error_code"] == "artifact_unavailable"
        finally:
            await service.close()
    asyncio.run(run())


def test_known_independent_goals_are_not_limited_by_unplanned_scope_review(engine):
    async def run():
        backend = configured()
        discover = load()
        discover.tool_calls.append({"name": "load_mcp_tools", "args": {"server": "compute"}, "id": "load-compute"})
        dialogue = RawDialogue(discover,
            batch(["first"], remote("search", query="资源"), operations=[goal("first"), goal("other")]),
            batch(["other"], remote("multiply", x=2, y=3)))
        service = DatasetQA(engine, dialogue, blocked_gateway(backend))
        try:
            sid = session(service)
            events = await collect(service, sid, "执行查询和独立计算")
            assert len(backend.calls) == 2 and len(dialogue.inputs) == 3
            assert len(result_cards(events)) == 1
            assert payload(service, sid, events)["error"]["error_code"] == "artifact_unavailable"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("code", ["invalid_parameters", "invalid_pointer", "result_not_found", "invalid_tool_call", "invalid_delivery"])
def test_final_bookkeeping_error_does_not_replace_causal_failure(code):
    ops = Operations()
    parent = ops.register("查询", {"server": "s", "name": "q"}, required=False)
    child = ops.register("文件", {"server": "s", "name": "e"})
    ops.start(parent, "attempt")
    ops.finish(parent, "attempt", error=QAError("artifact_unavailable", "private", 503))
    ops.get(child).update(state="unavailable", unavailable_dependency=parent)
    assert ops.resolve_error(QAError(code, "later")).code == "artifact_unavailable"
    assert ops.error().code == "artifact_unavailable"
    ops.get(parent)["state"] = ops.get(child)["state"] = "succeeded"
    assert ops.resolve_error(QAError(code, "later")).code == code


def test_read_only_annotation_cannot_make_configuration_failure_retryable():
    ops = Operations()
    first = ops.register("查询", {"server": "s", "name": "q"})
    ops.start(first, "one", retry_safe=True, invocation="same")
    ops.finish(first, "one", error=QAError("artifact_unavailable", "private", 503))
    for key in (first, ops.register("新的登记", {"server": "s", "name": "other"})):
        with pytest.raises(QAError) as raised:
            ops.start(key, "again", retry_safe=True, invocation="same")
        assert raised.value.code == "artifact_unavailable"


def test_internal_validation_feedback_is_not_a_user_clarification():
    for code in ("invalid_parameters", "invalid_pointer", "result_not_found", "invalid_tool_call"):
        text = notice(QAError(code, "PRIVATE"))
        assert "确认操作对象" not in text and "PRIVATE" not in text
