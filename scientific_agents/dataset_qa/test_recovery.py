"""Recover invalid calls and transport faults without replaying completed work."""
import asyncio
from dataclasses import replace
import json

import httpx
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
import pytest

from .contracts import Limits, QAError
from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session, with_operations
from .test_delivery import deliver
from .test_runtime import RawDialogue


def malformed():
    return AIMessageChunk(content="", invalid_tool_calls=[{
        "name": "broken", "args": '{"x":', "id": "broken", "error": "invalid JSON"}])


def test_json_and_schema_errors_share_bounded_actionable_correction(engine):
    async def run():
        backend = Backend()

        def after_json(messages, definitions):
            feedback = json.loads(messages[-1].content)["runtime_feedback"]
            assert feedback["error"]=="invalid_tool_call" and feedback["executed"] is False
            assert not any(isinstance(m, AIMessage) and m.invalid_tool_calls for m in messages)
            return load("compute")

        def after_schema(messages, definitions):
            feedback = json.loads(messages[-1].content)
            assert feedback["detail"]=={"path": ["x"], "constraint": "type", "expected": "number"}
            assert "input" not in feedback["detail"]
            return remote("multiply", x=2, y=3)(messages, definitions)

        dialogue = RawDialogue(malformed(), after_json, remote("multiply", x="wrong", y=3),
            after_schema, deliver(), AIMessageChunk(content="Result: 6"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="COMPLETED" and len(dialogue.inputs)==6
        assert backend.calls==[("compute", "multiply", {"x": 2, "y": 3})]
        assert result_cards(values)[0]["data"]=={"items": [6]}
        assert "invalid_tool_call" not in "".join(v.get("text", "") for v in values)
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("fault", ["missing_id", "duplicate_id", "mixed_invalid_json", "nonfinite"])
def test_malformed_batch_is_not_executed_or_replayed(engine, fault):
    async def run():
        backend = Backend()

        def bad_batch(messages, definitions):
            call = remote("multiply", x=2, y=3)(messages, definitions).tool_calls[0]
            if fault=="missing_id":
                return AIMessageChunk(content="", tool_calls=[{**call, "id": ""}])
            if fault=="duplicate_id":
                return AIMessageChunk(content="", tool_calls=[call, call])
            if fault=="nonfinite":
                return AIMessageChunk(content="", tool_call_chunks=[{"name": call["name"], "id": call["id"],
                    "index": 0, "args": '{"x":NaN,"y":3}'}])
            return AIMessageChunk(content="", tool_calls=[call], invalid_tool_calls=malformed().invalid_tool_calls)

        def corrected(messages, definitions):
            assert json.loads(messages[-1].content)["runtime_feedback"]["error"]=="invalid_tool_call"
            assert not any(isinstance(m, AIMessage) and (m.tool_calls or m.invalid_tool_calls) for m in messages)
            return remote("multiply", x=2, y=3)(messages, definitions)

        gateway = backend.gateway()
        async with gateway.session() as tools:
            await tools.load("compute")
        dialogue = RawDialogue(bad_batch, corrected, deliver(), AIMessageChunk(content="Done"))
        service = DatasetQA(engine, dialogue, gateway)
        values = await collect(service, session(service))
        assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_delivery_correction_reuses_sampling_even_after_another_tool_succeeds(engine):
    async def run():
        backend = Backend()

        def bad_delivery(messages, definitions):
            first = next(json.loads(m.content)["result_id"] for m in messages
                if isinstance(m, ToolMessage) and "result_id" in json.loads(m.content))
            return action("deliver_results", result_ids=[first, "unselected"])

        def retry_sample(messages, definitions):
            feedback = json.loads(messages[-1].content)
            assert feedback["error"]=="invalid_delivery"
            assert feedback["detail"]["unrelated"]==["unselected"]
            assert feedback["executed"] is False
            return remote("sample", count=2, reference="a")(messages, definitions)

        dialogue = RawDialogue(load(), remote("sample", reference="a", count=2), bad_delivery, retry_sample,
            load("compute"), remote("multiply", x=2, y=3), remote("sample", reference="a", count=2),
            deliver([0]), AIMessageChunk(content="Original sample"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED"
        assert [name for _, name, _ in backend.calls]==["sample", "multiply"]
        sample_messages = [json.loads(m.content) for m in dialogue.inputs[-2][0]
            if isinstance(m, ToolMessage) and m.name.endswith("_sample")]
        assert len(sample_messages)==3 and len({v["result_id"] for v in sample_messages})==1
        assert all(v["executed"] is False for v in sample_messages[1:])
        dialogue.responses = [remote("sample", reference="a", count=2), deliver(), AIMessageChunk(content="New sample")]
        assert (await collect(service, sid, rid="new-sampling"))[-1]["status"]=="COMPLETED"
        assert [name for _, name, _ in backend.calls]==["sample", "multiply", "sample"]
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("fault", ["connect", "auth", "configuration", "wrapped"])
def test_connection_faults_are_classified_before_tool_dispatch(engine, fault):
    async def run():
        backend, attempts = Backend(), []
        gateway = backend.gateway(limits=replace(Limits(), retry_delay=0))
        async with gateway.session() as tools:
            await tools.load("compute")
        factory = gateway.client_factory

        def flaky(*args, **kwargs):
            client = factory(*args, **kwargs)
            enter = client.__class__.__aenter__

            async def connect(self):
                attempts.append("connect")
                if len(attempts)==1:
                    if fault=="configuration":
                        raise ValueError("invalid configuration")
                    if fault=="auth":
                        response = httpx.Response(401, request=httpx.Request("GET", "https://example.invalid"))
                        raise httpx.HTTPStatusError("unauthorized", request=response.request, response=response)
                    if fault=="wrapped":
                        raise ExceptionGroup("transport", [httpx.ConnectError("offline")])
                    raise httpx.ConnectError("offline")
                return await enter(self)

            client.__class__.__aenter__ = connect
            return client

        gateway.client_factory = flaky
        dialogue = RawDialogue(remote("multiply", x=2, y=3), deliver(), AIMessageChunk(content="6"))
        service = DatasetQA(engine, dialogue, gateway)
        values = await collect(service, session(service))
        if fault in {"connect", "wrapped"}:
            assert values[-1]["status"]=="COMPLETED" and len(attempts)==2 and len(backend.calls)==1
            assert len(dialogue.inputs)==3
        else:
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="mcp_unavailable"
            assert len(attempts)==1 and not backend.calls and len(dialogue.inputs)==1
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("hints,expected", [
    ({"readOnlyHint": True, "idempotentHint": True}, 2),
    ({"readOnlyHint": True}, 1), ({"idempotentHint": True}, 1), ({}, 1),
])
def test_lost_response_retries_only_explicitly_readonly_idempotent_tools(hints, expected):
    async def run():
        backend = Backend()
        backend.catalog["compute"][0].annotations = hints
        gateway = backend.gateway(limits=replace(Limits(), retry_delay=0))
        factory, attempts, closed = gateway.client_factory, [], []

        def flaky(*args, **kwargs):
            client = factory(*args, **kwargs)
            execute, exit_client = client.call_tool, client.__class__.__aexit__

            async def call(*args, **kwargs):
                result = await execute(*args, **kwargs)
                attempts.append("call")
                if len(attempts)==1:
                    raise httpx.ReadError("response lost after execution")
                return result

            async def close(self, *args):
                closed.append("close")
                return await exit_client(self, *args)

            client.call_tool = call
            client.__class__.__aexit__ = close
            return client

        gateway.client_factory = flaky
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            if expected==2:
                _, result = await tools.call(alias, {"x": 2, "y": 3})
                assert result.data==6
            else:
                with pytest.raises(QAError) as error:
                    await tools.call(alias, {"x": 2, "y": 3})
                assert error.value.code=="execution_unknown"
        assert len(attempts)==len(backend.calls)==expected
        assert len(closed)==len(backend.connections)
    asyncio.run(run())


def test_read_retry_is_bounded_and_call_timeout_is_not_restarted():
    async def run():
        for mode in ("immediate", "timeout"):
            backend, attempts = Backend(), []
            backend.catalog["compute"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
            gateway = backend.gateway(limits=replace(Limits(), timeout=0.04, retry_delay=0))
            factory = gateway.client_factory

            def flaky(*args, **kwargs):
                client = factory(*args, **kwargs)

                async def call(*args, **kwargs):
                    attempts.append("call")
                    if mode=="timeout":
                        await asyncio.Event().wait()
                    raise httpx.ReadError("offline")

                client.call_tool = call
                return client

            gateway.client_factory = flaky
            async with gateway.session() as tools:
                alias = (await tools.load("compute"))["items"][0]["name"]
                with pytest.raises(QAError) as error:
                    await asyncio.wait_for(tools.call(alias, {"x": 2, "y": 3}), 1)
                assert error.value.code=="execution_unknown"
            assert len(attempts)==(2 if mode=="immediate" else 1)
    asyncio.run(run())


@pytest.mark.parametrize("partial", [False, True])
def test_final_generation_failure_keeps_selected_result_stream_history_and_replay(engine, partial):
    async def run():
        backend = Backend()

        class Streaming(RawDialogue):
            async def respond(self, messages, definitions):
                if definitions:
                    async for chunk in super().respond(messages, definitions):
                        yield chunk
                    return
                self.inputs.append((messages, definitions))
                if partial:
                    yield AIMessageChunk(content="first")
                    yield AIMessageChunk(content=" tail")
                raise RuntimeError("model offline")

        dialogue = Streaming(load(), remote("sample", reference="a", count=1), deliver())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED" and "code" not in values[-1]
        text = "".join(v["text"] for v in values if v["type"]=="message")
        assert "答复生成中断" in text and ("first tail" in text)==partial
        assert len(result_cards(values))==1 and len(backend.calls)==1 and len(dialogue.inputs)==4
        history = await service.get_session("alice", sid)
        assert next(i["payload"]["text"] for i in history["items"] if i["item_type"]=="ASSISTANT_MESSAGE")==text
        assert values==await collect(service, sid) and len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_persistence_error_is_not_downgraded_to_success(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, Dialogue(load(), remote("search"), AIMessageChunk(content="answer")), backend.gateway())
        write = service.store.write

        def fail_answer(user, sid, tid, data=None, **values):
            if data and data.get("type")=="message" and data.get("text")=="answer":
                raise RuntimeError("database failure")
            return write(user, sid, tid, data, **values)

        service.store.write = fail_answer
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="service_unavailable"
        assert "答复生成中断" not in "".join(v.get("text", "") for v in values)
        assert len(result_cards(values))==1 and len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_final_timeout_degrades_only_when_a_display_result_is_confirmed(engine):
    async def run():
        for selected in (True, False):
            backend = Backend()

            class Waiting(RawDialogue):
                async def respond(self, messages, definitions):
                    if definitions:
                        async for chunk in super().respond(messages, definitions):
                            yield chunk
                    else:
                        self.inputs.append((messages, definitions))
                        await asyncio.Event().wait()

            final_delivery = deliver() if selected else action("deliver_results", result_ids=[])
            def search(messages, definitions):
                return with_operations(remote("search")(messages, definitions), messages, definitions, output="result" if selected else "answer")
            dialogue = Waiting(load(), search, final_delivery)
            service = DatasetQA(engine, dialogue, backend.gateway(limits=replace(Limits(), model_timeout=0.03)))
            sid = session(service, request=str(selected))
            values = await asyncio.wait_for(collect(service, sid), 2)
            assert values[-1]["status"]==("COMPLETED" if selected else "FAILED")
            assert len(result_cards(values))==int(selected) and len(backend.calls)==1
            if not selected:
                assert values[-1]["code"]=="model_timeout" and len(service.store.results("alice", sid))==1
            await service.close()
    asyncio.run(run())


def test_cancellation_during_safe_retry_does_not_reexecute():
    async def run():
        backend, failed, attempts = Backend(), asyncio.Event(), []
        backend.catalog["compute"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        gateway = backend.gateway(limits=replace(Limits(), retry_delay=10))
        factory = gateway.client_factory

        def flaky(*args, **kwargs):
            client = factory(*args, **kwargs)

            async def call(*args, **kwargs):
                attempts.append("call")
                failed.set()
                raise httpx.ReadError("offline")

            client.call_tool = call
            return client

        gateway.client_factory = flaky
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            job = asyncio.create_task(tools.call(alias, {"x": 2, "y": 3}))
            await asyncio.wait_for(failed.wait(), 1)
            job.cancel()
            with pytest.raises(asyncio.CancelledError):
                await job
        assert attempts==["call"]
    asyncio.run(run())
