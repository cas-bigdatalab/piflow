from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RunStore(ABC):
    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...
