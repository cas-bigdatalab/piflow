"""PostgreSQL persistence for the additive XDC session feature."""

from __future__ import annotations

import threading
from contextlib import closing
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from database.postgres import get_connection

_SCHEMA_LOCK = threading.Lock()
_SCHEMA_READY = False


def initialize_xdc_session_schema() -> None:
    """Create only XDC-owned tables in the existing configured database."""
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS xdc_session (
                id BIGSERIAL PRIMARY KEY,
                session_id VARCHAR(64) NOT NULL UNIQUE,
                user_id VARCHAR(64) NOT NULL,
                title VARCHAR(255) NOT NULL DEFAULT '',
                status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
                is_deleted SMALLINT NOT NULL DEFAULT 0,
                create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_xdc_session_user
                    FOREIGN KEY (user_id) REFERENCES sys_user(user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS xdc_task (
                id BIGSERIAL PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL UNIQUE,
                session_id VARCHAR(64) NOT NULL,
                task_order INT NOT NULL DEFAULT 1,
                parent_task_id VARCHAR(64),
                task_name VARCHAR(255) NOT NULL DEFAULT '',
                user_request TEXT NOT NULL,
                mode VARCHAR(32),
                status VARCHAR(32) NOT NULL DEFAULT 'CREATED',
                current_stage VARCHAR(32) NOT NULL DEFAULT 'created',
                plan_revision INT NOT NULL DEFAULT 1,
                plan_id VARCHAR(128),
                process_id VARCHAR(128),
                error_message TEXT NOT NULL DEFAULT '',
                create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finish_time TIMESTAMP,
                CONSTRAINT fk_xdc_task_session
                    FOREIGN KEY (session_id) REFERENCES xdc_session(session_id),
                CONSTRAINT fk_xdc_task_parent
                    FOREIGN KEY (parent_task_id) REFERENCES xdc_task(task_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS xdc_session_item (
                item_id BIGSERIAL PRIMARY KEY,
                item_key VARCHAR(128) NOT NULL UNIQUE,
                session_id VARCHAR(64) NOT NULL,
                task_id VARCHAR(64),
                parent_item_id BIGINT,
                role VARCHAR(32) NOT NULL DEFAULT 'system',
                item_type VARCHAR(32) NOT NULL,
                item_status VARCHAR(32) NOT NULL DEFAULT '',
                payload_json JSONB NOT NULL,
                create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_xdc_item_session
                    FOREIGN KEY (session_id) REFERENCES xdc_session(session_id),
                CONSTRAINT fk_xdc_item_task
                    FOREIGN KEY (task_id) REFERENCES xdc_task(task_id),
                CONSTRAINT fk_xdc_item_parent
                    FOREIGN KEY (parent_item_id) REFERENCES xdc_session_item(item_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS xdc_task_snapshot (
                id BIGSERIAL PRIMARY KEY,
                task_id VARCHAR(64) NOT NULL,
                revision INT NOT NULL DEFAULT 1,
                snapshot_type VARCHAR(32) NOT NULL,
                schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
                payload_json JSONB NOT NULL,
                is_current SMALLINT NOT NULL DEFAULT 1,
                create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_xdc_snapshot_task
                    FOREIGN KEY (task_id) REFERENCES xdc_task(task_id),
                CONSTRAINT uk_xdc_task_snapshot
                    UNIQUE (task_id, revision, snapshot_type)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_xdc_session_user_time ON xdc_session(user_id, update_time DESC)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_task_session_time ON xdc_task(session_id, create_time)",
            "CREATE UNIQUE INDEX IF NOT EXISTS uk_xdc_task_order ON xdc_task(session_id, task_order)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_task_plan ON xdc_task(plan_id)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_task_process ON xdc_task(process_id)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_item_session ON xdc_session_item(session_id, item_id)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_item_task ON xdc_session_item(task_id, item_id)",
            "CREATE INDEX IF NOT EXISTS idx_xdc_snapshot_task ON xdc_task_snapshot(task_id, revision)",
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uk_xdc_session_active_task
            ON xdc_task(session_id)
            WHERE status IN ('PROCESSING', 'PLANNED', 'EXECUTING')
            """,
        ]
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    for statement in ddl:
                        cursor.execute(statement)
        _SCHEMA_READY = True


def create_session(*, session_id: str, user_id: str, title: str) -> dict[str, Any]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO xdc_session (session_id, user_id, title)
                    VALUES (%s, %s, %s)
                    RETURNING session_id, user_id, title, status,
                              create_time, update_time
                    """,
                    (session_id, user_id, title),
                )
                return dict(cursor.fetchone())


def list_sessions(
    *, user_id: str, page_num: int, page_size: int
) -> dict[str, Any]:
    _ensure_schema()
    offset = (page_num - 1) * page_size
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM xdc_session
                WHERE user_id = %s AND is_deleted = 0
                """,
                (user_id,),
            )
            total = int(cursor.fetchone()["total"])
            cursor.execute(
                """
                SELECT
                    s.session_id,
                    s.title,
                    s.status,
                    s.create_time,
                    s.update_time,
                    COUNT(t.id)::INT AS task_count,
                    latest.task_id AS latest_task_id,
                    latest.status AS latest_task_status,
                    latest.current_stage AS latest_task_stage
                FROM xdc_session s
                LEFT JOIN xdc_task t ON t.session_id = s.session_id
                LEFT JOIN LATERAL (
                    SELECT task_id, status, current_stage
                    FROM xdc_task lt
                    WHERE lt.session_id = s.session_id
                    ORDER BY lt.task_order DESC, lt.id DESC
                    LIMIT 1
                ) latest ON TRUE
                WHERE s.user_id = %s AND s.is_deleted = 0
                GROUP BY s.id, latest.task_id, latest.status, latest.current_stage
                ORDER BY s.update_time DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, page_size, offset),
            )
            items = [dict(row) for row in cursor.fetchall()]
    return {
        "items": items,
        "pagination": {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": total,
        },
    }


def get_session(*, session_id: str, user_id: str) -> dict[str, Any] | None:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT session_id, user_id, title, status,
                       create_time, update_time
                FROM xdc_session
                WHERE session_id = %s AND user_id = %s AND is_deleted = 0
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()
    return dict(row) if row else None


def delete_session(*, session_id: str, user_id: str) -> bool:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE xdc_session
                    SET is_deleted = 1,
                        status = 'ARCHIVED',
                        update_time = CURRENT_TIMESTAMP
                    WHERE session_id = %s AND user_id = %s AND is_deleted = 0
                    """,
                    (session_id, user_id),
                )
                return cursor.rowcount > 0


def create_task(
    *,
    task_id: str,
    session_id: str,
    user_id: str,
    user_request: str,
    task_name: str,
    parent_task_id: str | None = None,
) -> dict[str, Any]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT session_id
                    FROM xdc_session
                    WHERE session_id = %s AND user_id = %s AND is_deleted = 0
                    FOR UPDATE
                    """,
                    (session_id, user_id),
                )
                if cursor.fetchone() is None:
                    raise LookupError(f"Session不存在或无权访问: {session_id}")
                cursor.execute(
                    """
                    SELECT task_id
                    FROM xdc_task
                    WHERE session_id = %s
                      AND status IN ('PROCESSING', 'PLANNED', 'EXECUTING')
                    LIMIT 1
                    """,
                    (session_id,),
                )
                active = cursor.fetchone()
                if active is not None:
                    raise RuntimeError(
                        f"Session中已有未完成任务: {active['task_id']}"
                    )
                if parent_task_id:
                    cursor.execute(
                        """
                        SELECT task_id
                        FROM xdc_task
                        WHERE task_id = %s AND session_id = %s
                        """,
                        (parent_task_id, session_id),
                    )
                    if cursor.fetchone() is None:
                        raise LookupError(
                            f"父任务不属于当前 Session: {parent_task_id}"
                        )
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(task_order), 0) + 1 AS next_order
                    FROM xdc_task
                    WHERE session_id = %s
                    """,
                    (session_id,),
                )
                task_order = int(cursor.fetchone()["next_order"])
                cursor.execute(
                    """
                    INSERT INTO xdc_task (
                        task_id, session_id, task_order, parent_task_id,
                        task_name, user_request, status, current_stage
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'PROCESSING', 'intent')
                    RETURNING task_id, session_id, task_order, parent_task_id,
                              task_name, user_request, mode, status, current_stage,
                              plan_revision, plan_id, process_id, error_message,
                              create_time, update_time, finish_time
                    """,
                    (
                        task_id,
                        session_id,
                        task_order,
                        parent_task_id,
                        task_name,
                        user_request,
                    ),
                )
                task = dict(cursor.fetchone())
                cursor.execute(
                    """
                    UPDATE xdc_session
                    SET title = CASE WHEN title = '' THEN %s ELSE title END,
                        update_time = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                    """,
                    (task_name, session_id),
                )
                return task


def get_task(*, task_id: str, user_id: str) -> dict[str, Any] | None:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT t.task_id, t.session_id, t.task_order, t.parent_task_id,
                       t.task_name, t.user_request, t.mode, t.status,
                       t.current_stage, t.plan_revision, t.plan_id, t.process_id,
                       t.error_message, t.create_time, t.update_time, t.finish_time
                FROM xdc_task t
                JOIN xdc_session s ON s.session_id = t.session_id
                WHERE t.task_id = %s
                  AND s.user_id = %s
                  AND s.is_deleted = 0
                """,
                (task_id, user_id),
            )
            row = cursor.fetchone()
    return dict(row) if row else None


def list_tasks(*, session_id: str, user_id: str) -> list[dict[str, Any]]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT t.task_id, t.session_id, t.task_order, t.parent_task_id,
                       t.task_name, t.user_request, t.mode, t.status,
                       t.current_stage, t.plan_revision, t.plan_id, t.process_id,
                       t.error_message, t.create_time, t.update_time, t.finish_time
                FROM xdc_task t
                JOIN xdc_session s ON s.session_id = t.session_id
                WHERE t.session_id = %s
                  AND s.user_id = %s
                  AND s.is_deleted = 0
                ORDER BY t.task_order, t.id
                """,
                (session_id, user_id),
            )
            return [dict(row) for row in cursor.fetchall()]


def update_task_state(
    *,
    task_id: str,
    status: str,
    current_stage: str,
    mode: str | None = None,
    plan_id: str | None = None,
    process_id: str | None = None,
    error_message: str | None = None,
    finished: bool = False,
) -> None:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE xdc_task
                    SET status = %s,
                        current_stage = %s,
                        mode = COALESCE(%s, mode),
                        plan_id = COALESCE(%s, plan_id),
                        process_id = COALESCE(%s, process_id),
                        error_message = COALESCE(%s, error_message),
                        finish_time = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE finish_time END,
                        update_time = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                    """,
                    (
                        status,
                        current_stage,
                        mode,
                        plan_id,
                        process_id,
                        error_message,
                        finished,
                        task_id,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE xdc_session s
                    SET update_time = CURRENT_TIMESTAMP
                    FROM xdc_task t
                    WHERE t.task_id = %s AND s.session_id = t.session_id
                    """,
                    (task_id,),
                )


def claim_task_for_execution(
    *, task_id: str, user_id: str
) -> dict[str, Any] | None:
    """Atomically move one owned PLANNED task to EXECUTING.

    The compare-and-set prevents two frontend retries from submitting the same
    persisted plan twice.
    """
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE xdc_task t
                    SET status = 'EXECUTING',
                        current_stage = 'bind',
                        error_message = '',
                        update_time = CURRENT_TIMESTAMP
                    FROM xdc_session s
                    WHERE t.task_id = %s
                      AND t.session_id = s.session_id
                      AND s.user_id = %s
                      AND s.is_deleted = 0
                      AND t.status = 'PLANNED'
                    RETURNING t.task_id, t.session_id, t.task_order,
                              t.parent_task_id, t.task_name, t.user_request,
                              t.mode, t.status, t.current_stage,
                              t.plan_revision, t.plan_id, t.process_id,
                              t.error_message, t.create_time, t.update_time,
                              t.finish_time
                    """,
                    (task_id, user_id),
                )
                row = cursor.fetchone()
                if row is not None:
                    cursor.execute(
                        """
                        UPDATE xdc_session
                        SET update_time = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                        """,
                        (row["session_id"],),
                    )
                return dict(row) if row else None


def save_snapshot(
    *,
    task_id: str,
    revision: int,
    snapshot_type: str,
    payload: dict[str, Any],
    schema_version: str = "1.0",
) -> None:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO xdc_task_snapshot (
                        task_id, revision, snapshot_type,
                        schema_version, payload_json, is_current
                    )
                    VALUES (%s, %s, %s, %s, %s, 1)
                    ON CONFLICT (task_id, revision, snapshot_type)
                    DO UPDATE SET
                        schema_version = EXCLUDED.schema_version,
                        payload_json = EXCLUDED.payload_json,
                        is_current = 1,
                        update_time = CURRENT_TIMESTAMP
                    """,
                    (task_id, revision, snapshot_type, schema_version, Json(payload)),
                )


def get_snapshot(
    *, task_id: str, revision: int, snapshot_type: str
) -> dict[str, Any] | None:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT task_id, revision, snapshot_type,
                       schema_version, payload_json, create_time, update_time
                FROM xdc_task_snapshot
                WHERE task_id = %s AND revision = %s
                  AND snapshot_type = %s AND is_current = 1
                """,
                (task_id, revision, snapshot_type),
            )
            row = cursor.fetchone()
    return dict(row) if row else None


def list_public_snapshots(*, task_id: str) -> list[dict[str, Any]]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT snapshot_type, revision, schema_version,
                       payload_json, create_time, update_time
                FROM xdc_task_snapshot
                WHERE task_id = %s
                  AND snapshot_type IN (
                      'PRE_BIND_VIEW', 'BOUND_VIEW', 'EXECUTION', 'RESULT'
                  )
                  AND is_current = 1
                ORDER BY revision, id
                """,
                (task_id,),
            )
            return [dict(row) for row in cursor.fetchall()]


def save_session_item(
    *,
    item_key: str,
    session_id: str,
    task_id: str | None,
    role: str,
    item_type: str,
    item_status: str,
    payload: dict[str, Any],
    parent_item_id: int | None = None,
) -> dict[str, Any]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO xdc_session_item (
                        item_key, session_id, task_id, parent_item_id,
                        role, item_type, item_status, payload_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (item_key)
                    DO UPDATE SET
                        item_status = EXCLUDED.item_status,
                        payload_json = EXCLUDED.payload_json,
                        update_time = CURRENT_TIMESTAMP
                    RETURNING item_id, item_key, session_id, task_id,
                              parent_item_id, role, item_type, item_status,
                              payload_json, create_time, update_time
                    """,
                    (
                        item_key,
                        session_id,
                        task_id,
                        parent_item_id,
                        role,
                        item_type,
                        item_status,
                        Json(payload),
                    ),
                )
                return dict(cursor.fetchone())


def list_session_items(
    *, session_id: str, user_id: str, after_item_id: int = 0, limit: int = 1000
) -> list[dict[str, Any]]:
    _ensure_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT i.item_id, i.item_key, i.session_id, i.task_id,
                       i.parent_item_id, i.role, i.item_type, i.item_status,
                       i.payload_json, i.create_time, i.update_time
                FROM xdc_session_item i
                JOIN xdc_session s ON s.session_id = i.session_id
                WHERE i.session_id = %s
                  AND s.user_id = %s
                  AND s.is_deleted = 0
                  AND i.item_id > %s
                ORDER BY i.item_id
                LIMIT %s
                """,
                (session_id, user_id, after_item_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]


def _ensure_schema() -> None:
    initialize_xdc_session_schema()
