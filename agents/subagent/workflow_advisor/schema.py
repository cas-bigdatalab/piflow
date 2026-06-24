from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# =========================
# 请求入参
# =========================

class AdvisorChatRequest(BaseModel):
    user_id: str = Field(..., description="当前用户ID")
    advisor_session_id: str = Field(..., description="编排向导会话ID，用于thread_id")
    workflow_id: str = Field(..., description="当前工作流/任务ID")
    message: str = Field(..., description="用户本轮问题")
    canvas_dsl: Dict[str, Any] = Field(..., description="当前画板DSL JSON")
    selected_node_id: Optional[str] = Field(default=None, description="当前前端选中的节点ID，可选")


# =========================
# DSL 摘要结构
# =========================

class AdvisorNodeParam(BaseModel):
    param_name: str
    value_mode: Optional[str] = None           # manual / reference
    param_value: Optional[Any] = None
    ref_type: Optional[str] = None             # manual / reference
    binding_id: Optional[str] = None


class AdvisorNodeOutputParam(BaseModel):
    param_name: str
    param_type: Optional[str] = None


class AdvisorCanvasNode(BaseModel):
    node_id: str
    node_name: str
    node_type: Optional[str] = None
    role: Literal["source", "processor", "sink", "unknown"] = "unknown"

    # 由 DSL + skill_id 查询补齐
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    skill_name_zh: Optional[str] = None
    skill_description: Optional[str] = None
    skill_version: Optional[str] = None

    input_params: List[AdvisorNodeParam] = Field(default_factory=list)
    output_params: List[AdvisorNodeOutputParam] = Field(default_factory=list)


class AdvisorCanvasEdge(BaseModel):
    edge_id: str
    from_node_id: str
    to_node_id: str


class AdvisorCanvasBinding(BaseModel):
    binding_id: str
    from_node_id: str
    from_param_name: str
    to_node_id: str
    to_param_name: str


class AdvisorCanvasContext(BaseModel):
    workflow_id: Optional[str] = None
    task_name: Optional[str] = None
    task_description: Optional[str] = None

    selected_node_id: Optional[str] = None

    nodes: List[AdvisorCanvasNode] = Field(default_factory=list)
    edges: List[AdvisorCanvasEdge] = Field(default_factory=list)
    bindings: List[AdvisorCanvasBinding] = Field(default_factory=list)

    node_count: int = 0
    edge_count: int = 0
    binding_count: int = 0

    # 给模型更容易读的摘要
    summary_text: Optional[str] = None


# =========================
# 编排向导结构化输出
# =========================

class AdvisorSuggestion(BaseModel):
    title: str = Field(..., description="建议标题")
    detail: str = Field(..., description="建议详情")
    related_node_ids: List[str] = Field(default_factory=list, description="相关节点ID")
    related_skill_names: List[str] = Field(default_factory=list, description="涉及的skill名称")


class AdvisorIssue(BaseModel):
    title: str = Field(..., description="发现的问题标题")
    detail: str = Field(..., description="问题说明")
    severity: Literal["low", "medium", "high"] = "medium"
    related_node_ids: List[str] = Field(default_factory=list)


class AdvisorResponse(BaseModel):
    summary: str = Field(..., description="给用户的总体回答摘要")
    suggestions: List[AdvisorSuggestion] = Field(default_factory=list, description="建议列表")
    issues: List[AdvisorIssue] = Field(default_factory=list, description="问题列表")
    next_questions: List[str] = Field(default_factory=list, description="建议用户进一步补充的信息")