from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from piflow_engine.cn.piflow.core.context import Context, CascadeContext
from piflow_engine.cn.piflow.core.stream_impl import JobInputStreamImpl, JobOutputStreamImpl

if TYPE_CHECKING:
    from piflow_engine.cn.piflow.core.flow import Flow
    from piflow_engine.cn.piflow.core.process import Process
    from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
    from piflow_engine.cn.piflow.core.stop_job import StopJob


class ProcessContext(Context, ABC):

    @abstractmethod
    def get_flow(self) -> "Flow":
        ...

    @abstractmethod
    def get_process(self) -> "Process":
        ...


class JobContext(Context, ABC):

    @abstractmethod
    def get_stop_job(self) -> "StopJob":
        ...

    @abstractmethod
    def get_input_stream(self) -> "JobInputStream":
        ...

    @abstractmethod
    def get_output_stream(self) -> "JobOutputStream":
        ...

    @abstractmethod
    def get_process_context(self) -> ProcessContext:
        ...


class JobContextImpl(CascadeContext, JobContext):
    def __init__(self, stop_job: StopJob, process_context: ProcessContext):
        super().__init__(process_context)
        self._stop_job = stop_job
        self._process_context = process_context
        self._input_stream: JobInputStream = JobInputStreamImpl()
        self._output_stream: JobOutputStream = JobOutputStreamImpl()

    def get_stop_job(self) -> StopJob:
        return self._stop_job

    def get_input_stream(self) -> JobInputStream:
        return self._input_stream

    def get_output_stream(self) -> JobOutputStream:
        return self._output_stream

    def get_process_context(self) -> ProcessContext:
        return self._process_context


class ProcessContextImpl(CascadeContext, ProcessContext):
    def __init__(self, flow: "Flow", process: "Process", parent: Context | None = None):
        super().__init__(parent)
        self._flow = flow
        self._process = process

    def get_flow(self) -> "Flow":
        return self._flow

    def get_process(self) -> "Process":
        return self._process
