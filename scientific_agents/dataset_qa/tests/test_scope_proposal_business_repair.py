"""Scope repair must stop replaying a proposal once its business inputs fail."""
import asyncio
import json

import pytest

from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, goals, text
from .test_independent_outcomes import batch, native
from .test_resource_index import Backend, POLICY


@pytest.mark.parametrize("wrong_parent", ["None", "root"])
def test_business_input_failure_discards_retained_calls_until_explicit_native_replacement(engine, wrong_parent):
    async def run():
        # Keep explicit null as a runtime compatibility case even though the
        # current model-facing schema expresses that value through omission.
        backend, dialogue = Backend(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        async def no_background(*args, **kwargs):
            return None
        service.resources.observe = no_background
        sid = session(service)
        try:
            baseline = len(backend.calls)
            declare = goals({"description": "Details", "tool": "dataset_info"},
                {"description": "Directory", "tool": "list_tree"})
            wrong = {"dataset": "one", "folder": wrong_parent}

            def repeat_goals_after_rejection(messages, definitions):
                detail = json.loads(messages[-1].content)["runtime_feedback"]["detail"]
                assert detail["origin"] == "directory_parent" and detail["dispatched"] is False
                assert detail["retained_proposal"] is False and detail["correction_action"] == "replace_calls"
                assert "remember.goals alone cannot repair business arguments" in detail["guidance"]
                assert len(backend.calls) == baseline
                return declare(messages, definitions)

            def corrected_native(messages, definitions):
                assert len(backend.calls) == baseline  # Pure goals did not resurrect the bad proposal.
                ledger = json.loads(messages[1].content)["operations"]["items"]
                assert len(ledger) == 2 and all(item["state"] == "pending" for item in ledger)
                return batch(native("dataset_info", dataset="one"),
                    native("list_tree", dataset="one", folder=None))(messages, definitions)

            dialogue.responses = [batch(native("dataset_info", dataset="one"), native("list_tree", **wrong)),
                declare, repeat_goals_after_rejection, corrected_native, text()]
            events = await collect(service, sid, "Show details and root directory for dataset=one", "repair-inputs")
            assert_completed(service, sid, events[-1])
            assert backend.calls[baseline:] == [("dataset_info", {"dataset": "one"}),
                ("list_tree", {"dataset": "one", "folder": None})]
            assert len(result_cards(events)) == 2
        finally:
            await service.close()
    asyncio.run(run())
