# runtime/workflow_advisor/advisor_api.py

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from runtime.engine import AgentEngine
from agents.subagent.workflow_advisor.schema import AdvisorChatRequest

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