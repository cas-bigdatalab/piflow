from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ScheduleJob:
    schedule_job_id: str
    schedule_name: str
    dag_task_id: str
    definition_id: str
    owner_id: str
    trigger_type: str
    status: str
    timezone: str = "Asia/Shanghai"
    cron_expression: str | None = None
    interval_seconds: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    misfire_policy: str = "FIRE_ONCE"
    max_running_instances: int = 1
    concurrency_policy: str = "SKIP_CURRENT"
    next_fire_time: datetime | None = None
    last_fire_time: datetime | None = None
    payload_json: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ScheduleRun:
    schedule_run_id: str
    schedule_job_id: str
    dag_task_id: str
    definition_id: str
    owner_id: str
    planned_fire_time: datetime
    status: str
    actual_fire_time: datetime | None = None
    process_id: str | None = None
    attempt: int = 0
    dispatch_owner: str | None = None
    dispatch_lease_until: datetime | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ScheduleLeaderLock:
    lock_name: str
    owner_id: str | None = None
    lease_until: datetime | None = None
    heartbeat_at: datetime | None = None
    updated_at: datetime | None = None
