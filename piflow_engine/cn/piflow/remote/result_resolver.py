from __future__ import annotations

import json
import mimetypes
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from piflow_engine.cn.piflow.runtime.run_status import RunStatus


class RemoteExecutionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ResultMeta:
    status: str
    file_name: str
    file_size: int
    mime_type: str = ""


class ResultResolver:
    def get_result_meta(
        self,
        *,
        run_id: str,
        result_node_id: str,
        result_output_name: str,
    ) -> ResultMeta:
        resolved = self._resolve(run_id=run_id, result_node_id=result_node_id, result_output_name=result_output_name)
        path = resolved["path"]
        mime_type, _ = mimetypes.guess_type(path.name)
        return ResultMeta(
            status=resolved["status"],
            file_name=path.name,
            file_size=path.stat().st_size,
            mime_type=mime_type or "",
        )

    def open_result_file(
        self,
        *,
        run_id: str,
        result_node_id: str,
        result_output_name: str,
    ):
        resolved = self._resolve(run_id=run_id, result_node_id=result_node_id, result_output_name=result_output_name)
        return resolved["path"].open("rb")

    def _resolve(
        self,
        *,
        run_id: str,
        result_node_id: str,
        result_output_name: str,
    ) -> dict[str, str | Path]:
        if not run_id.strip():
            raise RemoteExecutionError("INVALID_ARGUMENT", "run_id is required")

        from psycopg2.extras import RealDictCursor

        from database.postgres import get_connection

        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if result_node_id.strip():
                    cursor.execute(
                        """
                        SELECT
                            fr.status AS flow_status,
                            sjr.final_output_path,
                            sjr.log_path
                        FROM piflow_flow_run fr
                        LEFT JOIN piflow_stop_job_run sjr
                          ON sjr.flow_run_id = fr.id
                        WHERE fr.process_id = %s
                          AND (
                            sjr.stop_name = %s
                            OR sjr.stop_uuid = %s
                            OR sjr.job_id = %s
                          )
                        ORDER BY sjr.updated_at DESC NULLS LAST, sjr.id DESC
                        LIMIT 1
                        """,
                        (run_id, result_node_id, result_node_id, result_node_id),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT
                            fr.status AS flow_status,
                            sjr.final_output_path,
                            sjr.log_path
                        FROM piflow_flow_run fr
                        LEFT JOIN piflow_stop_job_run sjr
                          ON sjr.flow_run_id = fr.id
                        WHERE fr.process_id = %s
                        ORDER BY sjr.updated_at DESC NULLS LAST, sjr.id DESC
                        LIMIT 1
                        """,
                        (run_id,),
                    )
                row = cursor.fetchone()

                if row is None:
                    cursor.execute(
                        """
                        SELECT status
                        FROM piflow_flow_run
                        WHERE process_id = %s
                        """,
                        (run_id,),
                    )
                    flow_row = cursor.fetchone()
                    if flow_row is None:
                        raise RemoteExecutionError("RUN_NOT_FOUND", f"run not found: {run_id}")
                    raise RemoteExecutionError(
                        "RESULT_NOT_FOUND",
                        f"result not found for node {result_node_id or '<default>'} output {result_output_name or '<default>'}",
                    )

        status = str(row["flow_status"] or "")
        if status != RunStatus.SUCCESS:
            raise RemoteExecutionError("RUN_NOT_FINISHED", f"run {run_id} is not finished successfully: {status}")

        final_output_path = row.get("final_output_path")
        path = self._resolve_result_path(
            final_output_path=final_output_path,
            log_path=row.get("log_path"),
            result_output_name=result_output_name,
        )
        if not path.exists() or not path.is_file():
            raise RemoteExecutionError(
                "RESULT_FILE_NOT_FOUND",
                f"result file not found for node {result_node_id or '<default>'} output {result_output_name or '<default>'}",
            )

        return {
            "status": status,
            "path": path,
        }

    def _resolve_result_path(
        self,
        *,
        final_output_path: str | None,
        log_path: str | None,
        result_output_name: str,
    ) -> Path:
        if final_output_path:
            return Path(str(final_output_path)).expanduser().resolve()

        from_stop_log = self._resolve_path_from_stop_log(
            log_path=log_path,
            result_output_name=result_output_name,
        )
        if from_stop_log is not None:
            return from_stop_log

        raise RemoteExecutionError(
            "RESULT_NOT_FOUND",
            f"result file not recorded for node <default> output {result_output_name or '<default>'}",
        )

    def _resolve_path_from_stop_log(
        self,
        *,
        log_path: str | None,
        result_output_name: str,
    ) -> Path | None:
        if not log_path:
            return None

        resolved_log_path = Path(str(log_path)).expanduser().resolve()
        if not resolved_log_path.exists() or not resolved_log_path.is_file():
            return None

        try:
            lines = resolved_log_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None

        requested_output_name = str(result_output_name or "").strip()
        fallback_path: Path | None = None
        for raw_line in reversed(lines):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if event.get("event") != "STOP_COMPLETED":
                continue
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            outputs = payload.get("outputs")
            if not isinstance(outputs, dict):
                continue

            if requested_output_name:
                path = self._extract_output_file_path(outputs.get(requested_output_name))
                if path is not None:
                    return path

            for output in outputs.values():
                path = self._extract_output_file_path(output)
                if path is not None:
                    fallback_path = path
                    break
            if fallback_path is not None:
                return fallback_path
        return None

    @staticmethod
    def _extract_output_file_path(output: object) -> Path | None:
        if not isinstance(output, dict):
            return None
        path = output.get("path")
        if not path:
            return None
        return Path(str(path)).expanduser().resolve()
