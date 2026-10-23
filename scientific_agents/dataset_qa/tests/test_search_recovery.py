"""A later binding error must not erase successful, source-backed candidates."""
import asyncio
import pytest

from ..capabilities import OBJECT, TASK
from ..contracts import Limits, QAError
from ..operations import Operations
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_bounded_discovery import KEYWORDS, SearchBackend, discover, native, outcome, page
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, text


@pytest.mark.parametrize("count", [0, 1, 5])
def test_unconfirmed_search_survives_later_missing_object_identifier(engine, count):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(count), count))
        # Collection identity and detail identity are distinct contracts. Never
        # substitute /id when the detail service requires /accession.
        backend.catalogue[1].meta["piflow"]["qa"]["bind"] = {"reference": ["/accession"]}
        bad_detail = native("inspect", **{OBJECT: "object:1", TASK: {"complete_request": False}})
        dialogue = BareDialogue(discover(complete=False), bad_detail, bad_detail, bad_detail)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets", "recovery")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert [args["phrase"] for _, args in backend.calls]==KEYWORDS
            assert len(dialogue.inputs)==4  # Recovery neither reruns MCP nor calls another model.
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==list(map(str, range(count)))
            ledger = outcome(service, sid, events)
            search, = ledger["operations"]
            assert search["required"] is False and search["search"]["done"]
            assert ledger["delivery_sources"]==search["search"]["result_ids"]
            answer = "".join(event.get("text", "") for event in events if event["type"]=="message")
            assert "告诉我要查看的数据集名称" not in answer
            assert "操作对象或具体要求" not in answer
            if count:
                assert "Dataset 0" in answer and f"{count} 个候选" in answer
            else:
                assert "未找到" in answer and "检索范围" in answer
            assert "cstr" not in answer and "reference" not in answer
            assert events==await collect(service, sid, "Find chemical engineering datasets", "recovery")
            if count:
                # Partial presentation still supplies reliable follow-up handles.
                dialogue.responses = [native("directory", **{
                    OBJECT: "candidate:1", TASK: {"complete_request": True}}), text()]
                followup = await collect(service, sid, "Show the first candidate's directory", "followup")
                assert_completed(service, sid, followup[-1])
                assert backend.calls[-1]==("directory", {"reference": "0"})
        finally:
            await service.close()
    asyncio.run(run())


def test_partial_eligibility_preserves_scope_and_does_not_confirm_completion():
    operations = Operations()
    for label in ("required", "inferred", "supporting"):
        key = operations.register(label, {"server": "source", "name": label}, required=label=="required")
        if label=="inferred":
            operations.get(key)["inferred"] = True
        operations.start(key, label)
        operations.finish(key, label, result_id=label)
    assert operations.delivery_ids()==["required"]
    assert operations.delivery_ids(partial=True)==["required", "inferred"]
    operations.validate_delivery(["required", "inferred"], partial=True)
    for ids, partial in ((["inferred"], False), (["supporting"], True), (["foreign"], True)):
        with pytest.raises(QAError):
            operations.validate_delivery(ids, partial=partial)
    assert [item["description"] for item in operations.required]==["required"]


def test_exact_lookup_has_one_query_and_no_optional_detail(engine):
    async def run():
        title = "North station instrument observations"
        backend = SearchBackend(lambda query, number: {"items": [{"id": "station-1", "title": title}]})
        dialogue = BareDialogue(native("find_assets", phrase=title, **{
            TASK: {"complete_request": True, "keywords": None, "original_keywords": None}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find "+title)
            assert_completed(service, sid, events[-1])
            assert len(backend.calls)==1 and backend.calls[0][1]["phrase"]==title
            assert len(dialogue.inputs)==2 and len(result_cards(events))==1
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("ids", [[], ["saved-candidate"]])
def test_interrupted_keyword_plan_preserves_evidence_without_claiming_no_matches(engine, ids):
    async def run():
        backend = SearchBackend(lambda query, number: page(ids, len(ids)))
        backend.errors_at = {2: "PRIVATE_BACKEND_TRACE"}
        dialogue = BareDialogue(discover(complete=False))
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(max_corrections=0)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_handled(service, sid, events[-1], "tool_failed")
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==ids
            ledger = outcome(service, sid, events)
            search, = ledger["operations"]
            assert search["state"]=="failed" and not search["required"]
            assert search["search"]["completed"]==KEYWORDS[:1] and not search["search"]["done"]
            answer = "".join(event.get("text", "") for event in events if event["type"]=="message")
            assert "未找到" not in answer and "PRIVATE_BACKEND_TRACE" not in answer
            if ids:
                assert "saved-candidate" in answer
            assert len(backend.calls)==2 and len(dialogue.inputs)==1
        finally:
            await service.close()
    asyncio.run(run())
