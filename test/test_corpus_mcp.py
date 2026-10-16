import json
import asyncio

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastmcp.utilities.lifespan import combine_lifespans
from fastmcp.exceptions import ToolError

from mcp_servers.corpus_mcp import _dataset_filters, create_mcp_app


def _build_client() -> TestClient:
    app = FastAPI()
    mcp_app = create_mcp_app()
    app.router.lifespan_context = combine_lifespans(app.router.lifespan_context, mcp_app.lifespan)
    app.mount("/api/piflow/v1/mcp", mcp_app)
    return TestClient(app)


def _sse_json(response):
    data_line = next(line for line in response.text.splitlines() if line.startswith("data: "))
    return json.loads(data_line.removeprefix("data: "))


def test_corpus_mcp_lists_dataset_tools():
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
    }
    with _build_client() as client:
        initialize = client.post(
            "/api/piflow/v1/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
            headers=headers,
        )
        assert initialize.status_code == 200
        headers["mcp-session-id"] = initialize.headers["mcp-session-id"]

        response = client.post(
            "/api/piflow/v1/mcp/",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers=headers,
        )

    assert response.status_code == 200
    tools = _sse_json(response)["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert tool_names == {
        "search_corpus_datasets",
        "get_corpus_dataset_detail",
        "sample_corpus_dataset",
        "preview_corpus_dataset",
    }
    assert {tool["name"]: tool["_meta"]["piflow"]["view_type"] for tool in tools} == {
        "search_corpus_datasets": "data",
        "get_corpus_dataset_detail": "data",
        "sample_corpus_dataset": "url",
        "preview_corpus_dataset": "url",
    }

    search_tool = next(tool for tool in tools if tool["name"] == "search_corpus_datasets")
    assert "keywords" in search_tool["inputSchema"]["properties"]["query"]["description"]
    assert "不可用" in search_tool["inputSchema"]["properties"]["title"]["description"]
    assert search_tool["inputSchema"]["properties"]["page_size"]["default"]==5
    assert search_tool["inputSchema"]["properties"]["page_size"]["maximum"]==5
    assert search_tool["annotations"] == {
        "title": "数据集检索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    assert {key: value for key, value in search_tool["_meta"]["piflow"].items() if key != "usageExample"} == {
        "displayName": "数据集检索",
        "category": "数据集发现",
        "icon": "database-search",
        "view_type": "data",
        "riskLevel": "low",
        "version": "1.0.0",
        "tags": ["corpus", "dataset", "search"],
    }
    assert '"search_corpus_datasets"' in search_tool["_meta"]["piflow"]["usageExample"]


def test_search_corpus_datasets_builds_existing_service_filters():
    assert _dataset_filters(
        query="\u5730\u9707",
        title=None,
        field=None,
        subject=None,
        author=None,
        doi=None,
        sources=["connector-a"],
    ) == {"keywords": "\u5730\u9707", "sources": ["connector-a"]}


def test_search_rejects_unsupported_title_and_conflicting_aliases():
    values = dict(query=None, title="气象", field=None, subject=None,
        author=None, doi=None, sources=None)
    with pytest.raises(ToolError, match="标题筛选暂不可用"):
        _dataset_filters(**values)
    with pytest.raises(ValueError, match="mutually exclusive"):
        _dataset_filters(**{**values, "query": "气象"})
    assert _dataset_filters(**{**values, "title": None, "field": "地球科学"})=={"field": "地球科学"}
    assert _dataset_filters(**{**values, "title": None})=={}


def test_search_mcp_forwards_keywords_and_preserves_result_contract(monkeypatch):
    from fastmcp import Client
    from mcp_servers.corpus_mcp import mcp
    calls = []

    def upstream(*, page_num, page_size, filters):
        calls.append((page_num, page_size, filters))
        rows = [{"id": "weather", "cstr": "CSTR-WEATHER", "title": "气象数据"}] if filters.get("keywords")=="气象" else []
        return {"items": rows, "pagination": {"pageNum": page_num, "pageSize": page_size, "total": len(rows)}}

    monkeypatch.setattr("mcp_servers.corpus_mcp.list_dataset_details", upstream)

    async def run():
        async with Client(mcp) as client:
            found = await client.call_tool("search_corpus_datasets", {"query": "气象", "page": 2, "page_size": 3})
            missing = await client.call_tool("search_corpus_datasets", {"query": "不存在的关键词"})
            assert found.structured_content=={"items": [{"id": "weather", "cstr": "CSTR-WEATHER", "title": "气象数据"}],
                "pagination": {"pageNum": 2, "pageSize": 3, "total": 1}}
            assert missing.structured_content["items"]==[]
            assert calls==[(2, 3, {"keywords": "气象"}), (1, 5, {"keywords": "不存在的关键词"})]
            unsupported = await client.call_tool("search_corpus_datasets", {"title": "气象"}, raise_on_error=False)
            assert unsupported.is_error and "标题筛选暂不可用" in unsupported.content[0].text
            assert len(calls)==2  # Rejected before dispatch, never returns the default page.
            excessive = await client.call_tool("search_corpus_datasets", {"query": "气象", "page_size": 6}, raise_on_error=False)
            assert excessive.is_error and len(calls)==2
    asyncio.run(run())


@pytest.mark.parametrize("tool,cstr", [
    ("preview_corpus_dataset", "CHEM-CORPUS-B010"),
    ("preview_corpus_dataset", "SA-CORPUS-B031"),
    ("preview_corpus_dataset", "news-dataset"),
    ("sample_corpus_dataset", "CHEM-CORPUS-B010"),
])
def test_business_failure_is_an_mcp_error(monkeypatch, tool, cstr):
    from fastmcp import Client
    from mcp_servers.corpus_mcp import mcp
    payload = {"code": 500, "message": "数据暂不可用", "data": None}
    monkeypatch.setattr("mcp_servers.corpus_mcp.get_dataset_detail_by_cstr",
        lambda cstr: {"source": "新闻资讯" if cstr=="news-dataset" else "科研语料库"})
    for name in ("get_dataset_preview", "get_dataset_sampler", "_request_corpus_route"):
        monkeypatch.setattr("mcp_servers.corpus_mcp."+name, lambda *args, **kwargs: payload)

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool(tool, {"cstr": cstr}, raise_on_error=False)
            assert result.is_error and "数据暂不可用" in result.content[0].text
    asyncio.run(run())


@pytest.mark.parametrize("cstr,source,expected_path,expected_params", [
    ("SA-CORPUS-B031", None, "/corpus.preview/SA-CORPUS-B031", None),
    ("  SA-CORPUS-B031  ", None, "/corpus.preview/SA-CORPUS-B031", None),
    ("75ae2f15-435b-4426-8958-d8686f1baddd", "新闻资讯", "/corpus.preview/75ae2f15-435b-4426-8958-d8686f1baddd", None),
    ("f24264f1-ecbb-4c9e-809e-7227e61e6129", "新闻资讯", "/corpus.preview/f24264f1-ecbb-4c9e-809e-7227e61e6129", None),
    (" NEWS-DATASET-001 ", " 新闻资讯 ", "/corpus.preview/NEWS-DATASET-001", None),
    ("CHEM-CORPUS-B010", "科研语料库", "/corpus.dataset.preview", {"cstr": "CHEM-CORPUS-B010"}),
    ("SA-C0RPUS-B031", "科研语料库", "/corpus.dataset.preview", {"cstr": "SA-C0RPUS-B031"}),
    ("75ae2f15-435b-4426-8958-d8686f1baddd-extra", "科研语料库", "/corpus.dataset.preview", {"cstr": "75ae2f15-435b-4426-8958-d8686f1baddd-extra"}),
    ("75ae2f15-435b-4426-8958-d8686f1baddd", "科研语料库", "/corpus.dataset.preview", {"cstr": "75ae2f15-435b-4426-8958-d8686f1baddd"}),
    ("OTHER-DATASET", "新闻资讯备份", "/corpus.dataset.preview", {"cstr": "OTHER-DATASET"}),
    ("OTHER-DATASET", None, "/corpus.dataset.preview", {"cstr": "OTHER-DATASET"}),
])
def test_preview_mcp_routes_by_designated_id_or_actual_source(monkeypatch, cstr, source, expected_path, expected_params):
    from types import SimpleNamespace
    from fastmcp import Client
    from mcp_servers.corpus_mcp import mcp
    from services import corpus_connector_service

    calls = []
    payload = {"code": 200, "message": "OK", "data": {
        "records": [{"id": 1}], "imageUrl": "https://example.invalid/preview.png",
        "pdfUrl": "https://example.invalid/preview.pdf"}, "timestamp": 123}

    def get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        data = {"code": 200, "data": {"cstr": cstr.strip(), "source": source}} if "/dataset/" in url else payload
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: data)

    monkeypatch.setattr(corpus_connector_service, "get_settings", lambda: SimpleNamespace(
        corpus_route=SimpleNamespace(base_url="http://corpus.example/")))
    monkeypatch.setattr(corpus_connector_service.requests, "get", get)

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("preview_corpus_dataset", {"cstr": cstr})
            assert result.structured_content == payload
            expected = [] if cstr.strip()=="SA-CORPUS-B031" else [
                ("http://corpus.example/dataset/"+cstr.strip(), None, corpus_connector_service.REQUEST_TIMEOUT)]
            expected.append(("http://corpus.example"+expected_path, expected_params,
                corpus_connector_service.DATASET_PREVIEW_TIMEOUT))
            assert calls == expected

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["network", "business", "empty", "invalid"])
def test_preview_mcp_does_not_guess_route_when_detail_lookup_fails(monkeypatch, failure):
    from types import SimpleNamespace
    from fastmcp import Client
    from mcp_servers.corpus_mcp import mcp
    from services import corpus_connector_service

    calls = []

    def get(url, params=None, timeout=None):
        calls.append(url)
        assert url == "http://corpus.example/dataset/NEWS-DATASET-001"
        if failure=="network":
            raise corpus_connector_service.requests.ConnectionError("unavailable")
        payload = {"code": 500 if failure=="business" else 200,
            "message": "详情不可用", "data": ["invalid"] if failure=="invalid" else None}
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)

    monkeypatch.setattr(corpus_connector_service, "get_settings", lambda: SimpleNamespace(
        corpus_route=SimpleNamespace(base_url="http://corpus.example")))
    monkeypatch.setattr(corpus_connector_service.requests, "get", get)

    async def run():
        async with Client(mcp) as client:
            result = await client.call_tool("preview_corpus_dataset", {"cstr": "NEWS-DATASET-001"}, raise_on_error=False)
            assert result.is_error and "查询数据集来源失败，未执行预览" in result.content[0].text
            assert calls==["http://corpus.example/dataset/NEWS-DATASET-001"]
    asyncio.run(run())
