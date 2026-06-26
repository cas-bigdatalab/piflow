from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RunLogger:
    """
    Writes flow and stop runtime logs as JSON lines under a process workspace.
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root).resolve()

    def log_flow_event(
        self,
        process_id: str,
        event: str,
        *,
        level: str = "INFO",
        message: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        record = self._record(
            event=event,
            level=level,
            message=message,
            process_id=process_id,
            payload=payload,
        )
        self._append_json_line(self.flow_log_path(process_id), record)

    def log_stop_event(
        self,
        process_id: str,
        stop_name: str,
        event: str,
        *,
        job_id: str = "",
        level: str = "INFO",
        message: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        record = self._record(
            event=event,
            level=level,
            message=message,
            process_id=process_id,
            job_id=job_id,
            stop_name=stop_name,
            payload=payload,
        )
        self._append_json_line(self.stop_log_path(process_id, stop_name), record)

    def flow_log_path(self, process_id: str) -> Path:
        return self.workspace_root / process_id / "flow.log"

    def stop_log_path(self, process_id: str, stop_name: str) -> Path:
        return self.workspace_root / process_id / "stops" / _safe_name(stop_name) / "job.log"

    def _record(
        self,
        *,
        event: str,
        level: str,
        message: str,
        process_id: str,
        payload: dict[str, Any] | None = None,
        job_id: str = "",
        stop_name: str = "",
    ) -> dict[str, Any]:
        return {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            "message": message,
            "process_id": process_id,
            "job_id": job_id,
            "stop_name": stop_name,
            "payload": payload or {},
        }

    def _append_json_line(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _safe_name(value: str) -> str:
    return value.replace("/", "_").replace("\\", "_").replace(" ", "_")
