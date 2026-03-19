# tools/base.py
from typing import Any, Dict, Optional, Type, Union, Callable
from pydantic import BaseModel, Field

class ToolSpec(BaseModel):
    """
    统一工具规格：无论是本地 Skill 还是远程 MCP，最终都实例化为此对象。
    """
    name: str = Field(..., description="工具唯一标识符，格式：namespace.tool_name")
    description: str = Field(..., description="工具功能描述，DeepAgent 规划时依赖此项")
    args_schema: Type[BaseModel] = Field(..., description="参数验证模型 (Pydantic Class)")
    namespace: str = Field("default", description="所属命名空间 (local/mcp/shell等)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据，如权限级别、成本等")

class ToolResult(BaseModel):
    """
    工具执行后的标准返回格式
    """
    success: bool
    output: Any = None
    error: Optional[str] = None
    trace_id: Optional[str] = None

# 定义一个 Callable 协议，所有工具实现类都应具备
class BaseToolFunction:
    async def __call__(self, **kwargs) -> Any:
        pass