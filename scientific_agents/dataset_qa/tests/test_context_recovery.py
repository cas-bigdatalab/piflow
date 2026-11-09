"""Context capacity, bounded recovery, provenance and lossless summary coverage."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import httpx
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langchain_openai import ChatOpenAI
import pytest

from ..context import encode
from ..context_budget import TokenCounter, context_overflow, recovery_evidence, summary_batch
from ..contracts import Limits, QAError
from ..dialogue import BUILTINS, Dialogue
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_context_budget import cost, exchange
from .test_dataset_qa import Backend, collect, engine, result_cards, session


def test_counter_cache_is_bounded_and_usage_only_adjusts_upwards():
    counter = TokenCounter()
    text = '工具说明 {"name":"read_records"}'*100
    estimated = counter(text)
    assert 0<estimated<len(text.encode("utf-8"))
    counter.observe(estimated, estimated*2)
    assert counter(text)>=estimated*2
    corrected = counter(text)
    counter.observe(corrected, 1)
    assert counter(text)==corrected
    for index in range(300):
        counter(str(index))
    assert len(counter.cache)==256 and all(isinstance(key, bytes) for key in counter.cache)


def test_explicit_local_tokenizer_disables_saved_padding_and_truncation(tmp_path):
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    tokenizer = Tokenizer(WordLevel({"[UNK]": 0, "one": 1, "two": 2}, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    tokenizer.enable_truncation(2)
    tokenizer.enable_padding(length=10, pad_id=0, pad_token="[UNK]")
    path = tmp_path / "tokenizer.json"
    tokenizer.save(str(path))
    counter = TokenCounter(str(path))
    assert counter.mode=="local_tokenizer"
    assert counter("one two one two one")==5 and counter("one")==1


def test_concurrent_usage_samples_do_not_multiply_each_others_corrections():
    counter = TokenCounter()
    for _ in range(8):
        counter.observe(100, 200, request_scale=1.0)
    assert counter.scale==pytest.approx(2.2)


def test_old_40021_character_failure_fits_without_losing_required_information():
    dialogue = Dialogue(model=object())
    messages = dialogue.messages("查看详情和目录", {"memory": {"constraint": "x"}})
    missing = 40021-cost(messages, BUILTINS)
    messages = dialogue.messages("查看详情和目录", {"memory": {"constraint": "x"*(missing+1)}})
    assert cost(messages, BUILTINS)==40021
    bounded = dialogue.budget(messages, BUILTINS)
    assert bounded==messages
    assert dialogue.input_size(bounded, BUILTINS)<=65536


def test_expansion_does_not_load_more_ordinary_history():
    history = [{"role": role, "text": "Earlier discussion. "*200}
        for role in ["user", "assistant"]*6]
    messages = Dialogue(model=object()).messages("Read the current file", {"history": history})
    expanded = Dialogue(model=object()).budget(messages, BUILTINS)
    old_window = Dialogue(model=object(), limits=Limits(context_chars=40000)).budget(messages, BUILTINS)
    assert expanded==old_window


def test_rebuild_reads_full_artifact_and_keeps_calls_handles_and_required_fields():
    dialogue = Dialogue(model=object())
    url = "https://example.invalid/records.jsonl?signature="+"z"*300
    data = {"identifier": "source", "observations": [{"value": i} for i in range(500)], "url": url}
    card = {"result_id": "saved", "view_type": "data", "title": "Measurements", "data": data}
    # The old preview deliberately lacks the dependency URL.
    receipt = {"result_id": "saved", "data": {"observations": data["observations"]},
        "truncated": True, "executed": True, "objects": [{"handle": "source:1"}]}
    protected = {"memory": {"constraint": "Keep original units"}, "plan": {"revision": 1},
        "references": {"current": {"result_id": "saved", "path": ""}}}
    messages = dialogue.messages("Inspect the selected data", protected)+exchange(receipt, arguments={"url": url})
    before, artifact = deepcopy(messages), deepcopy(card)
    bounded = dialogue.recover(messages, BUILTINS, [card], required={"saved": {"inputs": {"/url": url}}})
    value = json.loads(bounded[-1].content)
    assert value["artifact"]["result_id"]=="saved" and value["required_evidence"]["inputs"]["/url"]==url
    assert value["objects"]==receipt["objects"] and value["executed"] is True
    assert bounded[-2]==messages[-2] and json.loads(bounded[1].content)==protected
    assert messages==before and card==artifact and cost(bounded, BUILTINS)<cost(messages, BUILTINS)


def test_focused_reads_and_unsaved_results_are_never_offloaded():
    dialogue = Dialogue(model=object())
    value = {"result_id": "saved", "data": {"text": "Important evidence. "*100}, "truncated": True}
    for name, cards in [("read_result", [{**value, "title": "File", "view_type": "data"}]), ("mcp_read", [])]:
        messages = dialogue.messages("Read this specific field", {})+exchange(value, name=name,
            arguments={"result_id": "saved", "path": "/nested", "offset": 3})
        bounded = dialogue.recover(messages, [], cards)
        assert bounded[-2:]==messages[-2:]


def test_parallel_result_recovery_preserves_each_call_and_result_identity():
    dialogue = Dialogue(model=object())
    cards = [{"result_id": str(i), "view_type": "data", "title": str(i),
        "data": {"available": bool(i), "rows": [{"source": str(i), "value": n} for n in range(300)]}} for i in range(2)]
    pairs = [exchange({"result_id": card["result_id"], "data": card["data"]},
        arguments={"source": card["result_id"]}, call_id=card["result_id"]) for card in cards]
    group = [AIMessage(content="", tool_calls=[pair[0].tool_calls[0] for pair in pairs]), *[pair[1] for pair in pairs]]
    messages = dialogue.messages("Compare both sources", {})+group
    bounded = dialogue.recover(messages, [], cards)
    assert bounded[-3]==group[0]
    for i, message in enumerate(bounded[-2:]):
        value = json.loads(message.content)
        assert message.tool_call_id==str(i) and value["result_id"]==str(i)
        assert value["data"]["available"] is bool(i)


def test_recovery_checks_use_full_data_and_preserve_dependency_values():
    url = "https://example.invalid/input.jsonl"
    data = {"rows": list(range(100)), "url": url}
    payload = {"operations": [{"id": "op1", "attempts": [{"state": "succeeded", "result_id": "r"}]}],
        "plan": {"operations": {"source": "op1", "next": "op2"}, "contracts": {
            "source": {"requires": [{"path": "/rows", "test": "at_least", "value": 100}]}},
            "spec": {"outcomes": [], "steps": [{"key": "source"},
                {"key": "next", "inputs": {"location": {"step": "source", "path": "/url"}}}]}}}
    before = deepcopy(payload)
    facts = recovery_evidence(payload, [{"result_id": "r", "data": data}])
    assert facts["r"]["checks"][0]["matched"] is True and facts["r"]["inputs"]["/url"]==url
    assert payload==before
    payload["plan"]["spec"]["steps"][1]["inputs"]["credential"] = {"step": "source", "path": "/token"}
    data["token"] = "private"
    assert "/token" not in recovery_evidence(payload, [{"result_id": "r", "data": data}])["r"]["inputs"]


@pytest.mark.parametrize("status,body,expected", [
    (400, {"error": {"code": "context_length_exceeded"}}, True),
    (400, {"message": "Input length exceeds the maximum allowed length"}, True),
    (400, {"code": "InvalidParameter", "message": "Range of input length should be [1, 65536]"}, True),
    (400, {"code": "InvalidParameter", "message": "Range of max_tokens should be [1, 8192]"}, False),
    (400, {"error": {"code": "invalid_parameters", "message": "Tool schema is invalid"}}, False),
    (429, {"message": "Too many input tokens"}, False),
    (503, {"message": "Context window exceeded"}, False),
    (400, {"message": "The tool description mentions context length"}, False),
])
def test_only_context_length_rejections_are_recoverable(status, body, expected):
    assert context_overflow(SimpleNamespace(status_code=status, body=body)) is expected


def test_partial_stream_is_not_reclassified_for_retry():
    class Rejection(Exception):
        status_code = 400
        body = {"error": {"code": "context_length_exceeded"}}

    class Model:
        async def astream(self, messages):
            yield AIMessageChunk(content="Already emitted")
            raise Rejection()

    async def run():
        dialogue = Dialogue(model=Model())
        stream = dialogue.respond(dialogue.messages("Answer", {}), [])
        assert (await anext(stream)).content=="Already emitted"
        with pytest.raises(Rejection):
            await anext(stream)
    asyncio.run(run())


@pytest.mark.parametrize("failures", [1, 2])
def test_real_sdk_recovery_preserves_results_and_never_repeats_mcp(engine, failures):
    backend = Backend()
    backend.items = [{"id": str(i), "title": "Dataset "+str(i), "description": "Measured values with units. "*30} for i in range(30)]
    requests, state = [], {"stage": 0, "failures": failures}

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        names = [item["function"]["name"] for item in body.get("tools", [])]
        alias = next((name for name in names if name.endswith("_search")), None)
        if not names:
            decision, state["stage"] = None, 0
        elif alias is None:
            decision = ("load_mcp_tools", {"server": "data"})
        elif state["stage"]==0:
            decision, state["stage"] = (alias, {"query": "observations"}), 1
        elif state["failures"]:
            state["failures"] -= 1
            return httpx.Response(400, json={"error": {"code": "context_length_exceeded", "message": "maximum context length exceeded"}})
        else:
            decision = ("deliver_results", {})
        delta = {"content": "已整理取得的数据集，请查看下方结果。"}
        if decision:
            name, args = decision
            delta = {"tool_calls": [{"index": 0, "id": "call-"+str(len(requests)), "type": "function",
                "function": {"name": name, "arguments": encode(args)}}]}
        chunk = {"id": str(len(requests)), "created": 0, "model": "test-model", "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": delta, "finish_reason": "tool_calls" if decision else "stop"}]}
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, text="data: "+encode(chunk)+"\n\ndata: [DONE]\n\n")

    class Conversation(Dialogue):
        def messages(self, message, context):
            history = [{"role": role, "text": "An earlier unrelated discussion. "*90} for role in ["user", "assistant"]*6]
            return super().messages(message, {**context, "history": history})

        async def summarize(self, summary, messages):
            return summary

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            model = ChatOpenAI(model="test-model", api_key="test", base_url="https://example.invalid/v1",
                http_async_client=client, max_retries=0)
            service = DatasetQA(engine, Conversation(model=model), backend.gateway())
            sid = session(service)
            try:
                values = await collect(service, sid, "List available observations", "first")
                (assert_completed if failures==1 else assert_handled)(service, None, values[-1])
                assert len(backend.calls)==1
                assert result_cards(values)[0]["data"]["items"]==backend.items
                assert not service.context_windows
                assert service.store.session("alice", sid)["active_task_id"] is None
                # The retry carries identical tool definitions and call IDs;
                # only its model view is smaller. There are no extra MCP calls.
                rejected, retry = requests[2:4]
                assert len(encode(retry))<len(encode(rejected)) and retry["tools"]==rejected["tools"]
                tool_ids = lambda value: [m["tool_call_id"] for m in value["messages"] if m["role"]=="tool"]
                assert tool_ids(retry)[-1:]==tool_ids(rejected)[-1:]
                if failures==2:
                    assert len(requests)==4  # One retry, then truthful retained-result closure.
                state["stage"] = 0
                later = await collect(service, sid, "List observations again", "second")
                assert_completed(service, None, later[-1])
                assert len(backend.calls)==2 and not service.context_windows
            finally:
                await service.close()
    asyncio.run(run())


def test_summary_batch_never_marks_a_partial_or_skipped_message_covered():
    rows = [{"id": i, "role": "user", "text": "Requirement "+str(i)+" "+"x"*200} for i in range(8)]
    selected = summary_batch("Previous", rows, 700, 32000)
    assert 0<len(selected)<len(rows) and selected==rows[:len(selected)]
    long = [{"id": 1, "role": "user", "text": "x"*12000}, rows[0]]
    assert summary_batch("", long, 10000, 32000)==long[:1]
    assert summary_batch("", long, 10000, 11000)==[]


@pytest.mark.parametrize("finish,text,valid", [("stop", "完整的摘要。"*400, True),
    ("length", "摘要被截断", False), ("stop", "", False), ("stop", "x"*6001, False)])
def test_summary_output_is_complete_or_not_committed(finish, text, valid):
    calls = []

    class Model:
        async def ainvoke(self, messages, **kwargs):
            calls.append((messages, kwargs))
            return AIMessage(content=text, response_metadata={"finish_reason": finish})

    async def run():
        dialogue = Dialogue(model=Model())
        if valid:
            assert await dialogue.summarize("", [{"role": "user", "text": "Keep the units"}])==text
        else:
            with pytest.raises(QAError, match="摘要"):
                await dialogue.summarize("", [{"role": "user", "text": "Keep the units"}])
        assert len(calls)==1 and calls[0][1]["max_tokens"]==1024
    asyncio.run(run())


def test_background_summary_cursor_matches_actual_input(engine):
    observed = []

    class Conversation(Dialogue):
        async def summarize(self, summary, messages):
            observed.append(deepcopy(messages))
            return "Retain the requested fields and original units."

    async def run():
        dialogue = Conversation(model=object(), limits=Limits(summary_input_chars=1200))
        service = DatasetQA(engine, dialogue, Backend().gateway())
        sid = session(service)
        try:
            for index in range(14):
                task, _ = service.store.submit("alice", sid, str(index), {"message": "User requirement. "*20}, None, service.owner)
                service.store.finish("alice", sid, task["id"], "COMPLETED", message="Assistant explanation. "*20)
            await service._summarize("alice", sid)
            context = json.loads(service.store.session("alice", sid)["context"])
            assert 0<len(observed[0])<16 and context["summary_after"]==observed[0][-1]["id"]
            remaining = service.store.memory("alice", sid, context["summary_after"])
            assert remaining[0]["id"]>observed[0][-1]["id"]
            assert len(service.store.memory("alice", sid, limit=100))==28
        finally:
            await service.close()
    asyncio.run(run())


def test_incomplete_background_summary_retains_previous_summary_and_cursor(engine):
    class Model:
        async def ainvoke(self, *args, **kwargs):
            return AIMessage(content="Unfinished", response_metadata={"finish_reason": "length"})

    async def run():
        service = DatasetQA(engine, Dialogue(model=Model()), Backend().gateway())
        sid = session(service)
        try:
            for index in range(12):
                task, _ = service.store.submit("alice", sid, str(index), {"message": "Keep original units"}, None, service.owner)
                service.store.finish("alice", sid, task["id"], "COMPLETED", message="Understood")
            assert service.store.save_summary("alice", sid, 0, "Previous summary", 1)
            await service._summarize("alice", sid)
            context = json.loads(service.store.session("alice", sid)["context"])
            assert context["summary"]=="Previous summary" and context["summary_after"]==1
        finally:
            await service.close()
    asyncio.run(run())


def test_summary_respects_input_budget_without_slicing_messages():
    class Model:
        async def ainvoke(self, *args, **kwargs):
            pytest.fail("An oversized summary must not be sent")

    async def run():
        dialogue = Dialogue(model=Model(), limits=Limits(input_tokens=100))
        rows = [{"role": "user", "text": "An indispensable requirement. "*100}]
        before = deepcopy(rows)
        with pytest.raises(QAError, match="摘要"):
            await dialogue.summarize("", rows)
        assert rows==before
    asyncio.run(run())
