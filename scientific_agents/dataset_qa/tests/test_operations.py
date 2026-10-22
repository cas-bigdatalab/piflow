"""Goal coverage, partial delivery and recovery across native MCP calls."""
import asyncio
from copy import deepcopy
import json

from langchain_core.messages import AIMessageChunk, ToolMessage
from pydantic import ValidationError
import pytest

from .assertions import assert_completed, assert_handled
from ..context import encode
from ..contracts import QAError
from ..operations import Operation, Operations
from ..service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session
from .test_delivery import deliver
from .test_runtime import RawDialogue


def goal(key, **values):
    return {"id": key, "description": "操作 "+key, **values}


def batch(bindings, *calls, operations=None, **values):
    def response(messages, definitions):
        arguments = {"calls": bindings, **values}
        if operations is not None:
            arguments["operations"] = operations
        native = [call(messages, definitions) if callable(call) else call for call in calls]
        return AIMessageChunk(content="", tool_calls=[
            {**action("remember", **arguments).tool_calls[0], "id": "state"},
            *[{**call.tool_calls[0], "id": "native-"+str(index)} for index, call in enumerate(native)]])
    return response


def saved(service, sid, tid):
    return json.loads(service.store.task("alice", sid, tid)["payload"])


def test_auxiliary_success_cannot_complete_or_become_sample_artifact(engine):
    async def run():
        backend = Backend()
        backend.failure = ("sample", ValueError("upstream unavailable"))
        dialogue = RawDialogue(load(), batch([None], remote("search"), operations=[goal("sample")]),
            deliver(), batch(["sample"], remote("sample", reference="a", count=1)))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "采样数据集 A")
            assert_handled(service, None, values[-1])
            assert not result_cards(values)
            assert [call[1] for call in backend.calls]==["search", "sample"]
            assert len(service.store.results("alice", sid, values[-1]["task_id"]))==1
            feedback = [json.loads(message.content) for message in dialogue.inputs[3][0]
                if isinstance(message, ToolMessage) and message.name=="deliver_results"][-1]
            assert feedback["error"]=="invalid_delivery" and "pending" in feedback["detail"]
        finally:
            await service.close()
    asyncio.run(run())


def test_same_tool_other_target_success_keeps_failure_and_delivers_qualified_partial(engine):
    async def run():
        backend = Backend()
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                backend.protocol_error = arguments.get("reference")=="a"
                return await execute(name, arguments, **options)
            connection.call_tool = call
            return connection

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = RawDialogue(load(), batch(["a", "b"], remote("sample", reference="a", count=1),
            remote("sample", reference="b", count=1), operations=[goal("a"), goal("b")]))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid, "分别采样 A 和 B")
            assert_handled(service, None, values[-1], "tool_failed")
            assert len(backend.calls)==2 and len(dialogue.inputs)==2
            assert len(result_cards(values))==1
            payload = saved(service, sid, values[-1]["task_id"])
            assert [item["state"] for item in payload["operations"]]==["failed", "succeeded"]
            text = "".join(value["text"] for value in values if value["type"]=="message")
            assert "已为您完成：操作 b" in text and "暂时还无法提供：操作 a" in text and "Invalid operation" not in text
            assert values==await collect(service, sid, "分别采样 A 和 B") and len(backend.calls)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_delivery_rejects_omitted_operation_then_merges_existing_evidence(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["a"], remote("sample", reference="a", count=1),
            operations=[goal("a"), goal("b")]), deliver([0]),
            batch(["b"], remote("sample", reference="b", count=1)), deliver(merge_path="/data"),
            AIMessageChunk(content="两个采样均已完成。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "分别采样 A、B")
            assert_completed(service, None, values[-1])
            assert len(backend.calls)==2
            assert len(result_cards(values))==1
            payload = saved(service, sid, values[-1]["task_id"])
            assert len(payload["delivery_sources"])==2 and all(item["state"]=="succeeded" for item in payload["operations"])
            feedback = next(json.loads(message.content) for message in dialogue.inputs[3][0]
                if isinstance(message, ToolMessage) and message.name=="deliver_results")
            assert feedback["detail"]["pending"]==["b"]
        finally:
            await service.close()
    asyncio.run(run())


def test_recovery_reuses_only_same_operation_and_new_sample_executes(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["a"], remote("sample", reference="a", count=1),
            operations=[goal("a"), goal("again")]), action("invalid_action"),
            batch(["a", "again"], remote("sample", reference="a", count=1), remote("sample", reference="a", count=1)),
            deliver([0, 1], merge_path="/data"), AIMessageChunk(content="完成。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "采样 A，然后再采样一次")
            assert_completed(service, None, values[-1])
            assert len(backend.calls)==2
            receipts = [json.loads(message.content) for message in dialogue.inputs[4][0]
                if isinstance(message, ToolMessage) and message.name.endswith("_sample")]
            assert len(receipts)==3 and receipts[1]["executed"] is False
            assert receipts[0]["result_id"]==receipts[1]["result_id"]!=receipts[2]["result_id"]
        finally:
            await service.close()
    asyncio.run(run())


def test_clarification_resumes_receipts_without_repeating_successful_operation(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["a"], remote("sample", reference="a", count=1),
            operations=[goal("a"), goal("b")]), action("request_input", missing="B 的标识", question="B 是哪个？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            waiting = await collect(service, sid, "采样 A 和 B", "first")
            parent = waiting[-1]["task_id"]
            assert waiting[-1]["status"]=="WAITING_INPUT"
            backend.gate = asyncio.Event()
            dialogue.responses = [batch(["a", "b"], remote("sample", reference="a", count=1),
                remote("sample", reference="b", count=1), resume=True), deliver(merge_path="/data"), AIMessageChunk(content="完成。")]
            child = asyncio.create_task(collect(service, sid, "B 的标识是 b", "continue"))
            for _ in range(100):
                if len(backend.calls)==2:
                    break
                await asyncio.sleep(.01)
            assert len(backend.calls)==2 and backend.calls[-1][2]["reference"]=="b"
            assert service.store.task("alice", sid, parent)["status"]=="WAITING_INPUT"
            backend.gate.set()
            values = await child
            assert_completed(service, None, values[-1])
            assert len(backend.calls)==2
            assert service.store.task("alice", sid, parent)["status"]=="COMPLETED"
            assert all(item["state"]=="succeeded" for item in saved(service, sid, parent)["operations"])
            assert (await service.get_session("alice", sid))["interaction"] is None
            assert len(result_cards(values))==1
            assert len(saved(service, sid, values[-1]["task_id"])["delivery_sources"])==2
        finally:
            if backend.gate:
                backend.gate.set()
            await service.close()
    asyncio.run(run())


def test_new_topic_does_not_inherit_or_complete_waiting_goal(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(action("remember", operations=[goal("old")]),
            action("request_input", missing="目标标识", question="原任务针对哪个对象？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            parent = (await collect(service, sid, "先处理原任务", "old"))[-1]["task_id"]
            dialogue.responses = [load(), batch(["new"], remote("search"), operations=[goal("new")], resume=False),
                deliver(), AIMessageChunk(content="找到新领域数据。")]
            values = await collect(service, sid, "先找另一个领域的数据", "new")
            assert_completed(service, None, values[-1])
            assert service.store.task("alice", sid, parent)["status"]=="WAITING_INPUT"
            assert [item["id"] for item in saved(service, sid, values[-1]["task_id"])["operations"]]==["new"]
        finally:
            await service.close()
    asyncio.run(run())


def test_text_answer_uses_verified_operation_evidence_without_card(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["size"], remote("inspect", reference="a"),
            operations=[goal("size", output="answer")]), action("deliver_results"), AIMessageChunk(content="大小为 0。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "A 有多大？")
            assert_completed(service, None, values[-1])
            assert not result_cards(values)
            assert len(dialogue.inputs)==4 and len(backend.calls)==1
            evidence = json.loads(dialogue.inputs[-1][0][-1].content)["answer_evidence"]
            assert evidence[0]["data"]["size"]==0
        finally:
            await service.close()
    asyncio.run(run())


def test_goals_cannot_be_removed_retargeted_or_marked_successful_by_model():
    operations = Operations()
    source = {"result_id": "source", "path": "/items/0"}
    operations.declare([Operation(**goal("a", target=source)), Operation(**goal("b"))])
    original = deepcopy(operations.items)
    for values in ([goal("a", target=source)], [goal("a", target={**source, "path": "/items/1"}), goal("b")]):
        with pytest.raises(QAError):
            operations.declare([Operation(**item) for item in values])
        assert operations.items==original
    with pytest.raises(ValidationError):
        Operation(**goal("a"), state="succeeded")


def test_receipts_distinguish_unknown_execution_rejected_parameters_and_other_targets():
    operations = Operations()
    operations.declare([Operation(**goal("a")), Operation(**goal("b"))])
    operations.start("a", "first")
    operations.finish("a", "first", error=QAError("invalid_parameters", "missing field"))
    assert operations.get("a")["state"]=="pending"
    operations.start("a", "corrected")
    operations.finish("a", "corrected", error=QAError("execution_unknown", "lost response"))
    operations.start("b", "other")
    operations.finish("b", "other", result_id="result-b")
    assert operations.error(["result-b"]).code=="execution_unknown"
    with pytest.raises(QAError, match="尚未确认"):
        operations.start("a", "again")
    operations.validate_delivery(["result-b"])
    with pytest.raises(QAError):
        operations.validate_delivery(["auxiliary"])


def test_model_operation_view_is_bounded_and_retains_saved_receipts():
    operations = Operations()
    operations.declare([Operation(**goal(str(index), description="操作"*100)) for index in range(16)])
    view = operations.view(budget=1500)
    assert len(encode(view))<1600 and "next_offset" in view and len(operations.items)==16
    offset = view["next_offset"]
    assert operations.view(offset=offset, budget=1500)["items"][0]["id"]==str(offset)


@pytest.mark.parametrize("metadata", [{"operations": [goal("a")], "calls": []},
    {"operations": [goal("a")], "calls": ["unknown"]}])
def test_invalid_explicit_legacy_bindings_are_corrected_before_any_dispatch(engine, metadata):
    class Unannotated(RawDialogue):
        async def respond(self, messages, definitions):
            self.inputs.append((messages, definitions))
            response = self.responses.pop(0)
            yield response(messages, definitions) if callable(response) else response

    def invalid(messages, definitions):
        response = remote("sample", reference="a", count=1)(messages, definitions)
        if metadata is not None:
            # Even when metadata follows the native call, preflight must reject the entire batch.
            response = response.model_copy(update={"tool_calls": [*response.tool_calls,
                {**action("remember", **metadata).tool_calls[0], "id": "metadata"}]})
        return response

    async def run():
        backend = Backend()
        dialogue = Unannotated(load(), invalid, invalid, invalid)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "采样 A")
            assert_handled(service, None, values[-1], "invalid_parameters")
            assert not backend.calls and not result_cards(values) and len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())


def test_target_reference_cannot_change_when_focus_switches_or_goal_is_redeclared(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][3].meta = {"piflow": {"qa": {"bind": {"reference": ["/id"]}}}}
        dialogue = Dialogue(load(), remote("search"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            source = result_cards(await collect(service, sid, "找候选", "search"))[0]["result_id"]
            a = {"result_id": source, "path": "/items/0"}
            b = {"result_id": source, "path": "/items/1"}
            dialogue.responses = [batch(["sample"], remote("sample", reference="a", count=1),
                operations=[goal("sample", target=a)], references={"current": b}),
                action("remember", operations=[goal("sample", target=b)]), deliver(), AIMessageChunk(content="A 已采样。")]
            values = await collect(service, sid, "采样 A，当前也在讨论 B", "sample")
            assert_completed(service, None, values[-1])
            assert len(backend.calls)==2
            operation = saved(service, sid, values[-1]["task_id"])["operations"][0]
            assert operation["target"]["path"]=="/items/0" and backend.calls[-1][2]["reference"]=="a"
            assert json.loads(service.store.session("alice", sid)["context"])["references"]["current"]["path"]=="/items/1"
            assert any("已登记操作及目标不能替换" in message.content for message in dialogue.inputs[-2][0])
        finally:
            await service.close()
    asyncio.run(run())


def test_heterogeneous_required_artifacts_are_not_dropped_or_force_merged(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].meta = {"piflow": {"view_type": "detail"}}
        backend.catalog["data"][1].meta = {"piflow": {"view_type": "data"}}
        dialogue = RawDialogue(load(), batch(["search", "detail"], remote("search"), remote("inspect", reference="a"),
            operations=[goal("search"), goal("detail")]), deliver(merge_path="/items"), deliver(),
            AIMessageChunk(content="两项成果分别展示。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "查找并展示 A 详情")
            assert_completed(service, None, values[-1])
            assert len(backend.calls)==2 and len(result_cards(values))==2
            assert {card["view_type"] for card in result_cards(values)}=={"detail", "data"}
            assert len(service.store.results("alice", sid))==2
            feedback = [json.loads(message.content) for message in dialogue.inputs[3][0]
                if isinstance(message, ToolMessage) and message.name=="deliver_results"]
            assert any(value.get("error")=="invalid_delivery" and value["executed"] is False for value in feedback)
        finally:
            await service.close()
    asyncio.run(run())


def test_cancelling_continuation_preserves_prior_evidence_without_reexecution(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), batch(["a"], remote("sample", reference="a", count=1),
            operations=[goal("a"), goal("b")]), action("request_input", missing="B 标识", question="B 是哪个？"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            parent = (await collect(service, sid, "分别采样", "first"))[-1]["task_id"]
            backend.gate = asyncio.Event()
            dialogue.responses = [batch(["b"], remote("sample", reference="b", count=1), resume=True)]
            pending = asyncio.create_task(collect(service, sid, "B 是 b", "continue"))
            for _ in range(100):
                if len(backend.calls)==2:
                    break
                await asyncio.sleep(.01)
            child = service.store.session("alice", sid)["active_task_id"]
            assert child and len(backend.calls)==2
            await service.cancel("alice", sid, child)
            values = await pending
            assert values[-1]["status"]=="CANCELLED" and service.store.task("alice", sid, parent)["status"]=="CANCELLED"
            assert len(service.store.results("alice", sid))==1 and len(backend.calls)==2
            assert (await service.get_session("alice", sid))["interaction"] is None
        finally:
            if backend.gate:
                backend.gate.set()
            await service.close()
    asyncio.run(run())


def test_large_receipt_history_does_not_hide_operation_or_duplicate_result_bodies():
    operations = Operations()
    target = {"result_id": "s"*180, "path": "/"+"p"*1999, "kind": "object"}
    operations.declare([Operation(**goal("a", target=target, description="操作"*100))])
    for index in range(24):
        operations.start("a", str(index))
        operations.finish("a", str(index), result_id=str(index)+"r"*170)
    view = operations.view()
    assert view["items"][0]["result_count"]==24 and len(view["items"][0]["result_ids"])==2
    assert len(encode(view))<3600 and len(operations.result_ids(operations.get("a")))==24


@pytest.mark.parametrize("safe", [True, False])
def test_model_retry_respects_previous_execution_safety_and_keeps_other_goal(engine, safe):
    async def run():
        backend = Backend()
        backend.catalog["data"][1].annotations = {"readOnlyHint": safe, "idempotentHint": safe}
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                backend.protocol_error = arguments.get("reference")=="a" and not backend.calls
                return await execute(name, arguments, **options)
            connection.call_tool = call
            return connection

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = RawDialogue(load(), batch(["a"], remote("inspect", reference="a"),
            operations=[goal("a", output="answer"), goal("b", output="answer")]),
            batch(["a", "b"], remote("inspect", reference="a"), remote("inspect", reference="b")),
            action("deliver_results"), AIMessageChunk(content="完成。"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid, "查询 A 和 B")
            if safe:
                assert_completed(service, None, values[-1])
                assert "outcome" not in values[-1]
            else:
                assert_handled(service, sid, values[-1], "tool_failed")
            assert len(backend.calls)==(3 if safe else 2)
            assert backend.calls[-1][2]["reference"]=="b"
            states = [item["state"] for item in saved(service, sid, values[-1]["task_id"])["operations"]]
            assert states==(["succeeded", "succeeded"] if safe else ["failed", "succeeded"])
        finally:
            await service.close()
    asyncio.run(run())


def test_safe_upstream_correction_uses_existing_global_budget(engine):
    async def run():
        backend = Backend()
        backend.protocol_error = True
        backend.catalog["data"][1].annotations = {"readOnlyHint": True, "idempotentHint": True}
        dialogue = RawDialogue(load(), *[batch(["a"], remote("inspect", reference="a"), operations=[goal("a")]) for _ in range(3)])
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "查看 A")
            assert_handled(service, None, values[-1], "tool_failed")
            assert len(backend.calls)==3 and len(dialogue.inputs)==4
            assert not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())
