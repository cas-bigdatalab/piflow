"""Successful native evidence remains reviewable without implying auxiliary intent."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from .assertions import assert_completed
from ..context import encode
from ..dialogue import Dialogue
from ..operations import Operations
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, text
from .test_projection import search_result


def test_native_evidence_pending_delivery_is_distinct_from_declared_support():
    operations = Operations()
    native = operations.register("Find resources", {"server": "generic", "name": "discover"}, required=False)
    operations.get(native)["inferred"] = True
    support = operations.register("Resolve metadata", {"server": "generic", "name": "metadata"}, required=False)
    for key in (native, support):
        operations.start(key, key+"-call")
        operations.finish(key, key+"-call", result_id=key+"-result")
    original = deepcopy(operations.items)

    native_view, support_view = operations.view()["items"]

    assert native_view["delivery_pending"] is True and "supporting" not in native_view
    assert support_view["supporting"] is True and "delivery_pending" not in support_view
    assert native_view["state"]=="succeeded" and native_view["result_ids"]==[native+"-result"]
    assert operations.items==original and not operations.required
    assert operations.delivery_ids()==[]  # A preview does not confirm delivery.


def test_confirmed_native_goal_no_longer_requests_a_delivery_classification():
    operations = Operations()
    key = operations.register("Find resources", {"server": "generic", "name": "discover"})
    operations.get(key)["inferred"] = True
    row, = operations.view()["items"]
    assert "delivery_pending" not in row and "supporting" not in row
    assert operations.required==operations.items


def test_review_decision_survives_context_budget_with_whole_result_ids():
    dialogue = Dialogue(model=object())
    decision = {"phase": "review", "remaining_rounds": 3, "remaining_calls": 19,
        "result_ids": ["task:"+"opaque"*29], "guidance": "Assess saved candidates before further exploration."}
    messages = dialogue.messages("Find relevant resources", {
        "execution_decision": decision, "unrelated": "Long optional history. "*4000})
    bounded = dialogue.budget(messages, [])
    assert isinstance(bounded[1], HumanMessage)
    assert json.loads(bounded[1].content)["execution_decision"]==decision
    assert len(encode([message.model_dump(mode="json", exclude_none=True) for message in bounded]))<dialogue.limits.context_chars


def test_review_projects_full_saved_records_once_and_keeps_descriptive_evidence(engine):
    """Large corpus-shaped results keep useful facts after several queries."""
    async def run():
        backend = configured()
        payload = search_result()
        original = deepcopy(payload)
        factory = backend.client

        def client(*args, **kwargs):
            connection = factory(*args, **kwargs)
            execute = connection.call_tool

            async def call(*args, **kwargs):
                await execute(*args, **kwargs)
                return SimpleNamespace(structured_content=deepcopy(payload), is_error=False)

            connection.call_tool = call
            return connection

        reviewed = []

        def review(messages, definitions):
            context = json.loads(messages[1].content)
            group = context["evidence"]
            assert len(group["items"])==2
            assert len(encode(group))<=8000
            for card in group["items"]:
                rows = card["data"]["items"]
                assert [row["id"] for row in rows]==[row["id"] for row in payload["items"]]
                assert [row["title"] for row in rows]==[row["title"] for row in payload["items"]]
                assert card["data"]["pagination"]==payload["pagination"]
                # Re-projecting an already truncated preview loses every
                # description here although the saved facts still fit.
                assert any(row.get("raw", {}).get("description") for row in rows)
                assert card["truncated"] is True
            reviewed.append(group)
            return action("deliver_results")

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = BareDialogue(load(), goals({"description": "Compare candidate descriptions across sources",
            "tool": "search", "output": "answer"}, calls=[remote("search", query="initial")]),
            remote("search", query="refined"), review, text())
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant resources")
            assert_completed(service, None, events[-1])
            assert len(reviewed)==1
            assert len(backend.calls)==2 and payload==original
            saved = service.store.results("alice", sid, events[-1]["task_id"])
            assert len(saved)==2 and all(card["data"]==original for card in saved)
        finally:
            await service.close()

    asyncio.run(run())


def test_confirmed_direct_result_finishes_despite_truncated_model_preview(engine):
    async def run():
        backend = configured()
        payload = search_result()
        original = deepcopy(payload)
        factory = backend.client

        def client(*args, **kwargs):
            connection = factory(*args, **kwargs)
            execute = connection.call_tool

            async def call(*args, **kwargs):
                await execute(*args, **kwargs)
                return SimpleNamespace(structured_content=deepcopy(payload), is_error=False)

            connection.call_tool = call
            return connection

        def direct_search(messages, definitions):
            native = remote("search", query="resources")(messages, definitions)
            confirmed = action("remember", operations=[{"id": "discovery",
                "description": "Return the first candidate set", "output": "result", "direct": True}],
                calls=["discovery"])
            return native.model_copy(update={"tool_calls": [*confirmed.tool_calls, *native.tool_calls]})

        def final_reply(messages, definitions):
            assert definitions==[]  # No extra delivery selection model round.
            context = json.loads(messages[1].content)
            assert "execution_decision" not in context
            preview, = json.loads(messages[-1].content)["final_delivery"]
            assert preview["truncated"] is True
            assert len(encode(preview["data"]))<len(encode(original))
            return text("The initial candidates are available.")

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = BareDialogue(load(), direct_search, final_reply)
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid, "Return an initial set of relevant resources")
            assert_completed(service, None, events[-1])
            assert len(backend.calls)==1 and len(dialogue.inputs)==3
            card, = result_cards(events)
            assert card["data"]==original and "truncated" not in card
            saved, = service.store.results("alice", sid, events[-1]["task_id"])
            assert saved["data"]==original and payload==original
        finally:
            await service.close()

    asyncio.run(run())
