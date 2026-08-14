# runtime/workflow_advisor/advisor_api.py

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse

from runtime.engine import AgentEngine
from agents.subagent.workflow_advisor.schema import AdvisorChatRequest
from runtime.skill_manage import get_generating_skill_by_thread_id
from security.auth_dependency import get_current_user
from services.dag_panel_service import get_dag_skills_by_condition

router = APIRouter(prefix="/workflow-advisor", tags=["workflow-advisor"])


def _encode_sse(data: dict, event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
    lines.append("")
    return "\n".join(lines) + "\n"


def get_engine(request: Request) -> AgentEngine:
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="agent engine is not initialized")
    return engine


def get_workflow_advisor_service(request: Request):
    engine = get_engine(request)
    service = getattr(engine, "workflow_advisor_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="workflow advisor service is not initialized")
    return service


@router.post("/chat/stream")
async def workflow_advisor_chat_stream(req: AdvisorChatRequest, request: Request):
    service = get_workflow_advisor_service(request)
    request_id = uuid.uuid4().hex[:8]

    async def event_generator():
        try:
            async for event in service.stream_chat(req, request_id=request_id):
                yield _encode_sse(event, event.get("type"))
        except Exception as exc:
            yield _encode_sse(
                {
                    "type": "error",
                    "request_id": request_id,
                    "message": str(exc),
                },
                "error",
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/generating_skill")
async def get_generating_skill(thread_id: str, request: Request, current_user=Depends(get_current_user)):
    try:
        row = get_generating_skill_by_thread_id(thread_id)
        if row is None:
            return {"message": "skill not found", "result": None, "code": 404}

        result = dict(row)

        skill_id = None
        if result.get("skill_name"):
            search = get_dag_skills_by_condition(keyword=result["skill_name"])
            skill_id = _latest_skill_id_by_name(search, result["skill_name"])
        result["skill_id"] = skill_id

        return {"message": "success", "result": result, "code": 200}
    except Exception as e:
        return {"message": str(e), "result": None, "code": 500}


def _version_key(version: str):
    parts = []
    for part in str(version or "").split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return parts


def _latest_skill_id_by_name(search: dict, skill_name: str):
    groups = search.get("data") if search else None
    if not groups:
        return None

    matches = []
    for group in groups:
        for skill in group.get("DagSkillInfoList", []):
            if getattr(skill, "skill_name", None) == skill_name:
                matches.append(skill)

    if not matches:
        return None

    latest = max(matches, key=lambda s: _version_key(getattr(s, "version", "")))
    return getattr(latest, "skill_id", None)