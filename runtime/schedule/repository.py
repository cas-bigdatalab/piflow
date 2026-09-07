from __future__ import annotations

import uuid
from contextlib import closing

from psycopg2.extras import RealDictCursor, Json

from database.postgres import get_connection
from runtime.schedule.constants import (
    ConcurrencyPolicy,
    MisfirePolicy,
    ScheduleRunStatus,
    ScheduleStatus,
    TriggerType,
)
from runtime.schedule.expression import (
    ScheduleExpression,
    compute_first_fire_time,
    compute_next_fire_time,
)
from runtime.schedule.models import ScheduleJob, ScheduleRun


SCHEDULE_DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schedule_job (
        id BIGSERIAL PRIMARY KEY,
        schedule_job_id VARCHAR(128) NOT NULL,
        schedule_name VARCHAR(255) NOT NULL,
        dag_task_id VARCHAR(128) NOT NULL,
        definition_id VARCHAR(128) NOT NULL,
        owner_id VARCHAR(128) NOT NULL,
        trigger_type VARCHAR(32) NOT NULL,
        cron_expression VARCHAR(255),
        interval_seconds INTEGER,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ,
        timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai',
        misfire_policy VARCHAR(32) NOT NULL DEFAULT 'FIRE_ONCE',
        max_running_instances INTEGER NOT NULL DEFAULT 1,
        concurrency_policy VARCHAR(32) NOT NULL DEFAULT 'SKIP_CURRENT',
        status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
        next_fire_time TIMESTAMPTZ,
        last_fire_time TIMESTAMPTZ,
        payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uk_schedule_job_id UNIQUE (schedule_job_id),
        CONSTRAINT ck_schedule_job_trigger_type
            CHECK (trigger_type IN ('ONCE', 'CRON', 'INTERVAL')),
        CONSTRAINT ck_schedule_job_status
            CHECK (status IN ('DRAFT', 'STARTED', 'PAUSED', 'STOPPED', 'EXPIRED', 'DELETED')),
        CONSTRAINT ck_schedule_job_misfire_policy
            CHECK (misfire_policy IN ('SKIP', 'FIRE_ONCE', 'CATCH_UP')),
        CONSTRAINT ck_schedule_job_concurrency_policy
            CHECK (concurrency_policy IN ('SKIP_CURRENT', 'QUEUE_CURRENT', 'FAIL_CURRENT')),
        CONSTRAINT ck_schedule_job_max_running_instances
            CHECK (max_running_instances > 0),
        CONSTRAINT ck_schedule_job_interval_seconds
            CHECK (interval_seconds IS NULL OR interval_seconds > 0),
        CONSTRAINT ck_schedule_job_time_range
            CHECK (end_time IS NULL OR start_time IS NULL OR end_time > start_time),
        CONSTRAINT ck_schedule_job_trigger_config
            CHECK (
                (trigger_type = 'ONCE' AND cron_expression IS NULL AND interval_seconds IS NULL)
                OR
                (trigger_type = 'CRON' AND cron_expression IS NOT NULL AND interval_seconds IS NULL)
                OR
                (trigger_type = 'INTERVAL' AND cron_expression IS NULL AND interval_seconds IS NOT NULL)
            )
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_schedule_job_due ON schedule_job(status, next_fire_time)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_job_owner_status ON schedule_job(owner_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_job_dag_task ON schedule_job(dag_task_id, status)",
    """
    CREATE TABLE IF NOT EXISTS schedule_run (
        id BIGSERIAL PRIMARY KEY,
        schedule_run_id VARCHAR(128) NOT NULL,
        schedule_job_id VARCHAR(128) NOT NULL,
        dag_task_id VARCHAR(128) NOT NULL,
        definition_id VARCHAR(128) NOT NULL,
        owner_id VARCHAR(128) NOT NULL,
        planned_fire_time TIMESTAMPTZ NOT NULL,
        actual_fire_time TIMESTAMPTZ,
        process_id VARCHAR(128),
        status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
        attempt INTEGER NOT NULL DEFAULT 0,
        dispatch_owner VARCHAR(128),
        dispatch_lease_until TIMESTAMPTZ,
        error_message TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uk_schedule_run_id UNIQUE (schedule_run_id),
        CONSTRAINT uk_schedule_run_job_planned_fire UNIQUE (schedule_job_id, planned_fire_time),
        CONSTRAINT ck_schedule_run_status
            CHECK (status IN ('PENDING', 'DISPATCHING', 'SUBMITTED', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', 'LOST')),
        CONSTRAINT ck_schedule_run_attempt
            CHECK (attempt >= 0)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_schedule_run_job_created ON schedule_run(schedule_job_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_run_status_updated ON schedule_run(status, updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_run_process_id ON schedule_run(process_id)",
    """
    CREATE TABLE IF NOT EXISTS schedule_leader_lock (
        lock_name VARCHAR(128) PRIMARY KEY,
        owner_id VARCHAR(128),
        lease_until TIMESTAMPTZ,
        heartbeat_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


def init_schedule_tables(cursor=None) -> None:
    if cursor is not None:
        for ddl in SCHEDULE_DDL_STATEMENTS:
            cursor.execute(ddl)
        cursor.execute(
            """
            INSERT INTO schedule_leader_lock(lock_name)
            VALUES ('global-scheduler')
            ON CONFLICT (lock_name) DO NOTHING
            """
        )
        return

    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as inner_cursor:
                init_schedule_tables(inner_cursor)


def _row_to_schedule_job(row: dict) -> ScheduleJob:
    return ScheduleJob(
        schedule_job_id=row["schedule_job_id"],
        schedule_name=row["schedule_name"],
        dag_task_id=row["dag_task_id"],
        definition_id=row["definition_id"],
        owner_id=row["owner_id"],
        trigger_type=row["trigger_type"],
        cron_expression=row["cron_expression"],
        interval_seconds=row["interval_seconds"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        timezone=row["timezone"],
        misfire_policy=row["misfire_policy"],
        max_running_instances=row["max_running_instances"],
        concurrency_policy=row["concurrency_policy"],
        status=row["status"],
        next_fire_time=row["next_fire_time"],
        last_fire_time=row["last_fire_time"],
        payload_json=row["payload_json"] or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_schedule_run(row: dict) -> ScheduleRun:
    return ScheduleRun(
        schedule_run_id=row["schedule_run_id"],
        schedule_job_id=row["schedule_job_id"],
        dag_task_id=row["dag_task_id"],
        definition_id=row["definition_id"],
        owner_id=row["owner_id"],
        planned_fire_time=row["planned_fire_time"],
        actual_fire_time=row["actual_fire_time"],
        process_id=row["process_id"],
        status=row["status"],
        attempt=row["attempt"],
        dispatch_owner=row["dispatch_owner"],
        dispatch_lease_until=row["dispatch_lease_until"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_schedule_job(
    *,
    schedule_name: str,
    dag_task_id: str,
    definition_id: str,
    owner_id: str,
    trigger_type: str,
    status: str = ScheduleStatus.DRAFT,
    timezone: str = "Asia/Shanghai",
    cron_expression: str | None = None,
    interval_seconds: int | None = None,
    start_time=None,
    end_time=None,
    next_fire_time=None,
    last_fire_time=None,
    misfire_policy: str = MisfirePolicy.FIRE_ONCE,
    max_running_instances: int = 1,
    concurrency_policy: str = ConcurrencyPolicy.SKIP_CURRENT,
    payload_json: dict | None = None,
    schedule_job_id: str | None = None,
) -> ScheduleJob:
    if status not in ScheduleStatus.ALL:
        raise ValueError(f"unsupported schedule status: {status}")
    if misfire_policy not in MisfirePolicy.ALL:
        raise ValueError(f"unsupported misfire policy: {misfire_policy}")
    if concurrency_policy not in ConcurrencyPolicy.ALL:
        raise ValueError(f"unsupported concurrency policy: {concurrency_policy}")

    ScheduleExpression(
        trigger_type=trigger_type,
        timezone=timezone,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
    ).validate()

    resolved_schedule_job_id = schedule_job_id or uuid.uuid4().hex
    resolved_payload_json = payload_json or {}
    resolved_next_fire_time = next_fire_time
    if resolved_next_fire_time is None and status == ScheduleStatus.STARTED:
        resolved_next_fire_time = compute_first_fire_time(
            trigger_type=trigger_type,
            cron_expression=cron_expression,
            start_time=start_time,
            end_time=end_time,
            timezone_name=timezone,
        )

    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO schedule_job (
                        schedule_job_id,
                        schedule_name,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        trigger_type,
                        cron_expression,
                        interval_seconds,
                        start_time,
                        end_time,
                        timezone,
                        misfire_policy,
                        max_running_instances,
                        concurrency_policy,
                        status,
                        next_fire_time,
                        last_fire_time,
                        payload_json
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING
                        schedule_job_id,
                        schedule_name,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        trigger_type,
                        cron_expression,
                        interval_seconds,
                        start_time,
                        end_time,
                        timezone,
                        misfire_policy,
                        max_running_instances,
                        concurrency_policy,
                        status,
                        next_fire_time,
                        last_fire_time,
                        payload_json,
                        created_at,
                        updated_at
                    """,
                    (
                        resolved_schedule_job_id,
                        schedule_name,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        trigger_type,
                        cron_expression,
                        interval_seconds,
                        start_time,
                        end_time,
                        timezone,
                        misfire_policy,
                        max_running_instances,
                        concurrency_policy,
                        status,
                        resolved_next_fire_time,
                        last_fire_time,
                        Json(resolved_payload_json),
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("failed to insert schedule_job")
                return _row_to_schedule_job(row)


def _select_schedule_job_row(cursor, schedule_job_id: str, owner_id: str | None = None):
    query = """
        SELECT
            schedule_job_id,
            schedule_name,
            dag_task_id,
            definition_id,
            owner_id,
            trigger_type,
            cron_expression,
            interval_seconds,
            start_time,
            end_time,
            timezone,
            misfire_policy,
            max_running_instances,
            concurrency_policy,
            status,
            next_fire_time,
            last_fire_time,
            payload_json,
            created_at,
            updated_at
        FROM schedule_job
        WHERE schedule_job_id = %s
    """
    params: list = [schedule_job_id]
    if owner_id is not None:
        query += " AND owner_id = %s"
        params.append(owner_id)
    cursor.execute(query, tuple(params))
    return cursor.fetchone()


def _update_schedule_job(
    *,
    schedule_job_id: str,
    owner_id: str | None,
    updates: dict,
    expected_status: str | None = None,
) -> ScheduleJob:
    assignments = []
    values = []
    for field, value in updates.items():
        assignments.append(f"{field} = %s")
        values.append(Json(value) if field == "payload_json" else value)

    assignments.append("updated_at = CURRENT_TIMESTAMP")
    query = f"""
        UPDATE schedule_job
        SET {", ".join(assignments)}
        WHERE schedule_job_id = %s
    """
    values.append(schedule_job_id)
    if owner_id is not None:
        query += " AND owner_id = %s"
        values.append(owner_id)
    if expected_status is not None:
        query += " AND status = %s"
        values.append(expected_status)
    query += """
        RETURNING
            schedule_job_id,
            schedule_name,
            dag_task_id,
            definition_id,
            owner_id,
            trigger_type,
            cron_expression,
            interval_seconds,
            start_time,
            end_time,
            timezone,
            misfire_policy,
            max_running_instances,
            concurrency_policy,
            status,
            next_fire_time,
            last_fire_time,
            payload_json,
            created_at,
            updated_at
    """

    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(values))
                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"schedule job not found or state changed: {schedule_job_id}")
                return _row_to_schedule_job(row)


def get_schedule_job_by_id(
    schedule_job_id: str,
    *,
    owner_id: str | None = None,
) -> ScheduleJob | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            row = _select_schedule_job_row(cursor, schedule_job_id, owner_id)

    if row is None:
        return None
    return _row_to_schedule_job(row)


def list_schedule_jobs(
    *,
    owner_id: str | None = None,
    status: str | None = None,
    dag_task_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    if status is not None and status not in ScheduleStatus.ALL:
        raise ValueError(f"unsupported schedule status: {status}")

    conditions = ["status <> %s"]
    params: list = [ScheduleStatus.DELETED]
    if owner_id is not None:
        conditions.append("owner_id = %s")
        params.append(owner_id)
    if status is not None:
        conditions.append("status = %s")
        params.append(status)
    if dag_task_id is not None:
        conditions.append("dag_task_id = %s")
        params.append(dag_task_id)
    where_clause = " AND ".join(conditions)
    offset = (page - 1) * page_size

    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM schedule_job WHERE {where_clause}",
                tuple(params),
            )
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT
                    schedule_job_id,
                    schedule_name,
                    dag_task_id,
                    definition_id,
                    owner_id,
                    trigger_type,
                    cron_expression,
                    interval_seconds,
                    start_time,
                    end_time,
                    timezone,
                    misfire_policy,
                    max_running_instances,
                    concurrency_policy,
                    status,
                    next_fire_time,
                    last_fire_time,
                    payload_json,
                    created_at,
                    updated_at
                FROM schedule_job
                WHERE {where_clause}
                ORDER BY created_at DESC, schedule_job_id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params + [page_size, offset]),
            )
            items = [_row_to_schedule_job(row) for row in cursor.fetchall()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def update_schedule_job(
    schedule_job_id: str,
    *,
    owner_id: str | None = None,
    schedule_name: str | None = None,
    cron_expression: str | None = None,
    start_time=None,
    end_time=None,
    timezone: str | None = None,
    misfire_policy: str | None = None,
    max_running_instances: int | None = None,
    concurrency_policy: str | None = None,
    payload_json: dict | None = None,
) -> ScheduleJob:
    current = get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)
    if current is None:
        raise ValueError(f"schedule job not found: {schedule_job_id}")
    if current.status == ScheduleStatus.DELETED:
        raise ValueError(f"cannot update deleted schedule job: {schedule_job_id}")

    next_timezone = timezone or current.timezone
    next_cron = cron_expression if cron_expression is not None else current.cron_expression
    next_start = start_time if start_time is not None else current.start_time
    next_end = end_time if end_time is not None else current.end_time
    ScheduleExpression(
        trigger_type=current.trigger_type,
        timezone=next_timezone,
        cron_expression=next_cron,
        interval_seconds=current.interval_seconds,
    ).validate()
    compute_first_fire_time(
        trigger_type=current.trigger_type,
        cron_expression=next_cron,
        start_time=next_start,
        end_time=next_end,
        timezone_name=next_timezone,
    )

    updates = {}
    if schedule_name is not None:
        updates["schedule_name"] = schedule_name
    if cron_expression is not None:
        updates["cron_expression"] = cron_expression
    if start_time is not None:
        updates["start_time"] = start_time
    if end_time is not None:
        updates["end_time"] = end_time
    if timezone is not None:
        updates["timezone"] = timezone
    if misfire_policy is not None:
        if misfire_policy not in MisfirePolicy.ALL:
            raise ValueError(f"unsupported misfire policy: {misfire_policy}")
        updates["misfire_policy"] = misfire_policy
    if max_running_instances is not None:
        if max_running_instances <= 0:
            raise ValueError("max_running_instances must be > 0")
        updates["max_running_instances"] = max_running_instances
    if concurrency_policy is not None:
        if concurrency_policy not in ConcurrencyPolicy.ALL:
            raise ValueError(f"unsupported concurrency policy: {concurrency_policy}")
        updates["concurrency_policy"] = concurrency_policy
    if payload_json is not None:
        updates["payload_json"] = payload_json
    if not updates:
        return current

    trigger_fields_changed = any(
        value is not None
        for value in (cron_expression, start_time, end_time, timezone)
    )
    if current.status == ScheduleStatus.STARTED and trigger_fields_changed:
        updates["next_fire_time"] = compute_first_fire_time(
            trigger_type=current.trigger_type,
            cron_expression=next_cron,
            start_time=next_start,
            end_time=next_end,
            timezone_name=next_timezone,
        )
    return _update_schedule_job(
        schedule_job_id=schedule_job_id,
        owner_id=owner_id,
        updates=updates,
    )


def start_schedule_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    current = get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)
    if current is None:
        raise ValueError(f"schedule job not found: {schedule_job_id}")
    if current.status not in (ScheduleStatus.DRAFT, ScheduleStatus.PAUSED, ScheduleStatus.STOPPED):
        raise ValueError(f"cannot start schedule job from status: {current.status}")

    next_fire_time = compute_first_fire_time(
        trigger_type=current.trigger_type,
        cron_expression=current.cron_expression,
        interval_seconds=current.interval_seconds,
        start_time=current.start_time,
        end_time=current.end_time,
        timezone_name=current.timezone,
    )
    return _update_schedule_job(
        schedule_job_id=schedule_job_id,
        owner_id=owner_id,
        expected_status=current.status,
        updates={
            "status": ScheduleStatus.STARTED,
            "next_fire_time": next_fire_time,
            "last_fire_time": None,
        },
    )


def pause_schedule_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    current = get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)
    if current is None:
        raise ValueError(f"schedule job not found: {schedule_job_id}")
    if current.status != ScheduleStatus.STARTED:
        raise ValueError(f"cannot pause schedule job from status: {current.status}")
    return _update_schedule_job(
        schedule_job_id=schedule_job_id,
        owner_id=owner_id,
        expected_status=ScheduleStatus.STARTED,
        updates={"status": ScheduleStatus.PAUSED, "next_fire_time": None},
    )


def stop_schedule_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    current = get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)
    if current is None:
        raise ValueError(f"schedule job not found: {schedule_job_id}")
    if current.status not in (ScheduleStatus.STARTED, ScheduleStatus.PAUSED):
        raise ValueError(f"cannot stop schedule job from status: {current.status}")
    return _update_schedule_job(
        schedule_job_id=schedule_job_id,
        owner_id=owner_id,
        expected_status=current.status,
        updates={"status": ScheduleStatus.STOPPED, "next_fire_time": None},
    )


def delete_schedule_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    current = get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)
    if current is None:
        raise ValueError(f"schedule job not found: {schedule_job_id}")
    if current.status == ScheduleStatus.DELETED:
        return current
    return _update_schedule_job(
        schedule_job_id=schedule_job_id,
        owner_id=owner_id,
        expected_status=current.status,
        updates={"status": ScheduleStatus.DELETED, "next_fire_time": None},
    )


# Stage 3 public repository names. The longer names above remain useful for
# compatibility with the stage 1 API.
def create_job(**kwargs) -> ScheduleJob:
    return create_schedule_job(**kwargs)


def update_job(schedule_job_id: str, **kwargs) -> ScheduleJob:
    return update_schedule_job(schedule_job_id, **kwargs)


def start_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    return start_schedule_job(schedule_job_id, owner_id=owner_id)


def pause_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    return pause_schedule_job(schedule_job_id, owner_id=owner_id)


def stop_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    return stop_schedule_job(schedule_job_id, owner_id=owner_id)


def delete_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob:
    return delete_schedule_job(schedule_job_id, owner_id=owner_id)


def list_jobs(**kwargs) -> dict:
    return list_schedule_jobs(**kwargs)


def get_job(schedule_job_id: str, *, owner_id: str | None = None) -> ScheduleJob | None:
    return get_schedule_job_by_id(schedule_job_id, owner_id=owner_id)


def _schedule_job_select_sql() -> str:
    return """
        SELECT
            schedule_job_id,
            schedule_name,
            dag_task_id,
            definition_id,
            owner_id,
            trigger_type,
            cron_expression,
            interval_seconds,
            start_time,
            end_time,
            timezone,
            misfire_policy,
            max_running_instances,
            concurrency_policy,
            status,
            next_fire_time,
            last_fire_time,
            payload_json,
            created_at,
            updated_at
        FROM schedule_job
    """


def advance_job_schedule(
    cursor,
    *,
    job: ScheduleJob,
    planned_fire_time,
    next_fire_time,
    skip_last_fire: bool = False,
) -> ScheduleJob:
    next_status = (
        ScheduleStatus.STARTED
        if next_fire_time is not None
        else ScheduleStatus.EXPIRED
    )
    if skip_last_fire:
        cursor.execute(
            """
            UPDATE schedule_job
            SET
                status = %s,
                next_fire_time = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE schedule_job_id = %s
            """,
            (next_status, next_fire_time, job.schedule_job_id),
        )
    else:
        cursor.execute(
            """
            UPDATE schedule_job
            SET
                status = %s,
                last_fire_time = %s,
                next_fire_time = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE schedule_job_id = %s
            """,
            (
                next_status,
                planned_fire_time,
                next_fire_time,
                job.schedule_job_id,
            ),
        )
    job.status = next_status
    if not skip_last_fire:
        job.last_fire_time = planned_fire_time
    job.next_fire_time = next_fire_time
    return job


def claim_due_jobs(*, now, limit: int = 100) -> list[tuple[ScheduleJob, ScheduleRun]]:
    """Atomically create runs and advance due jobs for one scheduler tick."""
    if limit < 1:
        raise ValueError("limit must be >= 1")

    claimed: list[tuple[ScheduleJob, ScheduleRun]] = []
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 自动过期 end_time 到的任务
                cursor.execute(
                    """
                    UPDATE schedule_job
                    SET status = %s, next_fire_time = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE status = %s AND end_time IS NOT NULL AND end_time < %s
                    """,
                    (ScheduleStatus.EXPIRED, ScheduleStatus.STARTED, now),
                )

                cursor.execute(
                    _schedule_job_select_sql()
                    + """
                    WHERE status = %s
                      AND next_fire_time IS NOT NULL
                      AND next_fire_time <= %s
                    ORDER BY next_fire_time, schedule_job_id
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                    """,
                    (ScheduleStatus.STARTED, now, limit),
                )
                rows = cursor.fetchall()

                for row in rows:
                    job = _row_to_schedule_job(row)
                    planned_fire_time = job.next_fire_time
                    if planned_fire_time is None:
                        continue

                    is_overdue = planned_fire_time < now

                    # misfire 策略 - SKIP：跳过过期点，直接推进到未来
                    if is_overdue and job.misfire_policy == MisfirePolicy.SKIP:
                        next_fire_time = compute_next_fire_time(
                            trigger_type=job.trigger_type,
                            cron_expression=job.cron_expression,
                            interval_seconds=job.interval_seconds,
                            start_time=job.start_time,
                            end_time=job.end_time,
                            timezone_name=job.timezone,
                            after=now,
                        )
                        advance_job_schedule(
                            cursor,
                            job=job,
                            planned_fire_time=planned_fire_time,
                            next_fire_time=next_fire_time,
                            skip_last_fire=True,
                        )
                        continue

                    # 并发控制 - SKIP_CURRENT：活跃 run 数达上限时跳过本次触发
                    if job.max_running_instances > 0:
                        cursor.execute(
                            """
                            SELECT COUNT(*) AS cnt FROM schedule_run
                            WHERE schedule_job_id = %s
                              AND status IN (%s, %s, %s)
                            """,
                            (
                                job.schedule_job_id,
                                ScheduleRunStatus.DISPATCHING,
                                ScheduleRunStatus.SUBMITTED,
                                ScheduleRunStatus.RUNNING,
                            ),
                        )
                        active_count = cursor.fetchone()["cnt"]
                        if active_count >= job.max_running_instances:
                            next_fire_time = compute_next_fire_time(
                                trigger_type=job.trigger_type,
                                cron_expression=job.cron_expression,
                                interval_seconds=job.interval_seconds,
                                start_time=job.start_time,
                                end_time=job.end_time,
                                timezone_name=job.timezone,
                                after=planned_fire_time,
                            )
                            advance_job_schedule(
                                cursor,
                                job=job,
                                planned_fire_time=planned_fire_time,
                                next_fire_time=next_fire_time,
                                skip_last_fire=True,
                            )
                            continue

                    # 建 run（FIRE_ONCE / CATCH_UP / 正常触发）
                    schedule_run_id = uuid.uuid4().hex

                    cursor.execute(
                        """
                        INSERT INTO schedule_run (
                            schedule_run_id,
                            schedule_job_id,
                            dag_task_id,
                            definition_id,
                            owner_id,
                            planned_fire_time,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (schedule_job_id, planned_fire_time)
                        DO NOTHING
                        RETURNING
                            schedule_run_id,
                            schedule_job_id,
                            dag_task_id,
                            definition_id,
                            owner_id,
                            planned_fire_time,
                            actual_fire_time,
                            process_id,
                            status,
                            attempt,
                            dispatch_owner,
                            dispatch_lease_until,
                            error_message,
                            created_at,
                            updated_at
                        """,
                        (
                            schedule_run_id,
                            job.schedule_job_id,
                            job.dag_task_id,
                            job.definition_id,
                            job.owner_id,
                            planned_fire_time,
                            ScheduleRunStatus.PENDING,
                        ),
                    )
                    run_row = cursor.fetchone()
                    if run_row is None:
                        continue

                    # misfire 策略 - FIRE_ONCE：补一次但 next 推到未来
                    if is_overdue and job.misfire_policy == MisfirePolicy.FIRE_ONCE:
                        advance_after = now
                    else:
                        # CATCH_UP 或正常触发：逐点推进
                        advance_after = planned_fire_time

                    next_fire_time = compute_next_fire_time(
                        trigger_type=job.trigger_type,
                        cron_expression=job.cron_expression,
                        interval_seconds=job.interval_seconds,
                        start_time=job.start_time,
                        end_time=job.end_time,
                        timezone_name=job.timezone,
                        after=advance_after,
                    )
                    advance_job_schedule(
                        cursor,
                        job=job,
                        planned_fire_time=planned_fire_time,
                        next_fire_time=next_fire_time,
                    )
                    claimed.append((job, _row_to_schedule_run(run_row)))

    return claimed


def mark_schedule_run_submitted(
    schedule_run_id: str,
    *,
    process_id: str,
) -> ScheduleRun:
    if not process_id:
        raise ValueError("process_id is required")
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE schedule_run
                    SET
                        status = %s,
                        process_id = %s,
                        actual_fire_time = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE schedule_run_id = %s
                      AND status = %s
                    RETURNING
                        schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message,
                        created_at,
                        updated_at
                    """,
                    (
                        ScheduleRunStatus.SUBMITTED,
                        process_id,
                        schedule_run_id,
                        ScheduleRunStatus.DISPATCHING,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"schedule run not found or already submitted: {schedule_run_id}")
                return _row_to_schedule_run(row)


def mark_schedule_run_failed(
    schedule_run_id: str,
    *,
    error_message: str,
) -> ScheduleRun:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE schedule_run
                    SET
                        status = %s,
                        error_message = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE schedule_run_id = %s
                      AND status IN (%s, %s)
                    RETURNING
                        schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message,
                        created_at,
                        updated_at
                    """,
                    (
                        ScheduleRunStatus.FAILED,
                        error_message,
                        schedule_run_id,
                        ScheduleRunStatus.PENDING,
                        ScheduleRunStatus.DISPATCHING,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"schedule run not found or already completed: {schedule_run_id}")
                return _row_to_schedule_run(row)


def create_schedule_run(
    *,
    schedule_job_id: str,
    dag_task_id: str,
    definition_id: str,
    owner_id: str,
    planned_fire_time,
    status: str = ScheduleRunStatus.PENDING,
    actual_fire_time=None,
    process_id: str | None = None,
    attempt: int = 0,
    dispatch_owner: str | None = None,
    dispatch_lease_until=None,
    error_message: str | None = None,
    schedule_run_id: str | None = None,
) -> ScheduleRun:
    if status not in ScheduleRunStatus.ALL:
        raise ValueError(f"unsupported schedule run status: {status}")

    resolved_schedule_run_id = schedule_run_id or uuid.uuid4().hex
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO schedule_run (
                        schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message,
                        created_at,
                        updated_at
                    """,
                    (
                        resolved_schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("failed to insert schedule_run")
                return _row_to_schedule_run(row)


def list_schedule_runs(
    *,
    schedule_job_id: str,
    owner_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    if status is not None and status not in ScheduleRunStatus.ALL:
        raise ValueError(f"unsupported schedule run status: {status}")

    conditions = ["schedule_job_id = %s"]
    params: list = [schedule_job_id]
    if owner_id is not None:
        conditions.append("owner_id = %s")
        params.append(owner_id)
    if status is not None:
        conditions.append("status = %s")
        params.append(status)
    where_clause = " AND ".join(conditions)
    offset = (page - 1) * page_size

    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM schedule_run WHERE {where_clause}",
                tuple(params),
            )
            total = cursor.fetchone()["total"]
            cursor.execute(
                f"""
                SELECT
                    schedule_run_id,
                    schedule_job_id,
                    dag_task_id,
                    definition_id,
                    owner_id,
                    planned_fire_time,
                    actual_fire_time,
                    process_id,
                    status,
                    attempt,
                    dispatch_owner,
                    dispatch_lease_until,
                    error_message,
                    created_at,
                    updated_at
                FROM schedule_run
                WHERE {where_clause}
                ORDER BY created_at DESC, schedule_run_id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params + [page_size, offset]),
            )
            items = [_row_to_schedule_run(row) for row in cursor.fetchall()]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def get_schedule_run_by_id(
    schedule_run_id: str,
    *,
    owner_id: str | None = None,
) -> ScheduleRun | None:
    query = """
        SELECT
            schedule_run_id,
            schedule_job_id,
            dag_task_id,
            definition_id,
            owner_id,
            planned_fire_time,
            actual_fire_time,
            process_id,
            status,
            attempt,
            dispatch_owner,
            dispatch_lease_until,
            error_message,
            created_at,
            updated_at
        FROM schedule_run
        WHERE schedule_run_id = %s
    """
    params: list = [schedule_run_id]
    if owner_id is not None:
        query += " AND owner_id = %s"
        params.append(owner_id)

    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()

    if row is None:
        return None
    return _row_to_schedule_run(row)


def list_runs(**kwargs) -> dict:
    return list_schedule_runs(**kwargs)


def get_run(schedule_run_id: str, *, owner_id: str | None = None) -> ScheduleRun | None:
    return get_schedule_run_by_id(schedule_run_id, owner_id=owner_id)


def mark_run_dispatching(
    schedule_run_id: str,
    *,
    owner_id: str,
    lease_seconds: int = 30,
) -> ScheduleRun | None:
    """PENDING -> DISPATCHING，写 dispatch_owner/lease_until/attempt+1。"""
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE schedule_run
                    SET
                        status = %s,
                        dispatch_owner = %s,
                        dispatch_lease_until = CURRENT_TIMESTAMP + (%s || ' seconds')::interval,
                        attempt = attempt + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE schedule_run_id = %s
                      AND status = %s
                    RETURNING
                        schedule_run_id,
                        schedule_job_id,
                        dag_task_id,
                        definition_id,
                        owner_id,
                        planned_fire_time,
                        actual_fire_time,
                        process_id,
                        status,
                        attempt,
                        dispatch_owner,
                        dispatch_lease_until,
                        error_message,
                        created_at,
                        updated_at
                    """,
                    (
                        ScheduleRunStatus.DISPATCHING,
                        owner_id,
                        str(lease_seconds),
                        schedule_run_id,
                        ScheduleRunStatus.PENDING,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return _row_to_schedule_run(row)


def recover_expired_dispatching_runs(*, now, lease_seconds: int = 60) -> int:
    """租约过期的 DISPATCHING -> LOST（保守策略，不重试）。"""
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE schedule_run
                    SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE status = %s
                      AND dispatch_lease_until IS NOT NULL
                      AND dispatch_lease_until < %s
                    """,
                    (
                        ScheduleRunStatus.LOST,
                        "dispatch lease expired",
                        ScheduleRunStatus.DISPATCHING,
                        now,
                    ),
                )
                return cursor.rowcount


def list_submitted_runs(*, limit: int = 50) -> list[ScheduleRun]:
    """查 SUBMITTED 状态的 run（终态回写低频同步用）。"""
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    schedule_run_id,
                    schedule_job_id,
                    dag_task_id,
                    definition_id,
                    owner_id,
                    planned_fire_time,
                    actual_fire_time,
                    process_id,
                    status,
                    attempt,
                    dispatch_owner,
                    dispatch_lease_until,
                    error_message,
                    created_at,
                    updated_at
                FROM schedule_run
                WHERE status = %s
                ORDER BY updated_at
                LIMIT %s
                """,
                (ScheduleRunStatus.SUBMITTED, limit),
            )
            return [_row_to_schedule_run(row) for row in cursor.fetchall()]


def mark_run_completed(
    schedule_run_id: str,
    *,
    status: str,
    error_message: str | None = None,
) -> int:
    """回写终态（SUCCESS/FAILED/CANCELLED），返回受影响行数。"""
    if status not in (
        ScheduleRunStatus.SUCCESS,
        ScheduleRunStatus.FAILED,
        ScheduleRunStatus.CANCELLED,
    ):
        raise ValueError(f"unsupported terminal status: {status}")
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE schedule_run
                    SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE schedule_run_id = %s
                      AND status = %s
                    """,
                    (
                        status,
                        error_message,
                        schedule_run_id,
                        ScheduleRunStatus.SUBMITTED,
                    ),
                )
                return cursor.rowcount
