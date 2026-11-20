"""BDBE metadata and GenBank tools registered on the corpus MCP server."""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

import anyio
from fastmcp.exceptions import ToolError
from pydantic import Field

from infra.config_loader import resolve_workspace_root
from services.bdbe_service import BdbeUpstreamError, get_metadata_detail, query_metadata, stream_genbank
from mcp_servers.corpus_mcp import mcp


def _upstream_tool_error(exc: BdbeUpstreamError) -> ToolError:
    if exc.status_code == 401:
        return ToolError("BDBE 认证失败，请检查服务端 AccessKey 配置")
    if exc.status_code == 403:
        return ToolError("BDBE 接口权限不足")
    if exc.status_code == 422:
        return ToolError("BDBE 请求参数校验失败")
    return ToolError("BDBE 服务暂时不可用")


def _safe_filename(content_disposition: str | None) -> str:
    raw = ""
    for marker in ("filename*=", "filename="):
        if marker in (content_disposition or "").lower():
            raw = (content_disposition or "").split("=", 1)[1]
            break
    raw = raw.split(";", 1)[0].strip().strip('"')
    if raw.lower().startswith("utf-8''"):
        raw = raw[7:]
    filename = Path(raw or "genbank.gbff").name
    return filename or "genbank.gbff"


@mcp.tool(
    annotations={"title": "BDBE 数据检索", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    meta={"piflow": {"displayName": "BDBE 数据检索", "category": "BDBE 数据发现", "icon": "database-search", "view_type": "data", "riskLevel": "low", "version": "1.0.0", "tags": ["bdbe", "search", "metadata"]}},
)
async def search_bdbe_metadata(
    term: Annotated[str, Field(min_length=1, max_length=500, description="BDBE 全文检索关键词")],
    db: Annotated[str | None, Field(max_length=200, description="数据库标识，可选")] = None,
    page: Annotated[int, Field(ge=1, description="页码，从 1 开始")] = 1,
    pagesize: Annotated[int, Field(ge=1, le=1000, description="每页条数")] = 100,
    genome_next: Annotated[str | None, Field(alias="genomeNext", max_length=200, description="Genome 聚合分页参数")] = None,
    sessionid: Annotated[str | None, Field(max_length=500, description="可选的上游会话 ID")] = None,
) -> Any:
    """通过 BDBE 检索元数据，返回上游检索结果。"""
    try:
        return await anyio.to_thread.run_sync(partial(query_metadata, term=term, db=db, page=page, pagesize=pagesize, genome_next=genome_next, sessionid=sessionid))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except BdbeUpstreamError as exc:
        raise _upstream_tool_error(exc) from exc


@mcp.tool(
    annotations={"title": "BDBE 数据详情", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    meta={"piflow": {"displayName": "BDBE 数据详情", "category": "BDBE 数据访问", "icon": "database", "view_type": "data", "riskLevel": "low", "version": "1.0.0", "tags": ["bdbe", "metadata", "detail"]}},
)
async def get_bdbe_metadata_detail(
    db: Annotated[str, Field(min_length=1, max_length=200, description="数据库标识")],
    sdi: Annotated[str, Field(min_length=1, max_length=500, description="数据集唯一标识")],
    fmt: Annotated[str | None, Field(max_length=100, description="可选返回格式")] = None,
    itype: Annotated[str | None, Field(max_length=100, description="可选数据项类型")] = None,
    sessionid: Annotated[str | None, Field(max_length=500, description="可选的上游会话 ID")] = None,
) -> Any:
    """根据数据库标识和数据集标识查询 BDBE 详细元数据。"""
    try:
        return await anyio.to_thread.run_sync(partial(get_metadata_detail, db=db, sdi=sdi, fmt=fmt, itype=itype, sessionid=sessionid))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except BdbeUpstreamError as exc:
        raise _upstream_tool_error(exc) from exc


@mcp.tool(
    annotations={"title": "BDBE GenBank 下载", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    meta={"piflow": {"displayName": "BDBE GenBank 下载", "category": "BDBE 数据下载", "icon": "download", "view_type": "file", "riskLevel": "low", "version": "1.0.0", "tags": ["bdbe", "genbank", "download"]}},
)
async def download_bdbe_genbank(
    dataids: Annotated[str, Field(min_length=1, max_length=10000, description="多个 Accession，使用英文逗号分隔")],
    sessionid: Annotated[str | None, Field(max_length=500, description="可选的上游会话 ID")] = None,
) -> dict[str, Any]:
    """下载 BDBE GBFF 文件并保存到当前项目 workspace 临时目录。"""
    target_dir = resolve_workspace_root() / "temp" / "bdbe_genbank"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path: Path | None = None
    try:
        with stream_genbank(dataids=dataids, sessionid=sessionid) as (response, chunks):
            filename = _safe_filename(response.headers.get("content-disposition"))
            target_path = target_dir / f"{uuid4().hex}_{filename}"
            with target_path.open("wb") as handle:
                for chunk in chunks:
                    if chunk:
                        handle.write(chunk)
        return {"status": "ready", "file_name": filename, "file_path": str(target_path), "media_type": response.headers.get("content-type", "application/octet-stream"), "size_bytes": target_path.stat().st_size, "dataids": [item.strip() for item in dataids.split(",") if item.strip()]}
    except (ValueError, OSError) as exc:
        if target_path is not None:
            target_path.unlink(missing_ok=True)
        raise ToolError(str(exc)) from exc
    except BdbeUpstreamError as exc:
        if target_path is not None:
            target_path.unlink(missing_ok=True)
        raise _upstream_tool_error(exc) from exc
