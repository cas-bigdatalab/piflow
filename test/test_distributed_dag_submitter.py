from __future__ import annotations

import json

from runtime.distributed_dag_submitter import submit_cross_domain_dag


class _FakeSubmitResponse:
    def __init__(self, run_id: str, status: str):
        self.run_id = run_id
        self.status = status


class _FakeRemoteExecutionClient:
    last_target = None
    last_payload = None
    closed = False

    def __init__(self, target: str):
        type(self).last_target = target
        type(self).closed = False

    def submit_remote_root_dag(self, dag_definition_json: str):
        type(self).last_payload = json.loads(dag_definition_json)
        return _FakeSubmitResponse("remote-process-1", "SUBMITTED")

    def close(self) -> None:
        type(self).closed = True


def test_submit_cross_domain_dag_schedules_and_submits_remotely(monkeypatch):
    scheduled_definition = {
        "task": {"dag_task_id": "dag-1"},
        "nodes": [{"node_id": "remote-subdag-source-B"}],
        "edges": [],
        "bindings": [],
    }

    def _fake_schedule(definition_json, *, execution_node_id=None, random_seed=None):
        assert definition_json == {"task": {"dag_task_id": "dag-1"}}
        assert execution_node_id is None
        assert random_seed == 7

        class _Plan:
            execution_node_id = "10.0.0.2"
            dag_definition = scheduled_definition

        return _Plan()

    monkeypatch.setattr(
        "runtime.distributed_dag_submitter.schedule_frontend_dag",
        _fake_schedule,
    )
    monkeypatch.setattr(
        "runtime.distributed_dag_submitter.create_remote_execution_client",
        _FakeRemoteExecutionClient,
    )

    result = submit_cross_domain_dag(
        {"task": {"dag_task_id": "dag-1"}},
        remote_grpc_target="192.168.1.20:50061",
        random_seed=7,
    )

    assert result.process_id == "remote-process-1"
    assert result.status == "SUBMITTED"
    assert result.execution_node_id == "10.0.0.2"
    assert result.remote_grpc_target == "192.168.1.20:50061"
    assert result.dag_definition == scheduled_definition
    assert _FakeRemoteExecutionClient.last_target == "192.168.1.20:50061"
    assert _FakeRemoteExecutionClient.last_payload == scheduled_definition
    assert _FakeRemoteExecutionClient.closed is True


def test_submit_cross_domain_dag_requires_remote_target():
    try:
        submit_cross_domain_dag(
            {"task": {"dag_task_id": "dag-1"}},
            remote_grpc_target=" ",
        )
    except ValueError as exc:
        assert str(exc) == "remote_grpc_target must not be empty"
    else:
        raise AssertionError("expected ValueError")
