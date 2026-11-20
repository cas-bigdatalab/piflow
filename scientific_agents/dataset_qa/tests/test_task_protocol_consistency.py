"""Exercise task admission and follow-up without model-side bookkeeping helpers."""
import asyncio
import json

import pytest

from ..capabilities import OBJECT, SUPPORTING, TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import KEYWORDS, SearchBackend, continue_keywords, discover, native, outcome, page
from .test_dataset_qa import action, collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, goals, text


def test_missing_search_task_is_corrected_before_any_mcp_dispatch(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))

        def correct(messages, definitions):
            # A schema omission must not create a half-declared search first.
            assert backend.calls == []
            assert not json.loads(messages[1].content).get("operations", {}).get("items")
            return discover()(messages, definitions)

        dialogue = BareDialogue(remote("find_assets", phrase=KEYWORDS[0]), correct, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert [arguments["phrase"] for _, arguments in backend.calls] == KEYWORDS
            assert len(dialogue.inputs) == 3
            operation, = outcome(service, sid, events)["operations"]
            assert operation["search"]["completed"] == KEYWORDS
            assert operation["required"] is True
            assert len(result_cards(events)[0]["data"]["items"]) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_partial_search_can_confirm_existing_goal_then_resume_without_repeating_work(engine):
    async def run():
        request = "Find chemical engineering datasets"
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))

        def confirm(messages, definitions):
            current, = json.loads(messages[1].content)["operations"]["items"]
            assert current["delivery_pending"] is True
            assert len(backend.calls) == 1
            return goals({"description": request, "tool": "find_assets"})(messages, definitions)

        def continue_search(messages, definitions):
            current, = json.loads(messages[1].content)["operations"]["items"]
            assert not current.get("delivery_pending") and not current.get("supporting")
            assert current["id"] == "op1"
            assert len(backend.calls) == 1
            return continue_keywords()(messages, definitions)

        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1], complete=False),
            confirm, continue_search, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, request)
            assert_completed(service, sid, events[-1])
            assert [arguments["phrase"] for _, arguments in backend.calls] == KEYWORDS
            operation, = outcome(service, sid, events)["operations"]
            assert operation["id"] == "op1" and operation["required"] is True
            assert operation["planned"] is True
            assert operation["search"]["completed"] == KEYWORDS
            assert len(operation["search"]["records"]) == 1
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_atomic_followup_missing_task_is_corrected_without_duplicate_execution(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find chemical engineering datasets", "search")
            assert_completed(service, sid, first[-1])

            def correct(messages, definitions):
                assert len(backend.calls) == 4
                return native("inspect", **{
                    OBJECT: "candidate:1", TASK: {"complete_request": True}})(messages, definitions)

            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1"}), correct, text()]
            events = await collect(service, sid, "Inspect this dataset", "detail")
            assert_completed(service, sid, events[-1])
            assert backend.calls[4:] == [("inspect", {"reference": "station-1"})]
            assert len(result_cards(events)) == 1
            assert len(dialogue.inputs) == 5
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_independent_goals_keep_atomic_calls_and_both_followup_deliveries(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find chemical engineering datasets", "search")
            assert_completed(service, sid, first[-1])
            # Explicit goals already supply semantic scope; no duplicate task
            # directive should be needed on each co-emitted operation.
            dialogue.responses = [goals(
                {"description": "Show details", "tool": "inspect", "object": "candidate:1"},
                {"description": "Show directory", "tool": "directory", "object": "candidate:1"},
                calls=[remote("inspect", **{OBJECT: "candidate:1"}),
                    remote("directory", **{OBJECT: "candidate:1"})]), text()]
            events = await collect(service, sid, "Show this dataset's details and directory", "both")
            assert_completed(service, sid, events[-1])
            assert sorted(backend.calls[4:], key=lambda call: call[0]) == [
                ("directory", {"reference": "station-1"}), ("inspect", {"reference": "station-1"})]
            cards = result_cards(events)
            assert {card["data"]["items"][0]["value"] for card in cards} == {"inspect", "directory"}
            assert len(cards) == 2 and len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("count", [1, 6])
def test_missing_original_keywords_is_corrected_before_dispatch_and_preserves_stop_policy(engine, count):
    async def run():
        backend = SearchBackend(lambda query, number: page(
            range(min(count, 5)) if number == 1 else [5], count))

        def correct(messages, definitions):
            assert not backend.calls
            return discover()(messages, definitions)

        dialogue = BareDialogue(remote("find_assets", phrase=KEYWORDS[0], **{
            TASK: {"complete_request": True, "keywords": KEYWORDS}}), correct, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            search = outcome(service, sid, events)["operations"][0]["search"]
            assert len(search["records"]) == count
            assert search["done"] is True
            if count == 6:
                assert search["stop"] == "enough"
                assert [args["page_number"] for _, args in backend.calls] == [1, 2]
                assert {args["phrase"] for _, args in backend.calls} == {KEYWORDS[0]}
            else:
                assert search["stop"] == "exhausted"
                assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert len(dialogue.inputs) == 3
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_supporting_scope_needs_no_task_but_does_not_become_a_deliverable(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find chemical engineering datasets", "search")
            assert_completed(service, sid, first[-1])

            def deliver_directory(messages, definitions):
                current, = json.loads(messages[1].content)["operations"]["items"]
                assert current["supporting"] is True
                assert not current.get("delivery_pending")
                assert backend.calls[4:] == [("inspect", {"reference": "station-1"})]
                return native("directory", **{
                    OBJECT: "candidate:1", TASK: {"complete_request": True}})(messages, definitions)

            # Replay the legacy supporting-only contract; current model schemas
            # explicitly request task scope for an otherwise unregistered call.
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1", SUPPORTING: True}),
                deliver_directory, text()]
            events = await collect(service, sid, "Show the directory, using details as supporting evidence", "directory")
            assert_completed(service, sid, events[-1])
            card, = result_cards(events)
            assert card["data"]["items"][0]["value"] == "directory"
            operations = outcome(service, sid, events)["operations"]
            supporting = next(item for item in operations if item["capability"]["name"] == "inspect")
            assert supporting["required"] is False and not supporting.get("inferred")
            assert backend.calls[4:] == [
                ("inspect", {"reference": "station-1"}), ("directory", {"reference": "station-1"})]
        finally:
            await service.close()
    asyncio.run(run())


def test_uncommitted_discovery_allows_explicit_scope_expansion(engine):
    async def run():
        request = "Find chemical engineering datasets and show the first directory"
        backend = SearchBackend(lambda query, number: page(["station-1"], 1))
        aliases = {}

        def begin(messages, definitions):
            for item in definitions:
                name = item["function"]["name"]
                for operation in ("find_assets", "directory"):
                    if name.endswith("_" + operation):
                        aliases[operation] = name
            return discover(keywords=KEYWORDS[:1], complete=False)(messages, definitions)

        def expand(messages, definitions):
            names = {item["function"]["name"] for item in definitions}
            assert aliases["find_assets"] in names and aliases["directory"] not in names
            assert "remember" in names
            memory = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
            assert aliases["directory"] in memory["parameters"]["$defs"]["Goal"]["properties"]["tool"]["enum"]
            assert len(backend.calls) == 1
            receipt = next(json.loads(message.content) for message in reversed(messages)
                if message.type == "tool" and json.loads(message.content).get("objects"))
            aliases["object"] = receipt["objects"][0]["handle"]
            return action("remember", goals=[
                {"description": request, "tool": aliases["find_assets"]},
                {"description": "Show the first directory", "tool": aliases["directory"], "object": aliases["object"]}])

        def execute_both(messages, definitions):
            names = {item["function"]["name"] for item in definitions}
            assert aliases["directory"] in names
            search = continue_keywords()(messages, definitions)
            directory = remote("directory", **{OBJECT: aliases["object"]})(messages, definitions)
            return search.model_copy(update={"tool_calls": [
                {**search.tool_calls[0], "id": "continue-search"},
                {**directory.tool_calls[0], "id": "requested-directory"}]})

        dialogue = BareDialogue(begin, expand, execute_both, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, request)
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for name, args in backend.calls if name == "find_assets"] == KEYWORDS
            assert [(name, args) for name, args in backend.calls if name != "find_assets"] == [
                ("directory", {"reference": "station-1"})]
            assert len(result_cards(events)) == 2 and len(dialogue.inputs) == 4
            assert len(outcome(service, sid, events)["operations"]) == 2
        finally:
            await service.close()
    asyncio.run(run())
