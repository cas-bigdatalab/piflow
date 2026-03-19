import uuid
from pathlib import Path

from langchain_core.tools import StructuredTool

from tools.core.base import ToolSpec, ToolResult
from runtime.workspace_manager import WorkspaceManager


MAX_OUTPUT = 2000
LAST_TOOL_RESULT = None

# 允许访问的虚拟目录
ALLOWED_ROOTS = ["temp", "outputs", "artifacts", "logs"]


def truncate_output(text: str, max_len: int = MAX_OUTPUT):

    if not isinstance(text, str):
        return text

    if len(text) <= max_len:
        return text

    return text[:max_len] + "\n\n...[output truncated]..."


def inject_last_result(data):

    global LAST_TOOL_RESULT

    if LAST_TOOL_RESULT is None:
        return data

    if isinstance(data, dict):
        return {k: inject_last_result(v) for k, v in data.items()}

    if isinstance(data, list):
        return [inject_last_result(x) for x in data]

    if isinstance(data, str):

        if "{{last_tool_result}}" in data:
            return data.replace(
                "{{last_tool_result}}",
                str(LAST_TOOL_RESULT)
            )

    return data


# -----------------------------
# Workspace 路径解析
# -----------------------------
def resolve_workspace_paths(kwargs: dict):

    workspace = WorkspaceManager()
    root = Path(workspace.get_root())

    new_kwargs = {}

    for k, v in kwargs.items():

        if not isinstance(v, str):
            new_kwargs[k] = v
            continue

        if not v.startswith("/"):
            new_kwargs[k] = v
            continue

        rel = v.lstrip("/")
        root_dir = rel.split("/")[0]

        if root_dir in ALLOWED_ROOTS:

            mapped = root / rel
            new_kwargs[k] = str(mapped)

        else:
            new_kwargs[k] = v

    return new_kwargs


class DeepAgentsAdapter:
    """
    ToolSpec -> deepAgents / LangChain StructuredTool
    """

    @staticmethod
    def to_deepagents_tool(spec: ToolSpec, registry):

        async def _async_wrapper(**kwargs):

            global LAST_TOOL_RESULT

            trace_id = str(uuid.uuid4())

            try:

                # 注入上一个 tool 的结果
                kwargs = inject_last_result(kwargs)

                # 解析 workspace 路径
                kwargs = resolve_workspace_paths(kwargs)

                internal = spec.name

                result = await registry.call_internal(
                    internal,
                    kwargs
                )

                if isinstance(result, ToolResult):

                    if result.trace_id is None:
                        result.trace_id = trace_id

                    if result.success:

                        output = result.output
                        LAST_TOOL_RESULT = output

                        return truncate_output(output)

                    return f"Tool Error: {result.error}"

                LAST_TOOL_RESULT = result

                return truncate_output(result)

            except Exception as e:

                return f"Execution Error: {str(e)}"

        tool_name = spec.name.replace(".", "__")

        return StructuredTool.from_function(
            name=tool_name,
            description=spec.description,
            args_schema=spec.args_schema,
            coroutine=_async_wrapper,
        )