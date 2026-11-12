"""Plan contracts and real runtime scheduling with unmodified model decisions."""
import asyncio
from copy import deepcopy
import json

import pytest
from pydantic import ValidationError

from ..contracts import QAError
from ..planning import Check, Plan, ResultContract, Review, validate_revision
from ..dialogue import Dialogue, builtin_definitions
from ..contracts import Limits
from ..plan_runtime import confirm_plan
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, load, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text


def specimen():
    return {"outcomes": [
        {"key": "details", "description": "第一个结果的详情", "kind": "inspect"},
        {"key": "records", "description": "同一对象的三条样例", "kind": "sample", "constraints": ["最多三条"]}],
        "steps": [
            {"key": "find", "tool": "search", "arguments": {"query": "资源"}},
            {"key": "detail", "tool": "inspect", "object": {"step": "find", "path": "/items/0"}, "produces": ["details"]},
            {"key": "sample", "tool": "sample", "arguments": {"count": 3},
                "object": {"step": "find", "path": "/items/0"}, "produces": ["records"]}]}


def approve(messages, definitions):
    plan = json.loads(messages[1].content)["plan"]
    assert "review_plan" in {item["function"]["name"] for item in definitions}
    assert not any(item["function"]["name"].startswith("mcp_") for item in definitions)
    return action("review_plan", revision=plan["revision"], covered=[item["key"] for item in plan["outcomes"]])


def test_scheduler_resolves_sources_runs_dependencies_and_delivers_only_outcomes(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), action("remember", plan=specimen()), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找资源，查看第一个的详情，并采样三条")
            assert_completed(service, None, values[-1])
            assert backend.calls == [("data", "search", {"query": "资源"}),
                ("data", "inspect", {"reference": "a"}), ("data", "sample", {"reference": "a", "count": 3})]
            assert len(dialogue.inputs) == 4  # load, plan, review, final; no per-step model call
            assert len(result_cards(values)) == 2
            saved = payload(service, sid, values)
            assert saved["plan"]["reviewed"] == 1
            assert {value["state"] for value in saved["plan"]["acceptance"].values()} == {"accepted"}
            assert [operation["state"] for operation in saved["operations"]] == ["succeeded"]*3
            assert [operation["required"] for operation in saved["operations"]] == [False, True, True]
            assert all(operation["target"]["result_id"].endswith(":0") for operation in saved["operations"][1:])
            assert {item["state"] for item in json.loads(dialogue.inputs[-1][0][1].content)["outcome_status"]} == {"accepted"}
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("mutation", [
    lambda p: p["steps"][0].update(depends_on=["sample"]),
    lambda p: p["steps"][1].update(depends_on=["missing"]),
    lambda p: p["steps"].pop(),
    lambda p: p["steps"].append({"key": "extra", "tool": "inspect"}),
    lambda p: p["steps"][1].update(produces=["records"]),
])
def test_invalid_dependency_or_coverage_contract_is_rejected(mutation):
    plan = specimen()
    mutation(plan)
    with pytest.raises(ValidationError):
        Plan.model_validate(plan)


def test_revision_cannot_erase_constraints_and_review_cannot_invent_outcomes():
    old = Plan.model_validate(specimen()).model_dump()
    revised = deepcopy(old)
    revised["outcomes"][1]["constraints"] = []
    with pytest.raises(QAError):
        validate_revision({"spec": old}, Plan.model_validate(revised))
    with pytest.raises(QAError):
        confirm_plan({"plan": {"revision": 1, "spec": old}}, Review(revision=1, covered=["details"]))


@pytest.mark.parametrize("data,status", [
    ({"previewable": False}, "unavailable"),
    ({"previewable": True, "schema": None}, "incomplete"),
    ({"schema": {"properties": {}}}, "accepted"),
    ({"data": [{"value": 1}]}, "incomplete"),
])
def test_result_acceptance_distinguishes_transport_success_from_content(data, status):
    contract = ResultContract(kind="schema", requires=[Check(path="/schema")],
        unavailable_when=[Check(path="/previewable", test="equals", value=False)])
    assert contract.assess(data) == status


def test_review_may_repair_missing_semantic_outcome_before_any_execution(engine):
    async def run():
        backend = configured()
        complete = specimen()
        incomplete = deepcopy(complete)
        incomplete["outcomes"].pop()
        incomplete["steps"].pop()
        def repair(messages, definitions):
            assert not backend.calls
            return action("remember", plan=complete)
        dialogue = BareDialogue(load(), action("remember", plan=incomplete), repair, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找资源，查看第一个的详情，并采样三条")
            assert_completed(service, None, values[-1])
            assert len(backend.calls) == 3
            assert payload(service, sid, values)["plan"]["revision"] == 2
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("fresh,expected", [(False, 2), (True, 3)])
def test_identical_safe_reads_are_shared_unless_fresh_execution_is_explicit(engine, fresh, expected):
    async def run():
        backend = configured()
        backend.catalog["data"][1].annotations = {"readOnlyHint": True, "idempotentHint": True}
        spec = specimen()
        spec["outcomes"][1].update(kind="inspect", description="同一对象的格式说明", constraints=[])
        spec["steps"][2] = {**spec["steps"][1], "key": "second", "produces": ["records"], "fresh": fresh}
        dialogue = BareDialogue(load(), action("remember", plan=spec), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找资源，查看第一个的详情和格式" + ("，分别重新获取" if fresh else ""))
            assert_completed(service, None, values[-1])
            assert len(backend.calls) == expected
            mapping = payload(service, sid, values)["plan"]["operations"]
            assert (mapping["detail"] == mapping["second"]) is not fresh
        finally:
            await service.close()
    asyncio.run(run())


def test_long_deterministic_chain_does_not_consume_model_decision_rounds(engine):
    async def run():
        backend = configured()
        spec = {"outcomes": [{"key": "answer", "description": "计算指定链的最终值", "kind": "multiply"}],
            "steps": [{"key": f"s{i}", "tool": "multiply", "arguments": {"y": 2, **({"x": 2} if i == 0 else {})},
                "inputs": {"x": {"step": f"s{i-1}"}} if i else {},
                "produces": ["answer"] if i == 12 else []} for i in range(13)]}
        dialogue = BareDialogue(load("compute"), action("remember", plan=spec), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "把2连续乘以2十三次，给我最终值")
            assert_completed(service, None, values[-1])
            assert len(backend.calls) == 13 and len(dialogue.inputs) == 4
            assert result_cards(values)[0]["data"] == {"items": [16384]}
        finally:
            await service.close()
    asyncio.run(run())


def test_progressive_schema_disclosure_preserves_single_step_budget():
    def memory(definitions):
        return next(item["function"]["parameters"] for item in definitions if item["function"]["name"] == "remember")
    simple, complex_ = memory(builtin_definitions()), memory(builtin_definitions(True))
    assert "plan" not in simple["properties"] and "planning" in simple["properties"]
    assert "plan" in complex_["properties"] and "Workflow" in complex_["$defs"]
    assert len(json.dumps(complex_)) > len(json.dumps(simple))+2000


def test_token_budget_reserves_output_and_preserves_plan_and_source_handles():
    from ..context import encode
    plan = {"revision": 1, "outcomes": [{"description": "保留原单位", "constraints": ["不得换算单位"]}],
        "steps": [{"object": "source:123456"}]}
    counter = lambda text: len(text.encode("utf-8"))
    limits = Limits(context_chars=40000, context_tokens=16000, output_tokens=2000)
    dialogue = Dialogue(model=object(), limits=limits, token_counter=counter)
    messages = dialogue.messages("查看原始内容", {"plan": plan,
        "history": [{"role": "user", "text": "无关旧讨论"*1500}]})
    bounded = dialogue.budget(messages, [])
    assert json.loads(bounded[1].content)["plan"] == plan
    size = sum(counter(encode(message.model_dump(mode="json", exclude_none=True)))+33 for message in bounded)
    assert size+counter("[]")+1+256+limits.output_tokens <= limits.context_tokens
    assert bounded[-1].content == "查看原始内容"


def test_token_budget_rejects_oversized_critical_state_without_truncating_it():
    dialogue = Dialogue(model=object(), limits=Limits(context_tokens=12000, output_tokens=2000))
    messages = dialogue.messages("查看", {"plan": {"constraints": ["关键约束"*3000]}})
    original = deepcopy(messages)
    with pytest.raises(QAError, match="上下文"):
        dialogue.budget(messages, [])
    assert messages == original
