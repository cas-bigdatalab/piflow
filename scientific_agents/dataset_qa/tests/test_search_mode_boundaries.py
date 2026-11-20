"""Raw decisions preserve ongoing work when additional outcomes are declared."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage
import pytest

from ..capabilities import GOAL, TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import SearchBackend, discover, native, outcome, page, KEYWORDS
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, text
from .test_planning import approve
from .test_runtime_transitions import keyword_extension


@pytest.mark.parametrize("include_remaining_queue", [False, True])
@pytest.mark.parametrize("declared_before_search", [False, True])
def test_partial_react_search_survives_transition_to_plan_for_independent_work(
        engine, include_remaining_queue, declared_before_search):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        backend.catalogue[1].meta["piflow"]["qa"]["plan_required"] = True
        plan = {"steps": [
            {"key": "find", "tool": "find_assets", "arguments": {"phrase": KEYWORDS[0]}},
            {"key": "inspect", "tool": "inspect", "arguments": {"reference": "asset-2"}},
        ]}
        if include_remaining_queue:
            plan["steps"][0]["arguments"][TASK] = {"complete_request": False,
                "keywords": KEYWORDS, "original_keywords": KEYWORDS[:1]}
        replies = []
        if declared_before_search:
            replies.append(action("remember", goals=[{"description": "Find datasets", "tool": "find_assets"}]))
        replies.extend([
            discover(keywords=KEYWORDS[:1], complete=False),
            action("remember", goals=[{"description": "Inspect asset-2", "tool": "inspect"}]),
            action("remember", plan=plan), approve])
        if not include_remaining_queue:
            replies.append(keyword_extension)
        replies.append(text())
        dialogue = BareDialogue(*replies)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets and inspect asset-2")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert len(saved["operations"]) == 2
            assert saved["plan"]["operations"] == {"find": "op1", "inspect": "op2"}
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            assert [args["phrase"] for name, args in backend.calls if name == "find_assets"] == KEYWORDS
            assert [args for name, args in backend.calls if name == "inspect"] == [{"reference": "asset-2"}]
            assert len(dialogue.inputs) == 6 + int(declared_before_search) - int(include_remaining_queue)
        finally:
            await service.close()
    asyncio.run(run())


def test_rejected_search_redeclaration_leaves_independent_work_and_original_continuation_available(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1], complete=False),
            action("remember", goals=[
                {"description": "Find datasets", "tool": "find_assets"},
                {"description": "Inspect asset-2", "tool": "inspect"}]),
            action("remember", goals=[{"description": "Inspect asset-2", "tool": "inspect"}]),
            native("inspect", reference="asset-2", **{TASK: {"complete_request": False}}),
            discover(keywords=KEYWORDS, legacy=True), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets and inspect asset-2")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert len(saved["operations"]) == 2
            assert [args["phrase"] for name, args in backend.calls if name == "find_assets"] == KEYWORDS
            search = saved["operations"][0]
            assert search["id"] == "op1" and search["required"] is True and search["search"]["done"]
            assert len(dialogue.inputs) == 6
        finally:
            await service.close()
    asyncio.run(run())


def test_independent_searches_keep_separate_queues_and_evidence_during_continuation(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        queues = {
            "Find climate records": ["climate", "weather", "meteorology", "atmosphere"],
            "Find ocean records": ["ocean", "marine", "sea", "pelagic"],
        }

        def search_pair(first):
            def decide(messages, definitions):
                alias = next(item["function"]["name"] for item in definitions
                    if item["function"]["name"].endswith("_find_assets"))
                targets = json.loads(messages[1].content)["operations"]["items"]
                calls = []
                for goal in targets:
                    words = queues[goal["description"]]
                    call = action(alias, phrase=words[0], **{GOAL: goal["id"], TASK: {
                        "complete_request": False, "keywords": words[:1] if first else words,
                        "original_keywords": words[:1]}}).tool_calls[0]
                    calls.append({**call, "id": "continue-" + goal["id"]})
                return AIMessageChunk(content="", tool_calls=calls)
            return decide

        dialogue = BareDialogue(action("remember", goals=[{"description": description, "tool": "find_assets"}
            for description in queues]), search_pair(True), search_pair(False), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find climate records and ocean records separately")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert len(saved["operations"]) == 2 and len(backend.calls) == 8
            for item in saved["operations"]:
                assert item["search"]["completed"] == queues[item["description"]]
                assert len(item["search"]["records"]) == 1 and len(item["attempts"]) == 4
            assert set(saved["operations"][0]["search"]["result_ids"]).isdisjoint(
                saved["operations"][1]["search"]["result_ids"])
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("changed_arguments", [
    {"phrase": KEYWORDS[0], "per_page": 4},
    {"phrase": KEYWORDS[0], TASK: {"complete_request": False,
        "keywords": ["chemical"], "original_keywords": ["chemical"]}},
])
def test_rejected_plan_scope_change_preserves_search_for_valid_migration(engine, changed_arguments):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        invalid = {"steps": [{"key": "find", "tool": "find_assets", "arguments": changed_arguments}]}
        valid = {"steps": [{"key": "find", "tool": "find_assets", "arguments": {"phrase": KEYWORDS[0]}}]}

        def repair(messages, definitions):
            context = json.loads(messages[1].content)
            assert "plan" not in context
            operation, = context["operations"]["items"]
            assert operation["id"] == "op1"
            assert operation["search"]["completed_keywords"] == KEYWORDS[:1]
            assert operation["search"]["original_keywords"] == KEYWORDS[:1]
            assert len(backend.calls) == 1
            feedback = next(json.loads(message.content) for message in reversed(messages)
                if isinstance(message, (HumanMessage, ToolMessage)) and '"error"' in message.content)
            feedback = feedback.get("runtime_feedback", feedback)
            assert feedback["error"] == "invalid_parameters"
            return action("remember", plan=valid)

        dialogue = BareDialogue(
            action("remember", goals=[{"description": "Find datasets", "tool": "find_assets"}]),
            discover(keywords=KEYWORDS[:1], complete=False),
            action("remember", plan=invalid), repair, approve, keyword_extension, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert len(saved["operations"]) == 1 and saved["plan"]["operations"] == {"find": "op1"}
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert all(args["per_page"] == 5 for _, args in backend.calls)
            assert len(dialogue.inputs) == 7
        finally:
            await service.close()
    asyncio.run(run())
