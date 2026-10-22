"""A rejected continuation must not silently commit the previous task scope."""
import asyncio

from langchain_core.messages import AIMessageChunk

from .service import DatasetQA
from .capabilities import SUPPORTING
from .test_dataset_qa import action, collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, seed, text


def relation(value, native):
    def response(messages, definitions):
        call = native(messages, definitions)
        return AIMessageChunk(content="", tool_calls=[
            {**action("remember", continuation=value).tool_calls[0], "id": "relation"},
            {**call.tool_calls[0], "id": "native"},
        ])
    return response


def test_invalid_continuation_can_be_corrected_to_new_without_inheriting_old_goal(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样第一个", "tool": "sample", "object": "candidate:1"}),
                action("request_input", missing="采样数量", question="需要采样几条？")]
            waiting = await collect(service, sid, "采样第一个", "waiting")
            assert waiting[-1]["status"]=="WAITING_INPUT"

            dialogue.responses = [relation("continue", remote("sample", count=0)),
                relation("new", remote("search", query="新领域")), action("deliver_results"), text()]
            values = await collect(service, sid, "改为查找新领域的数据集", "new-request")

            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}),
                ("data", "search", {"query": "新领域"})]
            assert len(result_cards(values))==1
            ledger = payload(service, sid, values)
            assert ledger["resume"] is False
            required = [item for item in ledger["operations"] if item.get("required", True)]
            assert len(required)==1 and required[0]["capability"]["name"]=="search"
            assert all(item["capability"]["name"]!="sample" for item in ledger["operations"])
            original = payload(service, sid, waiting)
            assert original["operations"][0]["state"]=="pending"
        finally:
            await service.close()
    asyncio.run(run())


def test_valid_mixed_batch_commits_continuation_and_preserves_its_successful_receipt(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样第一个", "tool": "sample", "object": "candidate:1"}),
                action("request_input", missing="采样数量", question="需要采样几条？")]
            waiting = await collect(service, sid, "采样第一个", "waiting")
            assert waiting[-1]["status"]=="WAITING_INPUT"

            def mixed(messages, definitions):
                calls = [remote("search", query="补充证据", **{SUPPORTING: True})(messages, definitions),
                    remote("sample", count=0)(messages, definitions)]
                return AIMessageChunk(content="", tool_calls=[
                    {**action("remember", continuation="continue").tool_calls[0], "id": "relation"},
                    *[{**call.tool_calls[0], "id": "native-"+str(index)} for index, call in enumerate(calls)],
                ])

            dialogue.responses = [mixed, remote("sample", count=2), text()]
            values = await collect(service, sid, "采样两条", "continue")

            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}),
                ("data", "search", {"query": "补充证据"}),
                ("data", "sample", {"reference": "a", "count": 2})]
            ledger = payload(service, sid, values)
            assert ledger["resume"] is True
            required = [item for item in ledger["operations"] if item.get("required", True)]
            assert len(required)==1 and required[0]["description"]=="采样第一个"
            assert required[0]["state"]=="succeeded"
            supporting = [item for item in ledger["operations"] if not item.get("required", True)]
            assert len(supporting)==1 and supporting[0]["attempts"][0]["state"]=="succeeded"
            card, = result_cards(values)
            assert card["result_id"] in ledger["delivery_sources"]
            assert card["result_id"] not in [receipt["result_id"] for receipt in supporting[0]["attempts"]]
        finally:
            await service.close()
    asyncio.run(run())


def test_rejected_relation_switch_does_not_discard_already_executed_current_work(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "采样第一个", "tool": "sample", "object": "candidate:1"}),
                action("request_input", missing="采样数量", question="需要采样几条？")]
            assert (await collect(service, sid, "采样第一个", "waiting"))[-1]["status"]=="WAITING_INPUT"

            dialogue.responses = [relation("new", remote("search", query="独立新请求")),
                relation("continue", remote("sample", count=0)), action("deliver_results"), text()]
            values = await collect(service, sid, "先查看其他领域的数据", "new-request")

            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}),
                ("data", "search", {"query": "独立新请求"})]
            assert len(result_cards(values))==1
            ledger = payload(service, sid, values)
            assert ledger["resume"] is False
            assert len(ledger["operations"])==1
            assert ledger["operations"][0]["capability"]["name"]=="search"
            assert len(ledger["operations"][0]["attempts"])==1
        finally:
            await service.close()
    asyncio.run(run())
