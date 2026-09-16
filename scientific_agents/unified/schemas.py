"""Small public contract and projections shared by the adapters."""
from typing import AsyncGenerator, Protocol
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

PREFIX = "/api/piflow/v1/agents"


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSession(Input):
    agent_id: str = "cross_dag"
    title: str = Field(default="", max_length=255)
    request_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1, max_length=160)


class Turn(Input):
    user_request: str = Field(min_length=1)
    request_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1, max_length=160)
    parent_task_id: str | None = None
    attachments: list[str] = Field(default_factory=list)
    detail: bool | None = None
    params: dict = Field(default_factory=dict)


class ChatTurn(Turn):
    """Chat-style request; reuse the same internal turn without business branching."""
    user_request: str = Field(alias="message", min_length=1)


class Action(Input):
    action: str = "execute"
    detail: bool | None = None
    selected_dataset_id: str | None = None
    request_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1, max_length=160)
    params: dict = Field(default_factory=dict)


class Adapter(Protocol):
    """Request-scoped adapters reuse host resources. Optional methods are capability-gated."""
    agent_id: str
    label: str
    capabilities: tuple[str, ...]
    def owns_session(self, session_id: str) -> bool: ...
    def task_session(self, task_id: str) -> str | None: ...
    async def create_session(self, body: CreateSession) -> dict: ...
    async def list_sessions(self, page: int, size: int) -> dict: ...
    async def get_session(self, sid: str, after: int, limit: int) -> dict: ...
    async def delete_session(self, sid: str) -> dict: ...
    def stream_turn(self, sid: str, body: Turn) -> AsyncGenerator[dict | None, None]: ...
    async def get_task(self, sid: str, tid: str) -> dict: ...
    async def detail(self, sid: str, tid: str) -> dict: ...
    async def execution_status(self, sid: str, tid: str, query: dict) -> dict: ...
    def stream_action(self, sid: str, tid: str, body: Action) -> AsyncGenerator[dict | None, None]: ...
    async def get_results(self, sid: str, tid: str) -> dict: ...
    async def download_file(self, sid: str, tid: str, fid: str): ...


def segment(value: str) -> str:
    if not value or value in {".", ".."} or any(c in value for c in "/\\?#%") or any(ord(c) < 32 for c in value):
        raise HTTPException(422, "资源编号不合法")
    return value


def params(values, allowed):
    unknown = set(values) - set(allowed)
    if unknown:
        raise HTTPException(422, "不支持的参数：" + ", ".join(sorted(unknown)))
    return values


def options(body, allowed):
    values = dict(body.params)
    for key in ("detail", "selected_dataset_id"):
        value = getattr(body, key, None)
        if value is not None:
            if key in values and values[key] != value:
                raise HTTPException(422, f"参数 {key} 重复且不一致")
            values[key] = value
    return params(values, allowed)


def status(value):
    value = str(value or "unknown").lower()
    return {"processing": "running", "executing": "running", "submitted": "queued",
            "pending": "queued", "planned": "waiting_confirmation", "success": "completed",
            "finished": "completed", "selected": "completed", "started": "running", "evaluating": "running",
            "unavailable": "failed", "error": "failed"}.get(value, value)


def session_view(data, agent_id):
    return {**data, "agent_id": agent_id,
            "create_time": data.get("create_time", data.get("created_at")),
            "update_time": data.get("update_time", data.get("updated_at"))}


def available(action, label):
    return {"action": action, "label": label, "enabled": True}


def task_view(tid, state, *, stage=None, outputs=None, actions=None, data=None):
    return {**(data or {}), "task_id": tid, "status": str(state or "UNKNOWN").upper(), "current_stage": stage,
            "needs_poll": status(state) in {"queued", "running", "cancelling"} or
                any(o["status"] in {"pending", "queued", "running"} for o in outputs or []),
            "outputs": outputs or [], "available_actions": actions or []}


def result_view(tid, kind, title, data, *, state="ready", artifacts=None, actions=None, key=None):
    return {"result_id": f"{tid}:{key or kind}", "task_id": tid, "view_type": kind, "title": title,
            "status": state, "data": data, "artifacts": artifacts or [], "available_actions": actions or []}


def file_view(fid, name, url):
    # Cross DAG file fields are canonical; keep the early unified aliases additive.
    return {"file_id": fid, "file_name": name, "download_url": url, "name": name, "url": url}


def event(kind, data, tid=None):
    return {**data, "type": kind, "task_id": tid}


def item(identifier, kind, payload, tid=None, state="completed", *, role="assistant", created=None):
    return {"item_id": identifier, "task_id": tid, "item_type": kind, "item_status": state,
            "role": role, "create_time": created, "payload": payload}
