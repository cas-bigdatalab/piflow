from __future__ import annotations

from pathlib import Path

import piflow_engine.cn.piflow.engine.local.s3_file_source_stop as s3_source_module
from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.engine.local.s3_file_source_stop import S3FileSourceStop


def test_s3_file_source_stop_outputs_file_artifact(tmp_path: Path, monkeypatch) -> None:
    workspace_root = tmp_path / "workspace"
    source_file = tmp_path / "downloads" / "nested" / "sample.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("hello s3 source", encoding="utf-8")

    def fake_download_s3_source_file(source_id: str, *, relative_path: str, target_dir: str | Path | None = None):
        assert source_id == "s3-source-1"
        assert relative_path == "nested/sample.txt"
        return {
            "localPath": str(source_file),
        }

    monkeypatch.setattr(s3_source_module, "download_s3_source_file", fake_download_s3_source_file)

    stop = S3FileSourceStop()
    stop.set_properties(
        {
            "source_id": "s3-source-1",
            "input_file_path": "/nested/sample.txt",
        }
    )

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("S3Source", stop, process_context)
    outputs = stop_job.perform({})

    artifact = outputs.get_artifact("output")
    assert artifact.path == str(source_file.resolve())
    assert stop.source_id == "s3-source-1"
