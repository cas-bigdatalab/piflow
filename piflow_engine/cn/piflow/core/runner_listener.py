from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext


class RunnerListener(ABC):

    def on_process_submitted(self, ctx: "ProcessContext") -> None:
        ...

    @abstractmethod
    def on_process_started(self, ctx: "ProcessContext") -> None:
        ...

    @abstractmethod
    def on_process_completed(self, ctx: "ProcessContext") -> None:
        ...

    @abstractmethod
    def on_process_failed(self, ctx: "ProcessContext", error: Exception) -> None:
        ...

    @abstractmethod
    def on_process_aborted(self, ctx: "ProcessContext") -> None:
        ...

    @abstractmethod
    def on_job_initialized(self, ctx: "JobContext") -> None:
        ...

    @abstractmethod
    def on_job_started(self, ctx: "JobContext") -> None:
        ...

    @abstractmethod
    def on_job_completed(self, ctx: "JobContext") -> None:
        ...

    @abstractmethod
    def on_job_failed(self, ctx: "JobContext", error: Exception) -> None:
        ...
