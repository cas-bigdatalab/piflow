"""Refreshing an object's source must not create a self-consuming outcome."""
import asyncio

from ..capabilities import OBJECT
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload, seed, text


def test_repeated_detail_after_focus_refresh_reuses_one_inferred_operation(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1"}),
                remote("inspect", **{OBJECT: "current"}), action("deliver_results"), text()]
            values = await collect(service, sid, "查看第一个数据集的详情", "detail")

            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}),
                ("data", "inspect", {"reference": "a"})]
            card, = result_cards(values)
            assert card["data"]["items"][0]["reference"]=="a"
            ledger = payload(service, sid, values)
            inferred = [item for item in ledger["operations"] if item.get("inferred")]
            assert len(inferred)==1 and inferred[0]["required"] is True
            assert inferred[0]["target"]["result_id"]!=card["result_id"]
            assert len(inferred[0]["attempts"])==1
            assert ledger["delivery_sources"]==[card["result_id"]]
        finally:
            await service.close()
    asyncio.run(run())


def test_search_detail_and_repeated_detail_deliver_only_the_terminal_detail(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="资源"),
            remote("inspect", **{OBJECT: "object:1"}), remote("inspect", **{OBJECT: "current"}),
            action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            values = await collect(service, sid, "找到第一个资源后查看详情")

            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "资源"}),
                ("data", "inspect", {"reference": "a"})]
            card, = result_cards(values)
            assert card["title"].endswith("inspect")
            assert card["data"]["items"][0]["reference"]=="a"
            ledger = payload(service, sid, values)
            search, detail = ledger["operations"]
            assert search["capability"]["name"]=="search" and search["required"] is False
            assert detail["capability"]["name"]=="inspect" and detail["required"] is True
            assert search["inferred"] and detail["inferred"]
            assert len(detail["attempts"])==1
            assert detail["target"]["result_id"]==search["attempts"][0]["result_id"]
            assert ledger["delivery_sources"]==[detail["attempts"][0]["result_id"]]
            assert card["result_id"]==ledger["delivery_sources"][0]
        finally:
            await service.close()
    asyncio.run(run())
