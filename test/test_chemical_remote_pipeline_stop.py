from __future__ import annotations

import json
from pathlib import Path

from piflow_engine.cn.piflow.core.artifact import FileArtifact

from chemical.remote_pipeline_stop import ChemicalRemotePipelineStop


RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class _FakeProcess:
    def pid(self) -> str:
        return "process-1"


class _FakeProcessContext:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def get(self, key: str, default=None):
        if key == RUNNER_CONTEXT_WORKSPACE_ROOT:
            return str(self.workspace_root)
        return default

    def get_process(self):
        return _FakeProcess()


class _FakeStopJob:
    def get_stop_name(self) -> str:
        return "chemical-remote"

    def jid(self) -> str:
        return "job-1"


class _FakeJobContext:
    def __init__(self, workspace_root: Path):
        self._process_context = _FakeProcessContext(workspace_root)

    def get_process_context(self):
        return self._process_context

    def get_stop_job(self):
        return _FakeStopJob()


class _FakeInputStream:
    def __init__(self, artifacts):
        self._artifacts = artifacts

    def ports(self):
        return list(self._artifacts)

    def read(self, port="output"):
        return self._artifacts[port]


class _FakeOutputStream:
    def __init__(self):
        self.artifacts = {}

    def write(self, artifact, port="output") -> None:
        self.artifacts[port] = artifact


class _FakeSubmitResponse:
    run_id = "remote-run-1"


class _FakeStatusResponse:
    status = "SUCCESS"
    message = ""


class _FakeMetaResponse:
    def __init__(self, file_name: str):
        self.file_name = file_name


class _FakeRemoteClient:
    def __init__(self):
        self.submitted = []
        self.downloads = []

    def submit_dag(self, dag_definition_json: str):
        self.submitted.append(json.loads(dag_definition_json))
        return _FakeSubmitResponse()

    def get_run_status(self, run_id: str):
        assert run_id == "remote-run-1"
        return _FakeStatusResponse()

    def get_run_result_meta(self, *, run_id: str, result_node_id: str = "", result_output_name: str = ""):
        assert run_id == "remote-run-1"
        return _FakeMetaResponse(f"{result_output_name}.dat")

    def download_result(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
        target_path: str | Path,
    ) -> str:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"downloaded {result_output_name}", encoding="utf-8")
        self.downloads.append((run_id, result_node_id, result_output_name, target))
        return str(target)

    def close(self) -> None:
        pass


def test_chemical_remote_pipeline_stop_builds_single_node_dag_and_dynamic_outputs(tmp_path: Path) -> None:
    node = {
        "node_id": "node-5",
        "node_name": "编辑单点能计算 gjf 文件",
        "skill": {"skill_id": "gjf_editor"},
        "input_params": [
            {"param_name": "oldchk", "value_mode": "reference"},
        ],
        "out_params": [
            {"param_name": "output_path", "param_value": "outputs/a.gjf"},
            {"param_name": "report_path", "param_value": "outputs/report.txt"},
        ],
    }
    fake_client = _FakeRemoteClient()
    stop = ChemicalRemotePipelineStop()
    stop.client_factory = lambda _stop: fake_client
    stop.set_properties(
        {
            "node_definition_json": node,
            "target_server": "10.0.0.2:50061",
            "local_server": "10.0.0.1:50061",
            "poll_interval_seconds": 0.01,
        }
    )
    assert stop.inport_list == ["oldchk"]
    assert stop.outport_list == ["output_path", "report_path"]
    stop.initialize(_FakeProcessContext(tmp_path / "workspace"))

    outputs = _FakeOutputStream()
    stop.perform(
        _FakeInputStream({"oldchk": FileArtifact(path="/workspace/inputs/a.chk")}),
        outputs,
        _FakeJobContext(tmp_path / "workspace"),
    )

    submitted = fake_client.submitted[0]
    source_node = submitted["nodes"][0]
    assert source_node["skill"]["skill_id"] == "chemical.file_source_stop.ChemicalFileSourceStop"
    assert source_node["input_params"] == [
        {"param_name": "source_type", "value_mode": "manual", "param_value": "remote"},
        {"param_name": "remote_ip", "value_mode": "manual", "param_value": "10.0.0.1"},
        {"param_name": "remote_port", "value_mode": "manual", "param_value": 50061},
        {"param_name": "remote_path", "value_mode": "manual", "param_value": "/workspace/inputs/a.chk"},
    ]
    assert submitted["bindings"][0]["to_node_id"] == "node-5"
    assert submitted["bindings"][0]["to_param_name"] == "oldchk"

    assert set(outputs.artifacts) == {"output_path", "report_path"}
    assert Path(outputs.artifacts["output_path"].path).read_text(encoding="utf-8") == "downloaded output_path"
    assert Path(outputs.artifacts["report_path"].path).read_text(encoding="utf-8") == "downloaded report_path"


def test_chemical_remote_pipeline_stop_replaces_existing_source_node(tmp_path: Path) -> None:
    dag = {
        "task": {"dag_task_id": "flow-1", "dag_task_name": "demo"},
        "nodes": [
            {
                "node_id": "node-1",
                "node_name": "输入",
                "skill": {"skill_id": "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop"},
                "input_params": [{"param_name": "file_path", "value_mode": "manual", "param_value": "old.smi"}],
                "out_params": [],
            },
            {
                "node_id": "node-2",
                "node_name": "计算",
                "skill": {"skill_id": "calc"},
                "input_params": [{"param_name": "input", "value_mode": "reference"}],
                "out_params": [{"param_name": "output"}],
            },
        ],
        "bindings": [
            {
                "from_node_id": "node-1",
                "to_node_id": "node-2",
                "from_param_name": "output",
                "to_param_name": "input",
            }
        ],
    }

    fake_client = _FakeRemoteClient()
    stop = ChemicalRemotePipelineStop()
    stop.client_factory = lambda _stop: fake_client
    stop.set_properties(
        {
            "node_definition_json": dag,
            "target_server": "10.0.0.2:50061",
            "local_ip": "10.0.0.1",
            "local_port": 50061,
            "poll_interval_seconds": 0.01,
        }
    )
    stop.initialize(_FakeProcessContext(tmp_path / "workspace"))

    outputs = _FakeOutputStream()
    stop.perform(
        _FakeInputStream({"file_path": FileArtifact(path="/workspace/inputs/a.smi")}),
        outputs,
        _FakeJobContext(tmp_path / "workspace"),
    )

    source_node = fake_client.submitted[0]["nodes"][0]
    assert source_node["skill"]["skill_id"] == "chemical.file_source_stop.ChemicalFileSourceStop"
    assert source_node["input_params"][3]["param_value"] == "/workspace/inputs/a.smi"
    assert stop.inport_list == ["file_path"]
    assert stop.outport_list == ["output"]
    assert set(outputs.artifacts) == {"output"}
