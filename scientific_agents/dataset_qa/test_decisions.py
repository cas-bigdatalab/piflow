"""Raw model decisions: no helper inserts operations, calls, IDs or delivery."""
import asyncio
from copy import deepcopy
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest

from .capabilities import GOAL, OBJECT, SUPPORTING, inputs
from .dialogue import BUILTINS, Dialogue
from .contracts import QAError, Server
from .mcp import MCPGateway
from .service import DatasetQA
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session


class BareDialogue(Dialogue):
    def __init__(self, *responses):
        super().__init__(model=object())
        self.responses, self.inputs = list(responses), []

    async def respond(self, messages, definitions):
        self.inputs.append((deepcopy(messages), deepcopy(definitions)))
        response = self.responses.pop(0)
        if callable(response):
            response = response(messages, definitions)
        if isinstance(response, Exception):
            raise response
        yield response

    async def summarize(self, summary, messages):
        return summary


def text(value="请查看结果。"):
    return AIMessageChunk(content=value)


def goals(*values, calls=()):
    def response(messages, definitions):
        items = []
        for value in values:
            value = dict(value)
            name = value.pop("tool")
            alias = next(item["function"]["name"] for item in definitions if item["function"]["name"].endswith("_"+name))
            items.append({**value, "tool": alias})
        native = [call(messages, definitions) if callable(call) else call for call in calls]
        return AIMessageChunk(content="", tool_calls=[
            {**action("remember", goals=items).tool_calls[0], "id": "meaning"},
            *[{**call.tool_calls[0], "id": "action-"+str(index)} for index, call in enumerate(native)]])
    return response


def for_goal(description, native):
    """Select a supplied runtime goal by meaning, never by pending order."""
    def response(messages, definitions):
        context = json.loads(messages[1].content)
        item = next(item for item in context["operations"]["items"] if item["description"]==description)
        reply = native(messages, definitions)
        call = reply.tool_calls[0]
        return reply.model_copy(update={"tool_calls": [{**call, "args": {**call["args"], GOAL: item["id"]}}]})
    return response


def configured():
    backend = Backend()
    backend.catalog["data"][0].meta = {"piflow": {"view_type": "detail", "qa": {"collection": "/items"}}}
    for definition in backend.catalog["data"][1:]:
        descriptor = {"bind": {"reference": ["/id", "/reference"]}}
        if definition.name=="inspect":
            descriptor["object"] = ""
        definition.meta = {"piflow": {"qa": descriptor}}
    backend.catalog["data"][3].inputSchema["properties"]["count"]["default"] = 5
    return backend


async def seed(service, dialogue, sid):
    dialogue.responses = [load(), remote("search", query="资源"), action("deliver_results"), text()]
    values = await collect(service, sid, "找资源", "seed")
    assert values[-1]["status"]=="COMPLETED"
    return result_cards(values)[0]


def payload(service, sid, values):
    return json.loads(service.store.task("alice", sid, values[-1]["task_id"])["payload"])


def test_native_call_without_bookkeeping_executes_and_finishes(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load(), remote("search", query="天文"), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找天文数据")
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "天文"})]
            assert len(dialogue.inputs)==4 and len(result_cards(values))==1
            assert not any("runtime_feedback" in message.content for messages, _ in dialogue.inputs for message in messages)
            operation = payload(service, sid, values)["operations"][0]
            assert operation["id"]=="op1" and operation["state"]=="succeeded"
            assert set(result_cards(values)[0])=={"result_id", "view_type", "title", "data"}
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("coemit", [False, True])
def test_semantic_goals_need_no_model_operation_ids_or_call_mapping(engine, coemit):
    async def run():
        backend = configured()
        intent = {"description": "查找相关资源", "tool": "search"}
        responses = [load()]
        if coemit:
            responses.append(goals(intent, calls=[remote("search", query="化工")]))
        else:
            responses += [goals(intent), remote("search", query="化工")]
        dialogue = BareDialogue(*responses, text("找到了，请查看列表。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找化工资源")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert len(dialogue.inputs)==(3 if coemit else 4)
            assert dialogue.inputs[-1][1]==[]  # no selector/evaluator round
            assert payload(service, sid, values)["operations"][0]["planned"] is True
        finally:
            await service.close()
    asyncio.run(run())


def test_current_object_switch_ordinal_defaults_and_history_survive(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:2"}), action("deliver_results"), text()]
            values = await collect(service, sid, "看看第二个", "detail")
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls[-1]==("data", "inspect", {"reference": "b"})
            dialogue.responses = [remote("sample"), action("deliver_results"), text()]
            sampled = await collect(service, sid, "采样这个", "sample")
            assert sampled[-1]["status"]=="COMPLETED"
            assert backend.calls[-1]==("data", "sample", {"reference": "b", "count": 5})
            restored = json.loads(service.store.session("alice", sid)["context"])["references"]
            assert restored["current"]["result_id"]==result_cards(values)[0]["result_id"]
            assert restored["candidates"]  # sample does not discard search order
            assert await service.get_session("alice", sid)
        finally:
            await service.close()
    asyncio.run(run())


def test_parameter_target_mismatch_is_corrected_without_wrong_execution(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [action("remember", focus="candidate:1"),
                remote("sample", reference="b", count=2), remote("sample", count=2), action("deliver_results"), text()]
            values = await collect(service, sid, "确定第一个，然后采样这个", "sample")
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}), ("data", "sample", {"reference": "a", "count": 2})]
            feedback = [json.loads(message.content) for messages, _ in dialogue.inputs for message in messages
                if isinstance(message, ToolMessage) and message.name.endswith("_sample") and "error" in json.loads(message.content)]
            assert feedback and feedback[0]["detail"]["field"]=="reference"
            assert feedback[0]["executed"] is False
        finally:
            await service.close()
    asyncio.run(run())


def test_auxiliary_result_does_not_complete_sample_goal(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样第一个资源", "tool": "sample", "object": "candidate:1"}),
                remote("search", query="辅助信息", **{SUPPORTING: True}), action("deliver_results"),
                remote("sample", **{OBJECT: "candidate:1"}), text()]
            values = await collect(service, sid, "采样第一个资源", "sample")
            assert values[-1]["status"]=="COMPLETED"
            assert len(backend.calls)==3 and len(result_cards(values))==1
            assert result_cards(values)[0]["title"].endswith("sample")
            ledger = payload(service, sid, values)
            assert len(ledger["delivery_sources"])==1
            assert len([item for item in ledger["operations"] if item.get("required", True)])==1
        finally:
            await service.close()
    asyncio.run(run())


def test_multi_search_evidence_is_available_for_advice_without_model_paths(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        dialogue = BareDialogue(load(), goals({"description": "获取研究所需数据依据", "tool": "search", "output": "answer"},
            calls=[remote("search", query="降水"), remote("search", query="径流")]), action("deliver_results"), text("结合两次检索提供建议。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "做干旱预测需要哪些数据？")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            # Advisory outcomes use evidence in the answer; they don't force an
            # unrelated list card or claim that the prediction was executed.
            assert not result_cards(values)
            final = json.loads(dialogue.inputs[-1][0][-1].content)
            assert len(final["answer_evidence"])==2
            assert all(item["result_id"] for item in final["answer_evidence"])
        finally:
            await service.close()
    asyncio.run(run())


def test_complex_goal_coverage_prevents_early_completion(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "查询第一个资源", "tool": "inspect", "object": "candidate:1"},
                {"description": "查询第二个资源", "tool": "inspect", "object": "candidate:2"}),
                remote("inspect", **{OBJECT: "candidate:1"}), action("deliver_results"),
                remote("inspect", **{OBJECT: "candidate:2"}), action("deliver_results"), action("deliver_results")]
            values = await collect(service, sid, "分别查询这两个资源", "both")
            assert len(backend.calls)==3  # one search + both distinct targets
            assert [call[2]["reference"] for call in backend.calls[1:]]==["a", "b"]
            ledger = payload(service, sid, values)
            assert all(item["state"]=="succeeded" for item in ledger["operations"])
            # Existing frontend contract cannot combine heterogeneous object
            # artifacts. It must not silently discard one or select the last.
            assert values[-1]["status"]=="FAILED" and not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())


def test_model_schema_exposes_semantics_not_internal_bookkeeping():
    remember = next(item["function"]["parameters"] for item in BUILTINS if item["function"]["name"]=="remember")
    assert not ({"operations", "calls", "resume", "references"} & remember["properties"].keys())
    Draft202012Validator.check_schema(remember)
    assert Draft202012Validator(remember).is_valid({"goals": [{"description": "需要的数据", "tool": "available_tool"}]})
    assert not Draft202012Validator(remember).is_valid({"goals": [{"description": "需要的数据", "tool": "available_tool", "id": "model-generated"}]})


def test_metadata_adapter_binds_unfamiliar_parameter_names_without_name_rules():
    from .mcp import Tool
    tool = Tool("new-service", "unfamiliar", "Operate on a referenced object", {
        "type": "object", "properties": {"asset_key": {"type": "string"}, "limit": {"type": "integer", "default": 3}},
        "required": ["asset_key"], "additionalProperties": False}, {},
        {"piflow": {"qa": {"bind": {"asset_key": ["/identity/key"]}}}})
    schema = tool.definition()["function"]["parameters"]
    assert Draft202012Validator(schema).is_valid({OBJECT: "current"})
    assert inputs(tool, {OBJECT: "current"}, {"identity": {"key": "real-key"}})=={"asset_key": "real-key", "limit": 3}
    with pytest.raises(QAError, match="不一致"):
        inputs(tool, {"asset_key": "wrong-key"}, {"identity": {"key": "real-key"}})


def test_real_mcp_receives_bound_business_parameters_only(engine):
    from fastmcp import FastMCP

    async def run():
        mcp, calls = FastMCP("new-capabilities"), []

        @mcp.tool(meta={"piflow": {"qa": {"collection": "/items"}}})
        def catalog() -> dict:
            calls.append("catalog")
            return {"items": [{"identity": {"key": "entry-1"}, "title": "A scientific asset"}]}

        @mcp.tool(meta={"piflow": {"view_type": "directory", "qa": {"bind": {"asset_key": ["/identity/key"]}}}})
        def directory(asset_key: str, limit: int = 5) -> dict:
            calls.append((asset_key, limit))
            return {"files": [{"name": "data.json", "url": "https://example.test/data.json"}]}

        dialogue = BareDialogue(load("working"), remote("catalog"), goals(
            {"description": "展示选定对象的内容", "tool": "directory", "object": "object:1"},
            calls=[remote("directory", **{OBJECT: "object:1"})]), text())
        service = DatasetQA(engine, dialogue, MCPGateway({"working": Server(mcp)}))
        sid = session(service)
        try:
            values = await collect(service, sid, "找到资源后，展示其内容")
            assert values[-1]["status"]=="COMPLETED" and calls==["catalog", ("entry-1", 5)]
            card, = result_cards(values)
            assert card["view_type"]=="directory" and card["data"]["items"][0]["files"][0]["name"]=="data.json"
            assert len(dialogue.inputs)==4 and dialogue.inputs[-1][1]==[]
            ledger = payload(service, sid, values)
            assert ledger["operations"][0]["required"] is False
            assert len(ledger["delivery_sources"])==1
            # Exercise the actual context budget: compacting duplicate result
            # bodies must not remove the handles needed for the next action.
            messages, definitions = dialogue.inputs[2]
            bounded = dialogue.budget(messages, definitions)
            assert any(isinstance(message, ToolMessage) and json.loads(message.content).get("objects")
                for message in bounded)
        finally:
            await service.close()
    asyncio.run(run())


def test_runtime_merges_compatible_batches_and_avoids_selection_round(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        dialogue = BareDialogue(load(), goals({"description": "查找两类相关资源", "tool": "search"},
            calls=[remote("search", query="降水"), remote("search", query="径流")]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找降水与径流相关资源")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            assert len(dialogue.inputs)==3
            card, = result_cards(values)
            assert card["data"]["items"]==backend.items
            assert len(payload(service, sid, values)["delivery_sources"])==2
        finally:
            await service.close()
    asyncio.run(run())


def test_clarification_continues_semantic_goal_without_resume_flag(engine):
    from .test_reference_recovery import continuation

    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样选定对象", "tool": "sample"}),
                action("request_input", missing="需要选择具体对象", question="请选择需要采样的对象", options=["第一个", "第二个"])]
            waiting = await collect(service, sid, "采样一个", "ask")
            assert waiting[-1]["status"]=="WAITING_INPUT"
            dialogue.responses = [continuation("continue", remote("sample", **{OBJECT: "candidate:2"})), text()]
            values = await collect(service, sid, "第二个", "continue")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            assert backend.calls[-1][2]=={"reference": "b", "count": 5}
            ledger = payload(service, sid, values)
            assert ledger["resume"] is True
            assert ledger["operations"][0]["description"]=="采样选定对象"
            assert ledger["operations"][0]["target"]["path"]=="/items/1"
        finally:
            await service.close()
    asyncio.run(run())


def test_new_target_does_not_silently_resume_another_pending_target(engine):
    from .test_reference_recovery import continuation

    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样第一个", "tool": "sample", "object": "candidate:1"}),
                action("request_input", missing="采样数量", question="需要几条？")]
            assert (await collect(service, sid, "采样第一个", "ask"))[-1]["status"]=="WAITING_INPUT"
            dialogue.responses = [continuation("new", remote("sample", count=2, **{OBJECT: "candidate:2"})), action("deliver_results"), text()]
            values = await collect(service, sid, "先采样第二个两条", "other")
            assert values[-1]["status"]=="COMPLETED"
            assert payload(service, sid, values)["resume"] is False
            assert backend.calls[-1][2]=={"reference": "b", "count": 2}
        finally:
            await service.close()
    asyncio.run(run())


def test_current_source_refresh_does_not_repeat_successful_mcp(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "理解第一个对象", "tool": "inspect", "object": "candidate:1", "output": "answer"},
                calls=[remote("inspect", **{OBJECT: "candidate:1"})]),
                remote("inspect", **{OBJECT: "current"}), action("deliver_results"), text()]
            values = await collect(service, sid, "解释第一个对象", "inspect")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            ledger = payload(service, sid, values)
            assert len(ledger["operations"])==1 and len(ledger["operations"][0]["attempts"])==1
            reused = [json.loads(message.content) for messages, _ in dialogue.inputs for message in messages
                if isinstance(message, ToolMessage) and json.loads(message.content).get("executed") is False]
            assert reused
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_repeat_goals_execute_twice_but_corrections_reuse_receipts(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "第一次采样", "tool": "sample", "object": "candidate:1", "output": "answer"},
                {"description": "第二次采样", "tool": "sample", "object": "candidate:1", "output": "answer"}),
                for_goal("第一次采样", remote("sample", count=1, **{OBJECT: "candidate:1"})),
                for_goal("第二次采样", remote("sample", count=1, **{OBJECT: "candidate:1"})),
                action("deliver_results"), text()]
            values = await collect(service, sid, "对第一个采样两次并解释", "twice")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==3
            assert len(payload(service, sid, values)["operations"])==2
        finally:
            await service.close()
    asyncio.run(run())


def test_final_model_failure_keeps_successful_native_artifact(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load(), remote("search", query="资源"), action("deliver_results"), RuntimeError("model unavailable"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service))
            assert values[-1]["status"]=="COMPLETED" and len(result_cards(values))==1 and len(backend.calls)==1
            assert "结果已保留" in "".join(event.get("text", "") for event in values)
        finally:
            await service.close()
    asyncio.run(run())


def test_auxiliary_success_reclassified_as_goal_reuses_execution(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="资源", **{SUPPORTING: True}),
            goals({"description": "展示已检索资源", "tool": "search"}), remote("search", query="资源"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "找资源")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert len(result_cards(values))==1
        finally:
            await service.close()
    asyncio.run(run())


def test_native_action_can_promote_auxiliary_receipt_without_any_memory_call(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="资源", **{SUPPORTING: True}),
            remote("search", query="资源"), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "找资源")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
            assert len(result_cards(values))==1
        finally:
            await service.close()
    asyncio.run(run())


def test_unknown_auxiliary_execution_cannot_be_repeated_under_required_goal(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            backend.failure = ("sample", ConnectionError("response lost"))
            dialogue.responses = [goals({"description": "采样第一个", "tool": "sample", "object": "candidate:1"}),
                remote("sample", **{OBJECT: "candidate:1", SUPPORTING: True}),
                remote("sample", **{OBJECT: "candidate:1"})]
            values = await collect(service, sid, "采样第一个", "unknown")
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="execution_unknown"
            assert len(backend.calls)==2  # seed + one dispatched sample
            assert not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())


def test_empty_search_can_be_reviewed_without_premature_completion(engine):
    async def run():
        backend = configured()
        backend.items = []
        dialogue = BareDialogue(load(), goals({"description": "检索资源", "tool": "search"},
            calls=[remote("search", query="确切条件")]), action("deliver_results"), text("当前条件下没有找到资源。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "查找符合条件的资源")
            assert values[-1]["status"]=="COMPLETED" and len(dialogue.inputs)==4
            assert result_cards(values)[0]["data"]["items"]==[]
            assert len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_direct_user_identifier_establishes_focus_for_following_turn(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        dialogue.responses = [load(), remote("inspect", reference="direct-id"), action("deliver_results"), text()]
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "查看 direct-id", "detail")
            assert values[-1]["status"]=="COMPLETED"
            dialogue.responses = [remote("sample"), action("deliver_results"), text()]
            sampled = await collect(service, sid, "采样这个", "sample")
            assert sampled[-1]["status"]=="COMPLETED"
            assert backend.calls[-1][2]=={"reference": "direct-id", "count": 5}
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_source_scopes_ordinal_without_reusing_recent_candidates(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            old = await seed(service, dialogue, sid)
            backend.items = [{"id": "c", "title": "New C"}, {"id": "d", "title": "New D"}]
            dialogue.responses = [remote("search", query="新领域"), action("deliver_results"), text()]
            await collect(service, sid, "找新领域的资源", "new-list")
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1"}), action("deliver_results"), text()]
            await collect(service, sid, "看看新的第一个", "focus")
            dialogue.responses = [remote("sample", **{OBJECT: "source:2"}), action("deliver_results"), text()]
            values = await collect(service, sid, "采样这个列表的第二个", "old-source", result_id=old["result_id"])
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls[-1][2]=={"reference": "b", "count": 5}
            view = json.loads(dialogue.inputs[-3][0][1].content)
            assert view["request_objects"]["candidates"]["items"][1]["handle"]=="source:2"
        finally:
            await service.close()
    asyncio.run(run())


def test_known_ambiguity_blocks_implicit_current_binding(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.items = [{"id": "b", "title": "B from one source"}, {"id": "b", "title": "B from another source"}]
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            old = await seed(service, dialogue, sid)
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1"}), action("deliver_results"), text()]
            await collect(service, sid, "先看看第一个", "focus")
            dialogue.responses = [remote("sample"), action("request_input", missing="需要区分同标识的来源记录", question="请选择具体来源")]
            values = await collect(service, sid, "采样这个", "ambiguous", result_id=old["result_id"], selected_dataset_id="b")
            assert values[-1]["status"]=="WAITING_INPUT"
            assert len(backend.calls)==2 and not result_cards(values)
            assert not any(event["type"]=="stage" and event["stage"]=="execute" for event in values)
        finally:
            await service.close()
    asyncio.run(run())
