"""Budget real message envelopes without losing task state or tool provenance."""
from copy import deepcopy
import asyncio
import json

from langchain_core.messages import AIMessage, ToolMessage
import pytest

from ..context import encode
from ..contracts import Limits, QAError, Server
from ..dialogue import BUILTINS, Dialogue, SYSTEM
from ..mcp import MCPGateway
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, remote, result_cards, session
from .test_decisions import text


def cost(messages, tools=()):
    return len(encode([message.model_dump(mode="json", exclude_none=True) for message in messages]))+len(encode(list(tools)))


def exchange(value, *, name="mcp_read", arguments=None, call_id="call"):
    return [AIMessage(content="", tool_calls=[{"name": name, "args": arguments or {}, "id": call_id}]),
        ToolMessage(content=encode(value), tool_call_id=call_id, name=name)]


@pytest.mark.parametrize("count", [1, 3])
def test_latest_call_group_has_space_before_old_history(count):
    protected = {"references": {"current": {"result_id": "source", "path": "/items/1", "value": {
        "downloadUrl": "https://example.invalid/file.jsonl?signature="+"x"*700}}},
        "operations": {"items": [{"id": "op1", "description": "Keep measurements in original units"}]},
        "memory": {"units": "Keep original units"}}
    value = {"result_id": "saved", "data": {"records": [{"value": 4, "unit": "original"}]}, "next_offset": 5}
    calls = [exchange(value, arguments={"url": protected["references"]["current"]["value"]["downloadUrl"]},
        call_id=str(index)) for index in range(count)]
    group = [AIMessage(content="Check the requested file. "*100,
        tool_calls=[pair[0].tool_calls[0] for pair in calls]), *[pair[1] for pair in calls]]
    dialogue = Dialogue(model=object())
    minimal = dialogue.messages("Read these records", protected)+group
    dialogue.limits = Limits(context_chars=cost(minimal, BUILTINS)+500)
    messages = dialogue.messages("Read these records", {**protected,
        "history": [{"role": "user", "text": "Earlier discussion. "*30},
            {"role": "assistant", "text": "Earlier answer. "*30}]})+group
    original = deepcopy(messages)
    bounded = dialogue.budget(messages, BUILTINS)
    assert bounded[-len(group):]==group
    for key, item in protected.items():
        assert json.loads(bounded[1].content)[key]==item
    assert messages==original and cost(bounded, BUILTINS)<=dialogue.limits.context_chars


def test_same_result_id_is_not_proof_of_duplicate_content():
    dialogue = Dialogue(model=object())
    card = {"result_id": "saved", "data": {"type": "object", "required": ["measurement"]}}
    pool = {"items": [{"result_id": "saved", "data": {"type": "object"}, "truncated": True}], "total": 1}
    messages = dialogue.messages("Inspect required fields", {"evidence": pool})+exchange(card)
    bounded = dialogue.budget(messages, BUILTINS)
    assert json.loads(bounded[-1].content)==card
    assert json.loads(bounded[1].content)["evidence"]==pool


def test_exact_duplicate_body_keeps_receipt_metadata_and_call_arguments():
    dialogue = Dialogue(model=object())
    body = {"rows": [{"value": 1}]}
    pool = {"items": [{"result_id": "saved", "data": body}], "total": 1}
    receipt = {"result_id": "saved", "data": body, "executed": True, "next_offset": 1,
        "field_paths": {"rows": "/rows"}, "objects": [{"handle": "source:1"}], "truncated": True}
    messages = dialogue.messages("Read records", {"evidence": pool})+exchange(receipt, arguments={"size": 1})
    bounded = dialogue.budget(messages, BUILTINS)
    assert json.loads(bounded[1].content)["evidence"]==pool
    assert json.loads(bounded[-1].content)=={key: value for key, value in receipt.items() if key!="data"}
    assert bounded[-2]==messages[-2]


def test_matching_structured_body_does_not_hide_different_text_content():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": {"value": 1},
        "content": [{"type": "text", "text": "Calibration is required before analysis."}]}
    pool = {"items": [{"result_id": "saved", "data": value["data"]}], "total": 1}
    bounded = dialogue.budget(dialogue.messages("Inspect the measurement", {"evidence": pool})+exchange(value), BUILTINS)
    assert json.loads(bounded[-1].content)==value


@pytest.mark.parametrize("receipt,pool", [
    ({"data": {"value": 1}}, {"data": {"value": True}}),
    ({"data": {"value": 1}, "offset": 1}, {"data": {"value": 1}, "offset": 0}),
    ({"data": {"value": 1}, "path": "/observations"}, {"data": {"value": 1}, "path": "/controls"}),
])
def test_json_types_and_reading_scope_are_part_of_duplicate_identity(receipt, pool):
    dialogue = Dialogue(model=object())
    receipt = {"result_id": "saved", **receipt}
    pool = {"items": [{"result_id": "saved", **pool}], "total": 1}
    bounded = dialogue.budget(dialogue.messages("Compare the result", {"evidence": pool})+exchange(receipt), BUILTINS)
    assert json.loads(bounded[-1].content)==receipt


def test_control_message_keeps_status_and_metadata_alongside_data():
    dialogue = Dialogue(model=object())
    value = {"status": "resolved", "object": "source:1", "data": {"name": "observations.jsonl"}}
    bounded = dialogue.budget(dialogue.messages("Resolve this file", {})+exchange(value, name="resolve_resource"), BUILTINS)
    assert json.loads(bounded[-1].content)==value


def test_optional_evidence_is_not_reintroduced_as_a_second_smaller_preview():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": {"text": "An observation with units. "*70}, "truncated": True}
    minimal = dialogue.messages("Read records", {})+exchange(value)
    dialogue.limits = Limits(context_chars=cost(minimal, BUILTINS)+50)
    pool = {"items": [{"result_id": "older", "data": {"text": "Old observations. "*250}}], "total": 1}
    bounded = dialogue.budget(dialogue.messages("Read records", {"evidence": pool})+exchange(value), BUILTINS)
    assert "evidence" not in json.loads(bounded[1].content)
    assert json.loads(bounded[-1].content)==value
    assert cost(bounded, BUILTINS)<=dialogue.limits.context_chars


def test_focused_reads_keep_their_page_and_pointer_even_when_result_ids_match():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": ["same value"], "next_offset": 2}
    pool = {"items": [{"result_id": "saved", "data": value["data"]}], "total": 1}
    messages = dialogue.messages("Compare fields", {"evidence": pool})
    for index, path in enumerate(["/observations", "/controls"]):
        messages += exchange(value, name="read_result", arguments={"result_id": "saved", "path": path, "offset": index},
            call_id=str(index))
    bounded = dialogue.budget(messages, BUILTINS)
    assert bounded[-4:]==messages[-4:]


def test_escaped_content_is_counted_as_a_complete_message():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": {"text": 'quoted "value" and \\ path\n'*150}, "truncated": True}
    messages = dialogue.messages("Read records", {"summary": "Earlier discussion. "*500})+exchange(value)
    required = dialogue.messages("Read records", {})+exchange(value)
    dialogue.limits = Limits(context_chars=cost(required, BUILTINS)+300)
    bounded = dialogue.budget(messages, BUILTINS)
    assert bounded[-2:]==messages[-2:]
    assert cost(bounded, BUILTINS)<=dialogue.limits.context_chars


def test_small_context_keeps_history_and_bounded_result_without_progressive_cropping():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": {"schema": {"fields": ["value", "time"]}}, "truncated": True}
    messages = dialogue.messages("Read this file", {"memory": {"filter": "After 2025"},
        "summary": "Keep the original units", "history": [{"role": "user", "text": "Use file B"},
            {"role": "assistant", "text": "File B selected"}]})+exchange(value)
    bounded = dialogue.budget(messages, BUILTINS)
    assert json.loads(bounded[1].content)==json.loads(messages[1].content)
    assert bounded[0]==messages[0] and bounded[2:]==messages[2:]
    assert dialogue.budget(bounded, BUILTINS)==bounded


def test_minimum_input_overflow_does_not_truncate_identifiers_or_rewrite_call_arguments():
    dialogue = Dialogue(model=object(), limits=Limits(context_chars=len(SYSTEM)+1000))
    messages = dialogue.messages("Inspect this file", {})+exchange({"result_id": "saved", "data": {}},
        arguments={"download_url": "https://example.invalid/"+"x"*2000})
    original = deepcopy(messages)
    with pytest.raises(QAError) as failure:
        dialogue.budget(messages, [])
    assert failure.value.code=="context_too_large" and messages==original
    assert failure.value.detail["context_chars"]==dialogue.limits.context_chars
    assert "download_url" not in encode(failure.value.detail)


@pytest.mark.parametrize("limit", [32000, 40000])
@pytest.mark.parametrize("tool", ["get_corpus_file_schema", "read_corpus_file_records"])
def test_real_model_budget_path_handles_long_conversations_without_repeating_mcp(engine, monkeypatch, limit, tool):
    from mcp_servers import corpus_mcp

    url = "https://example.invalid/observations.jsonl"
    calls, inputs = [], []
    records = [{"value": index, "unit": "original", "description": 'A "quoted" observation. '*40} for index in range(3)]
    schema = {"type": "object", "required": ["value", "unit"], "properties": {
        "value": {"type": "number"}, "unit": {"type": "string", "description": "Keep the original units."}}}
    payload = {"downloadUrl": url, "previewable": True,
        **({"schema": schema} if tool=="get_corpus_file_schema" else {"data": records, "returnedCount": 3})}

    def upstream(download_url, **kwargs):
        assert download_url==url
        calls.append((download_url, kwargs))
        return deepcopy(payload)

    monkeypatch.setattr(corpus_mcp, "get_file_schema" if tool=="get_corpus_file_schema" else "get_file_records", upstream)

    class Model:
        definitions = []

        def __init__(self):
            self.responses = []
            for _ in range(3):
                self.responses.extend([remote(tool, download_url=url), action("deliver_results"),
                    text("Available file content is shown.")])

        def bind_tools(self, definitions, **kwargs):
            self.definitions = definitions
            return self

        async def astream(self, messages):
            # Production Dialogue.respond calls the real budget before this
            # fake provider. Both planning and final-answer paths are exercised.
            definitions = self.definitions
            self.definitions = []
            assert cost(messages, definitions)<=limit
            inputs.append(deepcopy(messages))
            response = self.responses.pop(0)
            yield response(messages, definitions) if callable(response) else response

    class Conversation(Dialogue):
        def messages(self, message, context):
            return super().messages(message, {**context, "memory": {"units": "Keep original units"},
                "history": [{"role": "user", "text": "Previous dataset discussion. "*90},
                    {"role": "assistant", "text": "Previous dataset explanation. "*90}]})

        async def summarize(self, summary, messages):
            return summary

    async def run():
        limits = Limits(context_chars=limit)
        model = Model()
        service = DatasetQA(engine, Conversation(model=model, limits=limits),
            MCPGateway({"piflow-corpus": Server(corpus_mcp.mcp)}, limits=limits))
        sid = session(service)
        try:
            for index in range(3):
                values = await collect(service, sid, "Show the requested file content: " + url, str(index))
                assert_completed(service, None, values[-1])
                assert result_cards(values)[0]["data"]["items"][0]==payload
            assert len(calls)==3 and len(inputs)==9 and not model.responses
            assert all(json.loads(messages[1].content)["memory"]["units"]=="Keep original units" for messages in inputs)
            for messages in inputs[1::3]:
                receipts = [json.loads(message.content) for message in messages if isinstance(message, ToolMessage)
                    and message.name.startswith("mcp_")]
                evidence = json.loads(messages[1].content).get("evidence", {}).get("items", [])
                assert any(item.get("data")==payload for item in [*receipts, *evidence])
        finally:
            await service.close()
    asyncio.run(run())
