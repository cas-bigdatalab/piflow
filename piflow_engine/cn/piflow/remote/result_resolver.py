from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
import zipfile
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from piflow_engine.cn.piflow.runtime.logging import get_logger
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
        resolved = self._resolve(
            run_id=run_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
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
        resolved = self._resolve(
            run_id=run_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
        return resolved["path"].open("rb")

    def _resolve(
        self,
        *,
        run_id: str,
        result_node_id: str,
        result_output_name: str,
    ) -> dict[str, str | Path]:
        run_id = str(run_id or "").strip()
        result_node_id = str(result_node_id or "").strip()
        result_output_name = str(result_output_name or "").strip()
        if not run_id:
            raise RemoteExecutionError("INVALID_ARGUMENT", "run_id is required")

        logger.debug(
            "resolve result request: run_id=%s result_node_id=%s result_output_name=%s",
            run_id,
            result_node_id or "<default>",
            result_output_name or "<default>",
        )
        row = self._find_result_row(
            run_id=run_id,
            result_node_id=result_node_id,
        )
        if row is None:
            self._raise_missing_result(
                run_id=run_id,
                result_node_id=result_node_id,
                result_output_name=result_output_name,
            )

        status = str(row.get("flow_status") or "")
        if status != RunStatus.SUCCESS:
            raise RemoteExecutionError(
                "RUN_NOT_FINISHED",
                f"run {run_id} is not finished successfully: {status}",
            )

        if result_node_id:
            path = self._resolve_node_result_path(
                row=row,
                result_output_name=result_output_name,
            )
        else:
            final_output_path = str(row.get("final_output_path") or "").strip()
            if not final_output_path:
                raise RemoteExecutionError(
                    "RESULT_NOT_FOUND",
                    f"result file not recorded for run {run_id}",
                )
            path = Path(final_output_path).expanduser().resolve()

        logger.debug(
            "resolved result path before materialization: run_id=%s "
            "result_node_id=%s result_output_name=%s path=%s exists=%s "
            "is_file=%s is_dir=%s",
            run_id,
            result_node_id or "<default>",
            result_output_name or "<default>",
            path,
            path.exists(),
            path.is_file(),
            path.is_dir(),
        )
        if not path.exists():
            raise RemoteExecutionError(
                "RESULT_FILE_NOT_FOUND",
                f"result path not found for node "
                f"{result_node_id or '<default>'} output "
                f"{result_output_name or '<default>'}: {path}",
            )

        if path.is_dir():
            stop_workspace_path = str(row.get("stop_workspace_path") or "").strip()
            archive_root = (
                Path(stop_workspace_path).expanduser().resolve()
                if stop_workspace_path
                else path.parent
            )
            path = self._archive_result_directory(
                path,
                temp_root=archive_root / "temp",
            )
            logger.info(
                "directory result archived for download: run_id=%s "
                "result_node_id=%s result_output_name=%s archive_path=%s",
                run_id,
                result_node_id or "<default>",
                result_output_name or "<default>",
                path,
            )

        if not path.is_file():
            raise RemoteExecutionError(
                "RESULT_FILE_NOT_FOUND",
                f"result path is not a regular file for node "
                f"{result_node_id or '<default>'} output "
                f"{result_output_name or '<default>'}: {path}",
            )

        return {"status": status, "path": path}

    def _find_result_row(
        self,
        *,
        run_id: str,
        result_node_id: str,
    ) -> dict | None:
        from psycopg2.extras import RealDictCursor

        from database.postgres import get_connection

        if result_node_id:
            node_condition = "AND sjr.stop_uuid = %s"
            params = (run_id, result_node_id)
        else:
            node_condition = """
                AND sjr.final_output_path IS NOT NULL
                AND sjr.final_output_path <> ''
            """
            params = (run_id,)

        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    f"""
                    SELECT
                        fr.status AS flow_status,
                        sjr.status AS stop_status,
                        sjr.stop_name,
                        sjr.stop_uuid,
                        sjr.job_id,
                        sjr.final_output_path,
                        sjr.stop_workspace_path,
                        sjr.updated_at
                    FROM piflow_flow_run fr
                    JOIN piflow_stop_job_run sjr
                      ON sjr.flow_run_id = fr.id
                    WHERE fr.process_id = %s
                      {node_condition}
                    ORDER BY sjr.updated_at DESC NULLS LAST, sjr.id DESC
                    LIMIT 1
                    """,
                    params,
                )
                row = cursor.fetchone()
        if row is not None:
            logger.debug(
                "result database row matched: run_id=%s flow_status=%s "
                "stop_status=%s stop_name=%s stop_uuid=%s job_id=%s "
                "final_output_path=%s stop_workspace_path=%s updated_at=%s",
                run_id,
                row.get("flow_status", ""),
                row.get("stop_status", ""),
                row.get("stop_name", ""),
                row.get("stop_uuid", ""),
                row.get("job_id", ""),
                row.get("final_output_path", ""),
                row.get("stop_workspace_path", ""),
                row.get("updated_at", ""),
            )
        return row

    def _raise_missing_result(
        self,
        *,
        run_id: str,
        result_node_id: str,
        result_output_name: str,
    ) -> None:
        from psycopg2.extras import RealDictCursor

        from database.postgres import get_connection

        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            f"result not found for node {result_node_id or '<default>'} "
            f"output {result_output_name or '<default>'}",
        )

    def _resolve_node_result_path(
        self,
        *,
        row: dict,
        result_output_name: str,
    ) -> Path:
        stop_workspace_path = str(row.get("stop_workspace_path") or "").strip()
        if not stop_workspace_path:
            raise RemoteExecutionError(
                "RESULT_NOT_FOUND",
                f"stop workspace path is not recorded for node "
                f"{row.get('stop_uuid') or row.get('stop_name') or '<unknown>'}",
            )

        stop_workspace = Path(stop_workspace_path).expanduser().resolve()
        output_root = (stop_workspace / "output").resolve()
        if result_output_name:
            relative_path = Path(result_output_name)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise RemoteExecutionError(
                    "INVALID_ARGUMENT",
                    "result_output_name must be a relative path inside output",
                )
            path = (output_root / relative_path).resolve()
        else:
            path = output_root

        try:
            path.relative_to(output_root)
        except ValueError as exc:
            raise RemoteExecutionError(
                "INVALID_ARGUMENT",
                "result_output_name must stay inside output",
            ) from exc
        return path

    def _archive_result_directory(
        self,
        directory: Path,
        *,
        temp_root: Path | None = None,
    ) -> Path:
        """Create a stable ZIP outside the directory being archived."""

        directory = directory.expanduser().resolve()
        archive_root = (temp_root or directory.parent / "temp").expanduser().resolve()
        if archive_root == directory or directory in archive_root.parents:
            raise RemoteExecutionError(
                "RESULT_ARCHIVE_ERROR",
                f"archive directory must be outside result directory: {archive_root}",
            )
        archive_root.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256(str(directory).encode("utf-8")).hexdigest()[:16]
        archive_path = archive_root / f"result_{digest}.zip"
        if archive_path.is_file():
            return archive_path

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".result_{digest}.",
            suffix=".tmp",
            dir=str(archive_root),
        )
        os.close(fd)
        temporary_path = Path(temporary_name)
        try:
            with zipfile.ZipFile(
                temporary_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                for child in sorted(directory.rglob("*")):
                    if child.is_file():
                        archive.write(
                            child,
                            arcname=child.relative_to(directory),
                        )
            os.replace(temporary_path, archive_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
        return archive_path


logger = get_logger(__name__)
