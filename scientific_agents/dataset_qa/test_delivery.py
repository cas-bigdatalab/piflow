"""Public delivery is distinct from internal MCP evidence and model planning."""
import asyncio
from dataclasses import replace
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest
from sqlalchemy import insert, update

from .contracts import Options, QAError
from .context import public_result
from .persistence import dumps
from .results import combine_results
from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session
from ..unified.adapters.dataset_qa import DatasetQAAdapter


def deliver(indices=None, **arguments):
    def response(messages, definitions):
        ids = list(dict.fromkeys(json.loads(m.content)["result_id"] for m in messages
            if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content)))
        return action("deliver_results", result_ids=ids if indices is None else [ids[i] for i in indices], **arguments)
    return response


def test_only_selected_artifacts_are_public_after_final_reply(engine):
    async def run():
        backend = Backend()

        def preview(messages, definitions):
            return remote("preview", reference="b")(messages, definitions).model_copy(
                update={"content": "INTERNAL: inspect tools and fetch preview"})

        dialogue = Dialogue(load(), remote("search"), remote("inspect", reference="b"), preview,
            deliver([-1]), AIMessageChunk(content="这是选中数据集的预览。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        tid = values[-1]["task_id"]
        assert values[-1]["status"]=="COMPLETED"
        assert {v["type"] for v in values}=={"stage", "message", "result", "done"}
        assert sum(v["type"]=="result" for v in values)==1
        assert "".join(v["text"] for v in values if v["type"]=="message")=="这是选中数据集的预览。"
        result = next(i for i, v in enumerate(values) if v["type"]=="result")
        assert all(i<result for i, v in enumerate(values) if v["type"]=="message")
        assert result==len(values)-2
        assert all(set(v)=={"type", "text", "task_id", "event_seq"} for v in values if v["type"]=="message")
        assert all(set(v)=={"type", "stage", "summary", "task_id", "event_seq"} for v in values if v["type"]=="stage")
        assert [v["event_seq"] for v in values]==sorted({v["event_seq"] for v in values})
        cards = result_cards(values)
        assert len(cards)==1 and cards[0]["title"].endswith("preview")
        assert len(service.store.results("alice", sid, tid))==3
        assert [public_result(c) for c in service.store.display_results("alice", sid, tid)]==cards
        history = await service.get_session("alice", sid, limit=3, tail=True)
        shown = [i["payload"] for i in history["items"] if i["item_type"]=="RESULT_CARD"]
        assert shown==cards and not history["has_more"]
        assert [i["item_type"] for i in history["items"]]==["USER_MESSAGE", "ASSISTANT_MESSAGE", "RESULT_CARD"]
        assert dialogue.inputs[-1][1]==[]
        assert values==await collect(service, sid) and len(backend.calls)==3
        resumed = await collect(service, sid, after_event_seq=values[result-1]["event_seq"])
        assert [v["type"] for v in resumed]==["result", "done"]
    asyncio.run(run())


def test_multiple_requested_previews_share_one_result_event(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("preview", reference="a"),
            remote("preview", reference="b"), deliver()), backend.gateway())
        values = await collect(service, session(service))
        assert sum(v["type"]=="result" for v in values)==1
        assert [c["data"]["items"][0]["reference"] for c in result_cards(values)]==["a", "b"]
    asyncio.run(run())


def test_search_batches_merge_real_rows_without_invented_pagination(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("search", query="first"),
            remote("search", query="second"), deliver(merge_path="/items", title="检索结果")), backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        card, = result_cards(values)
        assert card["data"]=={"items": backend.items} and card["title"]=="检索结果"
        assert "pagination" not in card["data"]
        assert len(backend.calls)==2
        assert [public_result(c) for c in service.store.display_results("alice", sid, values[-1]["task_id"])]==[card]
    asyncio.run(run())


@pytest.mark.parametrize("terminal", ["cancel", "model_failure"])
def test_selected_result_survives_cancel_or_final_model_failure(engine, terminal):
    async def run():
        backend, gate = Backend(), asyncio.Event()

        class Streaming(Dialogue):
            async def respond(self, messages, definitions):
                if definitions:
                    async for chunk in super().respond(messages, definitions):
                        yield chunk
                    return
                yield AIMessageChunk(content="已取得预览。")
                await gate.wait()
                if terminal=="model_failure":
                    raise RuntimeError("model offline")
                yield AIMessageChunk(content="LATE OUTPUT")

        service = DatasetQA(engine, Streaming(load(), remote("preview", reference="a"), deliver()), backend.gateway())
        sid = session(service)
        stream = service.stream("alice", sid, "预览", "turn", Options())
        prefix = []
        async for value in stream:
            if value:
                prefix.append(value)
            if value and value["type"]=="message":
                break
        tid = prefix[-1]["task_id"]
        assert not service.store.display_results("alice", sid, tid)
        if terminal=="cancel":
            await service.cancel("alice", sid, tid)
        gate.set()
        suffix = [v async for v in stream if v is not None]
        await asyncio.gather(*list(service.jobs.values()), return_exceptions=True)
        values = prefix+suffix
        assert values[-1]["status"]==("CANCELLED" if terminal=="cancel" else "FAILED")
        if terminal=="model_failure":
            assert values[-1]["code"]=="service_unavailable"
        assert len(result_cards(values))==1 and sum(v["type"]=="result" for v in values)==1
        assert not any(v["type"] in {"task", "error"} for v in values)
        assert "LATE OUTPUT" not in "".join(v.get("text", "") for v in values)
        assert [public_result(c) for c in service.store.display_results("alice", sid, tid)]==result_cards(values)
        adapter = DatasetQAAdapter(SimpleNamespace(user="alice",
            extension=SimpleNamespace(session_services={"dataset_qa": service})))
        assert (await adapter.get_results(sid, tid))["items"]==result_cards(values)
    asyncio.run(run())


def test_delivery_rejects_foreign_references_and_preserves_raw_evidence(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(load(), remote("search"), deliver()), Backend().gateway())
        sid = session(service)
        card = result_cards(await collect(service, sid))[0]
        other = session(service, request="other")
        payload = {"message": "显示结果", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", other, "turn", payload, None, service.owner)
        with pytest.raises(QAError, match="不属于当前会话"):
            await service._deliver("alice", other, task["id"], {"result_ids": [card["result_id"]]}, payload)
        assert "delivery" not in json.loads(service.store.task("alice", other, task["id"])["payload"])
        service.store.finish("alice", other, task["id"], "FAILED")
        assert not service.store.display_results("alice", other, task["id"])
    asyncio.run(run())


def test_delivery_budget_can_be_corrected_without_publishing_partial_selection(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        service.gateway.limits = replace(service.gateway.limits, result_bytes=400)
        sid = session(service)
        payload = {"message": "获取结果", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "turn", payload, None, service.owner)
        ids = [task["id"]+":"+str(i) for i in range(2)]
        for result_id in ids:
            service.store.write("alice", sid, task["id"], card={"result_id": result_id,
                "title": "结果", "view_type": "tool_result", "data": "x"*180})
        with pytest.raises(QAError, match="超过运行预算"):
            await service._deliver("alice", sid, task["id"], {"result_ids": ids}, payload)
        assert "delivery" not in json.loads(service.store.task("alice", sid, task["id"])["payload"])
        assert not service.store.display_results("alice", sid, task["id"])
        await service._deliver("alice", sid, task["id"], {"result_ids": ids[:1]}, payload)
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        assert len(service.store.display_results("alice", sid, task["id"]))==1
        assert not service.store.finish("alice", sid, task["id"], "COMPLETED")
        assert sum(v["type"]=="result" for v in service.store.replay("alice", sid, task["id"], 0))==1
    asyncio.run(run())


def test_clarification_and_text_only_responses_do_not_publish_tool_evidence(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(load(), remote("search"),
            action("request_input", missing="多个候选中需要操作的对象", question="选择哪个？", options=["甲", "乙"])), Backend().gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="WAITING_INPUT" and not result_cards(values)
        assert [v["type"] for v in values][-2:]==["interaction", "done"]
        assert "missing" not in values[-2]
        assert "missing" not in (await service.get_session("alice", sid))["interaction"]
        assert not any(i["item_type"]=="RESULT_CARD" for i in (await service.get_session("alice", sid))["items"])
        service.dialogue.responses = [remote("search"), action("deliver_results"), AIMessageChunk(content="这是一段文字解释。")]
        following = await collect(service, sid, "解释一下", "text")
        assert following[-1]["status"]=="COMPLETED" and not result_cards(following)
    asyncio.run(run())


def test_merge_rejects_unknown_paths_and_preserves_resource_blocks():
    cards = [{"result_id": str(i), "title": "结果", "view_type": "tool_result", "data": {"rows": [1, 2]},
        "content": [{"type": "image", "url": "https://example.invalid/large.png", "mime_type": "image/png"}]} for i in range(2)]
    merged = combine_results(cards, "/rows", "merged", "合并结果")
    assert merged["data"]==[1, 2] and merged["content"]==cards[0]["content"]
    with pytest.raises(QAError):
        combine_results(cards, "/missing", "bad", "")
    with pytest.raises(QAError, match="必须指向数组"):
        combine_results(cards, "", "bad", "")


@pytest.mark.parametrize("views,expected", [
    (("data", "data"), "data"),
    (("url", "url"), "url"),
    (("data", "url"), "tool_result"),
    (("future_view", "future_view"), "future_view"),
    ((None, None), "tool_result"),
    (("data", None), "tool_result"),
])
def test_merge_preserves_common_view_type_without_changing_payload(views, expected):
    content = [{"type": "image", "url": "https://example.invalid/large.png", "mime_type": "image/png"}]
    cards = [{"result_id": str(i), "title": "Result", "data": {"rows": [1, 2]}, "content": content,
        **({"view_type": view} if view is not None else {})} for i, view in enumerate(views)]
    assert combine_results(cards, "/rows", "merged", "Combined")=={
        "result_id": "merged", "view_type": expected, "title": "Combined", "data": [1, 2], "content": content}


def test_worker_expiry_delivers_only_preselected_artifacts_once(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        payload = {"message": "获取结果", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "turn", payload, None, "old-worker")
        ids = [task["id"]+":"+str(i) for i in range(2)]
        for result_id in ids:
            service.store.write("alice", sid, task["id"], card={"result_id": result_id,
                "view_type": "tool_result", "title": "结果", "data": result_id})
        await service._deliver("alice", sid, task["id"], {"result_ids": ids[1:]}, payload)
        with service.store.transaction() as conn:
            conn.execute(update(service.store.tasks).where(service.store.tasks.c.id==task["id"]).values(expires=0))
        service.store.heartbeat("new-worker", [])
        values = service.store.replay("alice", sid, task["id"], 0)
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="execution_unknown"
        assert [c["result_id"] for c in result_cards(values)]==ids[1:]
        assert not service.store.finish("alice", sid, task["id"], "COMPLETED")
        assert len(service.store.display_results("alice", sid, task["id"]))==1
    asyncio.run(run())


def test_legacy_result_events_are_projected_without_reexecution(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(), backend.gateway())
        sid = session(service)
        payload = {"message": "继续", "params": Options().model_dump(exclude={"after_event_seq", "expected_version"}),
            "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "legacy", payload, None, service.owner)
        cards = [{"result_id": task["id"]+":"+str(i), "title": "旧结果", "view_type": "tool_result", "data": i}
            for i in range(2)]
        with service.store.transaction() as conn:
            for card in cards:
                service.store._item(conn, sid, task["id"], "RESULT_CARD", card, result_id=card["result_id"])
                conn.execute(insert(service.store.events).values(task_id=task["id"],
                    payload=dumps({"type": "result", "result_id": card["result_id"]})))
        service.store.finish("alice", sid, task["id"], "COMPLETED", message="旧回答")
        values = await collect(service, sid, rid="legacy")
        shown = [public_result(c) for c in cards]
        assert sum(v["type"]=="result" for v in values)==1 and result_cards(values)==shown
        assert values[-1]["status"]=="COMPLETED" and not backend.calls
        assert service.store.display_results("alice", sid, task["id"])==cards
        assert [i["payload"] for i in (await service.get_session("alice", sid))["items"]
            if i["item_type"]=="RESULT_CARD"]==shown
    asyncio.run(run())


def test_delivery_fallback_cannot_restart_mcp_execution(engine):
    async def run():
        backend = Backend()

        class RefusingDelivery(Dialogue):
            async def respond(self, messages, definitions):
                self.inputs.append((messages, definitions))
                if len(self.inputs)==1:
                    yield load()
                elif len(self.inputs)==2:
                    yield remote("search")(messages, definitions)
                elif len(self.inputs)==3:
                    yield AIMessageChunk(content="INTERNAL planning ends without selecting results")
                else:
                    # The tool-free final response attempts another tool call.
                    yield action("mcp_search", query="retry")

        service = DatasetQA(engine, RefusingDelivery(), backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="invalid_tool_call"
        assert len(backend.calls)==1 and len(result_cards(values))==1
        assert service.dialogue.inputs[-1][1]==[] and len(service.dialogue.inputs)==4
        assert not any(v["type"]=="message" for v in values)
    asyncio.run(run())
