"""Public delivery is distinct from internal MCP evidence and model planning."""
import asyncio
from dataclasses import replace
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessageChunk, ToolMessage
from jsonschema import Draft202012Validator
from pydantic import ValidationError
import pytest
from sqlalchemy import insert, update

from .contracts import Options, QAError
from .context import public_result
from .dialogue import BUILTINS, Deliver
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


@pytest.mark.parametrize("arguments,valid", [
    ({}, True),
    ({"result_ids": []}, True),
    ({"result_ids": ["a"]}, True),
    ({"result_ids": ["a"], "merge_path": None}, True),
    ({"result_ids": ["a"], "merge_path": ""}, True),
    ({"result_ids": ["a", "b"], "merge_path": "/items", "title": "Combined"}, True),
    ({"result_ids": ["a", "b"]}, False),
    ({"result_ids": ["a", "b"], "merge_path": None}, False),
    ({"result_ids": [], "merge_path": "/items"}, False),
    ({"merge_path": ""}, False),
    ({"result_ids": [""]}, False),
    ({"result_ids": ["a"], "unknown": True}, False),
])
def test_delivery_constraints_reach_the_model_schema_and_runtime(arguments, valid):
    schema = next(t["function"]["parameters"] for t in BUILTINS if t["function"]["name"]=="deliver_results")
    Draft202012Validator.check_schema(schema)
    assert Draft202012Validator(schema).is_valid(arguments) is valid
    if valid:
        Deliver.model_validate(arguments)
    else:
        with pytest.raises(ValidationError):
            Deliver.model_validate(arguments)


@pytest.mark.parametrize("selected", [0, 1, 2])
def test_one_selected_artifact_is_delivered_without_extra_model_or_mcp_calls(engine, selected):
    async def run():
        backend = Backend()
        backend.items = [{"id": str(i), "title": "Dataset "+str(i)} for i in range(5)]
        dialogue = Dialogue(load(), remote("search"), remote("inspect", reference="b"),
            remote("preview", reference="b"), deliver([selected]), AIMessageChunk(content="已取得结果。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        tid = values[-1]["task_id"]
        assert values[-1]["status"]=="COMPLETED"
        assert len(dialogue.inputs)==6 and dialogue.inputs[-1][1]==[]
        assert sum(v["type"]=="result" for v in values)==1
        saved = service.store.results("alice", sid, tid)
        assert len(saved)==3 and len(backend.calls)==3
        assert result_cards(values)==[public_result(saved[selected])]
        assert [i["payload"] for i in (await service.get_session("alice", sid))["items"]
            if i["item_type"]=="RESULT_CARD"]==result_cards(values)
        adapter = DatasetQAAdapter(SimpleNamespace(user="alice",
            extension=SimpleNamespace(session_services={"dataset_qa": service})))
        assert (await adapter.get_results(sid, tid))["items"]==result_cards(values)
        assert await collect(service, sid)==values and len(backend.calls)==3
    asyncio.run(run())


def test_invalid_multiple_selection_recovers_without_reexecuting_mcp(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(load(), remote("search"), remote("preview", reference="b"),
            deliver(), deliver([0]), AIMessageChunk(content="已取得结果。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
        cards = service.store.results("alice", sid, values[-1]["task_id"])
        assert len(cards)==2 and result_cards(values)==[public_result(cards[0])]
        feedback = next(json.loads(m.content) for m in dialogue.inputs[4][0]
            if isinstance(m, ToolMessage) and m.name=="deliver_results")
        assert feedback["error"]=="invalid_parameters" and feedback["executed"] is False
    asyncio.run(run())


def test_invalid_selection_does_not_change_saved_results_or_publish_partial_delivery(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        payload = {"message": "获取结果", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "turn", payload, None, service.owner)
        cards = [{"result_id": task["id"]+":"+str(i), "view_type": "data", "title": "结果",
            "data": {"items": [{"id": str(row)} for row in range(5)]}} for i in range(2)]
        for card in cards:
            service.store.write("alice", sid, task["id"], card=card)
        ids = [card["result_id"] for card in cards]
        with pytest.raises(ValidationError):
            await service._deliver("alice", sid, task["id"], {"result_ids": ids}, payload)
        assert "delivery" not in payload
        assert json.loads(service.store.task("alice", sid, task["id"])["payload"])==payload
        assert service.store.results("alice", sid, task["id"])==cards
        assert not service.store.display_results("alice", sid, task["id"])
        await service._deliver("alice", sid, task["id"], {"result_ids": [ids[0]]}, payload)
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        assert result_cards(service.store.replay("alice", sid, task["id"], 0))==[public_result(cards[0])]
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


def test_root_array_batches_keep_one_artifact_and_preserve_resources(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        payload = {"message": "获取结果", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "turn", payload, None, service.owner)
        content = [{"type": "image", "url": "https://example.invalid/a.png?signature=complete", "mime_type": "image/png"}]
        cards = [{"result_id": task["id"]+":"+str(i), "view_type": "future_view", "title": "Batch",
            "data": [{"id": str(i)}, {"id": "shared"}], "content": content} for i in range(2)]
        for card in cards:
            service.store.write("alice", sid, task["id"], card=card)
        await service._deliver("alice", sid, task["id"], {"result_ids": [c["result_id"] for c in cards],
            "merge_path": "", "title": "Combined"}, payload)
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        result, = result_cards(service.store.replay("alice", sid, task["id"], 0))
        assert public_result(result)=={"result_id": task["id"]+":delivery", "view_type": "future_view",
            "title": "Combined", "data": {"items": [{"id": "0"}, {"id": "shared"}, {"id": "1"}]}, "content": content}
        assert service.store.results("alice", sid, task["id"])[:2]==cards
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
        assert values[-1]["status"]==("CANCELLED" if terminal=="cancel" else "COMPLETED")
        if terminal=="model_failure":
            assert "code" not in values[-1]
            assert "答复生成中断" in "".join(v["text"] for v in values if v["type"]=="message")
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
        for result_id, size in zip(ids, [500, 180]):
            service.store.write("alice", sid, task["id"], card={"result_id": result_id,
                "title": "结果", "view_type": "tool_result", "data": "x"*size})
        with pytest.raises(QAError, match="超过运行预算"):
            await service._deliver("alice", sid, task["id"], {"result_ids": ids[:1]}, payload)
        assert "delivery" not in json.loads(service.store.task("alice", sid, task["id"])["payload"])
        assert not service.store.display_results("alice", sid, task["id"])
        await service._deliver("alice", sid, task["id"], {"result_ids": ids[1:]}, payload)
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


def test_final_tool_call_degrades_without_restarting_mcp_execution(engine):
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
        assert values[-1]["status"]=="COMPLETED" and "code" not in values[-1]
        assert len(backend.calls)==1 and len(result_cards(values))==1
        assert service.dialogue.inputs[-1][1]==[] and len(service.dialogue.inputs)==4
        assert "答复生成中断" in "".join(v["text"] for v in values if v["type"]=="message")
    asyncio.run(run())
