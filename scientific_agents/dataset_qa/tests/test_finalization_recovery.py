"""The final persistence boundary closes a turn even when streaming breaks."""
import asyncio
import json

import pytest

from ..contracts import Limits
from ..service import DatasetQA
from .assertions import assert_handled
from .test_dataset_qa import Backend, collect, engine, session
from .test_runtime import RawDialogue


@pytest.mark.parametrize("broken", ["message_write", "first_finish"])
def test_local_fallback_closes_task_when_response_finalization_is_interrupted(engine, broken):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(RuntimeError("PRIVATE_MODEL_ENDPOINT"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        attempts = []
        if broken == "message_write":
            write = service.store.write

            def reject_message(user, sid, tid, data=None, **kwargs):
                if data and data.get("type") == "message":
                    attempts.append("message")
                    raise RuntimeError("PRIVATE_STREAM_STORAGE_DETAIL")
                return write(user, sid, tid, data, **kwargs)

            service.store.write = reject_message
        else:
            finish = service.store.finish

            def reject_once(*args, **kwargs):
                attempts.append("finish")
                if len(attempts) == 1:
                    raise TimeoutError("PRIVATE_COMMIT_DETAIL")
                return finish(*args, **kwargs)

            service.store.finish = reject_once
        try:
            events = await asyncio.wait_for(collect(service, sid), 2)
            assert_handled(service, sid, events[-1], "service_unavailable")
            text = "".join(event["text"] for event in events if event["type"] == "message")
            assert text.strip() and "PRIVATE_" not in json.dumps(events)
            assert len(dialogue.inputs) == 1 and not backend.calls
            assert attempts == (["message"] if broken == "message_write" else ["finish", "finish"])
            history = await service.get_session("alice", sid)
            replies = [item["payload"]["text"] for item in history["items"] if item["item_type"] == "ASSISTANT_MESSAGE"]
            assert replies == [text]
            assert events == await collect(service, sid)
        finally:
            await service.close()

    asyncio.run(run())


def test_cancelled_question_replay_closes_without_old_interaction(engine):
    from .test_dataset_qa import action

    async def run():
        dialogue = RawDialogue(action("request_input", missing="数据集对象", question="请指定要查看的数据集。"))
        service = DatasetQA(engine, dialogue, Backend().gateway())
        sid = session(service)
        try:
            original = await collect(service, sid)
            assert original[-1]["status"] == "WAITING_INPUT"
            assert any(event["type"] == "interaction" for event in original)
            await service.cancel("alice", sid, original[-1]["task_id"])
            replay = await collect(service, sid)
            assert replay[-1]["status"] == "CANCELLED"
            assert not any(event["type"] == "interaction" for event in replay)
            assert any("已停止" in event.get("text", "") for event in replay)
            assert len(dialogue.inputs) == 1
        finally:
            await service.close()

    asyncio.run(run())


def test_stalled_error_reply_has_a_bounded_persistence_only_fallback(engine):
    async def run():
        backend = Backend()
        dialogue = RawDialogue(RuntimeError("PRIVATE_MODEL_ENDPOINT"))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(turn_timeout=0.2)))
        sid, entered = session(service), []

        async def blocked(*args, **kwargs):
            entered.append(True)
            await asyncio.Event().wait()

        service._failure_reply = blocked
        try:
            events = await asyncio.wait_for(collect(service, sid), 1)
            assert_handled(service, sid, events[-1], "service_unavailable")
            assert entered == [True] and len(dialogue.inputs) == 1 and not backend.calls
            assert any(event.get("text", "").strip() for event in events)
        finally:
            await service.close()

    asyncio.run(run())
