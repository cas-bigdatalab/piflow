from __future__ import annotations

from pathlib import Path

from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from piflow_engine.cn.piflow.engine.local.remote_subdag_source_stop import RemoteSubDagSourceStop


class _FakeSubmitResponse:
    def __init__(self, run_id: str):
        self.run_id = run_id


class _FakeStatusResponse:
    def __init__(self, status: str, message: str = ""):
        self.status = status
        self.message = message


class _FakeMetaResponse:
    def __init__(self, file_name: str):
        self.file_name = file_name


class _FakeRemoteClient:
    def __init__(self, remote_file: Path):
        self.remote_file = remote_file

    def submit_remote_subdag(self, dag_definition_json: str):
        return self.submit_dag(dag_definition_json)

    def submit_dag(self, dag_definition_json: str):
        assert dag_definition_json == '{"task": {"dag_task_id": "b"}}'
        return _FakeSubmitResponse("process-remote-1")

    def get_run_status(self, run_id: str):
        assert run_id == "process-remote-1"
        return _FakeStatusResponse("SUCCESS")

    def get_run_result_meta(self, *, run_id: str, result_node_id: str = "", result_output_name: str = ""):
        assert run_id == "process-remote-1"
        assert result_node_id == ""
        assert result_output_name == ""
        return _FakeMetaResponse(self.remote_file.name)

    def download_result(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
        target_path: str | Path,
    ) -> str:
        assert run_id == "process-remote-1"
        Path(target_path).write_bytes(self.remote_file.read_bytes())
        return str(target_path)

    def close(self) -> None:
        return None


def test_remote_subdag_source_stop_outputs_file_artifact(tmp_path: Path):
    remote_file = tmp_path / "remote.csv"
    remote_file.write_text("a,b\n1,2\n", encoding="utf-8")

    stop = RemoteSubDagSourceStop()
    stop.client_factory = lambda _stop: _FakeRemoteClient(remote_file)
    stop.set_properties(
        {
            "remote_grpc_target": "127.0.0.1:50061",
            "subdag_definition_json": '{"task": {"dag_task_id": "b"}}',
        }
    )

    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(tmp_path / "workspace"))
    flow = FlowImpl(name="test", uuid="flow-1")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("远端结果源", stop, process_context)
    outputs = stop_job.perform({})

    artifact = outputs.get_artifact("output")
    assert artifact.path
    assert Path(artifact.path).exists()
    assert Path(artifact.path).read_text(encoding="utf-8") == "a,b\n1,2\n"
