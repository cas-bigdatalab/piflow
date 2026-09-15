from __future__ import annotations

from pathlib import Path

from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.core.stream_impl import JobInputStreamImpl, JobOutputStreamImpl
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.engine.local.text_file_merge_stop import TextFileMergeStop


class _Artifact:
    def __init__(self, path: str):
        self.path = path


def test_text_file_merge_stop_merges_two_inputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    left_path = workspace_root / "left.txt"
    right_path = workspace_root / "right.txt"
    left_path.parent.mkdir(parents=True, exist_ok=True)
    left_path.write_text("left-side", encoding="utf-8")
    right_path.write_text("right-side", encoding="utf-8")

    stop = TextFileMergeStop()
    stop.set_properties(
        {
            "separator": "\n---\n",
            "output_file_name": "merged-demo.txt",
        }
    )

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace_root))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("MergeText", stop, process_context)
    job_context = stop_job._job_context
    inputs = JobInputStreamImpl(
        inputs={
            "left": _Artifact(str(left_path)),
            "right": _Artifact(str(right_path)),
        }
    )
    outputs = JobOutputStreamImpl()

    stop.perform(inputs, outputs, job_context)

    artifact = outputs.get_artifact("output")
    assert artifact.path
    merged_path = Path(artifact.path)
    assert merged_path.exists()
    assert merged_path.read_text(encoding="utf-8") == "left-side\n---\nright-side"
