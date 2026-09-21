"""Corpus dataset tools exposed through the in-process MCP endpoint."""

from __future__ import annotations

from functools import partial
from typing import Any

import anyio
from fastmcp import FastMCP

from services.corpus_connector_service import get_dataset_detail, list_dataset_details


mcp = FastMCP(
    "piflow-corpus",
    version="1.0.0",
    instructions=(
        "Search and inspect datasets that are visible through the PiFlow Corpus service. "
        "Use search_corpus_datasets before requesting a dataset detail when the ID is unknown."
    ),
)


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
        "title": "Corpus 数据集检索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "Corpus 数据集检索",
            "category": "数据检索",
            "icon": "database-search",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "dataset", "search"],
        }
    },
)
async def search_corpus_datasets(
    query: str | None = None,
    title: str | None = None,
    field: str | None = None,
    subject: str | None = None,
    author: str | None = None,
    doi: str | None = None,
    sources: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Search visible Corpus datasets with metadata filters and pagination.

    ``query`` is a convenience full-text-like input mapped to the existing
    Corpus title filter. Use ``title`` when an exact title filter is preferred.
    The response preserves the Corpus pagination total for the supplied filters.
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
        "title": "Corpus 数据集详情",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "Corpus 数据集详情",
            "category": "数据检索",
            "icon": "database",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "dataset", "detail"],
        }
    },
)
async def get_corpus_dataset_detail(dataset_id: str) -> dict[str, Any]:
    """Get one visible Corpus dataset and its available connector replicas."""
    return await anyio.to_thread.run_sync(partial(get_dataset_detail, dataset_id))


def create_mcp_app():
    """Create the Streamable HTTP ASGI app mounted by ``server.py``."""
    return mcp.http_app(path="/", transport="streamable-http")
