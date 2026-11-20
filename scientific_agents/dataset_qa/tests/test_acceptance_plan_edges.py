"""Acceptance probes for scheduler boundaries using unmodified model replies."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk
import pytest

from ..contracts import Limits
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import action, collect, engine, load, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_plan_decision_progress import spec
from .test_planning import approve


@pytest.mark.parametrize("max_calls,completed", [(4, True), (3, False)])
def test_review_on_last_model_round_dispatches_only_with_call_budget(engine, max_calls, completed):
    async def run():
        backend = configured()
        backend.catalog["data"][0].meta["piflow"]["qa"]["plan_required"] = True
        dialogue = BareDialogue(load(), action("remember", plan=spec()), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=3, max_calls=max_calls)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified records")
            saved = payload(service, sid, events)
            assert saved["plan"]["reviewed"] == saved["plan"]["revision"] == 1
            if completed:
                assert_completed(service, sid, events[-1])
                assert backend.calls == [("data", "search", {"query": "records"})]
                assert len(dialogue.inputs) == 4
                assert dialogue.inputs[-1][1] == []
            else:
                assert_handled(service, sid, events[-1], "step_limit")
                assert backend.calls == []
                assert len(dialogue.inputs) == 3
        finally:
            await service.close()
    asyncio.run(run())


def test_coemitted_plan_and_review_cannot_commit_partial_state(engine):
    async def run():
        backend = configured()
        plan = action("remember", plan=spec()).tool_calls[0]
        review = action("review_plan", revision=1, covered=["retrieve"]).tool_calls[0]
        combined = AIMessageChunk(content="", tool_calls=[plan, review])

        def corrected(messages, definitions):
            assert "plan" not in json.loads(messages[1].content)
            assert not backend.calls
            return action("remember", plan=spec())

        dialogue = BareDialogue(load(), combined, corrected, approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified records")
            assert_completed(service, sid, events[-1])
            saved = payload(service, sid, events)
            assert len(saved["operations"]) == 1
            assert saved["plan"]["reviewed"] == saved["plan"]["revision"] == 1
            assert backend.calls == [("data", "search", {"query": "records"})]
        finally:
            await service.close()
    asyncio.run(run())


def test_plain_text_before_review_cannot_claim_completion_and_can_recover(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), action("remember", plan=spec()),
            text("The records are ready."), approve, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the specified records")
            assert_completed(service, sid, events[-1])
            assert backend.calls == [("data", "search", {"query": "records"})]
            assert payload(service, sid, events)["plan"]["reviewed"] == 1
            # Premature model prose is not published as an evidence-backed answer.
            assert "The records are ready." not in json.dumps(events, ensure_ascii=False)
        finally:
            await service.close()
    asyncio.run(run())
