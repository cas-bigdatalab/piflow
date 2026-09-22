import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastmcp.utilities.lifespan import combine_lifespans

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
    assert search_tool["annotations"] == {
        "title": "Corpus 数据集检索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    assert {key: value for key, value in search_tool["_meta"]["piflow"].items() if key != "usageExample"} == {
        "displayName": "Corpus 数据集检索",
        "category": "语料发现",
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
    ) == {"title": "\u5730\u9707", "sources": ["connector-a"]}
