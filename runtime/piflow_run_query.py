from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def _serialize_flow_run_summary(flow_run: dict[str, Any]) -> dict[str, Any]:
    dag_task_id = flow_run.get("flow_uuid")
    return {
        "process_id": flow_run["process_id"],
        "dag_task_id": dag_task_id,
        "flow_uuid": dag_task_id,
        "flow_name": flow_run.get("flow_name"),
        "status": flow_run.get("status"),
        "progress": float(flow_run["progress"]) if flow_run.get("progress") is not None else None,
        "total_stop_count": flow_run.get("total_stop_count", 0),
        "success_stop_count": flow_run.get("success_stop_count", 0),
        "failed_stop_count": flow_run.get("failed_stop_count", 0),
        "skipped_stop_count": flow_run.get("skipped_stop_count", 0),
        "error_message": flow_run.get("error_message"),
        "started_at": flow_run.get("started_at"),
        "finished_at": flow_run.get("finished_at"),
        "created_at": flow_run.get("created_at"),
        "updated_at": flow_run.get("updated_at"),
    }


def _build_flow_run_filters(
    *,
    dag_task_id: str | None = None,
    status: str | None = None,
    running_only: bool | None = None,
    keyword: str | None = None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    if dag_task_id:
        conditions.append("flow_uuid = %s")
        params.append(dag_task_id)

    if status:
        conditions.append("status = %s")
        params.append(status)

    if running_only:
        conditions.append("finished_at IS NULL")

    if keyword:
        like_value = f"%{keyword}%"
        conditions.append("(process_id ILIKE %s OR flow_name ILIKE %s OR flow_uuid ILIKE %s)")
        params.extend([like_value, like_value, like_value])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where_clause, params


def get_piflow_run_detail(process_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    process_id,
                    flow_uuid,
                    flow_name,
                    status,
                    progress,
                    total_stop_count,
                    success_stop_count,
                    failed_stop_count,
                    skipped_stop_count,
                    workspace_path,
                    log_path,
                    error_message,
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                FROM piflow_flow_run
                WHERE process_id = %s
                """,
                (process_id,),
            )
            flow_run = cursor.fetchone()
            if flow_run is None:
                return None

            cursor.execute(
                """
                SELECT
                    job_id,
                    stop_name,
                    stop_uuid,
                    bundle,
                    status,
                    input_ports,
                    output_ports,
                    workspace_path,
                    log_path,
                    stdout_log_path,
                    stderr_log_path,
                    final_output_path,
                    error_message,
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                FROM piflow_stop_job_run
                WHERE flow_run_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (flow_run["id"],),
            )
            stop_runs = cursor.fetchall()

    final_output_paths = [
        str(row["final_output_path"])
        for row in stop_runs
        if row.get("final_output_path")
    ]

    return {
        "process_id": flow_run["process_id"],
        "dag_task_id": flow_run.get("flow_uuid"),
        "flow_uuid": flow_run.get("flow_uuid"),
        "flow_name": flow_run["flow_name"],
        "status": flow_run["status"],
        "progress": float(flow_run["progress"]) if flow_run.get("progress") is not None else None,
        "total_stop_count": flow_run.get("total_stop_count", 0),
        "success_stop_count": flow_run.get("success_stop_count", 0),
        "failed_stop_count": flow_run.get("failed_stop_count", 0),
        "skipped_stop_count": flow_run.get("skipped_stop_count", 0),
        "workspace_path": flow_run.get("workspace_path"),
        "log_path": flow_run.get("log_path"),
        "error_message": flow_run.get("error_message"),
        "started_at": flow_run.get("started_at"),
        "finished_at": flow_run.get("finished_at"),
        "created_at": flow_run.get("created_at"),
        "updated_at": flow_run.get("updated_at"),
        "final_output_paths": final_output_paths,
        "stops": [
            {
                "job_id": row["job_id"],
                "stop_name": row["stop_name"],
                "stop_uuid": row.get("stop_uuid"),
                "bundle": row.get("bundle"),
                "status": row["status"],
                "input_ports": row.get("input_ports") or [],
                "output_ports": row.get("output_ports") or [],
                "workspace_path": row.get("workspace_path"),
                "log_path": row.get("log_path"),
                "stdout_log_path": row.get("stdout_log_path"),
                "stderr_log_path": row.get("stderr_log_path"),
                "final_output_path": row.get("final_output_path"),
                "error_message": row.get("error_message"),
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in stop_runs
        ],
    }


def get_piflow_run_progress(process_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    process_id,
                    flow_uuid,
                    flow_name,
                    status,
                    progress,
                    total_stop_count,
                    success_stop_count,
                    failed_stop_count,
                    skipped_stop_count,
                    error_message,
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                FROM piflow_flow_run
                WHERE process_id = %s
                """,
                (process_id,),
            )
            flow_run = cursor.fetchone()

    if flow_run is None:
        return None

    return _serialize_flow_run_summary(flow_run)


def get_piflow_stop_log_paths_by_job_id(job_id: str) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    fr.process_id,
                    fr.flow_uuid,
                    sjr.job_id,
                    sjr.stop_name,
                    sjr.log_path,
                    sjr.stdout_log_path,
                    sjr.stderr_log_path
                FROM piflow_stop_job_run sjr
                JOIN piflow_flow_run fr
                  ON sjr.flow_run_id = fr.id
                WHERE sjr.job_id = %s
                """,
                (job_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "process_id": row.get("process_id"),
        "dag_task_id": row.get("flow_uuid"),
        "flow_uuid": row.get("flow_uuid"),
        "job_id": row.get("job_id"),
        "stop_name": row.get("stop_name"),
        "log_path": row.get("log_path"),
        "stdout_log_path": row.get("stdout_log_path"),
        "stderr_log_path": row.get("stderr_log_path"),
    }


def list_piflow_runs_by_task_id(
    dag_task_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    where_clause, params = _build_flow_run_filters(
        dag_task_id=dag_task_id,
        status=status,
    )
    offset = (page - 1) * page_size

    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM piflow_flow_run
                {where_clause}
                """,
                params,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    process_id,
                    flow_uuid,
                    flow_name,
                    status,
                    progress,
                    total_stop_count,
                    success_stop_count,
                    failed_stop_count,
                    skipped_stop_count,
                    error_message,
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                FROM piflow_flow_run
                {where_clause}
                ORDER BY created_at DESC, process_id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            rows = cursor.fetchall()

    return {
        "dag_task_id": dag_task_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [_serialize_flow_run_summary(row) for row in rows],
    }


def list_piflow_processes(
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    dag_task_id: str | None = None,
    running_only: bool | None = None,
    keyword: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            conditions: list[str] = []
            params: list[Any] = []

            if user_id:
                base_from = """
                FROM piflow_flow_run fr
                JOIN dag_task dt
                  ON dt.dag_task_id = fr.flow_uuid
                 AND dt.create_user_id = %s
                 AND dt.is_deleted = 0
                """
                params.append(user_id)
            else:
                base_from = "FROM piflow_flow_run fr"

            if dag_task_id:
                conditions.append("fr.flow_uuid = %s")
                params.append(dag_task_id)

            if status:
                conditions.append("fr.status = %s")
                params.append(status)

            if running_only:
                conditions.append("fr.finished_at IS NULL")

            if keyword:
                like_value = f"%{keyword}%"
                conditions.append("(fr.process_id ILIKE %s OR fr.flow_name ILIKE %s OR fr.flow_uuid ILIKE %s)")
                params.extend([like_value, like_value, like_value])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            offset = (page - 1) * page_size

            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                {base_from}
                {where_clause}
                """,
                params,
            )
            total = cursor.fetchone()["total"]

            cursor.execute(
                f"""
                SELECT
                    fr.process_id,
                    fr.flow_uuid,
                    fr.flow_name,
                    fr.status,
                    fr.progress,
                    fr.total_stop_count,
                    fr.success_stop_count,
                    fr.failed_stop_count,
                    fr.skipped_stop_count,
                    fr.error_message,
                    fr.started_at,
                    fr.finished_at,
                    fr.created_at,
                    fr.updated_at
                {base_from}
                {where_clause}
                ORDER BY fr.created_at DESC, fr.process_id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, page_size, offset],
            )
            rows = cursor.fetchall()

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [_serialize_flow_run_summary(row) for row in rows],
    }


def get_piflow_process_status_counts(
    *,
    dag_task_id: str | None = None,
    keyword: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            conditions: list[str] = []
            params: list[Any] = []

            if user_id:
                base_from = """
                FROM piflow_flow_run fr
                JOIN dag_task dt
                  ON dt.dag_task_id = fr.flow_uuid
                 AND dt.create_user_id = %s
                 AND dt.is_deleted = 0
                """
                params.append(user_id)
            else:
                base_from = "FROM piflow_flow_run fr"

            if dag_task_id:
                conditions.append("fr.flow_uuid = %s")
                params.append(dag_task_id)

            if keyword:
                like_value = f"%{keyword}%"
                conditions.append("(fr.process_id ILIKE %s OR fr.flow_name ILIKE %s OR fr.flow_uuid ILIKE %s)")
                params.extend([like_value, like_value, like_value])

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE status IN ('PENDING', 'RUNNING')) AS running_count,
                    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS completed_count,
                    COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_count
                {base_from}
                {where_clause}
                """,
                params,
            )
            row = cursor.fetchone()

    return {
        "dag_task_id": dag_task_id,
        "keyword": keyword,
        "total": row.get("total", 0) if row else 0,
        "running_count": row.get("running_count", 0) if row else 0,
        "completed_count": row.get("completed_count", 0) if row else 0,
        "failed_count": row.get("failed_count", 0) if row else 0,
    }
