"""Explicit late-goal confirmation preserves source ownership and execution truth."""
import asyncio
from copy import deepcopy

import pytest

from ..contracts import QAError
from ..operations import Operations
from .test_dataset_qa import engine


CAPABILITY = {"server": "resources", "name": "retrieve"}
TARGET = {"result_id": "selection", "path": "/items/0", "kind": "object"}


def save(operations, owner, result_id="result-A", invocation="query-A"):
    operations.start(owner, "key-"+invocation, CAPABILITY, retry_safe=True, invocation=invocation,
        presentation={"kind": "collection", "path": "/items"})
    operations.finish(owner, "key-"+invocation, result_id=result_id)
    return operations.get(owner)["attempts"][-1]


def scenario(*, target=None, inferred=True):
    operations = Operations()
    owner = operations.register("Unconfirmed evidence", CAPABILITY, target, required=False)
    if inferred:
        operations.get(owner)["inferred"] = True
    save(operations, owner)
    goal = operations.register("Requested outcome", CAPABILITY, target, planned=True)
    return operations, owner, goal


def confirmation(goal, *ids):
    return {"goal": goal, "result_ids": list(ids)}


@pytest.mark.parametrize("inferred", [False, True])
def test_late_goal_requires_explicit_selection_of_an_available_receipt(inferred):
    operations, owner, goal = scenario(inferred=inferred)
    original = deepcopy(operations.items)
    assert operations.confirmable(["result-A"])=={goal: ["result-A"]}
    operations.confirm([], ["result-A"])
    assert operations.items==original
    assert operations.get(goal)["state"]=="pending"

    operations.confirm([confirmation(goal, "result-A")], ["result-A"])
    adopted, = operations.get(goal)["attempts"]
    original_receipt, = operations.get(owner)["attempts"]
    assert adopted=={**original_receipt, "confirmation": True, "reused": True, "dispatched": False}
    assert operations.get(goal)["state"]=="succeeded"
    assert operations.get(owner)==original[0]
    assert operations.delivery_ids()==["result-A"]
    assert operations.error(["result-A"]) is None


def test_multiple_queries_are_candidates_without_automatic_cross_query_adoption():
    operations, owner, goal = scenario()
    # The second source query precedes its own late goal as well.
    save(operations, owner, "result-B", "query-B")
    other = operations.register("Another requested outcome", CAPABILITY, planned=True)
    assert operations.confirmable(["result-A", "result-B"])=={
        goal: ["result-A"], other: ["result-A", "result-B"]}
    operations.confirm([confirmation(goal, "result-A"), confirmation(other, "result-B")],
        ["result-A", "result-B"])
    assert operations.result_ids(operations.get(goal))==["result-A"]
    assert operations.result_ids(operations.get(other))==["result-B"]
    assert operations.get(goal)["attempts"][0]["invocation"]=="query-A"
    assert operations.get(other)["attempts"][0]["invocation"]=="query-B"


def test_one_late_goal_can_explicitly_select_multiple_original_successes():
    operations = Operations()
    owner = operations.register("Supporting queries", CAPABILITY, required=False)
    save(operations, owner)
    save(operations, owner, "result-B", "query-B")
    goal = operations.register("Both necessary sources", CAPABILITY, planned=True)
    operations.confirm([confirmation(goal, "result-A", "result-B")], ["result-A", "result-B"])
    assert operations.delivery_ids()==["result-A", "result-B"]
    assert operations.get(goal)["state"]=="succeeded"


def test_view_only_marks_inferred_source_resolved_when_all_its_results_have_owners():
    operations = Operations()
    owner = operations.register("Evidence", CAPABILITY, required=False)
    operations.get(owner)["inferred"] = True
    save(operations, owner)
    save(operations, owner, "result-B", "query-B")
    first = operations.register("First outcome", CAPABILITY, planned=True)
    second = operations.register("Second outcome", CAPABILITY, planned=True)
    assert operations.view()["items"][0]["delivery_pending"] is True
    operations.confirm([confirmation(first, "result-A")], ["result-A", "result-B"])
    assert operations.view()["items"][0]["delivery_pending"] is True
    operations.confirm([confirmation(second, "result-B")], ["result-A", "result-B"])
    source_view = operations.view()["items"][0]
    assert source_view["supporting"] is True and "delivery_pending" not in source_view
    assert operations.get(owner)["inferred"] is True  # The private execution history stays intact.


@pytest.mark.parametrize("change", [
    lambda operations, owner, goal: operations.get(owner).update(state="failed"),
    lambda operations, owner, goal: operations.get(owner).update(state="unknown"),
    lambda operations, owner, goal: operations.get(owner).update(required=True),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(state="rejected"),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(reused=True),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(dispatched=False),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(invocation=None),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(key=None),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(result_id=None),
    lambda operations, owner, goal: operations.get(owner)["attempts"][0].update(tool={"server": "other", "name": "retrieve"}),
    lambda operations, owner, goal: operations.get(goal).update(capability={"server": "resources", "name": "sample"}),
    lambda operations, owner, goal: operations.get(goal).update(target=TARGET),
    lambda operations, owner, goal: operations.get(goal).update(planned=False),
    lambda operations, owner, goal: operations.get(goal).update(required=False),
])
def test_unproven_or_incompatible_evidence_is_never_confirmable(change):
    operations, owner, goal = scenario()
    change(operations, owner, goal)
    original = deepcopy(operations.items)
    assert operations.confirmable(["result-A"])=={}
    with pytest.raises(QAError) as caught:
        operations.confirm([confirmation(goal, "result-A")], ["result-A"])
    assert caught.value.code=="invalid_delivery"
    assert caught.value.detail["eligible"]=={}
    assert operations.items==original


def test_grounded_targets_must_match_exact_canonical_source():
    operations, _, goal = scenario(target=TARGET)
    assert operations.confirmable(["result-A"])=={goal: ["result-A"]}
    operations.get(goal)["target"]={**TARGET, "path": "/items/1"}
    assert operations.confirmable(["result-A"])=={}
    with pytest.raises(QAError):
        operations.confirm([confirmation(goal, "result-A")], ["result-A"])


def test_only_loaded_turn_or_explicitly_inherited_results_can_be_confirmed():
    operations, _, goal = scenario()
    assert operations.confirmable([])=={}
    original = deepcopy(operations.items)
    with pytest.raises(QAError) as caught:
        operations.confirm([confirmation(goal, "result-A")], ["unrelated-history"])
    assert caught.value.detail["reason"]=="unavailable_result"
    assert operations.items==original
    # Restoring a continuation's actual cards is sufficient; session history alone is not.
    inherited = Operations(original)
    inherited.confirm([confirmation(goal, "result-A")], ["result-A"])
    assert inherited.get(goal)["state"]=="succeeded"


def test_a_predeclared_goal_cannot_use_late_confirmation_instead_of_execution():
    operations = Operations()
    goal = operations.register("Independent sample", CAPABILITY, planned=True)
    owner = operations.register("Supporting lookup", CAPABILITY, required=False)
    save(operations, owner)
    assert goal in operations.get(owner)["attempts"][0]["scope"]
    assert operations.confirmable(["result-A"])=={}
    with pytest.raises(QAError):
        operations.confirm([confirmation(goal, "result-A")], ["result-A"])
    assert operations.get(goal)["state"]=="pending"


def test_a_result_cannot_satisfy_two_independent_goals_and_rejection_is_atomic():
    operations, _, first = scenario()
    second = operations.register("Independent second sample", CAPABILITY, planned=True)
    original = deepcopy(operations.items)
    with pytest.raises(QAError) as caught:
        operations.confirm([confirmation(first, "result-A"), confirmation(second, "result-A")], ["result-A"])
    assert caught.value.detail["reason"]=="result_already_owned"
    assert operations.items==original

    operations.confirm([confirmation(first, "result-A")], ["result-A"])
    assert operations.confirmable(["result-A"])=={}
    with pytest.raises(QAError):
        operations.confirm([confirmation(second, "result-A")], ["result-A"])
    assert operations.get(second)["state"]=="pending"


def test_multiple_confirmations_validate_completely_before_committing_any():
    operations, _, goal = scenario()
    original = deepcopy(operations.items)
    with pytest.raises(QAError):
        operations.confirm([confirmation(goal, "result-A"), confirmation("invented", "result-A")], ["result-A"])
    assert operations.items==original


def test_identical_confirmation_is_idempotent_after_persistence_round_trip():
    operations, _, goal = scenario()
    selected = [confirmation(goal, "result-A")]
    operations.confirm(selected, ["result-A"])
    restored = Operations(operations.items)
    restored.confirm(selected, ["result-A"])
    assert restored.items==operations.items
    assert len(restored.get(goal)["attempts"])==1


@pytest.mark.parametrize("code,state", [
    ("invalid_parameters", "pending"), ("tool_failed", "failed"), ("execution_unknown", "unknown"),
    (None, "succeeded"),
])
@pytest.mark.parametrize("confirmed_before", [False, True])
def test_confirmation_never_overwrites_a_goal_with_existing_execution_history(code, state, confirmed_before):
    operations, _, goal = scenario()
    if confirmed_before:
        operations.confirm([confirmation(goal, "result-A")], ["result-A"])
    operations.start(goal, "later", CAPABILITY, retry_safe=True, invocation="new-query")
    operations.finish(goal, "later", result_id="new-result" if code is None else None,
        error=QAError(code, "Later operation") if code else None)
    original = deepcopy(operations.items)
    assert operations.get(goal)["state"]==state
    assert operations.confirmable(["result-A", "new-result"])=={}
    with pytest.raises(QAError):
        operations.confirm([confirmation(goal, "result-A")], ["result-A", "new-result"])
    assert operations.items==original


@pytest.mark.parametrize("values", [
    None, {}, [None], [{"goal": []}], [{"goal": "op2", "result_ids": []}],
    [{"goal": "op2", "result_ids": [None]}], [{"goal": "op2", "result_ids": ["result-A", "result-A"]}],
    [{"goal": "op2", "result_ids": ["result-A"]}, {"goal": "op2", "result_ids": ["result-A"]}],
])
def test_invalid_or_duplicate_confirmation_is_rejected_without_mutation(values):
    operations, _, _ = scenario()
    original = deepcopy(operations.items)
    with pytest.raises(QAError) as caught:
        operations.confirm(values, ["result-A"])
    assert caught.value.code=="invalid_delivery"
    assert "eligible" in caught.value.detail and "guidance" in caught.value.detail
    assert operations.items==original


@pytest.mark.parametrize("first_explicitly_confirmed", [False, True])
def test_native_receipt_replay_cannot_reassign_an_adopted_result_to_an_independent_goal(first_explicitly_confirmed):
    operations, _, first = scenario()
    second = operations.register("Independent second execution", CAPABILITY, planned=True)
    if first_explicitly_confirmed:
        operations.confirm([confirmation(first, "result-A")], ["result-A"])
    else:
        operations.reuse(first, "first-replay", operations.receipt("query-A", first))
    assert operations.receipt("query-A", first)["result_id"]=="result-A"
    assert operations.receipt("query-A", second) is None
    operations.start(second, "second-execution", CAPABILITY, retry_safe=False, invocation="query-A")
    operations.finish(second, "second-execution", result_id="result-second")
    assert operations.receipt("query-A", second)["result_id"]=="result-second"
    assert operations.receipt("query-A", first)["result_id"]=="result-A"


def test_post_execution_sample_goals_keep_independent_dispatch_and_same_goal_correction(engine):
    from ..capabilities import OBJECT
    from ..service import DatasetQA
    from .assertions import assert_completed
    from .test_dataset_qa import action, collect, remote, session
    from .test_decisions import BareDialogue, configured, for_goal, goals, payload, seed, text

    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            def sample():
                return remote("sample", count=1, **{OBJECT: "candidate:1"})
            dialogue.responses = [sample(), goals(
                {"description": "First independent sample", "tool": "sample", "object": "candidate:1", "output": "answer"},
                {"description": "Second independent sample", "tool": "sample", "object": "candidate:1", "output": "answer"}),
                for_goal("First independent sample", sample()),
                for_goal("First independent sample", sample()),
                for_goal("Second independent sample", sample()), action("deliver_results"), text()]
            events = await collect(service, sid, "Take two independent samples from the first dataset", "late-samples")
            assert_completed(service, None, events[-1])
            assert [name for _, name, _ in backend.calls]==["search", "sample", "sample"]
            ledger = payload(service, sid, events)
            first, second = [item for item in ledger["operations"] if item.get("required", True)]
            assert first["attempts"][0]["reused"] is True
            assert not second["attempts"][0].get("reused")
            assert len(first["attempts"])==len(second["attempts"])==1
            assert first["attempts"][0]["result_id"]!=second["attempts"][0]["result_id"]
        finally:
            await service.close()
    asyncio.run(run())
