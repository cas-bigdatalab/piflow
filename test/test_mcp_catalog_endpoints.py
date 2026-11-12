from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.mcp_catalog_router import router


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_mcp_catalog_returns_tool_summaries():
    with _build_client() as client:
        response = client.get("/mcp/catalog")

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["totalServers"] == 1
    assert result["totalTools"] == 8
    search_tool = next(tool for tool in result["servers"][0]["tools"] if tool["name"] == "search_corpus_datasets")
    assert search_tool["description"].startswith("检索数据集候选")
    assert "`keywords`" in search_tool["description"]
    assert {key: value for key, value in search_tool.items() if key != "description"} == {
        "name": "search_corpus_datasets",
        "displayName": "数据集检索",
        "category": "数据集发现",
        "icon": "database-search",
        "readOnly": True,
        "riskLevel": "low",
        "version": "1.0.0",
        "tags": ["corpus", "dataset", "search"],
        "inputCount": 9,
        "status": "available",
        "serverName": "piflow-corpus",
    }


def test_mcp_tool_detail_returns_full_contract():
    with _build_client() as client:
        response = client.get("/mcp/tools/search_corpus_datasets")

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["server"]["endpoint"] == "/api/piflow/v1/mcp/"
    assert result["tool"]["inputSchema"]["properties"]["page"]["default"] == 1
    assert result["tool"]["annotations"]["readOnlyHint"] is True
    assert result["tool"]["meta"]["piflow"]["category"] == "数据集发现"
    assert "async with Client(MCP_ENDPOINT)" in result["tool"]["usageExample"]
    assert 'MCP_ENDPOINT = "http://172.31.3.81:8086/api/piflow/v1/mcp/"' in result["tool"]["usageExample"]
    assert '"search_corpus_datasets"' in result["tool"]["usageExample"]

    with _build_client() as client:
        detail_response = client.get("/mcp/tools/get_corpus_dataset_detail")

    assert detail_response.status_code == 200
    detail_tool = detail_response.json()["result"]["tool"]
    assert detail_tool["inputSchema"]["required"] == ["cstr"]
    assert "dataset_id" not in detail_tool["inputSchema"]["properties"]
    assert '"cstr": "dataset_001"' in detail_tool["usageExample"]


def test_mcp_tool_detail_returns_404_for_unknown_tool():
    with _build_client() as client:
        response = client.get("/mcp/tools/not-found")

    assert response.status_code == 404
    assert response.json()["detail"] == "MCP tool not found: not-found"
