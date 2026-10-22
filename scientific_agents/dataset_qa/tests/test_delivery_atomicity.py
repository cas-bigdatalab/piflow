"""Rejected delivery must not turn an intermediate receipt into a fixed goal."""
import asyncio
import json

import pytest

from ..capabilities import OBJECT
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text


@pytest.mark.parametrize("failure", ["ownership", "references"])
def test_rejected_delivery_does_not_freeze_the_intermediate_artifact(engine, failure):
    def bad_delivery(messages, definitions):
        if failure=="ownership":
            return action("deliver_results", result_ids=["not-a-real-result"])
        return action("deliver_results", references={"candidates": {
            "result_id": "not-a-displayed-result", "path": "/items", "kind": "object"}})

    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resource"), bad_delivery,
            remote("inspect", **{OBJECT: "object:1"}), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "Find a resource and show its details")
            assert values[-1]["status"]=="COMPLETED"
            card, = result_cards(values)
            assert card["title"].endswith("inspect") and card["data"]["items"][0]["reference"]=="a"
            ledger = payload(service, sid, values)
            assert ledger["operations"][0]["required"] is False
            assert ledger["operations"][1]["required"] is True
            assert ledger["delivery_sources"]==[card["result_id"]]
            assert [call[1] for call in backend.calls]==["search", "inspect"]
            assert len(dialogue.inputs)==6  # One existing correction turn; no extra evaluator.
        finally:
            await service.close()
    asyncio.run(run())
