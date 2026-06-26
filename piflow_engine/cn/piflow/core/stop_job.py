from __future__ import annotations

from abc import ABC, abstractmethod
import uuid

from piflow_engine.cn.piflow.core.runtime_context import ProcessContext, JobContextImpl
from piflow_engine.cn.piflow.core.stream_impl import JobInputStreamImpl, JobOutputStreamImpl
from piflow_engine.cn.piflow.core.stop import Stop
from piflow_engine.cn.piflow.runtime.logging import get_logger


class StopJob(ABC):
    """
    Runtime wrapper of one stop execution.
    """

    @abstractmethod
    def jid(self) -> str:
        ...

    @abstractmethod
    def get_stop_name(self) -> str:
        ...

    @abstractmethod
    def get_stop(self) -> Stop:
        ...

class StopJobImpl(StopJob):
    def __init__(self, stop_name: str, stop: Stop, process_context: ProcessContext):
        self._id = f"job_{uuid.uuid4().hex}"
        self._stop_name = stop_name
        self._stop = stop
        self._context = JobContextImpl(self, process_context)

    def jid(self) -> str:
        return self._id

    def get_stop_name(self) -> str:
        return self._stop_name

    def get_stop(self) -> Stop:
        return self._stop

    def get_context(self) -> JobContextImpl:
        return self._context

    def attach_inputs(self, inputs: dict[str, object]) -> None:
        input_stream = self._context.get_input_stream()
        if isinstance(input_stream, JobInputStreamImpl):
            input_stream.attach(inputs)

    def perform(self, inputs: dict[str, object]) -> JobOutputStreamImpl:
        self.attach_inputs(inputs)
        input_stream = self._context.get_input_stream()
        input_ports = (
            input_stream.ports() if isinstance(input_stream, JobInputStreamImpl) else []
        )
        get_logger(__name__).info(
            "executing stop=%s input_ports=%s",
            self._stop_name,
            input_ports,
        )
        self._stop.perform(
            self._context.get_input_stream(),
            self._context.get_output_stream(),
            self._context,
        )
        return self._context.get_output_stream()  # type: ignore[return-value]
