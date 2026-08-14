from __future__ import annotations

from pathlib import Path

from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.engine.local.remote_source_stop import RemoteSourceStop


def test_remote_source_stop_outputs_file_artifact(tmp_path: Path):
    workspace_root = tmp_path / "workspace"
    source_file = workspace_root / "inputs" / "sample.txt"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("hello remote source", encoding="utf-8")

    stop = RemoteSourceStop()
    stop.set_properties(
        {
            "file_path": "workspace/inputs/sample.txt",
            "node_id": "10.0.0.1",
            "cpu_cores": 8,
            "memory_gb": 32,
            "free_disk_gb": 512,
        }
    )

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("RemoteSource", stop, process_context)
    outputs = stop_job.perform({})

    artifact = outputs.get_artifact("output")
    assert artifact.path == str(source_file.resolve())
    assert stop.node_id == "10.0.0.1"
    assert stop.cpu_cores == 8.0
    assert stop.memory_gb == 32.0
    assert stop.free_disk_gb == 512.0
