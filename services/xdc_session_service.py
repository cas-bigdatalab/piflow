"""Session-aware wrappers around the existing cross-DAG workflow.

This module owns persistence and frontend timeline projection only.  Planning,
replica binding, DAG nesting and execution are delegated unchanged to the
existing cross-DAG services.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncIterator, Callable

from repositories import xdc_session_repository as repository
from runtime.cross_dag.engine import plan_cross_dag_pre_bind
from runtime.cross_dag.plan_view import stage_brief
from runtime.cross_dag.schema import MODE_DIRECT, MODE_UNAVAILABLE
from runtime.cross_dag.session_codec import (
    PRE_BIND_SCHEMA_VERSION,
    decode_pre_bind_plan,
    encode_pre_bind_plan,
)
from services import cross_dag_service


class XdcSessionNotFound(LookupError):
    """The requested session does not belong to the current user."""


class XdcTaskNotFound(LookupError):
    """The requested task does not belong to the current user."""


class XdcSessionConflict(RuntimeError):
    """The requested session transition is incompatible with its state."""


def create_xdc_session(*, user_id: str, title: str = "") -> dict[str, Any]:
    normalized_title = " ".join(str(title or "").split())[:255]
    return repository.create_session(
        session_id=f"xdc-session-{uuid.uuid4().hex[:16]}",
        user_id=str(user_id),
        title=normalized_title,
    )


def list_xdc_sessions(
    *, user_id: str, page_num: int = 1, page_size: int = 20
) -> dict[str, Any]:
    return repository.list_sessions(
        user_id=str(user_id),
        page_num=max(1, int(page_num)),
        page_size=min(100, max(1, int(page_size))),
    )


def get_xdc_session_detail(
    *,
    session_id: str,
    user_id: str,
    after_item_id: int = 0,
    item_limit: int = 1000,
) -> dict[str, Any]:
    session = _require_session(session_id=session_id, user_id=user_id)
    tasks = repository.list_tasks(session_id=session_id, user_id=str(user_id))
    items = [
        _public_item(item)
        for item in repository.list_session_items(
            session_id=session_id,
            user_id=str(user_id),
            after_item_id=max(0, int(after_item_id)),
            limit=min(2000, max(1, int(item_limit))),
        )
    ]
    return {
        "session": session,
        "tasks": tasks,
        "items": items,
        "next_after_item_id": items[-1]["item_id"] if items else after_item_id,
    }


def delete_xdc_session(*, session_id: str, user_id: str) -> dict[str, Any]:
    _require_session(session_id=session_id, user_id=user_id)
    active = [
        task
        for task in repository.list_tasks(session_id=session_id, user_id=str(user_id))
        if str(task.get("status") or "").upper()
        in {"PROCESSING", "PLANNED", "EXECUTING"}
    ]
    if active:
        raise XdcSessionConflict(
            f"Session 中仍有未完成任务，暂不能删除: {active[0]['task_id']}"
        )
    if not repository.delete_session(session_id=session_id, user_id=str(user_id)):
        raise XdcSessionNotFound(f"Session 不存在或无权访问: {session_id}")
    return {"session_id": session_id, "deleted": True}


def get_xdc_task_detail(*, task_id: str, user_id: str) -> dict[str, Any]:
    task = _require_task(task_id=task_id, user_id=user_id)
    snapshots = {
        str(row["snapshot_type"]).lower(): row["payload_json"]
        for row in repository.list_public_snapshots(task_id=task_id)
    }
    all_items = repository.list_session_items(
        session_id=str(task["session_id"]),
        user_id=str(user_id),
        limit=2000,
    )
    return {
        "task": task,
        "items": [
            _public_item(item)
            for item in all_items
            if item.get("task_id") == task_id
        ],
        "snapshots": snapshots,
    }


async def stream_xdc_session_pre_bind(
    *,
    session_id: str,
    user_request: str,
    user_id: str,
    detail: bool = False,
    parent_task_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Create one task and stream intent through the pre-bind plan."""
    normalized_request = str(user_request or "").strip()
    if not normalized_request:
        yield {
            "type": "error",
            "code": "INVALID_REQUEST",
            "message": "user_request 不能为空",
        }
        return
    task_id = f"xdc-task-{uuid.uuid4().hex[:16]}"
    plan_id = f"xdc-{uuid.uuid4().hex[:12]}"
    events: list[dict[str, Any]] = []
    result: list[dict[str, Any]] = []
    errors: list[Exception] = []

    try:
        task = repository.create_task(
            task_id=task_id,
            session_id=session_id,
            user_id=str(user_id),
            user_request=normalized_request,
            task_name=_task_title(normalized_request),
            parent_task_id=(str(parent_task_id).strip() if parent_task_id else None),
        )
    except LookupError as exc:
        yield {"type": "error", "code": "SESSION_NOT_FOUND", "message": str(exc)}
        return
    except RuntimeError as exc:
        yield {"type": "error", "code": "SESSION_CONFLICT", "message": str(exc)}
        return

    revision = int(task.get("plan_revision") or 1)
    repository.save_session_item(
        item_key=f"{task_id}:user-request",
        session_id=session_id,
        task_id=task_id,
        role="user",
        item_type="USER_MESSAGE",
        item_status="finished",
        payload={"text": normalized_request},
    )
    yield {
        "type": "task",
        "status": "created",
        "session_id": session_id,
        "task_id": task_id,
        "plan_id": plan_id,
    }

    def collect(stage: str, payload: dict[str, Any]) -> None:
        event = _stage_event(stage, payload, detail=detail)
        events.append(event)
        _save_stream_event(
            event=event,
            session_id=session_id,
            task_id=task_id,
        )

    def run() -> None:
        try:
            pre_bind = plan_cross_dag_pre_bind(
                normalized_request,
                plan_id=plan_id,
                on_stage=collect,
            )
            view = cross_dag_service._summarize_pre_bind(pre_bind, detail=detail)
            view.update({"session_id": session_id, "task_id": task_id})
            view["next_action"] = {
                "method": "POST",
                "url": (
                    f"/api/piflow/v1/xdc/tasks/{task_id}"
                    "/bind-and-execute/stream"
                ),
                "body": {"detail": detail},
            }
            repository.save_snapshot(
                task_id=task_id,
                revision=revision,
                snapshot_type="PRE_BIND_INTERNAL",
                schema_version=PRE_BIND_SCHEMA_VERSION,
                payload=encode_pre_bind_plan(pre_bind),
            )
            repository.save_snapshot(
                task_id=task_id,
                revision=revision,
                snapshot_type="PRE_BIND_VIEW",
                payload=view,
            )
            terminal_unavailable = pre_bind.mode == MODE_UNAVAILABLE
            repository.save_session_item(
                item_key=f"{task_id}:plan-card",
                session_id=session_id,
                task_id=task_id,
                role="assistant",
                item_type="PLAN_CARD",
                item_status=("unavailable" if terminal_unavailable else "planned"),
                payload=view,
            )
            repository.update_task_state(
                task_id=task_id,
                status=("UNAVAILABLE" if terminal_unavailable else "PLANNED"),
                current_stage=("completed" if terminal_unavailable else "pre_bind"),
                mode=pre_bind.mode,
                plan_id=pre_bind.plan_id,
                error_message="",
                finished=terminal_unavailable,
            )
            result.append(view)
        except Exception as exc:  # persisted so refresh also shows the failure
            errors.append(exc)
            _mark_failed(
                task_id=task_id,
                session_id=session_id,
                stage="pre_bind",
                exc=exc,
            )

    async for event in _drain_worker(run, events):
        yield event
    if errors:
        yield {"type": "error", "code": "PLAN_FAILED", "message": str(errors[0])}
        return
    yield {"type": "done", "result": result[0]}


async def stream_xdc_task_bind_and_execute(
    *,
    task_id: str,
    user_id: str,
    detail: bool = False,
) -> AsyncIterator[dict[str, Any]]:
    """Resume a persisted pre-bind task and stream binding through submission."""
    try:
        task = _require_task(task_id=task_id, user_id=user_id)
    except XdcTaskNotFound as exc:
        yield {"type": "error", "code": "TASK_NOT_FOUND", "message": str(exc)}
        return

    if str(task.get("status") or "").upper() != "PLANNED":
        yield {
            "type": "error",
            "code": "TASK_STATE_CONFLICT",
            "message": f"任务状态不是 PLANNED，不能绑定执行: {task.get('status')}",
        }
        return

    revision = int(task.get("plan_revision") or 1)
    snapshot = repository.get_snapshot(
        task_id=task_id,
        revision=revision,
        snapshot_type="PRE_BIND_INTERNAL",
    )
    if snapshot is None:
        _mark_failed(
            task_id=task_id,
            session_id=str(task["session_id"]),
            stage="restore_pre_bind",
            exc=ValueError(f"任务缺少可恢复的预绑定方案: {task_id}"),
        )
        yield {
            "type": "error",
            "code": "PLAN_SNAPSHOT_NOT_FOUND",
            "message": f"任务缺少可恢复的预绑定方案: {task_id}",
        }
        return

    session_id = str(task["session_id"])
    try:
        pre_bind = decode_pre_bind_plan(dict(snapshot["payload_json"] or {}))
    except Exception as exc:
        _mark_failed(
            task_id=task_id,
            session_id=session_id,
            stage="restore_pre_bind",
            exc=exc,
        )
        yield {"type": "error", "code": "PLAN_SNAPSHOT_INVALID", "message": str(exc)}
        return

    claimed = repository.claim_task_for_execution(
        task_id=task_id,
        user_id=str(user_id),
    )
    if claimed is None:
        yield {
            "type": "error",
            "code": "TASK_STATE_CONFLICT",
            "message": "任务已被其他请求绑定执行，请勿重复提交",
        }
        return
    task = claimed
    yield {
        "type": "task",
        "status": "executing",
        "session_id": session_id,
        "task_id": task_id,
        "plan_id": pre_bind.plan_id,
    }

    events: list[dict[str, Any]] = []
    result: list[dict[str, Any]] = []
    errors: list[Exception] = []
    candidates_emitted = False

    def append(event: dict[str, Any]) -> None:
        events.append(event)
        _save_stream_event(
            event=event,
            session_id=session_id,
            task_id=task_id,
        )

    def collect(stage: str, payload: dict[str, Any]) -> None:
        nonlocal candidates_emitted
        stage_event = _stage_event(stage, payload, detail=detail)
        if (
            stage in {"bind", "access"}
            and payload.get("status") == "started"
            and not candidates_emitted
        ):
            append(stage_event)
            for event in cross_dag_service._replica_candidate_events(
                pre_bind, detail=detail
            ):
                append(event)
            candidates_emitted = True
            return
        if stage in {"bind", "access"} and payload.get("status") == "finished":
            for event in cross_dag_service._replica_selection_events(
                pre_bind,
                stage=stage,
                payload=payload,
                detail=detail,
            ):
                append(event)
        append(stage_event)

    def run() -> None:
        try:
            plan, execution = cross_dag_service._finalize_and_execute_pre_bind(
                pre_bind,
                user_id=str(user_id),
                on_stage=collect,
            )
            plan_view = cross_dag_service._summarize(plan, detail=detail)
            execution_view = dict(execution)
            process_id = str(execution_view.get("process_id") or "")
            if process_id:
                execution_view["process_status_url"] = execution_view.get(
                    "status_url",
                    f"/api/piflow/v1/xdc/execution/{process_id}/status",
                )
                execution_view["status_url"] = (
                    f"/api/piflow/v1/xdc/tasks/{task_id}/execution/status"
                )
            public = {
                "session_id": session_id,
                "task_id": task_id,
                "plan": plan_view,
                "execution": execution_view,
            }
            repository.save_snapshot(
                task_id=task_id,
                revision=revision,
                snapshot_type="BOUND_INTERNAL",
                payload=plan.to_json(),
            )
            repository.save_snapshot(
                task_id=task_id,
                revision=revision,
                snapshot_type="BOUND_VIEW",
                payload=plan_view,
            )
            repository.save_snapshot(
                task_id=task_id,
                revision=revision,
                snapshot_type="EXECUTION",
                payload=execution_view,
            )
            repository.save_session_item(
                item_key=f"{task_id}:execution",
                session_id=session_id,
                task_id=task_id,
                role="assistant",
                item_type="PROCESS",
                item_status=("completed" if plan.mode == MODE_DIRECT else "executing"),
                payload=execution_view,
            )
            if plan.mode == MODE_DIRECT:
                repository.save_snapshot(
                    task_id=task_id,
                    revision=revision,
                    snapshot_type="RESULT",
                    payload=execution_view,
                )
                repository.save_session_item(
                    item_key=f"{task_id}:result-card",
                    session_id=session_id,
                    task_id=task_id,
                    role="assistant",
                    item_type="RESULT_CARD",
                    item_status="completed",
                    payload=execution_view,
                )
                repository.update_task_state(
                    task_id=task_id,
                    status="COMPLETED",
                    current_stage="completed",
                    mode=plan.mode,
                    plan_id=plan.plan_id,
                    finished=True,
                )
            else:
                repository.update_task_state(
                    task_id=task_id,
                    status="EXECUTING",
                    current_stage="execution",
                    mode=plan.mode,
                    plan_id=plan.plan_id,
                    process_id=process_id,
                )
            result.append(public)
        except Exception as exc:
            errors.append(exc)
            _mark_failed(
                task_id=task_id,
                session_id=session_id,
                stage="bind_and_execute",
                exc=exc,
            )

    async for event in _drain_worker(run, events):
        yield event
    if errors:
        yield {"type": "error", "code": "EXECUTION_FAILED", "message": str(errors[0])}
        return
    yield {"type": "done", "result": result[0]}


def get_xdc_task_execution_status(
    *,
    task_id: str,
    user_id: str,
    result_node_id: str = "",
    result_output_name: str = "",
) -> dict[str, Any]:
    """Poll the existing executor and synchronize the task timeline."""
    task = _require_task(task_id=task_id, user_id=user_id)
    process_id = str(task.get("process_id") or "")
    if not process_id:
        if str(task.get("mode") or "") == MODE_DIRECT:
            snapshot = repository.get_snapshot(
                task_id=task_id,
                revision=int(task.get("plan_revision") or 1),
                snapshot_type="EXECUTION",
            )
            return {
                "session_id": task["session_id"],
                "task_id": task_id,
                **dict((snapshot or {}).get("payload_json") or {}),
            }
        raise XdcSessionConflict(f"任务尚未生成 process_id: {task_id}")

    status = cross_dag_service.get_cross_dag_execution_status(
        process_id=process_id,
        user_id=str(user_id),
        result_node_id=result_node_id,
        result_output_name=result_output_name,
    )
    remote_status = str(status.get("status") or "").upper()
    mapped = {
        "SUCCESS": "COMPLETED",
        "FAILED": "FAILED",
        "CANCELLED": "CANCELLED",
    }.get(remote_status, "EXECUTING")
    finished = mapped in {"COMPLETED", "FAILED", "CANCELLED"}
    repository.save_snapshot(
        task_id=task_id,
        revision=int(task.get("plan_revision") or 1),
        snapshot_type="EXECUTION",
        payload=status,
    )
    repository.save_session_item(
        item_key=f"{task_id}:execution",
        session_id=str(task["session_id"]),
        task_id=task_id,
        role="assistant",
        item_type="PROCESS",
        item_status=mapped.lower(),
        payload=status,
    )
    repository.update_task_state(
        task_id=task_id,
        status=mapped,
        current_stage=(
            "completed"
            if mapped == "COMPLETED"
            else mapped.lower()
            if mapped in {"FAILED", "CANCELLED"}
            else "execution"
        ),
        error_message=(
            str(status.get("message") or "") if mapped in {"FAILED", "CANCELLED"} else ""
        ),
        finished=finished,
    )
    result_file = status.get("result_file")
    if mapped == "COMPLETED" and isinstance(result_file, dict):
        repository.save_snapshot(
            task_id=task_id,
            revision=int(task.get("plan_revision") or 1),
            snapshot_type="RESULT",
            payload=result_file,
        )
        repository.save_session_item(
            item_key=f"{task_id}:result-card",
            session_id=str(task["session_id"]),
            task_id=task_id,
            role="assistant",
            item_type="RESULT_CARD",
            item_status="completed",
            payload=result_file,
        )
    return {"session_id": task["session_id"], "task_id": task_id, **status}


def _require_session(*, session_id: str, user_id: str) -> dict[str, Any]:
    session = repository.get_session(session_id=session_id, user_id=str(user_id))
    if session is None:
        raise XdcSessionNotFound(f"Session 不存在或无权访问: {session_id}")
    return session


def _require_task(*, task_id: str, user_id: str) -> dict[str, Any]:
    task = repository.get_task(task_id=task_id, user_id=str(user_id))
    if task is None:
        raise XdcTaskNotFound(f"任务不存在或无权访问: {task_id}")
    return task


def _task_title(user_request: str) -> str:
    normalized = " ".join(str(user_request or "").split())
    return normalized[:60] or "新建取数任务"


def _public_item(item: dict[str, Any]) -> dict[str, Any]:
    public = dict(item)
    payload = public.pop("payload_json", public.get("payload", {}))
    public["payload"] = payload
    return public


def _stage_event(
    stage: str,
    payload: dict[str, Any],
    *,
    detail: bool,
) -> dict[str, Any]:
    if detail:
        return {"type": "stage", "stage": stage, **payload}
    brief = stage_brief(stage, payload)
    if stage == "submit" and payload.get("status") == "finished":
        process_id = str(payload.get("process_id") or "")
        brief["summary"] = (
            f"任务已提交 · {process_id}"
            if process_id
            else "直接访问方案已确定，无需提交 DAG"
        )
    return {"type": "stage", **brief}


def _save_stream_event(
    *,
    event: dict[str, Any],
    session_id: str,
    task_id: str,
) -> None:
    event_type = str(event.get("type") or "")
    if event_type == "stage":
        stage = str(event.get("stage") or "unknown")
        repository.save_session_item(
            item_key=f"{task_id}:stage:{stage}",
            session_id=session_id,
            task_id=task_id,
            role="assistant",
            item_type="PROCESS_STEP",
            item_status=str(event.get("status") or ""),
            payload=event,
        )
    elif event_type == "replica":
        dataset_id = str(event.get("dataset_id") or "unknown")
        replica_status = str(event.get("status") or "unknown")
        repository.save_session_item(
            item_key=f"{task_id}:replica:{dataset_id}:{replica_status}",
            session_id=session_id,
            task_id=task_id,
            role="assistant",
            item_type="REPLICA",
            item_status=replica_status,
            payload=event,
        )


def _mark_failed(
    *, task_id: str, session_id: str, stage: str, exc: Exception
) -> None:
    message = str(exc)
    repository.update_task_state(
        task_id=task_id,
        status="FAILED",
        current_stage=stage,
        error_message=message,
        finished=True,
    )
    repository.save_session_item(
        item_key=f"{task_id}:error:{stage}",
        session_id=session_id,
        task_id=task_id,
        role="assistant",
        item_type="ERROR",
        item_status="failed",
        payload={"stage": stage, "message": message},
    )


async def _drain_worker(
    worker: Callable[[], None],
    events: list[dict[str, Any]],
) -> AsyncIterator[dict[str, Any]]:
    task = asyncio.get_running_loop().run_in_executor(None, worker)
    emitted = 0
    while not task.done() or emitted < len(events):
        while emitted < len(events):
            yield events[emitted]
            emitted += 1
        if task.done():
            break
        await asyncio.sleep(0.05)
    await task
    while emitted < len(events):
        yield events[emitted]
        emitted += 1
