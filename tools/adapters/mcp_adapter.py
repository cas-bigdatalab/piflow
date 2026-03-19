from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model

from tools.core.base import ToolSpec


class MCPAdapter:

    @staticmethod
    def _build_args_model(
        tool_name: str,
        schema: Optional[Dict[str, Any]]
    ) -> Type[BaseModel]:

        if not isinstance(schema, dict):
            schema = {}

        props = schema.get("properties", {}) or {}
        required = set(schema.get("required", []) or [])

        fields: Dict[str, Any] = {}

        for key, prop in props.items():

            if not isinstance(prop, dict):
                prop = {}

            desc = prop.get("description", "")

            if key in required:
                fields[key] = (
                    Any,
                    Field(..., description=desc),
                )
            else:
                fields[key] = (
                    Optional[Any],
                    Field(default=None, description=desc),
                )

        model_name = f"MCPArgs_{tool_name.replace('.', '_')}"

        return create_model(model_name, **fields)  # type: ignore[arg-type]

    @staticmethod
    def to_toolspec_and_func(server: str, client, tool):

        input_schema = (
            getattr(tool, "inputSchema", None)
            or getattr(tool, "input_schema", None)
            or {}
        )

        # tool name 加 server namespace
        tool_name = f"{server}.{tool.name}"

        args_model = MCPAdapter._build_args_model(
            tool_name,
            input_schema
        )

        async def executor(**kwargs):

            try:

                result = await client.call_tool(
                    tool.name,
                    kwargs
                )

                return result

            except Exception as e:

                raise RuntimeError(
                    f"MCP tool call failed: {tool_name} -> {e}"
                ) from e

        spec = ToolSpec(
            name=tool_name,
            description=tool.description or "",
            args_schema=args_model,
            namespace="mcp",
            metadata={
                "mcp_tool": True,
                "server": server,
                "tool": tool.name,
                "input_schema": input_schema,
            },
        )

        return spec, executor