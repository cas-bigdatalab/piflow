from __future__ import annotations

import os
from pathlib import Path

import pytest

from cn.piflow.core.artifact import Artifact
from cn.piflow.core.context import CascadeContext
from cn.piflow.core.flow import FlowImpl
from cn.piflow.core.flow_bean import FlowBean
from cn.piflow.core.process import Process
from cn.piflow.core.runtime_context import JobContext, ProcessContext
from cn.piflow.core.runtime_keys import RUN_CONTEXT_FINAL_OUTPUT_PATH
from cn.piflow.core.stop_job import StopJob
from cn.piflow.core.stream import JobInputStream, JobOutputStream
from cn.piflow.core.stream_impl import JobInputStreamImpl, JobOutputStreamImpl
from cn.piflow.core.runner import Runner
from cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from cn.piflow.engine.local.llm_file_transform_stop import LLMFileTransformStop


class _MockLLMClient:
    def __init__(self, transformed_text: str) -> None:
        self.transformed_text = transformed_text
        self.calls: list[dict[str, str]] = []

    def transform_file(
        self,
        *,
        model: str,
        instruction: str,
        filename: str,
        content: str,
    ) -> str:
        self.calls.append(
            {
                "model": model,
                "instruction": instruction,
                "filename": filename,
                "content": content,
            }
        )
        return self.transformed_text


class _TestProcess(Process):
    def __init__(self, process_id: str = "process_test") -> None:
        self._process_id = process_id
        self._flow = FlowImpl(name="test-flow", uuid="flow-1")

    def pid(self) -> str:
        return self._process_id

    def get_flow(self):
        return self._flow

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def await_termination(self, timeout: float | None = None) -> bool:
        return True

    def is_alive(self) -> bool:
        return False


class _TestProcessContext(CascadeContext, ProcessContext):
    def __init__(self, workspace_root: Path):
        super().__init__()
        self._flow = FlowImpl(name="test-flow", uuid="flow-1")
        self._process = _TestProcess()
        self.put(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))

    def get_flow(self):
        return self._flow

    def get_process(self):
        return self._process


class _TestStopJob(StopJob):
    def __init__(self, stop_name: str = "LLMTransform") -> None:
        self._stop_name = stop_name

    def jid(self) -> str:
        return "job_test"

    def get_stop_name(self) -> str:
        return self._stop_name

    def get_stop(self):
        raise NotImplementedError


class _TestJobContext(CascadeContext, JobContext):
    def __init__(self, process_context: ProcessContext):
        super().__init__(process_context)
        self._stop_job = _TestStopJob()
        self._process_context = process_context
        self._input_stream = JobInputStreamImpl()
        self._output_stream = JobOutputStreamImpl()

    def get_stop_job(self) -> StopJob:
        return self._stop_job

    def get_input_stream(self) -> JobInputStream:
        return self._input_stream

    def get_output_stream(self) -> JobOutputStream:
        return self._output_stream

    def get_process_context(self) -> ProcessContext:
        return self._process_context


def test_llm_file_transform_stop_writes_transformed_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    input_path = workspace / "input.md"
    input_path.write_text("# title\nhello", encoding="utf-8")
    mock_client = _MockLLMClient("```md\n# TITLE\nHELLO\n```")
    monkeypatch.setattr(
        LLMFileTransformStop,
        "client_factory",
        lambda stop: mock_client,
    )

    flow_data = {
        "flow": {
            "uuid": "flow-llm-transform-001",
            "name": "llm-transform-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source-001",
                    "name": "SourceFile",
                    "bundle": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "properties": {
                        "file_path": "input.md",
                    },
                },
                {
                    "uuid": "llm-001",
                    "name": "LLMTransform",
                    "bundle": "cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop",
                    "properties": {
                        "instruction": "把内容转成大写",
                        "model": "mock-model",
                    },
                },
            ],
            "paths": [
                {
                    "from": "source-001",
                    "outport": "output",
                    "inport": "",
                    "to": "llm-001",
                }
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()
    process = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace)).start(flow)
    process.await_termination()

    output_files = list(workspace.rglob("input_transformed.md"))
    assert len(output_files) == 1
    output_path = output_files[0]
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# TITLE\nHELLO"
    assert output_path.suffix == ".md"
    assert mock_client.calls == [
        {
            "model": "mock-model",
            "instruction": "把内容转成大写",
            "filename": "input.md",
            "content": "# title\nhello",
        }
    ]


def test_llm_file_transform_stop_rejects_non_file_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_client = _MockLLMClient("ignored")
    monkeypatch.setattr(
        LLMFileTransformStop,
        "client_factory",
        lambda stop: mock_client,
    )

    stop = LLMFileTransformStop()
    stop.set_properties(
        {
            "instruction": "处理这个输入",
            "model": "mock-model",
        }
    )

    process_context = _TestProcessContext(tmp_path / "workspace")
    stop.initialize(process_context)
    job_context = _TestJobContext(process_context)
    inputs = JobInputStreamImpl(inputs={"": Artifact()})
    outputs = JobOutputStreamImpl()

    with pytest.raises(ValueError, match="no file path"):
        stop.perform(inputs, outputs, job_context)


def test_llm_file_transform_stop_rejects_large_file(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("abcdef", encoding="utf-8")

    stop = LLMFileTransformStop()
    stop.set_properties(
        {
            "instruction": "压缩内容",
            "model": "mock-model",
            "api_key": "dummy-key",
            "max_input_chars": 3,
        }
    )

    process_context = _TestProcessContext(tmp_path / "workspace")
    stop.initialize(process_context)
    job_context = _TestJobContext(process_context)
    inputs = JobInputStreamImpl(inputs={"": Artifact(value=str(input_path))})
    outputs = JobOutputStreamImpl()

    with pytest.raises(ValueError, match="exceeds max_input_chars"):
        stop.perform(inputs, outputs, job_context)

    assert not job_context.contains(RUN_CONTEXT_FINAL_OUTPUT_PATH)


def test_llm_file_transform_stop_runs_with_dashscope_qwen(
    tmp_path: Path,
) -> None:
    if os.getenv("PIFLOW_RUN_REAL_LLM_TESTS") != "1":
        pytest.skip("set PIFLOW_RUN_REAL_LLM_TESTS=1 to run real LLM integration test")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        pytest.skip("DASHSCOPE_API_KEY is not set")

    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    input_path = workspace / "input.txt"
    input_path.write_text("x", encoding="utf-8")

    flow_data = {
        "flow": {
            "uuid": "flow-qwen-real-test",
            "name": "qwen-real-test",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source",
                    "name": "SourceFile",
                    "bundle": "cn.piflow.engine.local.source_file_stop.SourceFileStop",
                    "properties": {
                        "file_path": "input.txt",
                    },
                },
                {
                    "uuid": "llm",
                    "name": "LLMTransform",
                    "bundle": "cn.piflow.engine.local.llm_file_transform_stop.LLMFileTransformStop",
                    "properties": {
                        "instruction": "只返回OK",
                        "model": "qwen3.7-plus",
                        "api_key": api_key,
                        "base_url": "https://ws-lf8y8o8rvpst65zw.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
                        "max_output_tokens": 8,
                        "max_input_chars": 10,
                    },
                },
            ],
            "paths": [
                {
                    "from": "source",
                    "outport": "output",
                    "inport": "",
                    "to": "llm",
                }
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()
    process = (
        Runner.create()
        .bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
        .start(flow)
    )
    process.await_termination(timeout=90)

    output_files = list(workspace.rglob("input_transformed.txt"))
    assert len(output_files) == 1
    assert output_files[0].read_text(encoding="utf-8").strip() == "OK"
