"""Validated keyword continuations retain their explicitly saved role."""
import asyncio

import pytest

from ..capabilities import OBJECT, SUPPORTING, TASK
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_bounded_discovery import KEYWORDS, SearchBackend, continue_keywords, discover, native, outcome, page
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, goals, text


@pytest.mark.parametrize("supporting", [True, False])
def test_saved_auxiliary_continuation_can_accompany_a_requested_outcome_without_reclassifying_inferred_work(engine, supporting):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        first = discover(keywords=KEYWORDS[:1], complete=False, **({SUPPORTING: True} if supporting else {}))
        combined = goals({"description": "Inspect asset-1", "tool": "inspect", "object": "object:1"}, calls=[
            continue_keywords(), native("inspect", **{OBJECT: "object:1", TASK: {"complete_request": False}})])
        dialogue = BareDialogue(first, *([combined, text()] if supporting else [combined] * 3 + [text()]))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid,
                "Find chemical engineering datasets as supporting evidence and inspect asset-1")
            saved = outcome(service, sid, events)
            if supporting:
                assert_completed(service, sid, events[-1])
                assert [args["phrase"] for name, args in backend.calls if name == "find_assets"] == KEYWORDS
                assert [name for name, _ in backend.calls].count("inspect") == 1
                search = next(item for item in saved["operations"] if item.get("search"))
                assert search["search"]["done"] and not search["required"] and not search.get("inferred")
                assert len(saved["operations"]) == 2 and len(result_cards(events)) == 1
                assert len(dialogue.inputs) == 3
            else:
                assert_handled(service, sid, events[-1], "no_progress")
                assert len(backend.calls) == 1
                search, = saved["operations"]
                assert search.get("inferred") and not search["required"] and not search["search"]["done"]
        finally:
            await service.close()
    asyncio.run(run())
