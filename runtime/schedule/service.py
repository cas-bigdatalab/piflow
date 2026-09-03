from __future__ import annotations

from datetime import datetime
from typing import Any

from database.postgres import get_connection
from runtime.dag_manager import get_dag_task
from runtime.schedule.constants import (
    ConcurrencyPolicy,
    MisfirePolicy,
    ScheduleStatus,
    TriggerType,
)
from runtime.schedule.repository import (
    create_job,
    delete_job,
    get_job,
    list_jobs,
    pause_job,
    start_job,
    stop_job,
    update_job,
)


def _require_user(user_id: str) -> str:
    if not user_id or not user_id.strip():
        raise ValueError("user_id is required")
    return user_id


def _require_text(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def _validate_definition_binding(
    *,
    dag_task_id: str,
    definition_id: str,
    owner_id: str,
) -> None:
    task = get_dag_task(dag_task_id)
    if task is None or task.create_user_id != owner_id:
        raise ValueError(f"dag task not found or not owned by user: {dag_task_id}")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM dag_definition
                WHERE definition_id = %s
                  AND dag_task_id = %s
                  AND create_user_id = %s
                """,
                (definition_id, dag_task_id, owner_id),
            )
            if cursor.fetchone() is None:
                raise ValueError(
                    "definition not found, not owned by user, "
                    "or does not belong to dag task"
                )


def create_schedule_job(
    *,
    owner_id: str,
    schedule_name: str,
    dag_task_id: str,
    definition_id: str,
    trigger_type: str,
    timezone: str = "Asia/Shanghai",
    cron_expression: str | None = None,
    interval_seconds: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    misfire_policy: str = MisfirePolicy.FIRE_ONCE,
    max_running_instances: int = 1,
    concurrency_policy: str = ConcurrencyPolicy.SKIP_CURRENT,
    payload_json: dict[str, Any] | None = None,
):
    owner_id = _require_user(owner_id)
    schedule_name = _require_text(schedule_name, "schedule_name")
    dag_task_id = _require_text(dag_task_id, "dag_task_id")
    definition_id = _require_text(definition_id, "definition_id")

    if trigger_type not in TriggerType.ALL:
        raise ValueError(f"unsupported trigger_type: {trigger_type}")
    if misfire_policy not in MisfirePolicy.ALL:
        raise ValueError(f"unsupported misfire policy: {misfire_policy}")
    if concurrency_policy not in ConcurrencyPolicy.ALL:
        raise ValueError(f"unsupported concurrency policy: {concurrency_policy}")
    if max_running_instances <= 0:
        raise ValueError("max_running_instances must be > 0")

    _validate_definition_binding(
        dag_task_id=dag_task_id,
        definition_id=definition_id,
        owner_id=owner_id,
    )

    # Jobs are created inactive. start_job() is the only lifecycle operation
    # that initializes next_fire_time.
    return create_job(
        schedule_name=schedule_name,
        dag_task_id=dag_task_id,
        definition_id=definition_id,
        owner_id=owner_id,
        trigger_type=trigger_type,
        status=ScheduleStatus.DRAFT,
        timezone=timezone,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
        start_time=start_time,
        end_time=end_time,
        misfire_policy=misfire_policy,
        max_running_instances=max_running_instances,
        concurrency_policy=concurrency_policy,
        payload_json=payload_json,
    )


def update_schedule_job(
    schedule_job_id: str,
    *,
    owner_id: str,
    schedule_name: str | None = None,
    cron_expression: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    timezone: str | None = None,
    misfire_policy: str | None = None,
    max_running_instances: int | None = None,
    concurrency_policy: str | None = None,
    payload_json: dict[str, Any] | None = None,
):
    owner_id = _require_user(owner_id)
    _require_text(schedule_job_id, "schedule_job_id")
    if schedule_name is not None:
        _require_text(schedule_name, "schedule_name")
    return update_job(
        schedule_job_id,
        owner_id=owner_id,
        schedule_name=schedule_name,
        cron_expression=cron_expression,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        misfire_policy=misfire_policy,
        max_running_instances=max_running_instances,
        concurrency_policy=concurrency_policy,
        payload_json=payload_json,
    )


def start_schedule_job(*, schedule_job_id: str, owner_id: str):
    return start_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def pause_schedule_job(*, schedule_job_id: str, owner_id: str):
    return pause_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def stop_schedule_job(*, schedule_job_id: str, owner_id: str):
    return stop_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def delete_schedule_job(*, schedule_job_id: str, owner_id: str):
    return delete_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def get_schedule_job(*, schedule_job_id: str, owner_id: str):
    return get_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def list_schedule_jobs(
    *,
    owner_id: str,
    status: str | None = None,
    dag_task_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    owner_id = _require_user(owner_id)
    return list_jobs(
        owner_id=owner_id,
        status=status,
        dag_task_id=dag_task_id,
        page=page,
        page_size=page_size,
    )
