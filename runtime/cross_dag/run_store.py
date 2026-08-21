"""Persistent locator records for submitted cross-domain root runs."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def save_cross_dag_execution(
    *,
    process_id: str,
    plan_id: str,
    user_id: str,
    execution_center_id: str,
    remote_grpc_target: str,
    submit_status: str,
) -> None:
    """Remember where a public process id can be queried and downloaded."""
    normalized_status = str(submit_status or "SUBMITTED").strip().upper()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO cross_dag_execution (
                        process_id,
                        plan_id,
                        user_id,
                        execution_center_id,
                        remote_grpc_target,
                        submit_status,
                        last_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (process_id)
                    DO UPDATE SET
                        plan_id = EXCLUDED.plan_id,
                        user_id = EXCLUDED.user_id,
                        execution_center_id = EXCLUDED.execution_center_id,
                        remote_grpc_target = EXCLUDED.remote_grpc_target,
                        submit_status = EXCLUDED.submit_status,
                        last_status = EXCLUDED.last_status,
                        status_message = '',
                        update_time = CURRENT_TIMESTAMP
                    """,
                    (
                        process_id,
                        plan_id,
                        user_id,
                        execution_center_id,
                        remote_grpc_target,
                        normalized_status,
                        normalized_status,
                    ),
                )


def get_cross_dag_execution(process_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    process_id,
                    plan_id,
                    user_id,
                    execution_center_id,
                    remote_grpc_target,
                    submit_status,
                    last_status,
                    status_message,
                    create_time,
                    update_time
                FROM cross_dag_execution
                WHERE process_id = %s
                """,
                (process_id,),
            )
            row = cursor.fetchone()
    return dict(row) if row is not None else None


def update_cross_dag_execution_status(
    process_id: str,
    *,
    status: str,
    message: str = "",
) -> None:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE cross_dag_execution
                    SET
                        last_status = %s,
                        status_message = %s,
                        update_time = CURRENT_TIMESTAMP
                    WHERE process_id = %s
                    """,
                    (
                        str(status or "").strip().upper(),
                        str(message or ""),
                        process_id,
                    ),
                )
