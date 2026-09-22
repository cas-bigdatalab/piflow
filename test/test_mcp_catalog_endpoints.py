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
    assert result["totalTools"] == 4
    search_tool = next(tool for tool in result["servers"][0]["tools"] if tool["name"] == "search_corpus_datasets")
    assert search_tool == {
        "name": "search_corpus_datasets",
        "displayName": "Corpus 数据集检索",
        "description": "按元数据筛选条件和分页参数检索当前可见的 Corpus 数据集。\n\n``query`` 是便捷检索参数，会映射为现有的标题筛选条件；需要明确按标题筛选时请使用 ``title``。\n返回结果中的分页总数保持当前筛选条件下 Corpus 服务返回的总数。",
        "category": "语料发现",
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
    assert result["tool"]["meta"]["piflow"]["category"] == "语料发现"
    assert "async with Client(MCP_ENDPOINT)" in result["tool"]["usageExample"]
    assert '"search_corpus_datasets"' in result["tool"]["usageExample"]


def test_mcp_tool_detail_returns_404_for_unknown_tool():
    with _build_client() as client:
        response = client.get("/mcp/tools/not-found")

    assert response.status_code == 404
    assert response.json()["detail"] == "MCP tool not found: not-found"
