"""Delivered links remain usable in streamed replies, history and recovery."""
import asyncio
from copy import deepcopy
import csv
import io
import json

import pytest
from sqlalchemy import update

from mcp_servers.corpus_mcp import mcp
from ..contracts import Server
from ..mcp import MCPGateway, ToolSession
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import files
from .test_local_artifacts import download_client, file_plan
from .test_planning import approve
from .test_terminal_responses import replies, started


def card(result_id, url, name="result.csv"):
    return {"result_id": result_id, "view_type": "url", "title": "导出文件",
        "data": {"downloadUrl": url, "resource": {"name": name, "downloadUrl": url}}}


def save_delivery(store, sid, tid, cards, delivered=None):
    for value in cards:
        assert store.write("alice", sid, tid, card=value)
    state = json.loads(store.task("alice", sid, tid)["payload"])
    state.update(delivery=delivered if delivered is not None else [value["result_id"] for value in cards],
        delivery_sources=[value["result_id"] for value in cards])
    assert store.write("alice", sid, tid, payload=state)


@pytest.mark.parametrize("status", ["COMPLETED", "FAILED", "CANCELLED"])
def test_terminal_reply_adds_only_delivered_links_once_and_preserves_cards(engine, status):
    store, sid, tid = started(engine)
    middle = card("query", "https://files.example/intermediate.jsonl", "intermediate.jsonl")
    first = card("csv", "https://files.example/data.csv?signature=first")
    second = card("report", "https://files.example/report.csv?signature=second", "report.csv")
    original = deepcopy([middle, first, second])
    save_delivery(store, sid, tid, original, delivered=["csv", "report"])
    body = "已整理可交付的结果。"
    store.write("alice", sid, tid, {"type": "message", "text": body})
    error = {"code": 502, "error_code": "tool_failed", "message": "PRIVATE_ENDPOINT"} if status == "FAILED" else None
    assert store.finish("alice", sid, tid, status, message=body, error=error)
    events, reply, saved = replies(store, sid, tid)
    assert reply.startswith(body) and saved == [reply]
    assert reply.count(first["data"]["downloadUrl"]) == 1
    assert reply.count(second["data"]["downloadUrl"]) == 1
    assert middle["data"]["downloadUrl"] not in reply and "PRIVATE_ENDPOINT" not in reply
    assert store.selected_results("alice", sid, ["query", "csv", "report"]) == original
    assert [event["type"] for event in events][-2:] == ["result", "done"]
    assert not any(event.get("mode") == "replace" for event in events)
    assert not store.finish("alice", sid, tid, status, message=body, error=error)
    assert replies(store, sid, tid) == (events, reply, saved)
    tail = store.replay("alice", sid, tid, events[0]["event_seq"])
    assert body+"".join(event["text"] for event in tail if event["type"] == "message") == reply


@pytest.mark.parametrize("existing", ["https://files.example/data.csv?token=a", "https://files.example/data.csv?token=ab"])
def test_existing_complete_link_is_not_repeated_but_different_token_is_not_a_match(engine, existing):
    store, sid, tid = started(engine)
    target = "https://files.example/data.csv?token=a"
    save_delivery(store, sid, tid, [card("file", target)])
    body = f"已整理：[下载文件](<{existing}>)"
    store.write("alice", sid, tid, {"type": "message", "text": body})
    assert store.finish("alice", sid, tid, "COMPLETED", message=body)
    events, reply, saved = replies(store, sid, tid)
    assert saved == [reply] and reply.startswith(body)
    if existing == target:
        assert reply == body
        assert len([event for event in events if event["type"] == "message"]) == 1
    else:
        assert target in reply[len(body):]


@pytest.mark.parametrize("delivery", ["absent", "empty", "without_links"])
def test_turn_without_delivered_links_keeps_model_reply_unchanged(engine, delivery):
    store, sid, tid = started(engine)
    if delivery == "empty":
        save_delivery(store, sid, tid, [card("unselected", "https://files.example/not-delivered.csv")], delivered=[])
    elif delivery == "without_links":
        save_delivery(store, sid, tid, [{"result_id": "counts", "view_type": "table", "title": "统计", "data": {"count": 2}}])
    body = "共取得两条记录。"
    store.write("alice", sid, tid, {"type": "message", "text": body})
    assert store.finish("alice", sid, tid, "COMPLETED", message=body)
    events, reply, saved = replies(store, sid, tid)
    assert reply == body and saved == [body]
    assert len([event for event in events if event["type"] == "message"]) == 1


def test_link_is_not_appended_to_waiting_question_but_is_available_after_cancellation(engine):
    store, sid, tid = started(engine)
    url = "https://files.example/partial.csv"
    save_delivery(store, sid, tid, [card("partial", url)])
    question = "请选择下一步需要处理的字段。"
    store.write("alice", sid, tid, {"type": "message", "text": question})
    assert store.finish("alice", sid, tid, "WAITING_INPUT", message=question)
    assert replies(store, sid, tid)[1:] == (question, [question])
    assert store.finish("alice", sid, tid, "CANCELLED")
    _, reply, saved = replies(store, sid, tid)
    assert reply.startswith(question) and reply.count(url) == 1 and saved == [reply]


def test_expired_worker_retains_download_link_without_model_or_runtime_finish(engine):
    store, sid, tid = started(engine)
    url = "https://files.example/retained.csv"
    assert store.write("alice", sid, tid, card=card("saved", url))
    state = json.loads(store.task("alice", sid, tid)["payload"])
    state["operations"] = [{"id": "export", "required": True, "output": "result", "state": "succeeded",
        "attempts": [{"state": "succeeded", "result_id": "saved"}]}]
    store.write("alice", sid, tid, payload=state)
    with store.transaction() as conn:
        conn.execute(update(store.tasks).where(store.tasks.c.id == tid).values(expires=0))
    store.heartbeat("replacement-worker", [])
    events, reply, saved = replies(store, sid, tid)
    assert events[-1]["status"] == "FAILED"
    assert reply.count(url) == 1 and saved == [reply]
    store.heartbeat("replacement-worker", [])
    assert replies(store, sid, tid) == (events, reply, saved)


def test_real_qa_export_adds_csv_link_without_extra_model_or_mcp_calls(engine, files, download_client, monkeypatch):
    calls = []
    original = ToolSession.call

    async def count(tools, alias, arguments, **kwargs):
        calls.append(tools.loaded[alias].name)
        return await original(tools, alias, arguments, **kwargs)

    monkeypatch.setattr(ToolSession, "call", count)

    async def run():
        dialogue = BareDialogue(action("load_mcp_tools", server="piflow-corpus"),
            action("remember", plan=file_plan()), approve, text("已整理。"))
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        sid = session(service)
        try:
            events = await collect(service, sid, "按给定结构和数值条件检索，并导出 CSV")
            state = payload(service, sid, events)
            assert state.get("error") is None and events[-1]["status"] == "COMPLETED"
            delivered = service.store.selected_results("alice", sid, state["delivery"])
            assert len(delivered) == 1
            exported = delivered[0]["data"]
            if isinstance(exported, dict) and isinstance(exported.get("items"), list):
                exported = exported["items"][0]
            assert exported["resource"]["format"] == "csv"
            url = exported["downloadUrl"]
            reply = "".join(event["text"] for event in events if event["type"] == "message")
            assert reply.startswith("已整理。") and reply.count(url) == 1
            all_results = service.store.results("alice", sid, events[-1]["task_id"])
            for result in all_results:
                value = result.get("data", {})
                if isinstance(value, dict) and value.get("resource", {}).get("format") == "jsonl":
                    assert value["downloadUrl"] not in reply
            response = download_client.get(url)
            assert response.status_code == 200
            assert [row["CID"] for row in csv.DictReader(io.StringIO(response.text))] == ["1", "2"]
            _, replayed, saved = replies(service.store, sid, events[-1]["task_id"])
            assert replayed == reply and saved == [reply]
            assert len(dialogue.inputs) == 4
            assert calls == ["query_pubchem_compounds", "export_dataset"]
            assert len(files.requests) == 2
        finally:
            await service.close()

    asyncio.run(run())
