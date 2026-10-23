"""Only semantic goals or explicit delivery can confirm inferred outcomes."""
import asyncio
import json

from langchain_core.messages import ToolMessage

from .assertions import assert_completed, assert_handled
from ..capabilities import OBJECT
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, text


def repeat_read(messages, definitions):
    result_id = next(json.loads(message.content)["result_id"] for message in messages
        if isinstance(message, ToolMessage) and json.loads(message.content).get("result_id"))
    return action("read_result", result_id=result_id)


def test_no_progress_preserves_intermediate_search_without_confirming_the_unknown_goal(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resources"),
            repeat_read, repeat_read, repeat_read, text("The requested sample is not ready."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "Find a resource and sample the first one", "stalled")
            assert_handled(service, None, values[-1], "no_progress")
            card, = result_cards(values)
            assert card["data"]["items"]
            assert values[-1]["outcome"]=="partial"
            assert backend.calls==[("data", "search", {"query": "resources"})]
            ledger = payload(service, sid, values)
            assert ledger["delivery_sources"]==[card["result_id"]]
            assert all(not item.get("required", True) for item in ledger["operations"])
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_delivery_can_confirm_one_bare_native_search_without_semantic_bookkeeping(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resources"), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "Find related resources", "explicit")
            assert_completed(service, None, values[-1])
            assert len(result_cards(values))==1
            ledger = payload(service, sid, values)
            assert len(ledger["operations"])==1 and ledger["operations"][0]["required"] is True
            assert ledger["delivery_sources"]==[result_cards(values)[0]["result_id"]]
            assert len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_declared_goal_still_completes_without_an_extra_delivery_model_round(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), goals({"description": "Find resources", "tool": "search"},
            calls=[remote("search", query="resources")]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Find resources", "planned")
            assert_completed(service, None, values[-1])
            assert len(result_cards(values))==1
            assert len(dialogue.inputs)==3 and len(backend.calls)==1
        finally:
            await service.close()
    asyncio.run(run())


def test_declared_partial_result_is_retained_when_a_different_required_operation_fails(engine):
    async def run():
        backend = configured()
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def dispatch(name, arguments, **options):
                backend.protocol_error = name=="sample"
                try:
                    return await execute(name, arguments, **options)
                finally:
                    backend.protocol_error = False
            connection.call_tool = dispatch
            return connection

        backend.client = client
        dialogue = BareDialogue(load(), goals({"description": "Find resources", "tool": "search"},
            {"description": "Sample the first resource", "tool": "sample", "output": "answer"},
            calls=[remote("search", query="resources")]), remote("sample", count=1, **{OBJECT: "object:1"}))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "Find resources and sample the first one", "partial")
            assert_handled(service, None, values[-1], "tool_failed")
            card, = result_cards(values)
            assert card["title"].endswith("search")
            ledger = payload(service, sid, values)
            assert ledger["operations"][0]["state"]=="succeeded"
            assert ledger["operations"][1]["state"]=="failed"
            assert ledger["delivery_sources"]==[card["result_id"]]
            answer = "".join(value.get("text", "") for value in values if value.get("type")=="message")
            assert "Find resources" in answer and "Sample the first resource" in answer
            assert "保留" in answer
            assert len(backend.calls)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_empty_answer_only_response_does_not_complete_or_request_unnecessary_user_input(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), goals({"description": "Read asset size", "tool": "inspect", "output": "answer"},
            calls=[remote("inspect", reference="direct-id")]), action("deliver_results"), text(""))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "What is the size of direct-id?", "empty-answer")
            assert_handled(service, None, values[-1], "empty_response")
            assert not result_cards(values)
            answer = "".join(value.get("text", "") for value in values if value.get("type")=="message")
            assert answer.strip() and "没有取得可展示的内容" in answer and "指定其他" in answer
            assert "请补充需要处理的问题" not in answer
            assert backend.calls==[("data", "inspect", {"reference": "direct-id"})]
            assert len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())


def test_empty_response_with_a_confirmed_card_keeps_delivery_and_completes(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resources"), action("deliver_results"), text(""))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Find related resources", "empty-with-card")
            assert_completed(service, None, values[-1])
            assert len(result_cards(values))==1
            answer = "".join(value.get("text", "") for value in values if value.get("type")=="message")
            assert answer.strip() and "结果" in answer
            assert "请补充需要处理的问题" not in answer
            assert len(backend.calls)==1 and len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())
