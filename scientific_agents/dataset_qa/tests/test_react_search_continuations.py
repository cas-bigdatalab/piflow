"""Existing ReAct searches ask for new keywords without re-declaring intent."""
import asyncio
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import AIMessageChunk
import pytest

from ..capabilities import GOAL, SUPPORTING, TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import KEYWORDS, SearchBackend, continue_keywords, discover, native, outcome, page
from .test_dataset_qa import action, collect, engine, remote, session
from .test_decisions import BareDialogue, goals, text


@pytest.mark.parametrize("scope", ["direct", "declared", "inferred"])
def test_react_continuation_preserves_scope_filters_and_receipts(engine, scope):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        first = discover(keywords=KEYWORDS[:1], complete=scope == "direct", per_page=2)
        if scope == "declared":
            first = goals({"description": "Find datasets", "tool": "find_assets"}, calls=[first])
        observed = {}

        def extend(messages, definitions):
            observed["before"] = json.loads(messages[1].content)["operations"]["items"][0]
            names = {item["function"]["name"] for item in definitions}
            task = next(item["function"]["parameters"]["properties"][TASK] for item in definitions
                if item["function"]["name"].endswith("_find_assets"))
            assert task["properties"]["keywords"]["maxItems"] == len(KEYWORDS) - 1
            if scope == "direct":
                assert names == {"request_input", next(name for name in names if name.endswith("_find_assets"))}
            else:
                assert "read_result" in names
                assert any(name.endswith("_inspect") for name in names)
            return continue_keywords()(messages, definitions)

        def confirm_inferred(messages, definitions):
            current, = json.loads(messages[1].content)["operations"]["items"]
            observed["after"] = current
            return action("deliver_results")

        responses = [first, extend]
        if scope == "inferred":
            responses.append(confirm_inferred)
        dialogue = BareDialogue(*responses, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert "plan" not in saved
            operation, = saved["operations"]
            assert operation["id"] == observed["before"]["id"]
            assert operation["direct"] is (scope == "direct")
            assert operation["search"]["original_keywords"] == KEYWORDS[:1]
            assert operation["search"]["completed"] == KEYWORDS
            assert len(operation["attempts"]) == len(KEYWORDS)
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert all(args["per_page"] == 2 and args["page_number"] == 1 for _, args in backend.calls)
            assert len(dialogue.inputs) == 3 + (scope == "inferred")
            if scope == "inferred":
                assert observed["after"]["delivery_pending"] is True
                assert not observed["after"].get("direct")
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("coemit_continuation", [False, True])
def test_committed_search_rejects_scope_expansion_before_any_state_change(engine, coemit_continuation):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        observed = {}

        def expand(messages, definitions):
            observed["before"] = json.loads(messages[1].content)["operations"]
            assert "remember" not in {item["function"]["name"] for item in definitions}
            call = action("remember", goals=[{"description": "Inspect the first candidate", "tool": "inspect",
                "object": "object:1"}]).tool_calls[0]
            calls = [call]
            if coemit_continuation:
                calls.append(continue_keywords()(messages, definitions).tool_calls[0])
            return AIMessageChunk(content="", tool_calls=calls)

        def resume(messages, definitions):
            observed["after"] = json.loads(messages[1].content)["operations"]
            observed["calls_before_resume"] = len(backend.calls)
            return continue_keywords()(messages, definitions)

        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), expand, resume, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert observed["before"] == observed["after"]
            assert observed["calls_before_resume"] == 1
            operation, = outcome(service, sid, events)["operations"]
            assert operation["required"] and operation["direct"]
            assert [name for name, _ in backend.calls] == ["find_assets"] * len(KEYWORDS)
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
        finally:
            await service.close()
    asyncio.run(run())


def test_committed_search_cannot_reopen_scope_through_a_supporting_legacy_call(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        observed = {}

        def supporting(messages, definitions):
            observed["before"] = json.loads(messages[1].content)["operations"]
            return remote("find_assets", phrase=KEYWORDS[0], **{SUPPORTING: True,
                TASK: {"complete_request": False, "keywords": KEYWORDS[:1],
                    "original_keywords": KEYWORDS[:1]}})(messages, definitions)

        def resume(messages, definitions):
            observed["after"] = json.loads(messages[1].content)["operations"]
            observed["calls_before_resume"] = len(backend.calls)
            assert "remember" not in {item["function"]["name"] for item in definitions}
            return continue_keywords()(messages, definitions)

        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), supporting, resume, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert observed["before"] == observed["after"]
            assert observed["calls_before_resume"] == 1
            operation, = outcome(service, sid, events)["operations"]
            assert operation["required"] and operation["direct"]
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
        finally:
            await service.close()
    asyncio.run(run())


def test_old_full_react_arguments_still_continue_an_existing_search(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        # Replay an already emitted full-form call without pretending it is the
        # newly advertised narrow interface.
        old_call = remote("find_assets", phrase=KEYWORDS[1], **{TASK: {
            "complete_request": True, "keywords": KEYWORDS[1:], "original_keywords": KEYWORDS[:1]}})
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), old_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert len(outcome(service, sid, events)["operations"]) == 1
            assert len(dialogue.inputs) == 3
        finally:
            await service.close()
    asyncio.run(run())


def test_pending_independent_search_keeps_full_arguments_then_both_queues_continue(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        queues = {"Find climate records": ["climate", "weather", "meteorology", "atmosphere"],
            "Find ocean records": ["ocean", "marine", "sea", "pelagic"]}

        def start(description):
            def choose(messages, definitions):
                tool = next(item["function"] for item in definitions if item["function"]["name"].endswith("_find_assets"))
                assert "phrase" in tool["parameters"]["properties"]
                target = next(item for item in json.loads(messages[1].content)["operations"]["items"]
                    if item["description"] == description)
                word = queues[description][0]
                arguments = {"phrase": word, GOAL: target["id"], TASK: {
                    "complete_request": False, "keywords": [word], "original_keywords": [word]}}
                Draft202012Validator(tool["parameters"]).validate(arguments)
                return action(tool["name"], **arguments)
            return choose

        def extend_both(messages, definitions):
            calls = [continue_keywords(words[1:], description)(messages, definitions).tool_calls[0]
                for description, words in queues.items()]
            return AIMessageChunk(content="", tool_calls=[{**call, "id": "continue-" + str(index)}
                for index, call in enumerate(calls)])

        dialogue = BareDialogue(action("remember", goals=[{"description": description, "tool": "find_assets"}
            for description in queues]), *[start(description) for description in queues], extend_both, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find climate records and ocean records separately")
            assert_completed(service, sid, events[-1])
            operations = outcome(service, sid, events)["operations"]
            assert len(operations) == 2 and len(backend.calls) == 8
            for operation in operations:
                assert operation["search"]["completed"] == queues[operation["description"]]
                assert len(operation["attempts"]) == 4
            assert set(operations[0]["search"]["result_ids"]).isdisjoint(operations[1]["search"]["result_ids"])
            assert len(dialogue.inputs) == 5
        finally:
            await service.close()
    asyncio.run(run())


def test_narrow_continuation_can_accompany_an_independent_requested_capability(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))

        def continue_and_inspect(messages, definitions):
            calls = [continue_keywords()(messages, definitions).tool_calls[0],
                native("inspect", reference="asset-2", **{TASK: {"complete_request": False}})(messages, definitions).tool_calls[0]]
            return AIMessageChunk(content="", tool_calls=[{**call, "id": "work-" + str(index)}
                for index, call in enumerate(calls)])

        dialogue = BareDialogue(goals({"description": "Find datasets", "tool": "find_assets"},
            {"description": "Inspect asset-2", "tool": "inspect"},
            calls=[discover(keywords=KEYWORDS[:1], complete=False)]), continue_and_inspect, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets and inspect asset-2")
            assert_completed(service, sid, events[-1])
            assert len(outcome(service, sid, events)["operations"]) == 2
            assert [args["phrase"] for name, args in backend.calls if name == "find_assets"] == KEYWORDS
            assert [args for name, args in backend.calls if name == "inspect"] == [{"reference": "asset-2"}]
            assert len(dialogue.inputs) == 3
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("invalid", ["business_override", "unknown_goal", "duplicate_goal"])
def test_invalid_narrow_continuation_does_not_dispatch_or_change_saved_search(engine, invalid):
    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        observed = {}

        def malformed(messages, definitions):
            observed["before"] = json.loads(messages[1].content)["operations"]
            call = continue_keywords()(messages, definitions).tool_calls[0]
            if invalid == "business_override":
                call["args"]["per_page"] = 2
            elif invalid == "unknown_goal":
                call["args"][GOAL] = "not-an-offered-goal"
            calls = [call]
            if invalid == "duplicate_goal":
                calls.append({**call, "id": "duplicate"})
            return AIMessageChunk(content="", tool_calls=calls)

        def repair(messages, definitions):
            observed["after"] = json.loads(messages[1].content)["operations"]
            observed["calls_before_repair"] = len(backend.calls)
            return continue_keywords()(messages, definitions)

        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), malformed, repair, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert observed["before"] == observed["after"]
            assert observed["calls_before_repair"] == 1
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())
