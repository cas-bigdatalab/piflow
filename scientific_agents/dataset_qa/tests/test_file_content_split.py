"""Independent file tools preserve connector behavior and QA delivery contracts."""
import asyncio
from collections import Counter

from fastmcp import Client
import pytest

from mcp_servers.corpus_mcp import mcp
from services import corpus_connector_service as connector
from ..contracts import Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, goals, text


URL = "https://example.invalid/measurements.jsonl"
SCHEMA_ROUTE = "/api.schema.infer"
RECORD_ROUTE = "/corpus.url.sampler"
SCHEMA = {"type": "object", "properties": {"value": {"type": "number"}}}
RECORDS = [{"value": 1}, {"value": 2}]


@pytest.fixture
def upstream(monkeypatch):
    calls = []

    def request(method, path, *, params):
        calls.append((method, path, params))
        assert path in {SCHEMA_ROUTE, RECORD_ROUTE}
        return {"code": 200, "data": SCHEMA if path==SCHEMA_ROUTE else RECORDS}

    monkeypatch.setattr(connector, "_request_corpus_route", request)
    return calls


@pytest.mark.parametrize("tool,route,params,present,absent", [
    ("get_corpus_file_schema", SCHEMA_ROUTE, {"filePath": URL}, "schema", "data"),
    ("read_corpus_file_records", RECORD_ROUTE, {"url": URL, "size": 5}, "data", "schema"),
])
def test_each_mcp_tool_calls_only_its_own_endpoint(upstream, tool, route, params, present, absent):
    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, {"download_url": URL})
            assert not result.is_error
            assert result.structured_content[present]==(SCHEMA if present=="schema" else RECORDS)
            assert absent not in result.structured_content
            assert result.structured_content["downloadUrl"]==URL
    asyncio.run(run())
    assert upstream==[("GET", route, params)]


@pytest.mark.parametrize("reader", [connector.get_file_schema, connector.get_file_records])
def test_unsupported_format_keeps_availability_information_without_upstream_io(upstream, reader):
    result = reader("https://example.invalid/archive.tar")
    assert result["previewable"] is False
    assert result["format"] is None and result["message"] and result["warnings"]==[]
    assert not upstream


@pytest.mark.parametrize("reader", [connector.get_file_schema, connector.get_file_records])
@pytest.mark.parametrize("url", ["records.jsonl", "/tmp/records.json", "file:///tmp/records.json", "https:///records.json"])
def test_invalid_location_is_rejected_before_upstream_io(upstream, reader, url):
    with pytest.raises(ValueError, match="absolute http or https URL"):
        reader(url)
    assert not upstream


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_record_budget_is_rejected_before_upstream_io(upstream, size):
    with pytest.raises(ValueError, match="size must be positive"):
        connector.get_file_records(URL, size=size)
    assert not upstream


def test_record_tool_keeps_existing_size_cap(upstream):
    result = connector.get_file_records(URL, size=100)
    assert upstream==[("GET", RECORD_ROUTE, {"url": URL, "size": 20})]
    assert result["requestedSize"]==100 and result["effectiveSize"]==20
    assert result["returnedCount"]==len(RECORDS) and result["truncated"] is True


@pytest.mark.parametrize("raw,expected", [(None, []), ({"value": 3}, [{"value": 3}]), (RECORDS, RECORDS)])
def test_record_tool_preserves_sampler_value_normalization(monkeypatch, raw, expected):
    monkeypatch.setattr(connector, "_request_corpus_route", lambda *args, **kwargs: {"code": 200, "data": raw})
    result = connector.get_file_records(URL)
    assert result["data"]==expected and result["returnedCount"]==len(expected)
    assert result["truncated"] is False and result["warnings"]==[]


@pytest.mark.parametrize("kind", ["record", "response"])
def test_record_tool_preserves_byte_limits(monkeypatch, kind):
    records = [{"value": "x" * (connector.DATASET_SAMPLE_MAX_RECORD_BYTES + 1)}] if kind=="record" else [
        {"value": "x" * (connector.DATASET_SAMPLE_MAX_RECORD_BYTES // 2)} for _ in range(20)]
    monkeypatch.setattr(connector, "_request_corpus_route", lambda *args, **kwargs: {"code": 200, "data": records})
    result = connector.get_file_records(URL, size=20)
    assert result["truncated"] is True
    assert connector._json_size(result["data"])<=connector.DATASET_SAMPLE_MAX_RESPONSE_BYTES
    if kind=="record":
        assert result["data"][0]["__truncated__"] is True
    else:
        assert 0 < result["returnedCount"] < len(records)


@pytest.mark.parametrize("failed_route", [SCHEMA_ROUTE, RECORD_ROUTE])
def test_combined_python_api_preserves_partial_results_and_warning_order(monkeypatch, failed_route):
    calls = []

    def request(method, route, *, params):
        calls.append(route)
        if route==failed_route:
            return {"code": 503, "message": "upstream unavailable"}
        return {"code": 200, "data": SCHEMA if route==SCHEMA_ROUTE else RECORDS}

    monkeypatch.setattr(connector, "_request_corpus_route", request)
    result = connector.get_file_schema_and_sample(URL)
    assert calls==[SCHEMA_ROUTE, RECORD_ROUTE]
    assert result["schema"]==(None if failed_route==SCHEMA_ROUTE else SCHEMA)
    assert result["data"]==([] if failed_route==RECORD_ROUTE else RECORDS)
    assert len(result["warnings"])==1 and failed_route in result["warnings"][0]
    # Splitting does not introduce a fallback request to the other endpoint.
    calls.clear()
    reader = connector.get_file_schema if failed_route==SCHEMA_ROUTE else connector.get_file_records
    separate = reader(URL)
    assert calls==[failed_route] and separate["warnings"]==result["warnings"]


def test_combined_python_api_keeps_its_existing_response(upstream):
    assert connector.get_file_schema_and_sample(URL, size=3)=={
        "downloadUrl": URL, "previewable": True, "message": "", "format": "jsonl",
        "schema": SCHEMA, "data": RECORDS, "requestedSize": 3, "effectiveSize": 3,
        "returnedCount": 2, "truncated": False, "warnings": [],
    }
    assert upstream==[("GET", SCHEMA_ROUTE, {"filePath": URL}), ("GET", RECORD_ROUTE, {"url": URL, "size": 3})]


def test_qa_delivers_both_file_results_without_repeating_upstream_work(engine, upstream):
    async def run():
        dialogue = BareDialogue(load("piflow-corpus"),
            goals({"description": "Read file schema", "tool": "get_corpus_file_schema"},
                {"description": "Read file records", "tool": "read_corpus_file_records"}, calls=[
                    remote("get_corpus_file_schema", download_url=URL),
                    remote("read_corpus_file_records", download_url=URL, size=2)]),
            action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(mcp)}))
        try:
            result = await collect(service, session(service), "Read schema and 2 sample records from " + URL)
            assert_completed(service, None, result[-1])
            cards = result_cards(result)
            assert len(cards)==2
            assert next(card for card in cards if "schema" in card["data"]["items"][0])["view_type"]=="data"
            assert next(card for card in cards if "data" in card["data"]["items"][0])["view_type"]=="table"
            values = [card["data"]["items"][0] for card in cards]
            assert next(value for value in values if "schema" in value)["schema"]==SCHEMA
            assert next(value for value in values if "data" in value)["data"]==RECORDS
        finally:
            await service.close()
    asyncio.run(run())
    assert Counter(route for _, route, _ in upstream)=={SCHEMA_ROUTE: 1, RECORD_ROUTE: 1}
