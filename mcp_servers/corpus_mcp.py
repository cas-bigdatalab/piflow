"""Corpus dataset tools exposed through the in-process MCP endpoint."""

from __future__ import annotations

from functools import partial
from typing import Annotated, Any

import anyio
from fastmcp import FastMCP
from pydantic import Field

from services.corpus_connector_service import (
    get_dataset_detail_by_cstr,
    get_dataset_preview,
    get_dataset_sampler,
    list_dataset_details,
)


mcp = FastMCP(
    "piflow-corpus",
    version="1.0.0",
    instructions=(
        "检索和查看服务中当前可见的数据集。 "
        "当数据集 ID 未知时，请先使用 search_corpus_datasets，再请求数据集详情。"
    ),
)

_MCP_ENDPOINT_EXAMPLE = "https://172.31.3.81:8086/api/piflow/v1/mcp/"

_SEARCH_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "search_corpus_datasets",
            {{
                "query": "锂电池",
                "field": "材料科学",
                "page": 1,
                "page_size": 10,
            }},
        )
        print(result)
'''

_DETAIL_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "get_corpus_dataset_detail",
            {{"cstr": "dataset_001"}},
        )
        print(result)
'''

_SAMPLE_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "sample_corpus_dataset",
            {{"cstr": "dataset_001", "size": 5}},
        )
        print(result)
'''

_PREVIEW_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "preview_corpus_dataset",
            {{"cstr": "dataset_001"}},
        )
        print(result)
'''


def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _dataset_filters(
    *,
    query: str | None,
    title: str | None,
    field: str | None,
    subject: str | None,
    author: str | None,
    doi: str | None,
    sources: list[str] | None,
) -> dict[str, Any]:
    if query is not None and title is not None:
        raise ValueError("query and title are mutually exclusive")
    return _drop_none(
        {
            "title": title if title is not None else query,
            "field": field,
            "subject": subject,
            "author": author,
            "doi": doi,
            "sources": sources,
        }
    )


@mcp.tool(
    annotations={
        "title": "数据集检索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "数据集检索",
            "category": "数据集发现",
            "icon": "database-search",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "dataset", "search"],
            "usageExample": _SEARCH_USAGE_EXAMPLE,
        }
    },
)
async def search_corpus_datasets(
    query: Annotated[str | None, Field(description="便捷检索词，映射为数据集标题筛选条件")] = None,
    title: Annotated[str | None, Field(description="数据集标题筛选条件")] = None,
    field: Annotated[str | None, Field(description="数据集所属领域筛选条件")] = None,
    subject: Annotated[str | None, Field(description="数据集学科方向筛选条件")] = None,
    author: Annotated[str | None, Field(description="数据集作者筛选条件")] = None,
    doi: Annotated[str | None, Field(description="数据集 DOI 筛选条件")] = None,
    sources: Annotated[list[str] | None, Field(description="数据集来源或连接器名称列表")] = None,
    page: Annotated[int, Field(description="页码，从 1 开始", ge=1)] = 1,
    page_size: Annotated[int, Field(description="每页返回数量，范围为 1 到 50", ge=1, le=50)] = 10,
) -> dict[str, Any]:
    """按元数据筛选条件和分页参数检索当前可见的数据集。

    ``query`` 是便捷检索参数，会映射为现有的标题筛选条件；需要明确按标题筛选时请使用 ``title``。
    返回结果中的分页总数保持当前筛选条件下数据集服务返回的总数。
    """
    filters = _dataset_filters(
        query=query,
        title=title,
        field=field,
        subject=subject,
        author=author,
        doi=doi,
        sources=sources,
    )

    return await anyio.to_thread.run_sync(
        partial(
            list_dataset_details,
            page_num=page,
            page_size=page_size,
            filters=filters,
        )
    )


@mcp.tool(
    annotations={
        "title": "数据集详情",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "数据集详情",
            "category": "数据集访问",
            "icon": "database",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "dataset", "detail"],
            "usageExample": _DETAIL_USAGE_EXAMPLE,
        }
    },
)
async def get_corpus_dataset_detail(
    cstr: Annotated[str, Field(description="数据集 CSTR 标识")],
) -> dict[str, Any]:
    """根据数据集 CSTR 获取详情，并原样返回对应的数据集详情结果。"""
    return await anyio.to_thread.run_sync(partial(get_dataset_detail_by_cstr, cstr))


@mcp.tool(
    annotations={"title": "数据集随机采样", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    meta={"piflow": {"displayName": "数据集随机采样", "category": "数据集采样", "icon": "database-sample", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "sample"], "usageExample": _SAMPLE_USAGE_EXAMPLE}},
)
async def sample_corpus_dataset(
    cstr: Annotated[str, Field(description="数据集 CSTR 标识")],
    size: Annotated[int, Field(description="随机采样条数，默认为 5 条", ge=1)] = 5,
) -> dict[str, Any]:
    """根据数据集 CSTR 随机采样指定条数，并原样返回上游响应。"""
    return await anyio.to_thread.run_sync(partial(get_dataset_sampler, cstr, size=size))


@mcp.tool(
    annotations={"title": "数据集预览", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    meta={"piflow": {"displayName": "数据集预览", "category": "数据集预览", "icon": "database-preview", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "preview"], "usageExample": _PREVIEW_USAGE_EXAMPLE}},
)
async def preview_corpus_dataset(
    cstr: Annotated[str, Field(description="数据集 CSTR 标识")],
) -> dict[str, Any]:
    """根据数据集 CSTR 获取预览结果，并原样返回上游响应。"""
    return await anyio.to_thread.run_sync(partial(get_dataset_preview, cstr))


def create_mcp_app():
    """Create the Streamable HTTP ASGI app mounted by ``server.py``."""
    return mcp.http_app(path="/", transport="streamable-http")
