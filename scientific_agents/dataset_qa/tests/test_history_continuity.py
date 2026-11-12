"""Persisted but not yet summarized messages remain available to the next turn."""
import asyncio
import json

import pytest

from ..contracts import Limits, Options
from ..dialogue import Dialogue as ModelDialogue
from ..service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, engine, session


CONSTRAINT = "Keep original measurement units in all later exports; never normalize."


def seed(service, sid, turns):
    for index in range(turns):
        task, _ = service.store.submit("alice", sid, str(index), {
            "message": CONSTRAINT if index == 0 else f"Unrelated completed discussion {index}",
            "params": {}, "parent_task_id": None}, None, service.owner)
        service.store.finish("alice", sid, task["id"], "COMPLETED", message="Acknowledged")


async def next_context(service, sid):
    task, _ = service.store.submit("alice", sid, "next", {
        "message": "Export using my earlier requirements", "params": {}, "parent_task_id": None},
        None, service.owner)
    return (await service._context("alice", sid, task["id"], Options()))[1]


@pytest.mark.parametrize("summary_failure", [False, True])
def test_unsummarized_requirement_reaches_the_actual_next_model_input(engine, summary_failure):
    class FailedSummary(Dialogue):
        async def summarize(self, *args):
            raise TimeoutError("summary unavailable")

    async def run():
        service = DatasetQA(engine, FailedSummary() if summary_failure else Dialogue(), Backend().gateway())
        try:
            sid = session(service)
            seed(service, sid, 10 if summary_failure else 7)
            await service._summarize("alice", sid)
            context = await next_context(service, sid)
            dialogue = ModelDialogue(model=object())
            bounded = dialogue.budget(dialogue.messages("Export using my earlier requirements", context), [])
            assert any(message.content == CONSTRAINT for message in bounded)
            assert context["summary"] == "" and context["memory"] == {}
            assert context["history_coverage"]["incomplete"] is False
        finally:
            await service.close()
    asyncio.run(run())


def test_summary_cursor_prevents_reloading_already_summarized_old_messages(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        try:
            sid = session(service)
            seed(service, sid, 7)
            old = service.store.memory("alice", sid, limit=2)
            assert service.store.save_summary("alice", sid, 0, CONSTRAINT, old[-1]["id"])
            context = await next_context(service, sid)
            assert context["unsummarized_history"] == []
            assert len(context["history"]) == 12 and context["summary"] == CONSTRAINT
        finally:
            await service.close()
    asyncio.run(run())


def test_summary_backlog_is_bounded_and_explicitly_marked(engine):
    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        try:
            sid = session(service)
            seed(service, sid, 30)
            context = await next_context(service, sid)
            rows = [*context["unsummarized_history"], *context["history"]]
            expected = service.store.memory("alice", sid, limit=36, tail=True,
                exclude_task_id=service.store.session("alice", sid)["active_task_id"])
            assert rows == expected and len(rows) == 36
            assert context["history_coverage"]["incomplete"] is True
        finally:
            await service.close()
    asyncio.run(run())


def test_budget_marks_omitted_history_and_keeps_the_current_request():
    dialogue = ModelDialogue(model=object(), limits=Limits(working_chars=20000))
    context = {"history": [{"role": "user", "text": "Earlier discussion " * 1000},
        {"role": "assistant", "text": "Latest answer"}],
        "history_coverage": {"incomplete": False, "guidance": "Clarify missing earlier requirements."}}
    bounded = dialogue.budget(dialogue.messages("Current requirement", context), [])
    assert json.loads(bounded[1].content)["history_coverage"]["incomplete"] is True
    assert bounded[-1].content == "Current requirement"


def test_final_answer_retains_history_coverage_without_execution_diagnostics(engine):
    from langchain_core.messages import AIMessage

    async def run():
        service = DatasetQA(engine, Dialogue(), Backend().gateway())
        try:
            sid = session(service)
            task, _ = service.store.submit("alice", sid, "answer", {"message": "Explain earlier results",
                "params": {}, "parent_task_id": None}, None, service.owner)
            marker = {"incomplete": True, "guidance": "Clarify missing earlier requirements."}
            observed = {}
            async def capture(*args, **kwargs):
                observed.update(json.loads(args[3][1].content))
                args[5]["text"] = "Please specify the earlier requirement."
                return AIMessage(content=args[5]["text"])
            async def phase(*args):
                pass
            service._reply = capture
            messages = service.dialogue.messages("Explain earlier results", {
                "history_coverage": marker, "diagnostic": "PRIVATE_EXECUTION_ERROR"})
            await service._final_reply("alice", sid, task["id"], messages, {"text": ""}, phase)
            assert observed["history_coverage"] == marker
            assert "PRIVATE_EXECUTION_ERROR" not in json.dumps(observed)
        finally:
            await service.close()
    asyncio.run(run())
