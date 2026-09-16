from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def get_definition_for_batch(*, definition_id: str, user_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT definition_id, dag_task_id, definition_json
                FROM dag_definition
                WHERE definition_id = %s AND create_user_id = %s
                """,
                (definition_id, user_id),
            )
            row = cursor.fetchone()
    return dict(row) if row else None


def create_batch(**data: Any) -> None:
    items = data.pop("items")
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO piflow_batch_run (
                        batch_id, user_id, dag_task_id, definition_id,
                        input_dir, output_dir, status, max_parallel,
                        retry_count, stop_on_failure, total_count
                    )
                    VALUES (%(batch_id)s, %(user_id)s, %(dag_task_id)s,
                            %(definition_id)s, %(input_dir)s, %(output_dir)s,
                            'PENDING', %(max_parallel)s, %(retry_count)s,
                            %(stop_on_failure)s, %(total_count)s)
                    """,
                    {**data, "total_count": len(items)},
                )
                cursor.executemany(
                    """
                    INSERT INTO piflow_batch_item_run (
                        batch_run_id, item_index, input_name, input_path,
                        output_path, status
                    )
                    SELECT id, %s, %s, %s, %s, 'PENDING'
                    FROM piflow_batch_run WHERE batch_id = %s
                    """,
                    [
                        (
                            item["item_index"], item["input_name"],
                            item["input_path"], item["output_path"],
                            data["batch_id"],
                        )
                        for item in items
                    ],
                )


def update_batch(batch_id: str, **fields: Any) -> None:
    allowed = {
        "status", "submitted_count", "completed_count", "failed_count",
        "skipped_count", "error_message", "started_at", "finished_at",
    }
    fields = {key: value for key, value in fields.items() if key in allowed}
    if not fields:
        return
    assignments = ", ".join(f"{key} = %s" for key in fields)
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE piflow_batch_run SET {assignments} WHERE batch_id = %s",
                    (*fields.values(), batch_id),
                )


def update_batch_item(batch_id: str, item_index: int, **fields: Any) -> None:
    allowed = {"process_id", "status", "attempts", "error_message"}
    fields = {key: value for key, value in fields.items() if key in allowed}
    if not fields:
        return
    assignments = ", ".join(f"{key} = %s" for key in fields)
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE piflow_batch_item_run SET {assignments}
                    WHERE item_index = %s AND batch_run_id = (
                        SELECT id FROM piflow_batch_run WHERE batch_id = %s
                    )
                    """,
                    (*fields.values(), item_index, batch_id),
                )


def get_batch(batch_id: str, user_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM piflow_batch_run WHERE batch_id = %s AND user_id = %s",
                (batch_id, user_id),
            )
            batch = cursor.fetchone()
            if batch is None:
                return None
            cursor.execute(
                """
                SELECT item_index, input_name, input_path, output_path,
                       process_id, status, attempts, error_message,
                       started_at, finished_at, created_at, updated_at
                FROM piflow_batch_item_run
                WHERE batch_run_id = %s ORDER BY item_index
                """,
                (batch["id"],),
            )
            items = cursor.fetchall()
    result = dict(batch)
    result.pop("id", None)
    result["items"] = [dict(item) for item in items]
    return result
