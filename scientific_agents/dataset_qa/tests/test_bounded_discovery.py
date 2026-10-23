"""Production-shaped discovery without mock-inserted bookkeeping or delivery."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from jsonschema import Draft202012Validator
import pytest

from ..capabilities import OBJECT, TASK
from ..contracts import Limits, Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import action, collect, definition, engine, result_cards, session
from .test_decisions import BareDialogue, goals, text


KEYWORDS = ["chemical engineering", "chemical processes", "reaction engineering", "process chemistry"]


class SearchBackend:
    def __init__(self, pages):
        self.pages, self.calls, self.lists = pages, [], 0
        self.failures = []
        self.errors_at = {}
        self.blocked_page = None
        search = definition("find_assets", {
            "phrase": {"type": "string"},
            "page_number": {"type": "integer", "minimum": 1, "default": 1},
            "per_page": {"type": "integer", "minimum": 1, "maximum": 5, "default": 5},
            "classification": {"type": ["string", "null"], "default": None}}, ["phrase"],
            {"readOnlyHint": True, "idempotentHint": True})
        search.meta = {"piflow": {"qa": {"collection": "/items", "search": {
            "query": "phrase", "page": "page_number", "page_size": "per_page", "total": "/pagination/total",
            "identity": ["/id"], "opaque_filters": ["classification"]}}}}
        self.catalogue = [search]
        for name in ["inspect", "directory", "sample"]:
            tool = definition(name, {"reference": {"type": "string"}}, ["reference"],
                {"readOnlyHint": True, "idempotentHint": name!="sample"})
            tool.meta = {"piflow": {"qa": {"atomic": True, "bind": {"reference": ["/id"]},
                **({"object": ""} if name=="inspect" else {})}}}
            self.catalogue.append(tool)

    def client(self, *args, **kwargs):
        backend = self

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def list_tools(self):
                backend.lists += 1
                return backend.catalogue

            async def call_tool(self, name, arguments, **kwargs):
                backend.calls.append((name, deepcopy(arguments)))
                if name=="find_assets" and arguments["page_number"]==backend.blocked_page:
                    backend.entered.set()
                    await backend.release.wait()
                if len(backend.calls) in backend.errors_at:
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text=backend.errors_at[len(backend.calls)])])
                if backend.failures:
                    raise backend.failures.pop(0)
                if name=="find_assets":
                    data = backend.pages(arguments["phrase"], arguments["page_number"])
                else:
                    data = {"id": arguments["reference"], "title": "Verified object", "value": name}
                return SimpleNamespace(structured_content=data, is_error=False)
        return Client()

    def gateway(self, limits=None):
        return MCPGateway({"arbitrary-source": Server("test", "Dataset discovery and inspection")},
            client_factory=self.client, limits=limits)


def page(ids, total=None, revision=0):
    return {"items": [{"id": str(value), "title": "Dataset "+str(value), "revision": revision} for value in ids],
        "pagination": {} if total is None else {"total": total}}


def native(name, **arguments):
    def choose(messages, definitions):
        tool = next(item["function"] for item in definitions if item["function"]["name"].endswith("_"+name))
        Draft202012Validator(tool["parameters"]).validate(arguments)
        return action(tool["name"], **arguments)
    return choose


def discover(*, keywords=KEYWORDS, complete=True, **arguments):
    return native("find_assets", phrase=keywords[0],
        **{TASK: {"complete_request": complete, "keywords": keywords}}, **arguments)


def outcome(service, sid, events):
    return json.loads(service.store.task("alice", sid, events[-1]["task_id"])["payload"])


def test_five_actual_rows_require_a_second_page_and_six_stop_without_extra_model_calls(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 1000))

        def first(messages, definitions):
            names = {item["function"]["name"] for item in definitions}
            assert not {"list_mcp_servers", "load_mcp_tools"}.intersection(names)
            return discover()(messages, definitions)

        dialogue = BareDialogue(first, text("已找到六个候选数据集。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            assert [args["page_number"] for _, args in backend.calls]==[1, 2]
            assert {args["phrase"] for _, args in backend.calls}=={KEYWORDS[0]}
            assert len(dialogue.inputs)==2 and backend.lists==1
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==list(map(str, range(6)))
            payload = outcome(service, sid, events)
            assert payload["operations"][0]["search"]["stop"]=="enough"
            assert len(payload["delivery_lineage"][card["result_id"]])==6
            summary = json.loads(dialogue.inputs[-1][0][1].content)["search_outcomes"][0]
            assert summary["unique_count"]==6 and summary["done"] is True
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("count", [0, 1, 5])
def test_four_distinct_keywords_finish_even_when_each_has_no_new_evidence(engine, count):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(count), count, KEYWORDS.index(query)))
        dialogue = BareDialogue(discover(), text("候选结果已整理。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant datasets")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==KEYWORDS
            assert len(dialogue.inputs)==2
            card, = result_cards(events)
            assert len(card["data"]["items"])==count
            saved = outcome(service, sid, events)["operations"][0]["search"]
            assert saved["completed"]==KEYWORDS and saved["stop"]=="exhausted"
            assert len(saved["records"])==count
            final_context = json.loads(dialogue.inputs[-1][0][1].content)
            assert final_context["search_outcomes"][0]["completed_keyword_count"]==4
        finally:
            await service.close()
    asyncio.run(run())


def test_repeated_pages_do_not_inflate_count_or_loop_forever(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5), 100000, number))
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related resources")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls)==8 and len(dialogue.inputs)==2
            assert len(result_cards(events)[0]["data"]["items"])==5
            assert outcome(service, sid, events)["operations"][0]["search"]["completed"]==KEYWORDS
        finally:
            await service.close()
    asyncio.run(run())


def test_transport_retry_does_not_consume_another_keyword(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        backend.failures = [ConnectionError("temporary")]
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(retry_delay=0)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_completed(service, sid, events[-1])
            assert [args["page_number"] for _, args in backend.calls]==[1, 1, 2]
            assert {args["phrase"] for _, args in backend.calls}=={KEYWORDS[0]}
            assert len(outcome(service, sid, events)["operations"][0]["attempts"])==2
            assert len(dialogue.inputs)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_interrupted_search_is_not_recorded_as_four_empty_queries(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        backend.failures = [ConnectionError("private address"), ConnectionError("private address")]
        dialogue = BareDialogue(discover())
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(retry_delay=0)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_handled(service, sid, events[-1])
            saved = outcome(service, sid, events)["operations"][0]["search"]
            assert not saved["done"] and saved["completed"]==[]
            assert len(backend.calls)==2
            assert "private address" not in json.dumps(events)
        finally:
            await service.close()
    asyncio.run(run())


def test_exact_search_does_not_expand_keywords_or_pages(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(["exact"], 10000))
        dialogue = BareDialogue(native("find_assets", phrase="dataset-exact-id", **{TASK: {"complete_request": True, "keywords": None}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find the exact dataset")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls)==1 and len(dialogue.inputs)==2
            assert "search" not in outcome(service, sid, events)["operations"][0]
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("name", ["inspect", "directory", "sample"])
def test_explicit_operation_uses_published_ordinal_without_extra_mcp_calls(engine, name):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await collect(service, sid, "Find datasets", "first")
            baseline = len(backend.calls)
            dialogue.responses = [native(name, **{OBJECT: "candidate:2", TASK: {"complete_request": True}}), text()]
            events = await collect(service, sid, "Use "+name+" on the second dataset", "second")
            assert_completed(service, sid, events[-1])
            assert backend.calls[baseline:]==[(name, {"reference": "1"})]
            assert len(dialogue.inputs)==4 and backend.lists==1
        finally:
            await service.close()
    asyncio.run(run())


def test_discovery_prerequisite_does_not_finish_a_later_requested_operation(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        dialogue = BareDialogue(discover(complete=False),
            native("sample", **{OBJECT: "object:1", TASK: {"complete_request": True}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets and sample one of them")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls]==["find_assets", "find_assets", "sample"]
            assert len(dialogue.inputs)==3
            card, = result_cards(events)
            assert card["data"]["items"][0]["value"]=="sample"
        finally:
            await service.close()
    asyncio.run(run())


def test_search_pages_are_deduplicated_beside_a_separate_required_detail(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [4, 5], 7, number))
        dialogue = BareDialogue(goals(
            {"description": "Find related datasets", "tool": "find_assets"},
            {"description": "Inspect one dataset", "tool": "inspect"}, calls=[discover(complete=False)]),
            native("inspect", **{OBJECT: "object:1", TASK: {"complete_request": False}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets and also show details of one candidate")
            assert_completed(service, sid, events[-1])
            cards = result_cards(events)
            assert len(cards)==2
            candidates = next(card for card in cards if len(card["data"]["items"])>1)
            assert [row["id"] for row in candidates["data"]["items"]]==list(map(str, range(6)))
            ledger = outcome(service, sid, events)
            assert len(ledger["delivery_lineage"][candidates["result_id"]])==6
            assert len(ledger["delivery_sources"])==3
            assert len(backend.calls)==3 and len(dialogue.inputs)==3
            dialogue.responses = [native("sample", **{OBJECT: "candidate:6", TASK: {"complete_request": True}}), text()]
            followup = await collect(service, sid, "Sample the sixth candidate", "followup")
            assert_completed(service, sid, followup[-1])
            assert backend.calls[-1]==("sample", {"reference": "5"})
        finally:
            await service.close()
    asyncio.run(run())


def test_missing_keywords_can_be_supplied_without_new_goals_or_early_empty_delivery(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1]), action("deliver_results"),
            discover(keywords=KEYWORDS[1:]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant datasets")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==KEYWORDS
            ledger = outcome(service, sid, events)
            assert len(ledger["operations"])==1
            assert ledger["operations"][0]["search"]["done"] is True
            assert len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())


def test_recovering_second_page_preserves_first_page_and_unique_result_ids(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        backend.errors_at[2] = "backend private error"
        dialogue = BareDialogue(discover(), discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant datasets")
            assert_completed(service, sid, events[-1])
            assert [args["page_number"] for _, args in backend.calls]==[1, 2, 2]
            assert len(dialogue.inputs)==3
            assert len(result_cards(events)[0]["data"]["items"])==6
            ledger = outcome(service, sid, events)
            assert len(ledger["delivery_sources"])==len(set(ledger["delivery_sources"]))==2
            assert "backend private error" not in json.dumps(events)
        finally:
            await service.close()
    asyncio.run(run())


def test_new_request_reuses_schemas_but_executes_new_searches(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        dialogue = BareDialogue(discover(), text(), discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find datasets", "first")
            second = await collect(service, sid, "Find datasets again", "second")
            assert_completed(service, sid, first[-1])
            assert_completed(service, sid, second[-1])
            assert len(backend.calls)==4 and backend.lists==1
            assert set(outcome(service, sid, first)["delivery_sources"]).isdisjoint(outcome(service, sid, second)["delivery_sources"])
        finally:
            await service.close()
    asyncio.run(run())


def test_malformed_result_is_not_counted_as_an_empty_search(engine):
    async def run():
        backend = SearchBackend(lambda query, number: {"diagnostic": "not a collection"})
        dialogue = BareDialogue(discover())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_handled(service, sid, events[-1])
            ledger = outcome(service, sid, events)
            assert ledger["operations"][0]["state"]=="failed"
            assert ledger["operations"][0]["search"]["completed"]==[]
            assert len(backend.calls)==1 and not result_cards(events)
        finally:
            await service.close()
    asyncio.run(run())


def test_global_budget_does_not_pretend_four_keywords_completed(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([1], 1))
        dialogue = BareDialogue(discover(), text("已保留取得的候选信息。"))
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(max_calls=2)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_handled(service, sid, events[-1])
            assert len(backend.calls)==2
            search = outcome(service, sid, events)["operations"][0]["search"]
            assert search["completed"]==KEYWORDS[:2] and not search["done"]
            assert len(result_cards(events)[0]["data"]["items"])==1
            assert len(dialogue.inputs)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_late_bookkeeping_cannot_replace_an_unfinished_discovery(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1], complete=False),
            goals({"description": "Find related datasets", "tool": "find_assets"}),
            discover(keywords=KEYWORDS[1:]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant datasets")
            assert_completed(service, sid, events[-1])
            ledger = outcome(service, sid, events)
            assert len(ledger["operations"])==1
            assert ledger["operations"][0]["search"]["completed"]==KEYWORDS
            assert len(backend.calls)==4 and len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())


def test_a_prerequisite_search_cannot_be_abandoned_by_switching_to_an_exact_lookup(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        dialogue = BareDialogue(discover(keywords=KEYWORDS[:1], complete=False),
            native("find_assets", phrase=KEYWORDS[0], **{TASK: {"complete_request": True, "keywords": None}}),
            discover(keywords=KEYWORDS[1:]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant datasets")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==KEYWORDS
            assert len(outcome(service, sid, events)["operations"])==1
        finally:
            await service.close()
    asyncio.run(run())


def test_cancelling_between_pages_keeps_successes_and_stops_further_queries(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5), 10))
        backend.blocked_page = 2
        backend.entered, backend.release = asyncio.Event(), asyncio.Event()
        dialogue = BareDialogue(discover())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        running = asyncio.create_task(collect(service, sid, "Find datasets"))
        try:
            await asyncio.wait_for(backend.entered.wait(), 3)
            await service.cancel("alice", sid, next(iter(service.jobs)))
            events = await asyncio.wait_for(running, 3)
            assert events[-1]["status"]=="CANCELLED"
            ledger = outcome(service, sid, events)
            assert ledger["operations"][0]["state"]=="unknown"
            assert not ledger["operations"][0]["search"]["done"]
            assert len(result_cards(events)[0]["data"]["items"])==5
            assert len(backend.calls)==2
        finally:
            backend.release.set()
            await service.close()
    asyncio.run(run())


def test_real_fastmcp_discovery_keeps_control_metadata_out_of_wire_arguments(engine):
    from typing import Annotated
    from fastmcp import Client, FastMCP
    from pydantic import Field

    async def run():
        calls = []
        server = FastMCP("bounded-discovery-test")

        @server.tool(annotations={"readOnlyHint": True, "idempotentHint": True}, meta={"piflow": {"qa": {
            "collection": "/items", "search": {"query": "term", "page": "page_number", "page_size": "size",
                "identity": ["/id"], "total": "/pagination/total"}}}})
        def collect_resources(term: str, page_number: Annotated[int, Field(ge=1)] = 1,
                size: Annotated[int, Field(ge=1, le=5)] = 5) -> dict:
            calls.append((term, page_number, size))
            return page(range(5) if page_number==1 else [5], 6)

        gateway = MCPGateway({"local": Server("local")}, client_factory=lambda *args, **kwargs: Client(server))
        dialogue = BareDialogue(native("collect_resources", term=KEYWORDS[0],
            **{TASK: {"complete_request": True, "keywords": KEYWORDS}}), text())
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_completed(service, sid, events[-1])
            assert calls==[(KEYWORDS[0], 1, 5), (KEYWORDS[0], 2, 5)]
            assert len(dialogue.inputs)==2
            assert len(result_cards(events)[0]["data"]["items"])==6
        finally:
            await service.close()
    asyncio.run(run())


def test_declared_pagination_limit_is_respected_without_sending_invalid_pages(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5), 100))
        backend.catalogue[0].inputSchema["properties"]["page_number"]["maximum"] = 1
        dialogue = BareDialogue(discover(), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets")
            assert_completed(service, sid, events[-1])
            assert [args["page_number"] for _, args in backend.calls]==[1]*4
            assert len(dialogue.inputs)==2
            assert outcome(service, sid, events)["operations"][0]["search"]["stop"]=="exhausted"
        finally:
            await service.close()
    asyncio.run(run())
