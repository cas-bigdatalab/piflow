from __future__ import annotations

import threading
import uuid
from collections import deque
from typing import TYPE_CHECKING

from piflow_engine.cn.piflow.core.artifact import Artifact
from piflow_engine.cn.piflow.core.context import Context
from piflow_engine.cn.piflow.core.flow import Flow
from piflow_engine.cn.piflow.core.path import Edge
from piflow_engine.cn.piflow.core.process import Process
from piflow_engine.cn.piflow.core.runtime_context import ProcessContextImpl
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.core.stream_impl import JobOutputStreamImpl

if TYPE_CHECKING:
    from piflow_engine.cn.piflow.core.runner import Runner


class ProcessImpl(Process):
    def __init__(self, flow: Flow, runner_context: Context, runner: Runner):
        self._id = f"process_{uuid.uuid4().hex}"
        self._flow = flow
        self._runner = runner
        self._runner_context = runner_context
        self._listener = runner.get_listener()
        self._stopped = False
        self._done = threading.Event()
        self._error: Exception | None = None
        self._thread: threading.Thread | None = None
        self._start_lock = threading.Lock()
        self._process_context = ProcessContextImpl(flow, self, runner_context)
        self._job_outputs: dict[str, JobOutputStreamImpl] = {}

        self._listener.on_process_submitted(self._process_context)

    def pid(self) -> str:
        return self._id

    def start(self) -> None:
        with self._start_lock:
            if self._thread is not None:
                return
            self._thread = threading.Thread(
                target=self._execute,
                name=f"piflow-{self._id}",
                daemon=True,
            )
            self._thread.start()

    def await_termination(self, timeout: float | None = None) -> None:
        completed = self._done.wait(timeout)
        if not completed:
            raise TimeoutError(f"process {self._id} did not finish within timeout")
        if self._error is not None:
            raise self._error

    def get_flow(self) -> Flow:
        return self._flow

    def stop(self) -> None:
        self._stopped = True
        self._listener.on_process_aborted(self._process_context)
        self._done.set()

    def _execute(self) -> None:
        self._listener.on_process_started(self._process_context)
        try:
            jobs = self._create_jobs()
            execution_order = self._topological_sort()

            for stop_name in execution_order:
                if self._stopped:
                    return

                stop_job = jobs[stop_name]
                job_context = stop_job.get_context()

                try:
                    inputs = self._build_inputs(stop_name)
                    stop_job.attach_inputs(inputs)
                    self._listener.on_job_started(job_context)
                    outputs = stop_job.perform(inputs)
                    self._job_outputs[stop_name] = outputs
                    self._listener.on_job_completed(job_context)
                except Exception as error:
                    self._listener.on_job_failed(job_context, error)
                    raise

            self._listener.on_process_completed(self._process_context)
        except Exception as error:
            self._error = error
            self._listener.on_process_failed(self._process_context, error)
        finally:
            self._done.set()

    def _create_jobs(self) -> dict[str, StopJobImpl]:
        jobs: dict[str, StopJobImpl] = {}
        for stop_id in self._flow.get_stop_names():
            stop = self._flow.get_stop(stop_id)
            stop.initialize(self._process_context)
            stop_name = str(getattr(stop, "piflow_stop_name", stop_id))
            stop_job = StopJobImpl(stop_name, stop, self._process_context)
            jobs[stop_id] = stop_job
            self._listener.on_job_initialized(stop_job.get_context())
        return jobs

    def _topological_sort(self) -> list[str]:
        incoming_count: dict[str, int] = {
            stop_name: 0 for stop_name in self._flow.get_stop_names()
        }
        outgoing: dict[str, list[str]] = {
            stop_name: [] for stop_name in self._flow.get_stop_names()
        }

        for edge in self._flow.edges:
            incoming_count[edge.stop_to] += 1
            outgoing[edge.stop_from].append(edge.stop_to)

        queue = deque(
            stop_name for stop_name, count in incoming_count.items() if count == 0
        )
        ordered: list[str] = []

        while queue:
            stop_name = queue.popleft()
            ordered.append(stop_name)
            for next_stop in outgoing[stop_name]:
                incoming_count[next_stop] -= 1
                if incoming_count[next_stop] == 0:
                    queue.append(next_stop)

        if len(ordered) != len(incoming_count):
            raise ValueError("flow contains cycle or unresolved dependency")

        return ordered

    def _build_inputs(self, stop_name: str) -> dict[str, Artifact]:
        inputs: dict[str, Artifact] = {}
        for edge in self._incoming_edges(stop_name):
            upstream_output = self._job_outputs.get(edge.stop_from)
            if upstream_output is None:
                continue
            if not upstream_output.contains(edge.out_port):
                continue
            inputs[edge.in_port] = upstream_output.get_artifact(edge.out_port)
        return inputs

    def _incoming_edges(self, stop_name: str) -> list[Edge]:
        return [edge for edge in self._flow.edges if edge.stop_to == stop_name]
