"""Grounded object selection, displayed ordering and bounded recent conversation."""
import asyncio
from copy import deepcopy
import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
import pytest
from sqlalchemy import update

from .assertions import assert_completed
from ..context import encode
from ..contracts import Limits, Options, QAError
from ..dialogue import BUILTINS, Dialogue as ModelDialogue, ReferenceUpdate, SYSTEM
from ..persistence import dumps
from ..references import apply_update, at_path, compact_record, matching_objects, preview
from ..service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session


def ref(result_id, path, kind="dataset"):
    return {"result_id": result_id, "path": path, "kind": kind}


def stored(service, sid, rid, data, publish=True):
    payload = {"message": rid, "params": {}, "parent_task_id": None}
    task, _ = service.store.submit("alice", sid, rid, payload, None, service.owner)
    card = {"result_id": task["id"]+":0", "view_type": "data", "title": rid, "data": data}
    service.store.write("alice", sid, task["id"], card=card)
    if publish:
        payload["delivery"] = [card["result_id"]]
        service.store.write("alice", sid, task["id"], payload=payload)
    service.store.finish("alice", sid, task["id"], "COMPLETED", message="已展示" if publish else "")
    return card


def state(service, sid):
    return json.loads(service.store.session("alice", sid)["context"]).get("references", {})


def deliver_current(source, path, selected=None):
    def response(messages, definitions):
        result_id = next(json.loads(m.content)["result_id"] for m in reversed(messages)
            if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content))
        references = {"current": ref(source, path)}
        if selected is not None:
            references["selected"] = selected
        return action("deliver_results", result_ids=[result_id], references=references)
    return response


def sample_current(messages, definitions):
    context = json.loads(messages[1].content)
    identifier = context["references"]["current"]["value"]["id"]
    return remote("sample", reference=str(identifier), count=2)(messages, definitions)


def test_confirm_switch_and_pronouns_keep_sources_without_extra_model_round(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue(load(), remote("search"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = result_cards(await collect(service, sid, "查找数据集", "search"))[0]
            source = first["result_id"]
            dialogue.responses = [remote("inspect", reference="a"),
                deliver_current(source, "/items/0", [ref(source, "/items/0")]), AIMessageChunk(content="已确定 A。")]
            await collect(service, sid, "确定第一个 A", "choose-a")
            dialogue.responses = [sample_current]
            before = len(dialogue.inputs)
            assert_completed(service, None, (await collect(service, sid, "采样这个", "sample-a"))[-1])
            assert backend.calls[-1][2]["reference"]=="a"
            assert len(dialogue.inputs)-before==3  # MCP, existing delivery, final text.
            dialogue.responses = [remote("inspect", reference="b"),
                deliver_current(source, "/items/1"), AIMessageChunk(content="现在查看 B。")]
            await collect(service, sid, "切换到第二个 B", "choose-b")
            dialogue.responses = [sample_current]
            values = await collect(service, sid, "采样这个", "sample-b")
            assert_completed(service, None, values[-1])
            assert backend.calls[-1][2]["reference"]=="b"
            refs = state(service, sid)
            assert refs["current"]==ref(source, "/items/1")
            assert refs["selected"]==[ref(source, "/items/0")]
            assert refs["candidates"]["result_id"]==source
            assert at_path(service.store.results("alice", sid, result_id=source)[0]["data"], refs["current"]["path"])["id"]=="b"
            assert values==await collect(service, sid, "采样这个", "sample-b")
        finally:
            await service.close()
    asyncio.run(run())


def test_ordinal_uses_published_list_not_last_intermediate_lookup(engine):
    async def run():
        backend = Backend()
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                if name=="search":
                    backend.items = [{"id": prefix+str(i), "title": prefix+str(i)} for i in range(3)]
                return await execute(name, arguments, **options)
            prefix = "shown" if not backend.calls else "internal"
            # One connection serves both calls; use the request to distinguish them.
            async def dispatch(name, arguments, **options):
                nonlocal prefix
                prefix = arguments.get("query", "shown")
                return await call(name, arguments, **options)
            connection.call_tool = dispatch
            return connection

        def first_only(messages, definitions):
            ids = [json.loads(m.content)["result_id"] for m in messages
                if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content)]
            return action("deliver_results", result_ids=ids[:1])

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = Dialogue(load(), remote("search", query="shown"), remote("search", query="internal"), first_only)
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            shown = result_cards(await collect(service, sid, "查找候选", "search"))[0]

            def second(messages, definitions):
                candidates = json.loads(messages[1].content)["references"]["candidates"]
                assert candidates["result_id"]==shown["result_id"]
                return remote("inspect", reference=candidates["items"][1]["value"]["id"])(messages, definitions)
            dialogue.responses = [second]
            assert_completed(service, None, (await collect(service, sid, "看看第二个", "second"))[-1])
            assert backend.calls[-1][2]["reference"]=="shown1"
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("identifier", ["old-id", 2])
def test_old_frontend_selection_resolves_beyond_recent_eight_and_survives_restart(engine, identifier):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        oldest = stored(service, sid, "old", {"items": [{"id": identifier, "title": "Old object"}]})
        for index in range(9):
            stored(service, sid, "later-"+str(index), {"items": [{"id": "later-"+str(index), "title": "Later"}]})
        assert oldest["result_id"] not in {c["result_id"] for c in service.store.results("alice", sid)}
        payload = {"message": "采样这个", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "choose-old", payload, None, service.owner)
        context, model, _ = await service._context("alice", sid, task["id"], Options(selected_dataset_id=str(identifier)))
        assert model["references"]["current"]["value"]["id"]==identifier
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        await service.close()
        restored = DatasetQA(engine, Dialogue(load(), sample_current), Backend().gateway())
        try:
            assert state(restored, sid)["current"]==context["references"]["current"]
            assert_completed(restored, None, (await collect(restored, sid, "采样这个", "after-restart"))[-1])
        finally:
            await restored.close()
    asyncio.run(run())


def test_old_pin_and_summary_do_not_override_new_focus_or_recent_roles(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        old = stored(service, sid, "old", {"id": "A", "title": "Old A"})
        recent = stored(service, sid, "recent", {"items": [{"id": "B", "title": "Current B"}]})
        with service.store.transaction() as conn:
            conn.execute(update(service.store.sessions).where(service.store.sessions.c.id==sid).values(context=dumps({
                "result_id": old["result_id"], "summary": "以前确定了 A", "memory": {"selected_dataset_id": "A"},
                "references": {"current": ref(recent["result_id"], "/items/0")}})))
        payload = {"message": "采样这个", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "next", payload, None, service.owner)
        context, model, _ = await service._context("alice", sid, task["id"], Options())
        assert "result_id" not in context and "selected_dataset_id" not in model["memory"]
        assert model["references"]["current"]["value"]["id"]=="B"
        assert not model["evidence"]
        messages = ModelDialogue(model=object()).messages(payload["message"], model)
        assert isinstance(messages[-2], AIMessage) and messages[-1].content==payload["message"]
        assert sum(m.content==payload["message"] for m in messages)==1
        assert "history" not in json.loads(messages[1].content)
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        await service.close()
    asyncio.run(run())


def test_duplicate_identifier_clarifies_without_dispatch_or_stale_current(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(action("request_input", missing="目标记录不唯一", question="请选择具体来源中的记录", options=["第一个", "第二个"]))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        card = stored(service, sid, "duplicates", {"items": [{"id": "same", "title": "A"}, {"id": "same", "title": "B"}]})
        values = await collect(service, sid, "查看这个", "ambiguous", selected_dataset_id="same", result_id=card["result_id"])
        assert values[-1]["status"]=="WAITING_INPUT" and not backend.calls
        assert dialogue.contexts[-1]["reference_issue"]
        assert "current" not in dialogue.contexts[-1]["references"]
        await service.close()
    asyncio.run(run())


def test_remember_validates_sources_and_refreshes_model_context_in_same_turn(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        card = stored(service, sid, "known", {"items": backend.items})
        source = card["result_id"]
        dialogue.responses = [action("remember", references={"current": ref(source, "/items/1")}), load(), sample_current]
        values = await collect(service, sid, "对第二个采样", "sample")
        assert_completed(service, None, values[-1])
        assert backend.calls[-1][2]["reference"]=="b"
        assert state(service, sid)["current"]==ref(source, "/items/1")
        other = session(service, request="other")
        payload = {"message": "选择", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", other, "bad", payload, None, service.owner)
        with pytest.raises(QAError, match="当前会话"):
            await service._builtin("alice", other, task["id"], "remember", {"references": {"current": ref(source, "/items/0")}}, None, {})
        assert state(service, other)=={}
        service.store.finish("alice", other, task["id"], "CANCELLED")
        await service.close()
    asyncio.run(run())


def test_reference_publication_is_atomic_and_cancelled_intermediates_do_not_replace_list(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        first = stored(service, sid, "shown", {"items": [{"id": "A"}]})
        payload = {"message": "继续", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "next", payload, None, service.owner)
        await service._deliver("alice", sid, task["id"], {"result_ids": [first["result_id"]]}, payload)
        assert state(service, sid)=={}  # Selected, but not yet published.
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        assert state(service, sid)["candidates"]["result_id"]==first["result_id"]
        snapshot = deepcopy(state(service, sid))
        stored(service, sid, "cancelled-intermediate", {"items": [{"id": "B"}]}, publish=False)
        assert state(service, sid)==snapshot
        await service.close()
    asyncio.run(run())


def test_merged_candidate_snapshot_uses_actual_merged_order(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        first = stored(service, sid, "batch-1", {"items": [{"id": "A"}, {"id": "B"}]})
        second = stored(service, sid, "batch-2", {"items": [{"id": "B"}, {"id": "C"}]})
        payload = {"message": "合并展示", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "merge", payload, None, service.owner)
        await service._deliver("alice", sid, task["id"], {"result_ids": [first["result_id"], second["result_id"]],
            "merge_path": "/items", "references": {"candidates": ref(first["result_id"], "/items")}}, payload)
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        refs = state(service, sid)
        assert refs["candidates"]==ref(task["id"]+":delivery", "")
        model = await service._reference_view("alice", sid, refs)
        assert [entry["value"]["id"] for entry in model["candidates"]["items"]]==["A", "B", "C"]
        await service.close()
    asyncio.run(run())


def test_budget_protects_current_references_recent_roles_and_complete_tool_pairs():
    limits = Limits(context_chars=len(encode(BUILTINS))+len(SYSTEM)+7000, result_chars=800)
    dialogue = ModelDialogue(model=object(), limits=limits)
    reference = {**ref("saved-result", "/items/1"), "value": {"id": "B-"+"123"*80, "title": "Current B"}}
    history = [{"role": "user", "text": "OLD "*6000}, {"role": "assistant", "text": "OLD ANSWER "*3000},
        {"role": "user", "text": "明确切换到 B"}, {"role": "assistant", "text": "已切换到 B"}]
    messages = dialogue.messages("采样这个", {"references": {"current": reference}, "history": history,
        "summary": "旧对象 A "*5000, "evidence": [{"body": "x"*20000}]})
    for index in range(4):
        messages.extend([AIMessage(content="", tool_calls=[{"name": "any", "args": {}, "id": str(index)}]),
            ToolMessage(content=encode({"result_id": str(index), "data": {"body": "x"*4000}}), tool_call_id=str(index))])
    bounded = dialogue.budget(messages, BUILTINS)
    assert json.loads(bounded[1].content)["references"]["current"]==reference
    assert any(isinstance(m, HumanMessage) and m.content=="明确切换到 B" for m in bounded)
    assert any(isinstance(m, AIMessage) and m.content=="已切换到 B" for m in bounded)
    assert not any("OLD" in str(m.content) for m in bounded)
    assert sum(m.content=="采样这个" for m in bounded)==1
    for index, message in enumerate(bounded):
        if isinstance(message, ToolMessage):
            assert bounded[index-1].tool_calls[0]["id"]==message.tool_call_id
    assert len(encode([m.model_dump(mode="json", exclude_none=True) for m in bounded]))+len(encode(BUILTINS))<=limits.context_chars


@pytest.mark.parametrize("limit", [128, 512, 1200, 4000])
def test_reference_preview_is_bounded_and_keeps_identifiers_whole(limit):
    data = {"items": [{"id": "identifier-"+str(i), "title": "Title "+str(i), "body": "large "*10000,
        "raw": {"blob": "private"}, "token": "private"} for i in range(20)]}
    card = {"result_id": "source", "data": data}
    original = deepcopy(card)
    output = preview({"current": ref("source", "/items/1"), "candidates": ref("source", "/items")}, {"source": card}, limit)
    assert len(encode(output))<=limit and card==original and "private" not in encode(output)
    for index, entry in enumerate(output.get("candidates", {}).get("items", [])):
        assert entry["path"]=="/items/"+str(index)
        if "id" in entry["value"]:
            assert entry["value"]["id"]==data["items"][index]["id"]
    assert "large large" not in encode(output)


def test_reference_validation_rejects_leaf_list_and_invalid_sources_without_mutation():
    card = {"result_id": "source", "data": {"items": [{"id": "A", "raw": {"id": "A"}}]}}
    refs = {"current": ref("source", "/items/0")}
    original = deepcopy(refs)
    for pointer in ("/items", "/items/0/id", "/missing"):
        with pytest.raises(QAError):
            apply_update(refs, {"current": ref("source", pointer)}, {"source": card})
        assert refs==original
    assert matching_objects(card, "A")==[ref("source", "/items/0", "object")]
    assert at_path({"a/b": {"~key": [{"id": "A"}]}}, "/a~1b/~0key/0")=={"id": "A"}
    assert ReferenceUpdate.model_validate({"current": None}).model_dump(exclude_unset=True)=={"current": None}
    assert apply_update(refs, {"current": None}, {})=={}
    assert "token" not in compact_record({"id": "A", "token": "private"}, 100)


def test_invalid_reference_recovers_without_reexecuting_successful_mcp(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)

        def remember(path):
            def response(messages, definitions):
                source = next(json.loads(m.content)["result_id"] for m in messages
                    if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content))
                return action("remember", references={"current": ref(source, path)})
            return response
        dialogue.responses = [load(), remote("search"), remember("/items/99"),
            remote("search"), remember("/items/1")]
        values = await collect(service, sid, "查看第二个", "recover")
        assert_completed(service, None, values[-1])
        assert backend.calls==[("data", "search", {})]
        assert state(service, sid)["current"]["path"]=="/items/1"
        assert len(result_cards(values))==1
        await service.close()
    asyncio.run(run())


def test_clarification_answer_uses_the_same_display_list(engine):
    async def run():
        backend, dialogue = Backend(), Dialogue(load(), remote("search"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        source = result_cards(await collect(service, sid, "查找候选", "search"))[0]["result_id"]
        dialogue.responses = [action("request_input", missing="没有唯一指向的对象", question="您要查看哪一个？", options=["第一个", "第二个"])]
        assert (await collect(service, sid, "看这个", "ask"))[-1]["status"]=="WAITING_INPUT"

        def answer(messages, definitions):
            context = json.loads(messages[1].content)
            assert context["pending"]["question"]=="您要查看哪一个？"
            candidates = context["references"]["candidates"]
            assert candidates["result_id"]==source
            return remote("inspect", reference=candidates["items"][1]["value"]["id"])(messages, definitions)
        dialogue.responses = [answer, deliver_current(source, "/items/1")]
        values = await collect(service, sid, "第二个", "answer")
        assert_completed(service, None, values[-1])
        assert backend.calls[-1][2]["reference"]=="b"
        assert state(service, sid)["current"]==ref(source, "/items/1")
        assert (await service.get_session("alice", sid))["interaction"] is None
        await service.close()
    asyncio.run(run())


def test_many_confirmed_references_are_paged_without_losing_saved_choices(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        card = stored(service, sid, "many", {"items": [{"id": "object-"+str(i), "title": "Title "+str(i)+"x"*180} for i in range(24)]})
        selected = [ref(card["result_id"], "/items/"+str(i)) for i in range(24)]
        payload = {"message": "确定这些对象", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "confirm", payload, None, service.owner)
        context = {"references": {}}
        await service._builtin("alice", sid, task["id"], "remember", {"references": {"selected": selected}}, None, context)
        model = await service._reference_view("alice", sid, context["references"])
        assert len(encode(model))<=4000 and model["selected_total"]==24
        from ..dialogue import Read
        page = await service._read_result("alice", sid, Read(offset=8, limit=8))
        assert page["selected"]==selected[8:16] and page["selected_next_offset"]==16
        assert state(service, sid)["selected"]==selected
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        await service.close()
    asyncio.run(run())


def test_legacy_selection_cannot_reestablish_old_focus_after_different_display(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        old = stored(service, sid, "old", {"id": "A", "title": "Old A"})
        stored(service, sid, "latest", {"id": "B", "title": "Recent B"})
        with service.store.transaction() as conn:
            conn.execute(update(service.store.sessions).where(service.store.sessions.c.id==sid).values(
                context=dumps({"result_id": old["result_id"], "memory": {"selected_dataset_id": "A"}})))
        payload = {"message": "采样这个", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "next", payload, None, service.owner)
        context, model, _ = await service._context("alice", sid, task["id"], Options())
        assert "current" not in context["references"]
        assert model["evidence"][0]["data"]["id"]=="B"
        assert "selected_dataset_id" not in model["memory"] and "result_id" not in context
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        await service.close()
    asyncio.run(run())


def test_conflicting_frontend_source_and_selection_requests_clarification(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(action("request_input", missing="对象选择与来源冲突", question="您要查看 A 还是 B？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        first = stored(service, sid, "first", {"id": "A", "title": "A"})
        stored(service, sid, "second", {"id": "B", "title": "B"})
        values = await collect(service, sid, "查看这个", "conflict", result_id=first["result_id"], selected_dataset_id="B")
        assert values[-1]["status"]=="WAITING_INPUT" and not backend.calls
        context = dialogue.contexts[-1]
        assert context["request_source"]==first["result_id"] and context["reference_issue"]["identifier"]=="B"
        assert "current" not in context["references"]
        await service.close()
    asyncio.run(run())


def test_cleared_references_do_not_resurrect_legacy_memory_or_old_display(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        sid = session(service)
        stored(service, sid, "old", {"items": [{"id": "A", "title": "A"}]})
        with service.store.transaction() as conn:
            conn.execute(update(service.store.sessions).where(service.store.sessions.c.id==sid).values(
                context=dumps({"memory": {"selected_dataset_id": "A"}, "references": {}})))
        payload = {"message": "新问题", "params": {}, "parent_task_id": None}
        task, _ = service.store.submit("alice", sid, "next", payload, None, service.owner)
        context, model, _ = await service._context("alice", sid, task["id"], Options())
        assert context["references"]=={} and model["references"]=={}
        assert "selected_dataset_id" not in model["memory"] and not model["evidence"]
        service.store.finish("alice", sid, task["id"], "COMPLETED")
        await service.close()
    asyncio.run(run())


def test_legacy_numeric_identifier_ignores_protocol_codes_and_pagination_metadata():
    card = {"result_id": "source", "data": {"items": [{"id": 2, "title": "Object"}], "pagination": {"total": 2}}}
    assert matching_objects(card, "2", {"result_id": "source"})==[ref("source", "/items/0", "object")]
    assert matching_objects({"result_id": "source", "data": {"code": 200, "data": [{"id": 200}]}}, "200")==[
        ref("source", "/data/0", "object")]
