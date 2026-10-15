"""Invalid decisions are corrected without faking or repeating MCP execution."""
import asyncio
import json

from langchain_core.messages import AIMessageChunk, HumanMessage, ToolMessage
import pytest

from .contracts import Limits
from .service import DatasetQA
from .test_dataset_qa import Backend, action, collect, engine, load, remote, result_cards, session
from .test_delivery import deliver
from .test_runtime import RawDialogue


def decision(name, arguments=None, call_id="decision"):
    return AIMessageChunk(content="", tool_calls=[{"name": "agent_action", "id": call_id,
        "args": {"name": name, "arguments": {} if arguments is None else arguments}}])


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
            second = context["evidence"][0]["data"]["items"][1]["id"]
            return remote("sample", reference=second, count=2)(messages, definitions)

        dialogue.responses = [decision("deliver_results", {"result_ids": [found["result_id"]]}, "premature"),
            sample_second, deliver(), AIMessageChunk(content="采样完成。")]
        values = await collect(service, sid, "采样第二个数据集", "sample")
        assert values[-1]["status"]=="COMPLETED"
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
        assert values[-1]["status"]=="COMPLETED" and result_cards(values)[0]["data"]==6
        assert backend.calls==[("compute", "multiply", {"x": 2, "y": 3})]
        assert "INTERNAL" not in "".join(v["text"] for v in values if v["type"]=="message")
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("name,arguments", [(7, {}), ("request_input", []), ("remember", "wrong")])
def test_malformed_action_arguments_with_a_call_id_can_be_corrected(engine, name, arguments):
    async def run():
        backend = Backend()

        def clarify(messages, definitions):
            assert feedback_for(messages, "malformed")["error"]=="invalid_tool_call"
            return action("request_input", question="请选择需要操作的对象")

        dialogue = RawDialogue(decision(name, arguments, "malformed"), clarify)
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="WAITING_INPUT" and not backend.calls
        assert values[-2]["type"]=="interaction" and len(dialogue.inputs)==2
        await service.close()
    asyncio.run(run())


def test_changed_invalid_parameters_cannot_evade_correction_budget(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(load("compute"), *[remote("multiply", x="bad"+str(i), y=2) for i in range(3)],
            AIMessageChunk(content="No computation was performed."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="invalid_parameters"
        assert not backend.calls and len(dialogue.inputs)==5
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
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="tool_not_loaded"
        assert not backend.calls and not backend.connections and len(dialogue.inputs)==4
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
        assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1 and len(result_cards(values))==1
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
        assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
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
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="execution_unknown"
        assert len(backend.calls)==1 and len(dialogue.inputs)==4
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
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="step_limit"
            assert not backend.calls
            await service.close()
    asyncio.run(run())
