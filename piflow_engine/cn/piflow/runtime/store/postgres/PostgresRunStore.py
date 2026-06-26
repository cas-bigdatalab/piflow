from __future__ import annotations

import json
from typing import Any

from piflow_engine.cn.piflow.runtime.logging import get_logger
from piflow_engine.cn.piflow.runtime.run_store import RunStore
from piflow_engine.cn.piflow.runtime.store.postgres.PostgresConfig import PostgresConfig


class PostgresRunStore(RunStore):
    def __init__(self, connection=None, config: PostgresConfig | None = None):
        self._connection = connection or (config or PostgresConfig.from_env()).connect()
        self._logger = get_logger(__name__)

    def create_flow_run(
        self,
        *,
        process_id: str,
        flow_uuid: str,
        flow_name: str,
        status: str,
        total_stop_count: int,
        workspace_path: str,
        log_path: str = "",
    ) -> Any:
        sql = """
        INSERT INTO piflow_flow_run (
            process_id, flow_uuid, flow_name, status, progress,
            total_stop_count, workspace_path, log_path, started_at
        )
        VALUES (%s, %s, %s, %s, 0, %s, %s, %s, NULL)
        ON CONFLICT (process_id) DO UPDATE SET
            flow_uuid = EXCLUDED.flow_uuid,
            flow_name = EXCLUDED.flow_name,
            status = EXCLUDED.status,
            progress = EXCLUDED.progress,
            total_stop_count = EXCLUDED.total_stop_count,
            workspace_path = EXCLUDED.workspace_path,
            log_path = EXCLUDED.log_path,
            started_at = CASE
                WHEN EXCLUDED.status = 'RUNNING'
                THEN COALESCE(piflow_flow_run.started_at, now())
                ELSE piflow_flow_run.started_at
            END,
            finished_at = NULL,
            error_message = NULL
        RETURNING id
        """
        return self._fetch_one(
            sql,
            (
                process_id,
                flow_uuid,
                flow_name,
                status,
                total_stop_count,
                workspace_path,
                log_path,
            ),
        )[0]

    def update_flow_run(
        self,
        *,
        process_id: str,
        status: str | None = None,
        progress: float | None = None,
        success_stop_count: int | None = None,
        failed_stop_count: int | None = None,
        skipped_stop_count: int | None = None,
        error_message: str | None = None,
        finished: bool = False,
    ) -> None:
        assignments: list[str] = []
        params: list[Any] = []

        _add(assignments, params, "status", status)
        _add(assignments, params, "progress", progress)
        _add(assignments, params, "success_stop_count", success_stop_count)
        _add(assignments, params, "failed_stop_count", failed_stop_count)
        _add(assignments, params, "skipped_stop_count", skipped_stop_count)
        _add(assignments, params, "error_message", error_message)

        if finished:
            assignments.append("finished_at = now()")
        if status == "RUNNING":
            assignments.append("started_at = COALESCE(started_at, now())")

        if not assignments:
            return

        params.append(process_id)
        self._execute(
            f"UPDATE piflow_flow_run SET {', '.join(assignments)} WHERE process_id = %s",
            tuple(params),
        )

    def create_stop_job_run(
        self,
        *,
        process_id: str,
        job_id: str,
        stop_name: str,
        status: str,
        stop_uuid: str = "",
        bundle: str = "",
        workspace_path: str = "",
        log_path: str = "",
        stdout_log_path: str = "",
        stderr_log_path: str = "",
        final_output_path: str = "",
    ) -> Any:
        sql = """
        INSERT INTO piflow_stop_job_run (
            flow_run_id, job_id, stop_name, stop_uuid, bundle,
            status, workspace_path, log_path, stdout_log_path, stderr_log_path,
            final_output_path
        )
        SELECT id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        FROM piflow_flow_run
        WHERE process_id = %s
        ON CONFLICT (flow_run_id, job_id) DO UPDATE SET
            stop_name = EXCLUDED.stop_name,
            stop_uuid = EXCLUDED.stop_uuid,
            bundle = EXCLUDED.bundle,
            status = EXCLUDED.status,
            workspace_path = EXCLUDED.workspace_path,
            log_path = EXCLUDED.log_path,
            stdout_log_path = EXCLUDED.stdout_log_path,
            stderr_log_path = EXCLUDED.stderr_log_path,
            final_output_path = EXCLUDED.final_output_path,
            error_message = NULL
        RETURNING id
        """
        return self._fetch_one(
            sql,
            (
                job_id,
                stop_name,
                stop_uuid,
                bundle,
                status,
                workspace_path,
                log_path,
                stdout_log_path,
                stderr_log_path,
                final_output_path,
                process_id,
            ),
        )[0]

    def update_stop_job_run(
        self,
        *,
        process_id: str,
        job_id: str,
        status: str,
        input_ports: list[str] | None = None,
        output_ports: list[str] | None = None,
        stdout_log_path: str | None = None,
        stderr_log_path: str | None = None,
        final_output_path: str | None = None,
        error_message: str | None = None,
        finished: bool = False,
    ) -> None:
        assignments = ["status = %s"]
        params: list[Any] = [status]

        if input_ports is not None:
            assignments.append("input_ports = %s::jsonb")
            params.append(json.dumps(input_ports, ensure_ascii=False))
        if output_ports is not None:
            assignments.append("output_ports = %s::jsonb")
            params.append(json.dumps(output_ports, ensure_ascii=False))
        if stdout_log_path is not None:
            assignments.append("stdout_log_path = %s")
            params.append(stdout_log_path)
        if stderr_log_path is not None:
            assignments.append("stderr_log_path = %s")
            params.append(stderr_log_path)
        if final_output_path is not None:
            assignments.append("final_output_path = %s")
            params.append(final_output_path)
        if error_message is not None:
            assignments.append("error_message = %s")
            params.append(error_message)
        if status == "RUNNING":
            assignments.append("started_at = COALESCE(started_at, now())")
        if finished:
            assignments.append("finished_at = now()")

        params.extend([job_id, process_id])
        sql = f"""
        UPDATE piflow_stop_job_run
        SET {', '.join(assignments)}
        WHERE job_id = %s
          AND flow_run_id = (
              SELECT id FROM piflow_flow_run WHERE process_id = %s
          )
        """
        self._execute(sql, tuple(params))

    def close(self) -> None:
        self._connection.close()

    def _execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
        self._connection.commit()

    def _fetch_one(self, sql: str, params: tuple[Any, ...]):
        with self._connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        self._connection.commit()
        if row is None:
            raise RuntimeError("postgres run store query returned no row")
        return row


def _add(
    assignments: list[str],
    params: list[Any],
    column: str,
    value: Any,
) -> None:
    if value is not None:
        assignments.append(f"{column} = %s")
        params.append(value)
