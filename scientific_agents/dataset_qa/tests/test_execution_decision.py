"""Execution decisions follow goal acceptance across modes and action orders."""
from types import SimpleNamespace

import pytest

from ..contracts import QAError
from ..execution import Execution
from ..search import SearchProfile, SearchRun


def tools():
    def make(name, **qa):
        return SimpleNamespace(server="archive", name=name, alias=name,
            schema={"type": "object", "properties": {}}, annotations={}, meta={"piflow": {"qa": qa}})
    return {tool.alias: tool for tool in [make("search"), make("inspect"), make("transform", plan_required=True)]}


def goal(execution, name="search", *, required=True, direct=True):
    key = execution.operations.register(name, {"server": "archive", "name": name}, required=required)
    item = execution.operations.get(key)
    item["direct"] = direct
    return item


def receipt(execution, item, *, acceptance="accepted"):
    key = item["id"] + ":call"
    execution.operations.start(item["id"], key)
    execution.operations.finish(item["id"], key, result_id=key, acceptance=acceptance)
    execution.cards[key] = {"result_id": key}


def unfinished_search(execution, *, required=True):
    item = goal(execution, required=required)
    run = SearchRun.create(SearchProfile(query="term", identity=["/id"]), {"term": "alpha"}, ["alpha"])
    run.record({"items": [{"id": "a"}]}, "/items", "page-one")
    item["search"] = run.state
    receipt(execution, item)
    assert run.arguments() is None and not run.state["done"]
    return item


@pytest.mark.parametrize("recovering", [False, True])
@pytest.mark.parametrize("closing", [False, True])
def test_completed_page_does_not_close_the_goal_or_hide_its_continuation(recovering, closing):
    execution = Execution()
    item = unfinished_search(execution)
    execution.recovering = recovering
    available = execution.actions(tools(), closing=closing)
    assert item["state"] == "succeeded"
    assert not execution.finalizing
    assert not execution.settled
    assert execution.unfinished_searches == [item]
    assert {"search", "remember", "read_result", "load_mcp_tools"} <= available
    assert "deliver_results" not in available


def test_search_keeps_independent_work_and_discovery_available():
    execution = Execution()
    unfinished_search(execution)
    goal(execution, "inspect")
    available = execution.actions(tools())
    assert {"search", "inspect", "remember", "resolve_resource", "load_mcp_tools"} <= available
    assert "transform" not in available  # Its own execution contract still requires a plan.


@pytest.mark.parametrize("acceptance,expected", [("accepted", True), ("incomplete", False), ("unavailable", False)])
def test_finalization_requires_content_acceptance_not_transport_success(acceptance, expected):
    execution = Execution()
    receipt(execution, goal(execution, "inspect"), acceptance=acceptance)
    assert execution.finalizing is expected
    assert execution.settled


def test_success_without_a_receipt_is_not_finalization():
    execution = Execution()
    goal(execution)["state"] = "succeeded"
    assert not execution.finalizing
    assert not execution.settled


@pytest.mark.parametrize("retry_safe", [False, True])
def test_terminal_plan_search_keeps_only_a_real_safe_correction_opportunity(retry_safe):
    execution = Execution()
    item = unfinished_search(execution)
    execution.operations.start(item["id"], "next-page", retry_safe=retry_safe)
    execution.operations.finish(item["id"], "next-page", error=QAError("tool_failed", "unavailable"))
    receipt(execution, goal(execution, "inspect"))
    reason = execution.failure_decision(planned=True)
    assert (reason is None) is retry_safe
    assert not item["search"]["done"] and not execution.finalizing


def test_auxiliary_search_policy_cannot_disappear_when_required_output_is_ready():
    execution = Execution()
    unfinished_search(execution, required=False)
    receipt(execution, goal(execution, "inspect"))
    assert not execution.finalizing
    assert "search" in execution.actions(tools(), closing=True)
    assert "deliver_results" not in execution.actions(tools())


def test_complete_search_closes_normally_without_recovery_reopening_tools():
    execution = Execution()
    item = unfinished_search(execution)
    run = SearchRun(item["search"])
    run.extend({"term": "beta"}, ["beta", "gamma", "delta"])
    while run.arguments() is not None:
        run.record({"items": [{"id": "a"}]}, "/items", "next")
    assert execution.finalizing
    for recovering in (False, True):
        execution.recovering = recovering
        available = execution.actions(tools())
        assert "deliver_results" in available
        assert not set(tools()) & available


@pytest.mark.parametrize("reviewed", [None, 1])
def test_plan_only_opens_owned_continuations_after_review(reviewed):
    execution = Execution()
    unfinished_search(execution)
    plan = {"revision": 1, "reviewed": reviewed}
    available = execution.actions(tools(), planning=True, plan=plan, closing=True,
        continuations={"search", "inspect", "transform", "missing"})
    assert "remember" in available
    assert "deliver_results" not in available
    assert not {"inspect", "transform", "missing"} & available
    assert ("search" in available) is (reviewed == 1)
    assert ("review_plan" in available) is (reviewed is None)


def test_plan_entry_does_not_run_native_tools_before_plan_installation():
    execution = Execution()
    unfinished_search(execution)
    available = execution.actions(tools(), planning=True, continuations={"search"})
    assert not set(tools()) & available
    assert "remember" in available


@pytest.mark.parametrize("state,blocked", [("failed", False), ("unknown", False), ("unavailable", False), ("succeeded", True)])
def test_plan_continuation_never_reopens_blocked_or_uncertain_work(state, blocked):
    execution = Execution()
    item = unfinished_search(execution)
    item["state"] = state
    if blocked:
        execution.blocked.add(item["id"])
    available = execution.actions(tools(), plan={"revision": 1, "reviewed": 1}, continuations={"search"})
    assert "search" not in available


def test_unrelated_failure_does_not_terminate_an_unfinished_search_goal():
    execution = Execution()
    unfinished_search(execution)
    item = goal(execution, "inspect")
    execution.operations.start(item["id"], "inspect-call")
    execution.operations.finish(item["id"], "inspect-call", error=QAError("tool_failed", "unavailable", 502))
    assert execution.failure_decision(consume=True) is None
    assert execution.failure_decision(consume=True) is None


def test_identical_rejected_decision_receives_one_correction_opportunity():
    execution = Execution()
    decision = {"proposal": [{"name": "inspect", "args": {"id": 7}}], "state": {"tools": ["inspect"]}}
    first = QAError("invalid_parameters", "identifier must be a string", detail={"path": ["id"]})
    repeated = QAError("invalid_parameters", "identifier must be a string", detail={"path": ["id"]})
    assert execution.correct(first, 2, decision=decision) is None
    assert execution.correct(repeated, 2, decision=decision) is repeated
    assert execution.corrections == 1


@pytest.mark.parametrize("changed", [
    {"proposal": {"id": "7"}, "state": {"result": None}},
    {"proposal": {"id": 7}, "state": {"result": "new"}},
    {"proposal": {"id": 7}, "state": {"result": None, "schema": "updated"}},
])
def test_changed_arguments_or_context_keep_existing_correction_budget(changed):
    execution = Execution()
    error = QAError("invalid_parameters", "check input")
    assert execution.correct(error, 2, decision={"proposal": {"id": 7}, "state": {"result": None}}) is None
    assert execution.correct(error, 2, decision=changed) is None
    assert execution.corrections == 2
    assert execution.correct(error, 2, decision={"proposal": {"id": "another"}}) is error


def test_changed_validation_constraint_does_not_count_as_identical_rejection():
    execution = Execution()
    decision = {"proposal": {"id": 7}}
    assert execution.correct(QAError("invalid_parameters", "wrong type"), 2, decision=decision) is None
    assert execution.correct(QAError("invalid_parameters", "source not present"), 2, decision=decision) is None


@pytest.mark.parametrize("decision", [None, {"non_json": object()}, {"number": float("nan")}])
def test_missing_or_malformed_recurrence_context_preserves_hard_budget(decision):
    execution = Execution()
    error = QAError("invalid_parameters", "check input")
    assert execution.correct(error, 2, decision=decision) is None
    assert execution.correct(error, 2, decision=decision) is None
    assert execution.correct(error, 2, decision=decision) is error
