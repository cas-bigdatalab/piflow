"""Budget pressure must not change the meaning of navigation or delivery facts."""
from copy import deepcopy
import asyncio
import json

from langchain_core.messages import AIMessageChunk
import pytest

from ..contracts import QAError
from ..context_budget import navigation_identity
from ..dialogue import Dialogue, builtin_definitions
from ..operations import Operations
from ..service import DatasetQA
from .test_context_budget import cost, exchange
from .test_dataset_qa import Backend, action, collect, engine, session
from .test_decisions import BareDialogue, configured, seed, text
from .test_context_responses import respond
from .test_final_link_contract import FinalStream
from .test_reply_link_delivery import card, save_delivery
from .test_terminal_responses import replies, started


def navigation():
    return {
        "mcp_servers": {"items": [
            {"name": "measurements", "description": "Find and inspect observation datasets",
                "groups": [{"group": "catalogue", "source": "Measurements",
                    "operations": ["search", "inspect"], "inputs": ["query"], "outputs": ["dataset"]}],
                "discovered": False, "loaded_tools": 0},
            {"name": "files", "description": "Transform selected records", "discovered": True, "loaded_tools": 1},
        ], "next_offset": 2},
        "discovery_state": {"checked_servers": ["files"],
            "pending": [{"server": "measurements", "group": "catalogue", "next_offset": 4}], "complete": False},
        "artifact_catalog": {"tool": "find_artifacts", "guidance": "Find previously generated files only."},
    }


@pytest.mark.parametrize("extra", [0, 100])
def test_navigation_survives_when_unrelated_recent_files_exceed_budget(extra):
    dialogue = Dialogue(model=object())
    required = navigation()
    context = {**required, "available_artifacts": [
        {"handle": "artifact-"+str(i), "name": "old-export-"+str(i)+".csv", "fields": ["observation"]*20}
        for i in range(40)], "summary": "Earlier unrelated discussion. "*1000}
    messages = dialogue.messages("Find observations from this station", context)
    original = deepcopy(messages)
    ceiling = cost(dialogue.messages("Find observations from this station", required))+extra
    bounded = dialogue._budget(messages, [], len, ceiling)
    result = json.loads(bounded[1].content)
    for name, value in required.items():
        assert result[name] == value
    assert messages == original
    assert cost(bounded) <= ceiling
    assert len(result.get("available_artifacts", [])) < 40
    assert dialogue._budget(bounded, [], len, ceiling) == bounded


def test_delivery_acceptance_survives_beside_successful_execution_state():
    dialogue = Dialogue(model=object())
    status = [
        {"description": "Dataset details", "available": True, "requested": True,
            "delivered": True, "complete": True, "output": "result"},
        {"description": "File records", "available": False, "requested": True,
            "delivered": False, "complete": False, "output": "result"},
    ]
    required = {"execution_summary": {"business_results": 2, "inspected_saved_results": False},
        "operations": {"items": [{"id": "op1", "state": "succeeded"},
        {"id": "op2", "state": "succeeded"}]}, "delivery_status": status,
        "references": {"current": {"result_id": "selected", "path": "/items/0", "kind": "object"}}}
    context = {**required, "summary": "Old conversation. "*800}
    ceiling = cost(dialogue.messages("Show details and records", required))
    bounded = dialogue._budget(dialogue.messages("Show details and records", context), [], len, ceiling)
    assert json.loads(bounded[1].content) == required


def test_multiple_delivery_facts_remain_whole_with_latest_call_pair():
    dialogue = Dialogue(model=object())
    required = {"delivery_status": [{"description": f"Requested result {i}", "available": True,
        "requested": True, "delivered": i % 2 == 0, "complete": i % 2 == 0,
        "output": "result"} for i in range(16)], **navigation()}
    pair = exchange({"result_id": "saved", "data": {"available": False}},
        arguments={"source": "exact-selected-source"})
    minimal = dialogue.messages("Summarize the requested results", required)+pair
    ceiling = cost(minimal)
    actual = dialogue.messages("Summarize the requested results", {**required,
        "available_artifacts": [{"name": "unrelated.csv"}]*30})+pair
    bounded = dialogue._budget(actual, [], len, ceiling)
    assert json.loads(bounded[1].content) == required
    assert bounded[-2:] == pair
    assert cost(bounded) <= ceiling


def test_indispensable_navigation_cannot_be_silently_replaced_by_empty_rows():
    dialogue = Dialogue(model=object())
    required = navigation()
    required["mcp_servers"] = navigation_identity(required["mcp_servers"])
    messages = dialogue.messages("Find new datasets", required)
    original = deepcopy(messages)
    with pytest.raises(QAError, match="必要上下文") as failure:
        dialogue._budget(messages, [], len, cost(messages)-5)
    assert failure.value.code == "context_too_large"
    assert messages == original


def test_tight_navigation_omits_only_recoverable_descriptions():
    dialogue = Dialogue(model=object())
    required = navigation()
    thin = {**required, "mcp_servers": navigation_identity(required["mcp_servers"])}
    pair = exchange({"result_id": "saved", "data": {"value": 3}})
    ceiling = cost(dialogue.messages("Inspect the current result", thin)+pair)
    messages = dialogue.messages("Inspect the current result", required)+pair
    bounded = dialogue._budget(messages, [], len, ceiling)
    actual = json.loads(bounded[1].content)
    assert actual == thin
    assert [row["name"] for row in actual["mcp_servers"]["items"]] == ["measurements", "files"]
    assert actual["mcp_servers"]["items"][0]["groups"] == [{"group": "catalogue", "source": "Measurements"}]
    assert actual["mcp_servers"]["next_offset"] == 2
    assert actual["mcp_servers"]["details_tool"] == "list_mcp_servers"
    assert bounded[-2:] == pair


def test_saved_file_lookup_contract_distinguishes_new_source_retrieval():
    tool = next(item["function"] for item in builtin_definitions(artifacts=True)
        if item["function"]["name"] == "find_artifacts")
    assert "previously generated" in tool["description"]
    assert "does not search external data sources" in tool["description"]
    assert "empty saved-file lookup proves nothing" in tool["description"]
    assert "do not repeat data retrieval" not in tool["description"]


@pytest.mark.parametrize("mode", ["length", "character_limit"])
@pytest.mark.parametrize("second_available", [False, True])
def test_incomplete_final_prose_closes_every_goal_and_keeps_only_delivered_links(engine, mode, second_available):
    async def run():
        store, sid, tid = started(engine)
        first = card("first", "https://files.example/first.csv", "first.csv")
        second = card("second", "https://files.example/second.csv", "second.csv")
        delivered = ["first", "second"] if second_available else ["first"]
        save_delivery(store, sid, tid, [first, second], delivered=delivered)
        operations = Operations()
        for result_id, label, available in [("first", "第一个结果文件", True),
                ("second", "第二个结果文件", second_available)]:
            goal = operations.register(label, {"server": "files", "name": result_id}, planned=True)
            operations.start(goal, result_id)
            operations.finish(goal, result_id, result_id=result_id,
                acceptance="accepted" if available else "unavailable")
        payload = json.loads(store.task("alice", sid, tid)["payload"])
        payload["operations"] = operations.items
        assert store.write("alice", sid, tid, payload=payload)
        chunks = ([AIMessageChunk(content="已整理部分说明。", response_metadata={"finish_reason": "length"})]
            if mode == "length" else [AIMessageChunk(content="说明。"+"x"*16020),
                AIMessageChunk(content="不应再消费")])
        dialogue = FinalStream(chunks)
        service = DatasetQA(engine, dialogue, Backend().gateway())
        answer = {"text": ""}

        async def phase(*args):
            pass

        try:
            await service._final_reply("alice", sid, tid,
                dialogue.messages("请整理两个结果文件", {}), answer, phase)
            assert answer["incomplete"] is True
            assert "已为您提供：第一个结果文件" in answer["text"]
            if second_available:
                assert "第一个结果文件；第二个结果文件。" in answer["text"]
                assert "本次尚未提供" not in answer["text"]
            else:
                assert "本次尚未提供：第二个结果文件。" in answer["text"]
            assert dialogue.calls == 1 and dialogue.closed and dialogue.consumed == 1
            facts = json.loads(dialogue.input[1].content)["delivery_status"]
            assert [fact["state"] for fact in facts] == ["provided", "provided" if second_available else "unavailable"]
            assert store.finish("alice", sid, tid, "COMPLETED", message=answer["text"])
            _, public, saved = replies(store, sid, tid)
            assert saved == [public]
            assert public.count(first["data"]["downloadUrl"]) == 1
            assert public.count(second["data"]["downloadUrl"]) == int(second_available)
            assert "错误" not in public and "失败" not in public
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_read_of_historical_business_evidence_survives_final_filtering(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            original = await seed(service, dialogue, sid)
            dialogue.responses = [action("read_result", result_id=original["result_id"],
                path="/items", offset=1, limit=1), respond("evidence", [original["result_id"]]),
                text("已解释第二个历史候选。")]
            await collect(service, sid, "解释刚才第二个候选的内容", "explain-second")
            assert len(backend.calls) == 1 and not dialogue.responses
            messages, definitions = dialogue.inputs[-1]
            assert not definitions
            evidence = json.loads(messages[-1].content)["answer_evidence"]
            assert evidence[0]["result_id"] == original["result_id"]
            focused = [json.loads(message.content)["focused_evidence"] for message in messages[2:]
                if isinstance(message.content, str) and message.content.startswith('{"focused_evidence":')]
            assert len(focused) == 1
            assert focused[0]["result_id"] == original["result_id"]
            assert focused[0]["path"] == "/items" and focused[0]["offset"] == 1
            assert focused[0]["data"] == original["data"]["items"][1:2]
            summary = json.loads(messages[1].content)["execution_summary"]
            assert summary == {"business_results": 0, "inspected_saved_results": True}
        finally:
            await service.close()
    asyncio.run(run())
