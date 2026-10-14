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

    search_tool = next(tool for tool in tools if tool["name"] == "search_corpus_datasets")
    assert "keywords" in search_tool["inputSchema"]["properties"]["query"]["description"]
    assert "不可用" in search_tool["inputSchema"]["properties"]["title"]["description"]
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
            assert calls==[(2, 3, {"keywords": "气象"}), (1, 10, {"keywords": "不存在的关键词"})]
            unsupported = await client.call_tool("search_corpus_datasets", {"title": "气象"}, raise_on_error=False)
            assert unsupported.is_error and "标题筛选暂不可用" in unsupported.content[0].text
            assert len(calls)==2  # Rejected before dispatch, never returns the default page.
    asyncio.run(run())
