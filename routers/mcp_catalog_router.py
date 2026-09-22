"""REST catalog endpoints for presenting in-process MCP tools in the UI."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from mcp_servers.corpus_mcp import mcp


router = APIRouter()

_MCP_ENDPOINT = "/api/piflow/v1/mcp/"
_MCP_TRANSPORT = "streamable-http"


def _piflow_meta(tool: Any) -> dict[str, Any]:
    meta = tool.meta if isinstance(tool.meta, dict) else {}
    piflow = meta.get("piflow", {})
    return piflow if isinstance(piflow, dict) else {}


def _annotations(tool: Any) -> dict[str, Any]:
    return tool.annotations.model_dump(exclude_none=True) if tool.annotations else {}


def _tool_summary(tool: Any) -> dict[str, Any]:
    piflow = _piflow_meta(tool)
    parameters = tool.parameters if isinstance(tool.parameters, dict) else {}
    properties = parameters.get("properties", {})
    return {
        "name": tool.name,
        "displayName": piflow.get("displayName", tool.name),
        "description": tool.description or "",
        "category": piflow.get("category", "未分类"),
        "icon": piflow.get("icon"),
        "readOnly": _annotations(tool).get("readOnlyHint", False),
        "riskLevel": piflow.get("riskLevel", "unknown"),
        "version": piflow.get("version"),
        "tags": piflow.get("tags", []),
        "inputCount": len(properties) if isinstance(properties, dict) else 0,
        "status": "available",
        "serverName": mcp.name,
    }


def _server_summary(tool_count: int) -> dict[str, Any]:
    return {
        "name": mcp.name,
        "displayName": "PiFlow Corpus",
        "version": mcp.version,
        "transport": _MCP_TRANSPORT,
        "endpoint": _MCP_ENDPOINT,
        "status": "online",
        "instructions": mcp.instructions or "",
        "toolCount": tool_count,
    }


@router.get("/mcp/catalog")
async def get_mcp_catalog():
    """返回当前进程中已注册 MCP 工具的前端展示摘要。"""
    tools = await mcp.list_tools()
    server = _server_summary(len(tools))
    server["tools"] = [_tool_summary(tool) for tool in tools]
    return {
        "code": 200,
        "result": {
            "totalServers": 1,
            "totalTools": len(tools),
            "servers": [server],
        },
    }


@router.get("/mcp/tools/{tool_name}")
async def get_mcp_tool_detail(tool_name: str):
    """返回一个 MCP 工具的完整契约和 PiFlow 展示元数据。"""
    tools = await mcp.list_tools()
    tool = next((item for item in tools if item.name == tool_name), None)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"MCP tool not found: {tool_name}")

    return {
        "code": 200,
        "result": {
            "server": _server_summary(len(tools)),
            "tool": {
                **_tool_summary(tool),
                "inputSchema": tool.parameters,
                "outputSchema": tool.output_schema,
                "annotations": _annotations(tool),
                "meta": tool.meta or {},
                "usageExample": _piflow_meta(tool).get("usageExample", ""),
                "invocation": {
                    "method": "tools/call",
                    "endpoint": _MCP_ENDPOINT,
                },
            },
        },
    }
