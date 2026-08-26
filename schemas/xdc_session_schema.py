"""Request models for the additive XDC session APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class XdcSessionCreateRequest(BaseModel):
    title: str = Field(default="", max_length=255, description="会话标题，可留空")


class XdcSessionPreBindRequest(BaseModel):
    user_request: str = Field(min_length=1, description="用户自然语言取数需求")
    detail: bool = Field(default=False, description="是否在 SSE 中附带排障详情")
    parent_task_id: str | None = Field(
        default=None,
        max_length=64,
        description="可选：本次任务依赖的上一任务 ID",
    )


class XdcTaskBindExecuteRequest(BaseModel):
    detail: bool = Field(default=False, description="是否在 SSE 中附带排障详情")
    selected_dataset_id: str | None = Field(
        default=None,
        max_length=128,
        description="Direct 模式必填：用户从绑定前候选中选择的数据集 ID",
    )
