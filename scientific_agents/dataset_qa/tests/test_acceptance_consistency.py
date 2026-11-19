"""Identical receipts have identical content acceptance across execution modes."""
import asyncio
from copy import deepcopy

import pytest

from ..contracts import QAError
from ..capabilities import TASK
from ..execution import Execution
from ..operations import Operations
from ..planning import Check, Plan, ResultContract, require_delivery
from ..responses import compact_delivery_status, delivery_status, delivery_summary, notice
from ..search import SearchProfile, SearchRun
from ..service import DatasetQA
from .assertions import assert_handled
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, payload
from .test_planning import approve


def receipt(contract, data, *, acceptance=True):
    operations = Operations()
    key = operations.register("读取文件结构", {"server": "records", "name": "schema"}, planned=True)
    operations.start(key, "call", invocation="same-input")
    operations.finish(key, "call", result_id="result", acceptance=contract.assess(data) if acceptance else None)
    return operations, key


@pytest.mark.parametrize("data,expected", [
    ({"schema": {}}, "accepted"),
    ({"previewable": False}, "unavailable"),
    ({"schema": None}, "incomplete"),
    ({"records": []}, "incomplete"),
])
def test_native_and_planned_delivery_share_content_acceptance(data, expected):
    contract = ResultContract(kind="schema", requires=[Check(path="/schema")],
        unavailable_when=[Check(path="/previewable", test="equals", value=False)])
    operations, key = receipt(contract, data)
    plan = Plan.model_validate({"outcomes": [{"key": "schema", "description": "读取文件结构", "kind": "schema"}],
        "steps": [{"key": "read", "tool": "schema", "produces": ["schema"]}]})
    saved = {"spec": plan.model_dump(), "operations": {"read": key},
        "contracts": {"read": contract.model_dump()}, "revision": 1, "reviewed": 1}
    cards = [{"result_id": "result", "data": data}]
    assert operations.assessment(operations.get(key)) == expected
    if expected == "incomplete":
        with pytest.raises(QAError, match="成果"):
            operations.validate_delivery(["result"])
        with pytest.raises(QAError, match="成果"):
            require_delivery(saved, operations, cards)
        assert operations.error(["result"]).code == "invalid_delivery"
    else:
        operations.validate_delivery(["result"])
        require_delivery(saved, operations, cards)
        assert operations.error(["result"]) is None
    operations.validate_delivery(["result"], partial=True)
    facts = delivery_status(operations, ["result"])
    assert facts[0]["complete"] is (expected == "accepted")
    assert facts[0]["delivered"] is (expected != "unavailable")
    if expected == "unavailable":
        assert "已取得部分信息" not in operations.notice(["result"])


def test_incomplete_receipt_reuse_preserves_evidence_without_claiming_completion():
    contract = ResultContract(kind="records", requires=[Check(path="/records")])
    operations, owner = receipt(contract, {"rows": [1]})
    copied = deepcopy(operations.get(owner)["attempts"][0])
    target = operations.register("另一个引用下的相同请求", {"server": "records", "name": "schema"}, planned=True)
    operations.reuse(target, "reused", copied)
    assert operations.assessment(operations.get(target)) == "incomplete"
    with pytest.raises(QAError):
        operations.validate_delivery(["result"])
    assert operations.delivery_ids(partial=True) == ["result"]
    assert all(row["acceptance"] == "incomplete" for row in operations.view()["items"])


def test_legacy_receipt_and_valid_empty_result_remain_accepted():
    contract = ResultContract(kind="records", requires=[Check(path="/records")])
    for data, explicit in [({"records": []}, True), ({"legacy_rows": []}, False)]:
        operations, key = receipt(contract, data, acceptance=explicit)
        operations.validate_delivery(["result"])
        assert operations.assessment(operations.get(key)) == "accepted"
        assert delivery_status(operations, ["result"])[0]["complete"]


def test_protected_delivery_projection_keeps_every_whole_goal_and_label():
    operations = Operations()
    for index in range(16):
        key = operations.register("完整需求" * 45 + f"，目标文件{index}",
            {"server": "records", "name": f"read-{index}"}, planned=True)
        operations.start(key, str(index))
        operations.finish(key, str(index), result_id=f"result-{index}",
            acceptance="incomplete" if index % 2 else "accepted")
    facts = delivery_status(operations, operations.delivery_ids())
    compact = compact_delivery_status(facts)
    assert len(compact) == 16
    assert [row["description"] for row in compact] == [row["description"] for row in facts]
    assert [row["goal"] for row in compact] == [row["id"] for row in operations.required]
    assert [row["state"] for row in compact] == ["partial" if i % 2 else "provided" for i in range(16)]
    summary = delivery_summary(facts)
    assert "目标文件0" in summary and "目标文件15" in summary
    assert "已取得部分参考信息" in summary


@pytest.mark.parametrize("code", ["no_progress", "step_limit", "context_too_large", "invalid_delivery"])
def test_runtime_limits_do_not_invent_missing_user_requirements(code):
    response = notice(QAError(code, "private technical diagnosis"))
    assert "要求仍保留" in response
    assert not any(value in response for value in ("缩小", "补充", "指定优先", "private", "错误", "失败"))


@pytest.mark.parametrize("planned", [False, True])
def test_incomplete_content_closes_with_saved_evidence_and_one_business_call(engine, planned):
    async def run():
        backend = Backend()
        tool = backend.catalog["data"][1]
        tool.inputSchema.update(properties={}, required=[])
        tool.meta = {"piflow": {"qa": {"atomic": True, "label": "字段结构",
            "result": {"kind": "schema", "requires": [{"path": "/schema"}]}}}}
        backend.catalog = {"data": [tool]}
        script = [action("remember", plan={"steps": [{"key": "inspect", "tool": "inspect"}]}), approve] if planned else [
            remote("inspect", **{TASK: {"complete_request": True}})]
        # No final model response is supplied: partial facts have a deterministic
        # closure, so neither a bookkeeping repair nor another tool call is needed.
        dialogue = BareDialogue(load(), *script)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "查看字段结构")
            assert_handled(service, sid, events[-1], "invalid_delivery")
            assert backend.calls == [("data", "inspect", {})]
            assert len(dialogue.inputs) == (3 if planned else 2)
            card, = result_cards(events)
            ledger = payload(service, sid, events)
            operation, = ledger["operations"]
            assert operation["state"] == "succeeded"
            assert operation["attempts"][0]["acceptance"] == "incomplete"
            assert ledger["delivery"] == [card["result_id"]]
            answer = "".join(event.get("text", "") for event in events if event["type"] == "message")
            assert "字段结构" in answer and "部分" in answer
            assert not any(word in answer for word in ("错误", "失败", "schema", "invalid_delivery"))
        finally:
            await service.close()
    asyncio.run(run())


def test_partial_fast_delivery_waits_for_other_search_policy_to_finish(engine):
    async def run():
        service = DatasetQA(engine, BareDialogue(), Backend().gateway())
        try:
            execution = Execution()
            operation = execution.operations.register("字段结构", {"server": "records", "name": "schema"}, planned=True)
            execution.operations.start(operation, "schema-call")
            execution.operations.finish(operation, "schema-call", result_id="schema-result", acceptance="incomplete")
            search = execution.operations.register("候选数据", {"server": "records", "name": "search"}, planned=True)
            execution.operations.start(search, "search-call")
            execution.operations.finish(search, "search-call", result_id="search-result", acceptance="accepted")
            execution.operations.get(search)["search"] = SearchRun.create(SearchProfile(query="query"),
                {"query": "observation"}, ["observation"]).state
            saved = {}
            assert not await service._fast_delivery("alice", session(service), "unused", saved, execution, {})
            assert "delivery" not in saved
            assert not service.dialogue.inputs
        finally:
            await service.close()
    asyncio.run(run())


def test_plan_hard_checks_keep_valid_receipt_as_partial_content(engine):
    async def run():
        backend = Backend()
        tool = backend.catalog["data"][1]
        tool.inputSchema.update(properties={}, required=[])
        tool.meta = {"piflow": {"qa": {"atomic": True, "label": "非空内容",
            "result": {"kind": "inspect", "requires": [{"path": "/size"}]}}}}
        backend.catalog = {"data": [tool]}
        plan = {"outcomes": [{"key": "content", "description": "非空内容", "kind": "inspect",
                "checks": [{"path": "/size", "test": "at_least", "value": 1}]}],
            "steps": [{"key": "inspect", "tool": "inspect", "produces": ["content"]}]}
        dialogue = BareDialogue(load(), action("remember", plan=plan), approve)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "获取非空内容")
            assert_handled(service, sid, events[-1], "invalid_delivery")
            assert backend.calls == [("data", "inspect", {})]
            assert len(dialogue.inputs) == 3
            ledger = payload(service, sid, events)
            assert ledger["operations"][0]["attempts"][0]["acceptance"] == "accepted"
            assert ledger["plan"]["acceptance"]["content"]["state"] == "incomplete"
            assert len(result_cards(events)) == 1
            answer = "".join(event.get("text", "") for event in events if event["type"] == "message")
            assert "非空内容" in answer and "部分" in answer
        finally:
            await service.close()
    asyncio.run(run())
