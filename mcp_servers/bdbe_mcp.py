"""BDBE tools using shared QA capability and file delivery contracts."""
from __future__ import annotations

from functools import partial
from typing import Annotated, Any

import anyio
from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from services.bdbe_service import (BdbeUpstreamError, download_genbank_file,
    get_metadata_detail, metadata_detail, metadata_page, query_metadata)
from scientific_agents.dataset_qa.artifact_storage import ArtifactStorageError
from mcp_servers.corpus_mcp import mcp, _artifact_download_context, _artifact_error, _execution_context


def _metadata(title, operation, view, **contract):
    return {"piflow": {"displayName": title, "category": "BDBE", "icon": "database",
        "view_type": view, "riskLevel": "low", "version": "1.1.0", "tags": ["bdbe", operation],
        "qa": {"label": title, "routing": {"group": "bdbe", "source": "BDBE",
            "operations": [operation], "inputs": [], "outputs": []}, **contract}}}


def _upstream_tool_error(exc):
    if exc.status_code == 401:
        return ToolError("BDBE 认证失败，请检查服务端 AccessKey 配置")
    if exc.status_code == 403:
        return ToolError("BDBE 接口权限不足")
    if exc.status_code == 422:
        return ToolError("BDBE 请求参数校验失败")
    # Preserve the sanitized upstream status/detail from the service layer.
    # Without this, HTTP 500 diagnostics are reduced to an unhelpful generic
    # message and the actual BDBE failure cannot be fixed from the client.
    return ToolError(str(exc))


_SOURCE = [{"path": "/source", "test": "equals", "value": "BDBE"}]


@mcp.tool(
    annotations={"title": "BDBE 数据检索", "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": True},
    meta=_metadata("BDBE 数据检索", "search", "table", collection="/items", name_paths=["/title"],
        search={"query": "term", "page": "page", "page_size": "pagesize", "total": "/pagination/total",
            "identity": ["/source", "/db", "/id"], "identity_mode": "composite"},
        result={"kind": "metadata_candidates", "requires": [{"path": "/items"}]}),
)
async def search_bdbe_metadata(
    term: Annotated[str, Field(min_length=1, max_length=500, description="在 BDBE 上查找生物信息元数据的关键词；先保留用户原词")],
    db: Annotated[str | None, Field(max_length=200, description="上游实际数据库标识；未知时省略，不猜数据库代码")] = None,
    page: Annotated[int, Field(ge=1, description="页码，从 1 开始")] = 1,
    pagesize: Annotated[int, Field(ge=1, le=1000, description="每页数量，默认 5；按需分页，避免一次获取大量长文本")] = 5,
    genome_next: Annotated[str | None, Field(alias="genomeNext", max_length=200, description="上游明确提供的 Genome 聚合分页参数；通常省略，不自行生成")] = None,
    language: Annotated[str, Field(max_length=20, description="BDBE 返回语言，默认 ch")] = "ch",
    userid: Annotated[str, Field(max_length=100, description="BDBE 用户标识，默认 1")] = "1",
    sessionid: Annotated[str | None, Field(max_length=500, description="上游明确提供的会话标识；通常省略，不使用 QA 会话 ID 代替")] = None,
) -> dict[str, Any]:
    """在 BDBE 检索元数据候选，返回 items 和 pagination，不读取实体文件。

    items 保留 source、db、sdi、id、title、description、raw；存在真实 Accession 时才有 accessions。
    BDBE 记录可能是项目、序列或其他元数据，不一定是可下载数据集。total=null 表示总量未知。
    详情使用记录的 db 与 sdi；GenBank 下载使用真实 accessions，不能用 UID/SDI/CSTR 替代。
    本工具不执行分子结构相似度计算、性质区间筛选或文件格式导出。
    """
    def run():
        raw = query_metadata(term=term, db=db, page=page, pagesize=pagesize, genome_next=genome_next, language=language, userid=userid, sessionid=sessionid)
        return metadata_page(raw, db=db, page=page, pagesize=pagesize)
    try:
        return await anyio.to_thread.run_sync(run)
    except BdbeUpstreamError as exc:
        raise _upstream_tool_error(exc) from exc
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(
    annotations={"title": "BDBE 数据详情", "readOnlyHint": True, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": True},
    meta=_metadata("BDBE 数据详情", "detail", "detail", atomic=True, object="/item", name_paths=["/title"],
        bind={"db": ["/db"], "sdi": ["/sdi"]}, identity_paths=["/source", "/db"], input_checks=_SOURCE,
        result={"kind": "metadata_detail", "requires": [{"path": "/item"}],
            "unavailable_when": [{"path": "/item", "test": "equals", "value": None}],
            "argument_paths": {"db": "/item/db", "sdi": "/item/sdi"}}),
)
async def get_bdbe_metadata_detail(
    db: Annotated[str, Field(min_length=1, max_length=200, description="用户明确提供或已选 BDBE 记录中的 db 原值")],
    sdi: Annotated[str, Field(min_length=1, max_length=500, description="已选 BDBE 记录中的 sdi/SDI；不是 UID、CSTR 或 Accession")],
    fmt: Annotated[str | None, Field(max_length=100, description="上游支持的详情表示格式；通常省略，不是下载文件的导出格式")] = None,
    itype: Annotated[str | None, Field(max_length=100, description="上游明确支持的数据项类型；通常省略")] = None,
    sessionid: Annotated[str | None, Field(max_length=500, description="上游明确提供的会话标识；通常省略")] = None,
) -> dict[str, Any]:
    """读取已定位 BDBE 记录的详细元数据，返回 status 与 item。

    已有 db 和 sdi 时直接查询，不重复检索。item 保留真实标识、标题和完整 raw 元数据。
    item=null 表示本次没有取得详情，不代表检索候选不存在。详情不是文件正文或目录。
    """
    def run():
        raw = get_metadata_detail(db=db, sdi=sdi, fmt=fmt, itype=itype, sessionid=sessionid)
        return metadata_detail(raw, db=db, sdi=sdi)
    try:
        return await anyio.to_thread.run_sync(run)
    except BdbeUpstreamError as exc:
        raise _upstream_tool_error(exc) from exc
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(
    annotations={"title": "BDBE GenBank 下载", "readOnlyHint": False, "destructiveHint": False,
        "idempotentHint": True, "openWorldHint": True},
    meta=_metadata("BDBE GenBank 下载", "download", "url", atomic=True, object="/resource", name_paths=["/name"],
        bind={"dataids": ["/accessions"]}, input_checks=_SOURCE,
        artifact={"path": "/resource", "kind": "file", "execution_context": True, "replay_safe": True},
        result={"kind": "file_artifact", "requires": [{"path": "/resource/source_ref"},
            {"path": "/downloadUrl"}, {"path": "/resource/format", "test": "equals", "value": "gbff"},
            {"path": "/resource/size_bytes", "test": "at_least", "value": 1}]}),
)
async def download_bdbe_genbank(
    dataids: Annotated[
        Annotated[str, Field(min_length=1, max_length=10000)] |
        Annotated[list[Annotated[str, Field(min_length=1, max_length=500)]], Field(min_length=1, max_length=1000)],
        Field(description="真实核酸序列 Accession，优先传字符串列表，也兼容英文逗号分隔；来自用户或 BDBE 记录 accessions，不用项目号/SDI/UID 代替")],
    sessionid: Annotated[str | None, Field(max_length=500, description="上游明确提供的会话标识；通常省略")] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """下载指定 Accession 的 GBFF 文件，返回 resource 和可直接访问的 downloadUrl。

    仅用于核酸序列 GenBank 下载，不是通用元数据导出或任意数据集下载。
    文件由服务端保存与校验，模型不处理文件内容或拼接地址。相同执行请求复用已完成文件。
    resource.kind=file；record_count 为实际完成的 GBFF 记录数，不以请求编号数量冒充。
    """
    try:
        with _artifact_download_context():
            return await anyio.to_thread.run_sync(partial(download_genbank_file, dataids, sessionid,
                execution=_execution_context(ctx)))
    except BdbeUpstreamError as exc:
        raise _upstream_tool_error(exc) from exc
    except (ArtifactStorageError, OSError) as exc:
        return _artifact_error(exc)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
