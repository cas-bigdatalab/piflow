"""Corpus dataset tools exposed through the in-process MCP endpoint."""

from __future__ import annotations

from contextlib import nullcontext
from functools import partial
import logging
from typing import Annotated, Any, Literal

import anyio
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.tools.tool import ToolResult
from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel, ConfigDict, Field
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from scientific_agents.dataset_qa.artifact_storage import ArtifactStorageError, download_base_context, local_download

from services.corpus_connector_service import (
    get_dataset_detail_by_cstr,
    get_dataset_directory,
    get_dataset_sampler,
    get_file_schema,
    get_file_records,
    list_dataset_details,
    query_pubchem_records,
    export_record_file,
)


mcp = FastMCP(
    "piflow-corpus",
    version="1.0.0",
    instructions=(
        "检索和查看服务中当前可见的数据集。按请求目标选择工具：检索候选、数据集元信息、目录列表、"
        "JSON/JSONL 字段结构与样例、随机采样分别是不同能力。"
        "数据集 CSTR 未知时先检索；获得 CSTR 后直接执行用户需要的操作，无需固定经过详情查询。"
        "字段结构和样例记录使用两个独立的文件级工具；两项都需要时分别调用，可并行获取。"
        "未指定文件时先获取目录并定位实际文件，不把单个文件的结果当作整个数据集的内容。"
        "仅依据工具实际返回内容回答，不推测缺失字段、文件路径或读取范围。"
        "PubChem 化合物结构检索和通用结果导出属于独立能力组；不要将化合物检索当作数据集目录检索。"
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

_FILE_SCHEMA_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "get_corpus_file_schema",
            {{"download_url": "https://data.example.org/dataset_001/records.jsonl"}},
        )
        print(result)
'''

_FILE_PREVIEW_USAGE_EXAMPLE = f'''from fastmcp import Client

MCP_ENDPOINT = "{_MCP_ENDPOINT_EXAMPLE}"


async def main():
    async with Client(MCP_ENDPOINT) as client:
        result = await client.call_tool(
            "read_corpus_file_records",
            {{
                "download_url": "https://data.example.org/dataset_001/records.jsonl",
                "size": 5,
            }},
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
            "view_type": "detail",
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
    """检索数据集候选：用于找某一主题的数据集，或按已知名称定位数据集 CSTR。

    自然语言主题或领域相关检索优先使用 `query`，映射到上游 `keywords`。
    按具体名称定位时先保留用户提供的完整名称；已知 CSTR 时可直接调用所需的数据集工具。
    `field` / `subject` 只用于已从服务元数据确认的分类值；多个条件同时传入会收窄范围。
    空结果只表示当前条件未匹配，不代表用户需求不明确或整个相关领域没有数据。
    当前上游标题筛选不可用，非空 `title` 会返回错误，不会降级成无筛选列表。
    返回 items 候选记录和 pagination 分页信息；从记录获取真实 CSTR，不能把名称当作标识。
    总数是当前筛选条件下的服务统计。检索命中不代表文件正文、schema 或科研适用性已核实。
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
    cstr: Annotated[str, Field(description="用户明确提供或检索结果中的数据集 CSTR 原值；不是标题、文件名或目录 fileId")],
) -> dict[str, Any]:
    """查询数据集详情和元信息：简介、规模、格式、来源、作者等，以实际返回字段为准。

    输入真实 CSTR；不需要先查询目录。用于了解数据集概况、背景或元信息。
    返回数据集级说明，不返回文件列表、字段 schema 或样例记录；不要由元信息推断文件是否可读。
    用户明确要求目录、字段结构、记录预览或采样时，应直接选择对应能力。
    """
    return await anyio.to_thread.run_sync(partial(get_dataset_detail_by_cstr, cstr))


@mcp.tool(
    annotations={"title": "数据集随机采样", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    meta={"piflow": {"displayName": "数据集随机采样", "category": "数据集采样", "icon": "database-sample", "view_type": "url", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "sample"], "usageExample": _SAMPLE_USAGE_EXAMPLE}},
)
async def sample_corpus_dataset(
    cstr: Annotated[str, Field(description="待随机采样的数据集 CSTR 原值，来自用户或已确认的记录")],
    size: Annotated[int, Field(description="随机采样条数，默认为 5 条", ge=1)] = 5,
) -> dict[str, Any]:
    """按数据集 CSTR 随机采样指定条数，原样返回上游采样结果或结果地址。

    用于明确要求随机抽样或获取采样产物的请求；返回字段和实际数量以上游结果为准。
    此操作不保证重复调用得到相同样本。不要为查看 schema、字段说明或少量记录而重复随机采样。
    文件字段使用 schema 查询工具，内容示例使用文件记录读取工具；本工具不提供指定文件或按原始顺序取前 N 条的控制。
    """
    return _checked_result(await anyio.to_thread.run_sync(partial(get_dataset_sampler, cstr, size=size)))


@mcp.tool(
    annotations={
        "title": "查询文件字段结构",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "文件 Schema 查询",
            "category": "数据内容查看",
            "icon": "database-preview",
            "view_type": "data",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "file", "schema", "json"],
            "usageExample": _FILE_SCHEMA_USAGE_EXAMPLE,
        }
    },
)
async def get_corpus_file_schema(
    download_url: Annotated[str, Field(description="已定位文件的真实 downloadUrl 或用户明确提供的绝对 HTTP(S) URL，仅支持 .json/.jsonl；不能传文件名、fileId、相对路径，也不能拼接或猜测 URL")],
) -> dict[str, Any]:
    """查询指定 JSON/JSONL 文件的字段结构（schema）、字段类型和嵌套关系，不读取样例记录。

    输入目录提供的真实 downloadUrl，或用户明确给出的 HTTP(S) 文件 URL；只有文件名时先定位文件。
    可用于任意目录层级的已定位文件，不提供整个数据集的统一 schema。
    返回 downloadUrl、previewable、message、format、schema、warnings，schema 保持上游推断结果。
    按实际返回字段解释结构，不能补造缺失字段或宣称未提供的全量覆盖范围；schema 为空时不表示文件没有字段。
    用户只要字段结构时仅调用本工具；同时需要记录时另调用 read_corpus_file_records，两项可独立并行获取。
    """
    return await anyio.to_thread.run_sync(partial(get_file_schema, download_url))


@mcp.tool(
    annotations={
        "title": "读取文件样例记录",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    meta={
        "piflow": {
            "displayName": "文件 JSON 记录预览",
            "category": "数据内容查看",
            "icon": "database-preview",
            "view_type": "table",
            "riskLevel": "low",
            "version": "1.0.0",
            "tags": ["corpus", "file", "preview", "json"],
            "usageExample": _FILE_PREVIEW_USAGE_EXAMPLE,
        }
    },
)
async def read_corpus_file_records(
    download_url: Annotated[str, Field(description="已定位文件的真实 downloadUrl 或用户明确提供的绝对 HTTP(S) URL，仅支持 .json/.jsonl；不能传文件名、fileId、相对路径，也不能拼接或猜测 URL")],
    size: Annotated[int, Field(description="该文件的样例记录条数，默认 5，实际最多 20；仅为返回预算，不是分页偏移，也不保证严格按原始顺序取前 N 条", ge=1)] = 5,
) -> dict[str, Any]:
    """读取指定 JSON/JSONL 文件的有限条样例记录，用于内容预览，不查询字段 schema。

    输入目录节点提供的真实 downloadUrl，或用户明确给出的 HTTP(S) 文件 URL；只有文件名时先定位文件。
    可读取任意目录层级的已定位文件；不会读取整个数据集的记录。
    返回 downloadUrl、previewable、message、format、data、requestedSize、effectiveSize、returnedCount、truncated、warnings 等字段。
    按实际返回记录回答，不能把样例当作完整 schema、全量数据或全量统计；没有记录时不要编造数据。
    样例受条数和大小限制，工具没有 offset 或排序参数，不保证严格的前 N 条或完整统计；
    不可预览时如实说明内容可用范围，勿反复调用。仅要 schema 时使用 get_corpus_file_schema；两项都需要时分别调用。
    """
    return await anyio.to_thread.run_sync(
        partial(get_file_records, download_url, size=size)
    )


@mcp.tool(
    annotations={"title": "查看数据内容", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    meta={"piflow": {"displayName": "查看数据内容", "category": "数据内容查看", "icon": "database-directory", "view_type": "table", "riskLevel": "low", "version": "1.0.0", "tags": ["corpus", "dataset", "content"], "usageExample": _DIRECTORY_USAGE_EXAMPLE}},
)
async def get_corpus_dataset_directory(
    cstr: Annotated[str, Field(description="目录所属数据集的真实 CSTR，来自用户或检索/详情结果；不能用文件名或标题代替")],
    file_id: Annotated[str | None, Field(description="省略或传 null 获取根层；展开子目录须使用该数据集目录结果中 isFile=false 节点的 fileId 原值，不要自行填 root、路径或目录名")] = None,
) -> dict[str, Any]:
    """浏览数据集目录结构和文件列表，每次只返回指定目录的直接子节点。

    输入 CSTR；省略 file_id 或传 null 查看根层，传已有目录节点的 fileId 展开下一层。
    返回节点的 name、fileId、isFile、path、downloadUrl 等，以实际字段为准。
    isFile=false 是文件夹，可继续展开；isFile=true 是文件，可用实际 downloadUrl 调用文件级内容工具。
    不从目录名、文件名或 path 猜测 fileId/downloadUrl。一次返回不代表整棵目录树。
    此工具只提供文件组织结构，不读取字段 schema 或正文记录；字段结构使用文件 schema 工具，
    内容示例使用文件记录工具。用户要目录、文件列表或为具体文件定位时才用本工具。
    """
    return _checked_result(
        await anyio.to_thread.run_sync(partial(get_dataset_directory, cstr, file_id=file_id))
    )


def _file_capability(kind, group, source, operations, inputs, outputs, *, consume=None):
    label = "PubChem 化合物检索与筛选" if source == "PubChem" else "导出数据文件"
    return {"piflow": {"displayName": label, "category": "化合物发现" if source else "数据处理",
        "icon": "database-search" if source else "download", "riskLevel": "low", "version": "1.0.0",
        "tags": [group, *operations], "view_type": "url", "qa": {
        "label": label,
        "atomic": True, "object": "/resource",
        "bind": {consume: ["/source_ref"]} if consume else {},
        "routing": {"group": group, "source": source, "operations": operations, "inputs": inputs, "outputs": outputs},
        "artifact": {"path": "/resource", "consume": consume, "execution_context": True, "replay_safe": True},
        "result": {"kind": kind, "requires": [{"path": "/resource/source_ref"},
            {"path": "/record_count", "test": "at_least", "value": 1}],
            "unavailable_when": [{"path": "/resource", "test": "equals", "value": None}],
            "target_paths": ["/record_count"]}}}}


def _execution_context(ctx):
    request = ctx.request_context
    meta = request.meta.model_dump() if request and request.meta else {}
    return meta.get("piflow_execution", {})


def _artifact_download_context():
    # Use the ASGI origin/mount, including trusted proxy root_path. Do not parse
    # forwarding headers ourselves or share a request's address process-wide.
    try:
        request = get_http_request()
    except RuntimeError:
        # Keep the original QA HTTP adapter's public origin for in-process MCP.
        return nullcontext()
    base = request.url.replace(path=request.scope.get("root_path", ""), query="", fragment="")
    return download_base_context(str(base))


class _ToolFailure(ToolResult):
    """Preserve typed error metadata through FastMCP's result conversion."""
    def to_mcp_result(self):
        return CallToolResult(isError=True, content=self.content, _meta=self.meta)


def _artifact_error(error):
    phase = getattr(error, "phase", "storage")
    logging.getLogger("flow.corpus.artifacts").warning("Artifact storage unavailable: phase=%s", phase, exc_info=True)
    return _ToolFailure(
        content=[TextContent(type="text", text="本次结果文件尚未准备好，当前还不能提供下载。")],
        meta={"piflow": {"error_code": "artifact_unavailable", "phase": phase}})


class CompoundPropertyRange(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    field: Literal["MolecularWeight", "XLogP"]
    minimum: int | float | None = None
    maximum: int | float | None = None


@mcp.tool(annotations={"title": "PubChem 化合物检索与筛选", "readOnlyHint": False,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    meta=_file_capability("record_resource", "pubchem", "PubChem", ["similarity_search", "property_filter"],
        ["SMILES"], ["jsonl", "record_resource"]))
async def query_pubchem_compounds(
    ctx: Context,
    smiles: Annotated[str, Field(min_length=1, max_length=4000, description="用户提供的查询分子 SMILES，不改写结构")],
    similarity_threshold: Annotated[int, Field(ge=1, le=100, description="PubChem 二维 Tanimoto 相似度百分比下限，80 表示 80%；结果不提供每条相似度分数")]=80,
    filters: Annotated[list[CompoundPropertyRange] | None, Field(max_length=8, description="AND 数值范围条件；上下限至少一个，包含边界。XLogP 是计算值；缺失值不通过指定条件")]=None,
    limit: Annotated[int | None, Field(ge=1, le=20000, description="筛选后期望条数；不是最低交付条数。省略时处理本次候选直到完成或预算截止，不承诺全库穷尽")]=None,
) -> dict[str, Any]:
    """从 PubChem 按分子结构检索相似化合物并筛选属性，不检索数据集目录。

    工具内部批量获取属性、筛选、按 CID 去重并保存 JSONL；不是让模型逐条计算。
    返回 resource、record_count、target_count/target_met、statistics、coverage、stop_reason。
    任意数量的合格结果均可交付；不足目标不改条件重搜，截断不代表数据源穷尽。
    需要 CSV 时将 resource 引用交给 export_dataset；不要重跑检索或调用随机采样。
    文件写入有副作用，使用调用方签名的 _meta.piflow_execution 进行身份、期限和重放校验；不是模型参数。
    """
    try:
        rules = [value.model_dump(exclude_unset=True) for value in filters] if filters is not None else None
        with _artifact_download_context():
            return await anyio.to_thread.run_sync(partial(query_pubchem_records, smiles,
                similarity_threshold, rules, limit, execution=_execution_context(ctx)))
    except (ArtifactStorageError, OSError) as exc:
        return _artifact_error(exc)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except Exception as exc:
        raise ToolError("本次结果文件暂未准备完成，已有查询条件已保留") from exc


@mcp.tool(annotations={"title": "导出数据文件", "readOnlyHint": False,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
    meta=_file_capability("exported_file", "data_processing", "", ["export"],
        ["record_resource"], ["csv", "jsonl"], consume="source_ref"))
async def export_dataset(
    ctx: Context,
    source_ref: Annotated[str, Field(min_length=1, max_length=4000, description="本服务已生成 resource 中的 source_ref 原值；QA 可以用其产物对象绑定。不是 artifact_id、文件路径或自行构造的 URL")],
    format: Literal["csv", "jsonl"]="csv",
) -> dict[str, Any]:
    """将已取得的结构化记录资源导出为 CSV 或 JSONL；与原数据来源无关。

    本期接收本服务签发的资源引用，不接受任意文件路径或外部 URL，不执行额外检索/筛选。
    原文件保留，返回 resource、downloadUrl、record_count 和继承的筛选统计。
    同一源文件与格式复用已校验的导出，刷新下载地址不重新检索。需签名执行上下文，同查询工具。
    """
    try:
        with _artifact_download_context():
            return await anyio.to_thread.run_sync(partial(export_record_file, source_ref, format,
                execution=_execution_context(ctx)))
    except (ArtifactStorageError, OSError) as exc:
        return _artifact_error(exc)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except Exception as exc:
        raise ToolError("本次导出文件暂未准备完成，已取得的数据仍可继续使用") from exc


@mcp.custom_route("/artifacts/{token}/{name}", methods=["GET"], include_in_schema=False)
async def download_artifact(request: Request):
    """Download capability, separate from model tools and arbitrary file paths."""
    headers = {"Cache-Control": "private, no-store", "Referrer-Policy": "no-referrer",
               "X-Content-Type-Options": "nosniff"}
    try:
        path, name, fmt = await anyio.to_thread.run_sync(partial(local_download,
            request.path_params["token"], request.path_params["name"], 64 * 1024 * 1024))
        return FileResponse(path, filename=name, headers=headers,
            media_type="text/csv; charset=utf-8" if fmt == "csv" else "application/x-ndjson")
    except ArtifactStorageError:
        logging.getLogger("flow.corpus.artifacts").warning("Artifact download unavailable", exc_info=True)
        return JSONResponse({"message": "结果文件暂不可下载，您可以返回对话继续获取。"}, status_code=503, headers=headers)
    except FileNotFoundError:
        return JSONResponse({"message": "当前结果文件不可用，您可以返回对话重新获取。"}, status_code=404, headers=headers)
    except ValueError:
        return JSONResponse({"message": "下载链接已过期或无效，请返回对话获取新的链接。"}, status_code=403, headers=headers)


def create_mcp_app():
    """Create the Streamable HTTP ASGI app mounted by ``server.py``."""
    return mcp.http_app(path="/", transport="streamable-http")
