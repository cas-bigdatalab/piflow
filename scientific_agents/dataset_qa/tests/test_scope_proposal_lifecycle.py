"""A rejected scope repair cannot discard or execute its retained typed calls."""
import asyncio
import json

from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, seed, text
from .test_independent_outcomes import batch, native, outcomes, read_backend


def test_missing_goal_tool_preserves_proposal_until_valid_goals_only_repair(engine):
    async def run():
        backend, dialogue = read_backend(), BareDialogue()
        backend.catalog["data"][2].inputSchema["properties"].update({
            "section": {"type": ["string", "null"]}, "number": {"type": "integer"},
            "enabled": {"type": "boolean"}})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)
            detail_args = {"reference": "resource-1"}
            directory_args = {"reference": "resource-1", "section": None, "number": 0, "enabled": False}

            def malformed_scope(messages, definitions):
                feedback = json.loads(messages[-1].content)["runtime_feedback"]
                assert feedback["detail"]["retained_proposal"] is True
                assert len(backend.calls) == 1
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                return action("remember", goals=[{"description": "Dataset details"}])

            def valid_scope(messages, definitions):
                feedback = json.loads(messages[-1].content)["runtime_feedback"]
                assert feedback["error"] == "invalid_parameters"
                assert any(error["path"][-1] == "tool" for error in feedback["detail"]["errors"])
                assert len(backend.calls) == 1
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                # The repair supplies only missing semantic scope. Original
                # business values are neither regenerated nor auto-corrected.
                return outcomes()(messages, definitions)

            dialogue.responses = [batch(native("inspect", True, **detail_args),
                native("preview", True, **directory_args)), malformed_scope, valid_scope, text()]
            events = await collect(service, sid, "Show the dataset details and directory", "malformed-scope")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) - baseline == 4
            assert backend.calls[1:] == [("data", "inspect", detail_args), ("data", "preview", directory_args)]
            delivered = backend.calls[-1][2]
            assert delivered["section"] is None
            assert type(delivered["number"]) is int and delivered["enabled"] is False
            assert len(result_cards(events)) == 2
            ledger = payload(service, sid, events)
            assert "scope_proposal" not in ledger
            assert all(item["required"] and item["state"] == "succeeded" for item in ledger["operations"])
            replay = await collect(service, sid, "Show the dataset details and directory", "malformed-scope")
            assert result_cards(replay) == result_cards(events) and len(backend.calls) == 3
        finally:
            await service.close()
    asyncio.run(run())
