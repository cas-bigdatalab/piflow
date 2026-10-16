"""Corpus dataset tools exposed through the in-process MCP endpoint."""

from __future__ import annotations

from functools import partial
from typing import Annotated, Any

import anyio
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from services.corpus_connector_service import (
    get_dataset_detail_by_cstr,
    get_dataset_directory,
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

_MCP_ENDPOINT_EXAMPLE = "http://172.31.3.81:8086/api/piflow/v1/mcp/"

_SEARCH_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "search_corpus_datasets",
            {{
                "query": "锂电池",
                "page": 1,
                "page_size": 5,
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

_DIRECTORY_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "get_corpus_dataset_directory",
            {{"cstr": "dataset_001"}},
        )
        print(result)
'''


def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _checked_result(payload: dict[str, Any]) -> dict[str, Any]:
    # Only this server knows the upstream's business envelope. Keep successful
    # JSON intact; expose business failures as standard MCP errors.
    if "code" in payload and str(payload["code"])!="200":
        raise ToolError(str(payload.get("message") or "数据集服务执行失败")[:2000])
    return payload


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
    if title is not None and title.strip():
        raise ToolError("上游标题筛选暂不可用，请使用 query 按关键词检索，或使用 field/subject 等元数据条件")
    return _drop_none(
        {
            "keywords": query,
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
            "view_type": "data",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "dataset", "search"],
            "usageExample": _SEARCH_USAGE_EXAMPLE,
        }
    },
)
async def search_corpus_datasets(
    query: Annotated[str | None, Field(description="通用检索词，映射为上游 keywords 参数。自然语言表达的主题或领域相关检索优先使用此参数；具体匹配范围以上游服务为准")] = None,
    title: Annotated[str | None, Field(description="兼容旧参数；当前上游标题筛选不可用，传入非空标题会返回错误，请使用 query 或其他元数据条件")] = None,
    field: Annotated[str | None, Field(description="领域分类筛选，须使用服务已确认的分类值；不做同义词或语义扩展。未确认分类值时使用 query，不要把用户的领域用词直接猜成分类值")] = None,
    subject: Annotated[str | None, Field(description="学科分类筛选，须使用服务已确认的分类值；未确认分类值时使用 query，不要猜测分类名称")] = None,
    author: Annotated[str | None, Field(description="数据集作者筛选条件")] = None,
    doi: Annotated[str | None, Field(description="数据集 DOI 筛选条件")] = None,
    sources: Annotated[list[str] | None, Field(description="数据集来源或连接器名称列表")] = None,
    page: Annotated[int, Field(description="页码，从 1 开始", ge=1)] = 1,
    page_size: Annotated[int, Field(description="每页返回数量，默认 5 条，范围为 1 到 5；更多结果通过 page 翻页获取", ge=1, le=5)] = 5,
) -> dict[str, Any]:
    """按元数据筛选条件和分页参数检索当前可见的数据集。

    自然语言主题或领域相关检索优先使用 `query`，映射到上游 `keywords`。
    `field` / `subject` 只用于已从服务元数据确认的分类值；多个条件同时传入会收窄范围。
    空结果只表示当前条件未匹配，不代表用户需求不明确或整个相关领域没有数据。
    当前上游标题筛选不可用，非空 `title` 会返回错误，不会降级成无筛选列表。
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
            "view_type": "data",
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
    """根据数据集 CSTR 获取数据集级说明与元信息，如简介、大小、格式、来源和作者，原样返回上游详情。

    用户希望了解某个数据集，或仅说“看看这个数据集”且上下文未指向其他操作时使用。
    文件和文件夹列表、目录结构及子目录展开由目录工具提供。
    """
    return await anyio.to_thread.run_sync(partial(get_dataset_detail_by_cstr, cstr))


@mcp.tool(
    annotations={"title": "数据集随机采样", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    meta={"piflow": {"displayName": "数据集随机采样", "category": "数据集采样", "icon": "database-sample", "view_type": "url", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "sample"], "usageExample": _SAMPLE_USAGE_EXAMPLE}},
)
async def sample_corpus_dataset(
    cstr: Annotated[str, Field(description="数据集 CSTR 标识")],
    size: Annotated[int, Field(description="随机采样条数，默认为 5 条", ge=1)] = 5,
) -> dict[str, Any]:
    """根据数据集 CSTR 随机采样指定条数，并原样返回上游响应。"""
    return _checked_result(await anyio.to_thread.run_sync(partial(get_dataset_sampler, cstr, size=size)))


@mcp.tool(
    annotations={"title": "查看数据内容", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    meta={"piflow": {"displayName": "查看数据内容", "category": "数据内容查看", "icon": "database-directory", "view_type": "directory", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "content"], "usageExample": _DIRECTORY_USAGE_EXAMPLE}},
)
async def get_corpus_dataset_directory(
    cstr: Annotated[str, Field(description="数据集 CSTR 标识")],
    file_id: Annotated[str | None, Field(description="要展开的目录节点 fileId；不传时获取目录根层")] = None,
) -> dict[str, Any]:
    """根据数据集 CSTR 浏览文件和文件夹列表、目录结构，原样返回上游响应。

    当前服务中的“预览”或“查看数据内容”指目录浏览，返回内容组织结构，不读取文件正文或采样记录。
    省略 file_id 获取目录根层；传入已有目录节点的 fileId 获取该节点的下一层。
    数据集简介、大小、格式、来源等元信息由详情工具提供。
    """
    return _checked_result(
        await anyio.to_thread.run_sync(partial(get_dataset_directory, cstr, file_id=file_id))
    )


def create_mcp_app():
    """Create the Streamable HTTP ASGI app mounted by ``server.py``."""
    return mcp.http_app(path="/", transport="streamable-http")
