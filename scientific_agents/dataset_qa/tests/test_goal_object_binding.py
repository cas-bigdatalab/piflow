"""Outcome targets require the same declared bindings as native calls."""
import asyncio
from copy import deepcopy
import json

import pytest

from ..capabilities import OBJECT, TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import KEYWORDS, SearchBackend, continue_keywords, discover, native, outcome, page
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, goals, text


@pytest.mark.parametrize("preceding_valid_goal", [False, True])
def test_unbound_goal_object_cannot_split_an_active_search_or_commit_batch(engine, preceding_valid_goal):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        observed = {}

        def invalid_goal(messages, definitions):
            observed["before"] = deepcopy(json.loads(messages[1].content)["operations"])
            values = []
            if preceding_valid_goal:
                values.append({"description": "Inspect the first candidate", "tool": "inspect", "object": "object:1"})
            values.append({"description": "Find chemical engineering datasets", "tool": "find_assets", "object": "object:1"})
            return action("remember", goals=values)

        def continue_existing_search(messages, definitions):
            observed["after"] = deepcopy(json.loads(messages[1].content)["operations"])
            observed["feedback"] = [json.loads(message.content)["runtime_feedback"] for message in messages
                if '"runtime_feedback"' in message.content]
            return continue_keywords()(messages, definitions)

        dialogue = BareDialogue(goals({"description": "Find chemical engineering datasets", "tool": "find_assets"},
            calls=[discover(keywords=KEYWORDS[:1], complete=False)]), invalid_goal, continue_existing_search, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert observed["after"] == observed["before"], "Rejected goal declarations must leave targets, scope and receipts unchanged"
            assert any(value.get("error") == "invalid_parameters" and value.get("executed") is False
                for value in observed["feedback"]), "An object on a capability without bindings must be rejected before registration"
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["find_assets"] * len(KEYWORDS)
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            operation, = outcome(service, sid, events)["operations"]
            assert operation["target"] is None and operation["required"] is True
            assert operation["search"]["done"] and operation["search"]["stop"] == "exhausted"
        finally:
            await service.close()
    asyncio.run(run())


def test_bound_capability_keeps_explicit_goal_object(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        dialogue = BareDialogue(native("find_assets", phrase="asset-1", **{TASK: {
            "complete_request": True, "keywords": None, "original_keywords": None}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            initial = await collect(service, sid, "Find asset-1 only", "seed")
            assert_completed(service, sid, initial[-1])
            dialogue.responses = [goals({"description": "Inspect the selected dataset", "tool": "inspect",
                "object": "candidate:1"}, calls=[native("inspect", **{OBJECT: "candidate:1",
                    TASK: {"complete_request": True}})]), text()]
            events = await collect(service, sid, "Inspect the first dataset", "inspect")
            assert_completed(service, sid, events[-1])
            assert backend.calls[-1] == ("inspect", {"reference": "asset-1"})
            operation, = outcome(service, sid, events)["operations"]
            assert operation["target"] is not None and operation["required"] is True
        finally:
            await service.close()
    asyncio.run(run())
