"""Exercise model decision order, not only prearranged successful tool calls."""
import asyncio
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import ToolMessage
import pytest

from ..capabilities import GOAL, TASK
from ..contracts import Limits, QAError
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_bounded_discovery import SearchBackend, discover, native, outcome, page, KEYWORDS
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, goals, text
from .test_planning import approve


@pytest.mark.parametrize("count", [0, 1, 5])
def test_partial_queue_continues_on_last_decision_without_correction(engine, count):
    async def run():
        backend = SearchBackend(lambda word, number: page(range(count), count))
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), discover(keywords=KEYWORDS[1:]), text())
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(max_rounds=2)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert len(dialogue.inputs) == 3
            assert len(outcome(service, sid, events)["operations"]) == 1
            assert not any('"error"' in message.content for messages, _ in dialogue.inputs
                for message in messages if isinstance(message, ToolMessage))
        finally:
            await service.close()
    asyncio.run(run())


def test_feedback_matches_next_tool_surface_after_premature_delivery(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))

        def continue_search(messages, definitions):
            feedback = next(json.loads(message.content) for message in reversed(messages)
                if isinstance(message, ToolMessage) and '"available_actions"' in message.content)
            names = {item["function"]["name"] for item in definitions}
            assert set(feedback["available_actions"]) == names
            assert "deliver_results" not in names
            assert any(name.endswith("_find_assets") for name in names)
            return discover(keywords=KEYWORDS[1:])(messages, definitions)

        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), action("deliver_results"), continue_search, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 4 and len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_unfinished_search_does_not_block_separately_requested_detail(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        dialogue = BareDialogue(goals(
            {"description": "Find datasets", "tool": "find_assets"},
            {"description": "Inspect asset-2", "tool": "inspect"},
            calls=[discover(keywords=KEYWORDS[:1], complete=False)]),
            native("inspect", reference="asset-2", **{TASK: {"complete_request": False}}),
            discover(keywords=KEYWORDS[1:], complete=False), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets and inspect asset-2")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["find_assets", "inspect", *(["find_assets"] * 3)]
            assert len(outcome(service, sid, events)["operations"]) == 2
        finally:
            await service.close()
    asyncio.run(run())


def keyword_extension(messages, definitions):
    tool = next(item["function"] for item in definitions if item["function"]["name"].endswith("_find_assets"))
    params = tool["parameters"]
    assert set(params["properties"]) == {GOAL, TASK}
    args = {GOAL: params["properties"][GOAL]["enum"][0], TASK: {"keywords": KEYWORDS[1:]}}
    Draft202012Validator(params).validate(args)
    return action(tool["name"], **args)


def search_plan(dependent=False):
    steps = [{"key": "discover", "tool": "find_assets", "arguments": {"phrase": KEYWORDS[0]}}]
    if dependent:
        steps.append({"key": "inspect", "tool": "inspect", "object": {"step": "discover", "path": "/items/0"}})
    return {"steps": steps}


@pytest.mark.parametrize("count", [0, 1, 5])
def test_plan_can_extend_saved_search_without_revision_or_replaying_pages(engine, count):
    async def run():
        backend = SearchBackend(lambda word, number: page(range(count), count))
        dialogue = BareDialogue(action("remember", plan=search_plan()), approve, keyword_extension, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            assert len(saved["operations"]) == 1
            assert len(saved["operations"][0]["attempts"]) == 4
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_repeated_exhausted_queue_does_not_reset_progress_budget(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        dialogue = BareDialogue(*([discover(keywords=KEYWORDS[:1])] * 3), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_handled(service, sid, events[-1])
            assert events[-1]["outcome"] == "partial"
            assert len(backend.calls) == 1 and len(dialogue.inputs) == 4
            assert not outcome(service, sid, events)["operations"][0]["search"]["done"]
        finally:
            await service.close()
    asyncio.run(run())


def test_unparsed_decisions_keep_the_existing_parameter_correction_budget(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        dialogue = BareDialogue(QAError("invalid_tool_call", "Malformed response"),
            QAError("invalid_tool_call", "Malformed response"), discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) == 4 and len(backend.calls) == 4
        finally:
            await service.close()
    asyncio.run(run())
