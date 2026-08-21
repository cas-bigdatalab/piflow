from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from runtime.cross_dag.schema import (
    CrossDagPreBindPlan,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    LogicalNode,
    ReplicaCandidate,
    SatisfactionReport,
    ValidationReport,
)
from services import cross_dag_service


class _FakeRemoteClient:
    status = "RUNNING"
    message = ""
    payload = b"result"
    file_name = "result.tar"

    def __init__(self, target: str):
        self.target = target
        self.closed = False

    def get_run_status(self, run_id: str):
        return SimpleNamespace(status=self.status, message=self.message)

    def get_run_result_meta(self, **kwargs):
        return SimpleNamespace(
            status="SUCCESS",
            file_name=self.file_name,
            file_size=len(self.payload),
            mime_type="application/x-tar",
        )

    def download_result(self, *, target_path, **kwargs):
        Path(target_path).write_bytes(self.payload)
        return str(target_path)

    def close(self):
        self.closed = True


@pytest.fixture
def execution_record():
    return {
        "process_id": "process-1",
        "plan_id": "xdc-plan-1",
        "user_id": "user-1",
        "execution_center_id": "center-1",
        "remote_grpc_target": "center-1:50061",
    }


def _patch_run_dependencies(monkeypatch, execution_record):
    import piflow_engine.cn.piflow.remote.client as remote_client
    import runtime.cross_dag.run_store as run_store

    monkeypatch.setattr(
        cross_dag_service,
        "_require_cross_dag_execution",
        lambda **kwargs: execution_record,
    )
    monkeypatch.setattr(remote_client, "RemoteExecutionClient", _FakeRemoteClient)
    monkeypatch.setattr(run_store, "update_cross_dag_execution_status", lambda *args, **kwargs: None)


def test_execution_status_running(monkeypatch, execution_record):
    _patch_run_dependencies(monkeypatch, execution_record)
    _FakeRemoteClient.status = "RUNNING"
    _FakeRemoteClient.message = "working"

    result = cross_dag_service.get_cross_dag_execution_status(
        process_id="process-1",
        user_id="user-1",
    )

    assert result["status"] == "RUNNING"
    assert result["terminal"] is False
    assert result["downloadable"] is False
    assert result["result_file"] is None


def test_execution_status_success_exposes_download(monkeypatch, execution_record):
    _patch_run_dependencies(monkeypatch, execution_record)
    _FakeRemoteClient.status = "SUCCESS"
    _FakeRemoteClient.message = "done"

    result = cross_dag_service.get_cross_dag_execution_status(
        process_id="process-1",
        user_id="user-1",
        result_node_id="save-result",
        result_output_name="output",
    )

    assert result["terminal"] is True
    assert result["downloadable"] is True
    assert result["result_file"]["file_name"] == "result.tar"
    assert "result_node_id=save-result" in result["result_file"]["download_url"]
    assert "result_output_name=output" in result["result_file"]["download_url"]


def test_prepare_download_requires_success(monkeypatch, execution_record):
    _patch_run_dependencies(monkeypatch, execution_record)
    _FakeRemoteClient.status = "FAILED"
    _FakeRemoteClient.message = "bad input"

    with pytest.raises(cross_dag_service.CrossDagExecutionNotReady):
        cross_dag_service.prepare_cross_dag_result_download(
            process_id="process-1",
            user_id="user-1",
        )


def test_prepare_download_writes_api_temp_file(monkeypatch, execution_record, tmp_path):
    _patch_run_dependencies(monkeypatch, execution_record)
    _FakeRemoteClient.status = "SUCCESS"
    _FakeRemoteClient.message = "done"
    _FakeRemoteClient.payload = b"tar-result"
    _FakeRemoteClient.file_name = "earth_science_bundle.tar"
    monkeypatch.setattr(cross_dag_service, "resolve_workspace_root", lambda: tmp_path)

    result = cross_dag_service.prepare_cross_dag_result_download(
        process_id="process-1",
        user_id="user-1",
    )

    assert result.file_name == "earth_science_bundle.tar"
    assert result.path.read_bytes() == b"tar-result"
    assert result.path.parent == (tmp_path / "temp" / "xdc_downloads").resolve()


def test_execute_registers_remote_run(monkeypatch):
    import runtime.cross_dag.executor as executor
    import runtime.cross_dag.run_store as run_store

    plan = SimpleNamespace(
        plan_id="xdc-plan-1",
        mode="composition",
        validation=SimpleNamespace(ok=True, errors=[], warnings=[]),
    )
    submission = SimpleNamespace(
        process_id="process-1",
        status="SUBMITTED",
        execution_node_id="center-1",
        remote_grpc_target="center-1:50061",
    )
    recorded = {}
    monkeypatch.setitem(cross_dag_service._PLAN_CACHE, plan.plan_id, plan)
    monkeypatch.setattr(executor, "submit_cross_dag_plan", lambda value: submission)
    monkeypatch.setattr(run_store, "save_cross_dag_execution", lambda **kwargs: recorded.update(kwargs))

    result = cross_dag_service.execute_cross_dag_plan(
        plan_id=plan.plan_id,
        user_id="user-1",
    )

    assert recorded["process_id"] == "process-1"
    assert recorded["remote_grpc_target"] == "center-1:50061"
    assert result["status_url"].endswith("/process-1/status")
    assert result["download_url"].endswith("/process-1/download")


def test_pre_bind_summary_exposes_candidates_without_a_selection(monkeypatch):
    pre_bind = CrossDagPreBindPlan(
        plan_id="xdc-pre-1",
        intent=IntentSpec(
            goal="merge datasets",
            user_request="merge datasets",
            datasets=[
                IntentDataset(
                    alias="a",
                    dataset_id="dataset-a",
                    name="Dataset A",
                    replicas=[
                        ReplicaCandidate(
                            "replica-a",
                            "center-a",
                            "center-a",
                            "dataset-a",
                            metrics={"cpu_cores": 8},
                        )
                    ],
                )
            ],
        ),
        satisfaction=SatisfactionReport(
            mode="composition",
            reason="requires composition",
        ),
        logical_dag=LogicalDag(
            task_id="xdc-pre-1",
            task_name="merge",
            nodes=[
                LogicalNode(
                    node_id="source-a",
                    node_name="source_a",
                    skill_id="skill-a",
                    skill_name="source_skill",
                )
            ],
        ),
        validation=ValidationReport(),
    )
    monkeypatch.setattr(
        cross_dag_service,
        "resolve_cross_dc_config",
        lambda *args, **kwargs: SimpleNamespace(centers={}),
    )

    result = cross_dag_service._summarize_pre_bind(pre_bind)

    assert result["stage"] == "pre_bind"
    assert result["binding_status"] == "PENDING"
    assert result["can_continue"] is True
    assert result["datasets"][0]["replicas"] == [
        {
            "replica_id": "replica-a",
            "center_id": "center-a",
            "center_name": "center-a",
            "status": "AVAILABLE",
            "metrics": {"cpu_cores": 8},
        }
    ]
    assert "chosen" not in result["datasets"][0]
    assert "center_id" not in result["logical_dag"]["nodes"][0]
    assert result["next_action"]["body"] == {"plan_id": "xdc-pre-1"}


def test_pre_bind_cache_is_scoped_to_user():
    pre_bind = SimpleNamespace(plan_id="xdc-private")
    cross_dag_service._remember_pre_bind(pre_bind, user_id="user-1")

    assert (
        cross_dag_service._get_owned_pre_bind(
            plan_id="xdc-private", user_id="user-1"
        )
        is pre_bind
    )
    with pytest.raises(PermissionError):
        cross_dag_service._get_owned_pre_bind(
            plan_id="xdc-private", user_id="user-2"
        )


def test_bind_and_execute_finishes_plan_then_submits(monkeypatch):
    pre_bind = SimpleNamespace(
        plan_id="xdc-pre-2",
        mode="composition",
        validation=SimpleNamespace(ok=True, errors=[]),
    )
    plan = SimpleNamespace(plan_id="xdc-pre-2")
    calls: list[str] = []
    monkeypatch.setattr(
        cross_dag_service,
        "_get_owned_pre_bind",
        lambda **kwargs: pre_bind,
    )
    monkeypatch.setattr(
        cross_dag_service,
        "finalize_cross_dag_pre_bind",
        lambda value: calls.append("bind") or plan,
    )
    monkeypatch.setattr(
        cross_dag_service,
        "_remember",
        lambda value: calls.append("remember"),
    )
    monkeypatch.setattr(
        cross_dag_service,
        "execute_cross_dag_plan",
        lambda **kwargs: calls.append("execute")
        or {"process_id": "process-2", "status": "SUBMITTED"},
    )
    monkeypatch.setattr(
        cross_dag_service,
        "_summarize",
        lambda value, detail=False: {"plan_id": value.plan_id},
    )

    result = cross_dag_service.bind_and_execute_cross_dag_pre_bind(
        plan_id="xdc-pre-2",
        user_id="user-1",
    )

    assert calls == ["bind", "remember", "execute"]
    assert result == {
        "plan": {"plan_id": "xdc-pre-2"},
        "execution": {"process_id": "process-2", "status": "SUBMITTED"},
    }
