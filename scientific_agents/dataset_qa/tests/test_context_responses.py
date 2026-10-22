"""Evidence answers are distinct from new execution and cannot erase receipts."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk
import pytest

from ..contracts import QAError
from ..dialogue import Dialogue
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, seed, text


def respond(mode="conversation", ids=()):
    return action("respond_from_context", mode=mode, result_ids=list(ids),
        reason="The user asks about saved evidence or conversation state, not a new operation.")


def test_saved_evidence_can_be_explained_without_new_execution_or_republication(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            card = await seed(service, dialogue, sid)
            before = len(dialogue.inputs)
            dialogue.responses = [respond("evidence", [card["result_id"]]), text("There are two saved candidates.")]
            values = await collect(service, sid, "Explain the saved candidates", "explain")
            assert values[-1]["status"]=="COMPLETED" and not result_cards(values)
            assert len(backend.calls)==1 and len(dialogue.inputs)-before==2
            ledger = payload(service, sid, values)
            assert ledger["response_basis"]["executed"] is False and not ledger.get("operations")
            evidence = json.loads(dialogue.inputs[-1][0][-1].content)["answer_evidence"]
            assert evidence[0]["result_id"]==card["result_id"]
            assert evidence[0]["data"]["items"][0]["id"]=="a"
            assert "response_basis" in json.loads(dialogue.inputs[-1][0][1].content)
            assert await collect(service, sid, "Explain the saved candidates", "explain")==values
            assert len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_confirming_selection_needs_no_unrelated_mcp_call(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [AIMessageChunk(content="", tool_calls=[
                *action("remember", selected=["candidate:1", "candidate:2"]).tool_calls,
                *respond().tool_calls]), text("Both choices have been saved.")]
            values = await collect(service, sid, "Keep both datasets selected", "select")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            saved = json.loads(service.store.session("alice", sid)["context"])
            assert [ref["path"] for ref in saved["references"]["selected"]]==["/items/0", "/items/1"]
            assert not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())


def test_context_answer_cannot_read_another_sessions_artifact(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            first = session(service, request="first")
            card = await seed(service, dialogue, first)
            second = session(service, request="second")
            dialogue.responses = [respond("evidence", [card["result_id"]]), respond(), text("No data has been selected in this session.")]
            values = await collect(service, second, "Describe this session", "explain")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            ledger = payload(service, second, values)
            assert ledger["response_basis"]["result_ids"]==[]
            assert card["result_id"] not in json.dumps(json.loads(dialogue.inputs[-1][0][-1].content))
        finally:
            await service.close()
    asyncio.run(run())


def test_existing_execution_goal_cannot_be_replaced_with_context_response(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            dialogue.responses = [load(), goals({"description": "Retrieve evidence", "tool": "search", "output": "answer"},
                calls=[remote("search", query="data")]), respond(), action("deliver_results"), text("Retrieved two records.")]
            sid = session(service)
            values = await collect(service, sid, "Search for evidence", "search")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            ledger = payload(service, sid, values)
            assert "response_basis" not in ledger and ledger["operations"][0]["state"]=="succeeded"
            assert any("tool_not_loaded" in str(message.content) for message in dialogue.inputs[-1][0])
        finally:
            await service.close()
    asyncio.run(run())


def test_unsupported_answer_checks_capabilities_and_finishes_without_fake_execution(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(respond("unsupported"), load(), respond("unsupported"),
            text("The inspected tools support retrieval, details and sampling; this transformation is not available."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            values = await collect(service, sid, "Explain whether you support a transformation", "capability")
            assert values[-1]["status"]=="COMPLETED" and not backend.calls
            basis = payload(service, sid, values)["response_basis"]
            assert basis["mode"]=="unsupported" and len(basis["available_capabilities"])==4
            assert not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("raw", [
    '{"count":1,"count":2}', '{"filter":{"x":1,"x":2}}',
    '{"count":1e999}', '{"count":NaN}', '{"count":Infinity}',
])
def test_ambiguous_or_nonfinite_wire_arguments_are_rejected_before_dispatch(raw):
    reply = AIMessageChunk(content="", tool_call_chunks=[{
        "id": "call", "name": "sample", "args": raw, "index": 0}])
    with pytest.raises(QAError) as failure:
        Dialogue.validate_calls(reply)
    assert failure.value.code=="invalid_tool_call"


def test_context_and_native_actions_cannot_be_mixed(engine):
    async def run():
        backend = configured()
        def invalid(messages, definitions):
            return AIMessageChunk(content="", tool_calls=[*respond().tool_calls,
                *remote("search", query="unrequested")(messages, definitions).tool_calls])
        dialogue = BareDialogue(load(), invalid, respond(), text("The available capabilities are described."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Explain your capabilities", "explain")
            assert values[-1]["status"]=="COMPLETED" and not backend.calls
        finally:
            await service.close()
    asyncio.run(run())
