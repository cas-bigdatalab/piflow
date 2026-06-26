from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from piflow_engine.cn.piflow.core.context import CascadeContext, Context
from piflow_engine.cn.piflow.core.flow import Flow
from piflow_engine.cn.piflow.core.process import Process
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner_listener import RunnerListener


class CompositeRunnerListener(RunnerListener):
    """
    Dispatch lifecycle events to all registered listeners.
    """

    def __init__(self, listeners: list[RunnerListener]):
        self._listeners = listeners

    def on_process_submitted(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_process_submitted(ctx)

    def on_process_started(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_process_started(ctx)

    def on_process_completed(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_process_completed(ctx)

    def on_process_failed(self, ctx, error: Exception) -> None:
        for listener in self._listeners:
            listener.on_process_failed(ctx, error)

    def on_process_aborted(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_process_aborted(ctx)

    def on_job_initialized(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_job_initialized(ctx)

    def on_job_started(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_job_started(ctx)

    def on_job_completed(self, ctx) -> None:
        for listener in self._listeners:
            listener.on_job_completed(ctx)

    def on_job_failed(self, ctx, error: Exception) -> None:
        for listener in self._listeners:
            listener.on_job_failed(ctx, error)


@dataclass
class Runner:

    context: Context = field(default_factory=CascadeContext)
    listeners: list[RunnerListener] = field(default_factory=list)

    def bind(self, key: str, value: Any) -> "Runner":
        self.context.put(key, value)
        return self

    def start(self, flow: Flow) -> Process:
        process = ProcessImpl(flow, self.context, self)
        process.start()
        return process

    def add_listener(self, listener: RunnerListener) -> None:
        self.listeners.append(listener)

    def remove_listener(self, listener: RunnerListener) -> None:
        self.listeners.remove(listener)

    def get_listener(self) -> RunnerListener:
        return CompositeRunnerListener(self.listeners)

    @classmethod
    def create(cls) -> "Runner":
        return cls()
