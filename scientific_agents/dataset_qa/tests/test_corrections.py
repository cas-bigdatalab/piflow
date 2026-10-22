"""Invalid decisions are corrected without faking or repeating MCP execution."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage
import pytest

from .assertions import assert_completed, assert_handled
from ..contracts import Limits
from ..service import DatasetQA
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_delivery import deliver
from .test_runtime import RawDialogue


def decision(name, arguments=None, call_id="decision"):
    arguments = {} if arguments is None else arguments
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return AIMessageChunk(content="", invalid_tool_calls=[{"name": name if isinstance(name, str) else None,
            "id": call_id, "args": json.dumps(arguments), "error": "invalid arguments"}])
    return AIMessageChunk(content="", tool_calls=[{"name": name, "id": call_id, "args": arguments}])


def feedback_for(messages, call_id):
    return next(json.loads(m.content) for m in messages if isinstance(m, ToolMessage) and m.tool_call_id==call_id)


def test_second_dataset_sampling_recovers_from_premature_delivery(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), remote("search"), deliver(), AIMessageChunk(content="Found two datasets."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        found = result_cards(await collect(service, sid, "找数据集", "search"))[0]
        before = len(dialogue.inputs)

        def sample_second(messages, definitions):
            feedback = feedback_for(messages, "premature")
            assert feedback["error"]=="mcp_required" and feedback["executed"] is False
            assert "deliver_results" not in feedback["available_actions"]
            context = json.loads(messages[1].content)
            second = context["references"]["candidates"]["items"][1]["value"]["id"]
            return remote("sample", reference=second, count=2)(messages, definitions)

        dialogue.responses = [decision("deliver_results", {"result_ids": [found["result_id"]]}, "premature"),
            sample_second, deliver(), AIMessageChunk(content="采样完成。")]
        values = await collect(service, sid, "采样第二个数据集", "sample")
        assert_completed(service, None, values[-1])
        assert backend.calls==[("data", "search", {}), ("data", "sample", {"reference": "b", "count": 2})]
        assert len(dialogue.inputs)-before==4  # One correction beyond the normal warm path.
        assert len(result_cards(values))==1 and "采样完成。"=="".join(v["text"] for v in values if v["type"]=="message")
        assert not any("available_actions" in v for v in values)
        assert values==await collect(service, sid, "采样第二个数据集", "sample")
        assert len(backend.calls)==2
        await service.close()
    asyncio.run(run())


def test_plain_text_before_mcp_is_corrected_instead_of_published(engine):
    async def run():
        backend = Backend()

        def inspect_feedback(messages, definitions):
            feedback = json.loads(messages[-1].content)["runtime_feedback"]
            assert isinstance(messages[-1], HumanMessage) and feedback["error"]=="mcp_required"
            return load("compute")

        dialogue = RawDialogue(AIMessageChunk(content="INTERNAL: already completed"), inspect_feedback,
            remote("multiply", x=2, y=3), deliver(), AIMessageChunk(content="Result is 6."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_completed(service, None, values[-1])
        assert result_cards(values)[0]["data"]=={"items": [6]}
        assert backend.calls==[("compute", "multiply", {"x": 2, "y": 3})]
        assert "INTERNAL" not in "".join(v["text"] for v in values if v["type"]=="message")
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("name,arguments", [(7, {}), ("request_input", []), ("remember", "wrong")])
def test_malformed_action_arguments_with_a_call_id_can_be_corrected(engine, name, arguments):
    async def run():
        backend = Backend()

        def clarify(messages, definitions):
            assert json.loads(messages[-1].content)["runtime_feedback"]["error"]=="invalid_tool_call"
            assert not any(m.tool_calls or m.invalid_tool_calls for m in messages if isinstance(m, AIMessageChunk))
            return action("request_input", missing="待操作的对象", question="请选择需要操作的对象")

        dialogue = RawDialogue(decision(name, arguments, "malformed"), clarify)
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="WAITING_INPUT" and not backend.calls
        assert values[-2]["type"]=="interaction" and len(dialogue.inputs)==2
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("arguments", [{}, {"missing": "   "}])
def test_empty_search_does_not_suspend_without_required_missing_input(engine, arguments):
    async def run():
        backend = Backend()
        backend.items = []

        def finish_empty_search(messages, definitions):
            feedback = feedback_for(messages, "call-request_input")
            assert feedback["error"]=="invalid_parameters" and feedback["executed"] is False
            assert "deliver_results" in feedback["available_actions"]
            return deliver()(messages, definitions)

        dialogue = RawDialogue(load(), remote("search", query="化工"),
            action("request_input", question="没有匹配结果，是否查看其他领域？", **arguments),
            finish_empty_search, AIMessageChunk(content="当前检索条件没有匹配结果。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid, "我想查看化工领域相关的数据集")
        assert_completed(service, None, values[-1])
        assert backend.calls==[("data", "search", {"query": "化工"})]
        assert len(result_cards(values))==1 and result_cards(values)[0]["data"]["items"]==[]
        assert not any(v["type"]=="interaction" for v in values)
        assert "是否查看其他领域" not in "".join(v["text"] for v in values if v["type"]=="message")
        assert (await service.get_session("alice", sid))["interaction"] is None
        await service.close()
    asyncio.run(run())


def test_invalid_clarification_before_mcp_recovers_to_execution(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(action("request_input", question="要不要更换检索方向？"),
            load(), remote("search", query="材料"), deliver(), AIMessageChunk(content="已返回检索结果。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service), "查找材料相关数据集")
        assert_completed(service, None, values[-1])
        assert len(result_cards(values))==1
        assert backend.calls==[("data", "search", {"query": "材料"})]
        assert not any(v["type"]=="interaction" for v in values)
        await service.close()
    asyncio.run(run())


def test_invalid_clarification_cannot_evade_correction_budget(engine):
    async def run():
        backend = Backend()
        backend.items = []
        dialogue = RawDialogue(load(), remote("search"),
            *[action("request_input", question="是否尝试条件 "+str(i)) for i in range(3)],
            AIMessageChunk(content="检索已执行，未能完成后续决策。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_handled(service, None, values[-1], "invalid_parameters")
        assert len(backend.calls)==1 and len(dialogue.inputs)==5
        assert not any(v["type"]=="interaction" for v in values)
        assert result_cards(values)[0]["data"]["items"]==[]
        await service.close()
    asyncio.run(run())


def test_changed_invalid_parameters_cannot_evade_correction_budget(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load("compute"), *[remote("multiply", x="bad"+str(i), y=2) for i in range(3)],
            AIMessageChunk(content="No computation was performed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_handled(service, None, values[-1], "invalid_parameters")
        assert not backend.calls and len(dialogue.inputs)==4
        assert sum(bool(definitions) for _, definitions in dialogue.inputs)==4
        await service.close()
    asyncio.run(run())


def test_changed_unavailable_actions_cannot_evade_correction_budget(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(*[decision("unavailable_"+str(i), call_id=str(i)) for i in range(3)],
            AIMessageChunk(content="No operation was performed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_handled(service, None, values[-1], "tool_not_loaded")
        assert not backend.calls and not backend.connections and len(dialogue.inputs)==3
        await service.close()
    asyncio.run(run())


def test_successful_sampling_is_reused_during_correction(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load(), remote("sample", reference="a", count=2), decision("unavailable"),
            remote("sample", count=2, reference="a"), remote("sample", reference="a", count=2),
            deliver(), AIMessageChunk(content="Original sample retained."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_completed(service, None, values[-1])
        assert len(backend.calls)==1 and len(result_cards(values))==1
        references = [json.loads(m.content) for m in dialogue.inputs[-2][0]
            if isinstance(m, ToolMessage) and m.name.endswith("_sample")]
        assert len(references)==3 and all(v.get("executed") is False for v in references[1:])
        assert len({v["result_id"] for v in references})==1
        await service.close()
    asyncio.run(run())


def test_mixed_batch_keeps_call_pairs_and_does_not_repeat_sampling(engine):
    async def run():
        backend = Backend()

        def batch(messages, definitions):
            sampled = remote("sample", reference="a", count=1)(messages, definitions)
            early = action("deliver_results")
            return AIMessageChunk(content="", tool_calls=[sampled.tool_calls[0], early.tool_calls[0]])

        dialogue = RawDialogue(load(), batch, remote("sample", reference="a", count=1), deliver(), AIMessageChunk(content="Done."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_completed(service, None, values[-1])
        assert len(backend.calls)==1
        messages = dialogue.inputs[2][0]
        assert feedback_for(messages, "call-deliver_results")["executed"] is False
        assert "deliver_results" in feedback_for(messages, "call-deliver_results")["available_actions"]
        pairs = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
        assert "call-deliver_results" in pairs and len(pairs)>=3
        await service.close()
    asyncio.run(run())


def test_unknown_execution_after_correction_is_not_retried(engine):
    async def run():
        backend = Backend()
        backend.failure = ("sample", TimeoutError())
        dialogue = RawDialogue(decision("deliver_results"), load(), remote("sample", reference="a", count=1),
            AIMessageChunk(content="Execution could not be confirmed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert_handled(service, None, values[-1], "execution_unknown")
        assert len(backend.calls)==1 and len(dialogue.inputs)==3
        await service.close()
    asyncio.run(run())


def test_correction_respects_existing_round_and_call_budgets(engine):
    async def run():
        for limits in (Limits(max_rounds=1), Limits(max_calls=1)):
            backend = Backend()
            dialogue = RawDialogue(decision("deliver_results"), AIMessageChunk(content="Stopped."), AIMessageChunk(content="Stopped."))
            service = DatasetQA(engine, dialogue, backend.gateway(limits=limits))
            sid = session(service, request=str(limits))
            values = await collect(service, sid)
            assert_handled(service, None, values[-1], "step_limit")
            assert not backend.calls
            await service.close()
    asyncio.run(run())
