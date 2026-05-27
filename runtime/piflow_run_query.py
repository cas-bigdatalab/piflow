from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


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

    return {
        "process_id": flow_run["process_id"],
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
                "error_message": row.get("error_message"),
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in stop_runs
        ],
    }
