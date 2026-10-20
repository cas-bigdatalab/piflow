"""Bounded model summaries preserve record identity without changing artifacts."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from .context import encode, project, slice_result
from .persistence import dumps
from .results import evidence
from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, collect, engine, load, remote, result_cards, session


def search_result(count=5):
    rows = []
    for index in range(count):
        title = ("Energy Department Awards Contracts from the Strategic Petroleum Reserve, "
            "Advancing President Trump’s Historic Emergency Exchange "+str(index))
        connector = {"connectorId": "DS-NODE-9", "connectorOrganization": "U.S. Department of Energy",
            "fromName": "新闻资讯", "latency_ms": 4.354, "name": "新闻资讯", "recommended": True,
            "status": "可用", "sync": "2026-10-13 14:20:57"}
        rows.append({"id": "record-"+str(index), "cstr": "reference-"+str(index), "title": title,
            "connectorId": "DS-NODE-9", "fromName": "新闻资讯", "source": "新闻资讯",
            "connectors": [connector], "replicaCount": 1,
            "raw": {"title": title, "description": "News description. "*100, "usage": "News body. "*1000},
            "connectorOrganization": "U.S. Department of Energy", "name": "新闻资讯"})
    return {"items": rows, "pagination": {"total": 739, "pageNum": 1, "pageSize": count}}


def test_under_budget_projection_and_repeated_wrapping_are_lossless():
    value = {"data": {"items": [{"raw": {"body": "body "*40}, "id": str(i),
        "title": "A long title "*20+str(i)} for i in range(5)]}, "total": 739}
    assert len(encode(value))<8000
    assert project(value, 8000)==(value, False)
    wrapped = {"final_delivery": [value], "stop_reason": None}
    assert project(wrapped, 8000)==(wrapped, False)


def test_small_payload_still_filters_secrets_binary_and_excessive_depth():
    nested = {"value": "hidden"}
    for _ in range(14):
        nested = {"next": nested}
    value = {"title": "Object", "Authorization": "private", "nested": nested,
        "items": [{"token": "private", "zero": 0, "enabled": False, "empty": None,
            "media": [{"type": "image", "data": "YWJj", "mimeType": "image/png"},
                {"type": "audio", "data": "YWJj", "mimeType": "audio/wav"}],
            "file": {"base64": "YWJj", "blob": "YWJj", "url": "https://example.invalid/a.pdf"}}]}
    original = deepcopy(value)
    result, cut = project(value, 8000)
    assert cut and value==original and len(encode(result))<=8000
    assert "private" not in encode(result) and "YWJj" not in encode(result) and "hidden" not in encode(result)
    assert result["items"][0]=={"zero": 0, "enabled": False, "empty": None,
        "media": [{"type": "image", "mimeType": "image/png"}, {"type": "audio", "mimeType": "audio/wav"}],
        "file": {"url": "https://example.invalid/a.pdf"}}
    assert project(result, 8000)==(result, False)


def test_scalar_metadata_survives_large_earlier_fields():
    metadata = {"id": "abc-012345", "title": "A complete object title "*8,
        "custom_reference": "ref-345", "count": 0, "enabled": False, "name": "Source"}
    value = {"raw": {"body": "body "*4000}, "description": "description "*1000, **metadata}
    original = deepcopy(value)
    result, cut = project(value, 600)
    assert cut and len(encode(result))<=600 and value==original
    assert {key: result[key] for key in metadata}==metadata


@pytest.mark.parametrize("limit", [4, 32, 128, 512, 1500, 8000])
def test_projection_budget_and_list_positions_remain_valid(limit):
    value = search_result(20)
    result, cut = project(value, limit)
    assert cut and len(encode(result))<=limit and json.loads(encode(result))==result
    for index, item in enumerate((result or {}).get("items", [])):
        for key in ("id", "cstr", "title"):
            if key in item:
                assert item[key]==value["items"][index][key]


@pytest.mark.parametrize("limit", [64, 256, 2000])
def test_resource_urls_are_whole_or_omitted(limit):
    url = "https://example.invalid/preview.pdf?signature="+"signed"*80
    result, _ = project({"raw": {"body": "body "*1000}, "url": url, "title": "Preview"}, limit)
    assert len(encode(result))<=limit
    if "url" in result:
        assert result["url"]==url


@pytest.mark.parametrize("count", [1, 5])
def test_saved_search_titles_survive_final_delivery_projection(count):
    payload = search_result(count)
    card = json.loads(dumps({"result_id": "task:0", "view_type": "data", "title": "Search results", "data": payload}))
    original = deepcopy(card)
    summary = evidence(card, 8000)
    delivery, _ = project({"final_delivery": [summary], "stop_reason": None}, 8000)
    rows = delivery["final_delivery"][0]["data"]["items"]
    assert len(rows)==count and [row["title"] for row in rows]==[row["title"] for row in payload["items"]]
    assert slice_result(delivery["final_delivery"][0]["data"], "/items/0/title", 0, 1)==(payload["items"][0]["title"], False)
    assert card==original and len(encode(delivery))<=8000


@pytest.mark.parametrize("batches", [1, 2])
def test_final_model_receives_titles_within_budget_and_public_results_are_unchanged(engine, batches):
    async def run():
        backend, final_inputs = Backend(), []
        payload = search_result()
        factory = backend.client

        def client(*args, **kwargs):
            connection = factory(*args, **kwargs)
            execute = connection.call_tool

            async def call(*args, **kwargs):
                await execute(*args, **kwargs)
                return SimpleNamespace(structured_content=deepcopy(payload), is_error=False)
            connection.call_tool = call
            return connection

        class BudgetedDialogue(Dialogue):
            async def respond(self, messages, definitions):
                bounded = self.budget(messages, definitions)
                if not definitions:
                    final_inputs.append(bounded)
                async for chunk in super().respond(bounded, definitions):
                    yield chunk

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = BudgetedDialogue(load(), *[remote("search", query="batch-"+str(i)) for i in range(batches)])
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid)
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==batches
            messages, = final_inputs
            delivery = json.loads(messages[-1].content)
            assert len(encode(delivery))<=gateway.limits.result_chars
            assert len(encode([m.model_dump(mode="json", exclude_none=True) for m in messages]))<=gateway.limits.context_chars
            assert len(delivery["final_delivery"])==1
            for card in delivery["final_delivery"]:
                assert [row["title"] for row in card["data"]["items"]]==[row["title"] for row in payload["items"]]
                assert [row["id"] for row in card["data"]["items"]]==[row["id"] for row in payload["items"]]
                assert card["data"]["pagination"]==payload["pagination"]
            cards = result_cards(values)
            assert len(cards)==1 and cards[0]["data"]==payload
            saved = service.store.results("alice", sid, values[-1]["task_id"])
            assert len(saved)==batches and all(card["data"]==payload for card in saved)
            assert await collect(service, sid)==values and len(backend.calls)==batches
        finally:
            await service.close()
    asyncio.run(run())
