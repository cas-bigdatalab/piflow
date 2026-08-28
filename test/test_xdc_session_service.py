from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from runtime.cross_dag.schema import (
    CrossDagPreBindPlan,
    DatasetCoverage,
    FacetCoverage,
    IntentDataset,
    IntentSpec,
    LogicalDag,
    ReplicaCandidate,
    SatisfactionReport,
    ValidationReport,
)
from services import xdc_session_service


def _collect_events(generator):
    async def collect():
        return [event async for event in generator]

    return asyncio.run(collect())


def _pre_bind(plan_id: str) -> CrossDagPreBindPlan:
    return CrossDagPreBindPlan(
        plan_id=plan_id,
        mode="composition",
        intent=IntentSpec(
            goal="合并地球科学语料",
            user_request="合并地球科学资料",
            datasets=[
                IntentDataset(
                    alias="quake",
                    dataset_id="dataset-a",
                    name="地震目录",
                    replicas=[
                        ReplicaCandidate(
                            "replica-a",
                            "center-a",
                            "center-a",
                            "dataset-a",
                        ),
                        ReplicaCandidate(
                            "replica-b",
                            "center-b",
                            "center-b",
                            "dataset-a",
                        ),
                    ],
                )
            ],
        ),
        satisfaction=SatisfactionReport(
            mode="composition",
            reason="需要组合多个数据集",
        ),
        logical_dag=LogicalDag(task_id=plan_id, task_name="地学资料合并"),
        validation=ValidationReport(),
    )


class _MemoryRepository:
    def __init__(self):
        self.sessions = {
            "session-1": {
                "session_id": "session-1",
                "user_id": "user-1",
                "title": "",
                "status": "ACTIVE",
            }
        }
        self.tasks = {}
        self.items = {}
        self.snapshots = {}

    def get_session(self, *, session_id, user_id):
        value = self.sessions.get(session_id)
        return dict(value) if value and value["user_id"] == user_id else None

    def create_task(self, **kwargs):
        if self.get_session(
            session_id=kwargs["session_id"], user_id=kwargs["user_id"]
        ) is None:
            raise LookupError("missing session")
        active = [
            task
            for task in self.tasks.values()
            if task["session_id"] == kwargs["session_id"]
            and task["status"] in {"PROCESSING", "PLANNED", "EXECUTING"}
        ]
        if active:
            raise RuntimeError("active task")
        task = {
            "task_id": kwargs["task_id"],
            "session_id": kwargs["session_id"],
            "task_order": len(self.tasks) + 1,
            "parent_task_id": kwargs.get("parent_task_id"),
            "task_name": kwargs["task_name"],
            "user_request": kwargs["user_request"],
            "mode": None,
            "status": "PROCESSING",
            "current_stage": "intent",
            "plan_revision": 1,
            "plan_id": None,
            "process_id": None,
            "error_message": "",
        }
        self.tasks[task["task_id"]] = task
        return dict(task)

    def get_task(self, *, task_id, user_id):
        task = self.tasks.get(task_id)
        session = self.sessions.get(task["session_id"]) if task else None
        return dict(task) if session and session["user_id"] == user_id else None

    def list_tasks(self, *, session_id, user_id):
        if self.get_session(session_id=session_id, user_id=user_id) is None:
            return []
        return [
            dict(task)
            for task in self.tasks.values()
            if task["session_id"] == session_id
        ]

    def update_task_state(self, *, task_id, status, current_stage, **values):
        task = self.tasks[task_id]
        task.update(status=status, current_stage=current_stage)
        for key in ("mode", "plan_id", "process_id", "error_message"):
            if values.get(key) is not None:
                task[key] = values[key]

    def claim_task_for_execution(self, *, task_id, user_id):
        task = self.get_task(task_id=task_id, user_id=user_id)
        if task is None or task["status"] != "PLANNED":
            return None
        self.tasks[task_id].update(status="EXECUTING", current_stage="bind")
        return dict(self.tasks[task_id])

    def save_snapshot(
        self, *, task_id, revision, snapshot_type, payload, schema_version="1.0"
    ):
        self.snapshots[(task_id, revision, snapshot_type)] = {
            "task_id": task_id,
            "revision": revision,
            "snapshot_type": snapshot_type,
            "schema_version": schema_version,
            "payload_json": payload,
        }

    def get_snapshot(self, *, task_id, revision, snapshot_type):
        return self.snapshots.get((task_id, revision, snapshot_type))

    def list_public_snapshots(self, *, task_id):
        return [
            value
            for (stored_task, _, kind), value in self.snapshots.items()
            if stored_task == task_id
            and kind in {"PRE_BIND_VIEW", "BOUND_VIEW", "EXECUTION", "RESULT"}
        ]

    def save_session_item(self, *, item_key, **values):
        item = {"item_id": len(self.items) + 1, "item_key": item_key, **values}
        if item_key in self.items:
            item["item_id"] = self.items[item_key]["item_id"]
        self.items[item_key] = item
        return dict(item)

    def list_session_items(
        self, *, session_id, user_id, after_item_id=0, limit=1000
    ):
        return [
            dict(item)
            for item in self.items.values()
            if item["session_id"] == session_id and item["item_id"] > after_item_id
        ][:limit]


@pytest.fixture
def memory_repository(monkeypatch):
    memory = _MemoryRepository()
    names = (
        "get_session",
        "create_task",
        "get_task",
        "list_tasks",
        "update_task_state",
        "claim_task_for_execution",
        "save_snapshot",
        "get_snapshot",
        "list_public_snapshots",
        "save_session_item",
        "list_session_items",
    )
    for name in names:
        monkeypatch.setattr(xdc_session_service.repository, name, getattr(memory, name))
    return memory


def test_session_pre_bind_persists_plan_and_timeline(
    monkeypatch, memory_repository
):
    def plan(user_request, *, plan_id, on_stage):
        on_stage("intent", {"status": "started"})
        on_stage(
            "intent",
            {"status": "finished", "intent": {"requirements": [], "datasets": [1]}},
        )
        on_stage("planning", {"status": "started"})
        on_stage(
            "planning",
            {"status": "finished", "planning_json": {"nodes": [{}, {}]}},
        )
        return _pre_bind(plan_id)

    monkeypatch.setattr(xdc_session_service, "plan_cross_dag_pre_bind", plan)
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_summarize_pre_bind",
        lambda value, detail=False: {"plan_id": value.plan_id, "mode": value.mode},
    )

    events = _collect_events(
        xdc_session_service.stream_xdc_session_pre_bind(
            session_id="session-1",
            user_request="请把地球科学资料合并",
            user_id="user-1",
        )
    )

    task_id = events[0]["task_id"]
    assert events[0]["type"] == "task"
    assert events[-1]["type"] == "done"
    assert events[-1]["result"]["task_id"] == task_id
    assert memory_repository.tasks[task_id]["status"] == "PLANNED"
    assert (task_id, 1, "PRE_BIND_INTERNAL") in memory_repository.snapshots
    assert memory_repository.items[f"{task_id}:user-request"]["item_type"] == (
        "USER_MESSAGE"
    )
    assert memory_repository.items[f"{task_id}:plan-card"]["item_type"] == (
        "PLAN_CARD"
    )


def test_bind_execute_restores_snapshot_and_persists_replica_reason(
    monkeypatch, memory_repository
):
    pre_bind = _pre_bind("xdc-plan-1")
    task_id = "task-1"
    memory_repository.tasks[task_id] = {
        "task_id": task_id,
        "session_id": "session-1",
        "status": "PLANNED",
        "plan_revision": 1,
        "mode": "composition",
    }
    memory_repository.save_snapshot(
        task_id=task_id,
        revision=1,
        snapshot_type="PRE_BIND_INTERNAL",
        payload=xdc_session_service.encode_pre_bind_plan(pre_bind),
    )

    plan = SimpleNamespace(
        plan_id=pre_bind.plan_id,
        mode="composition",
        to_json=lambda: {"plan_id": pre_bind.plan_id},
    )

    def finish(value, *, user_id, on_stage):
        on_stage("bind", {"status": "started"})
        on_stage(
            "bind",
            {
                "status": "finished",
                "center_of": {"source": "center-a"},
                "replica_decisions": [
                    {
                        "dataset_id": "dataset-a",
                        "node_id": "source",
                        "preferred_center_id": "center-a",
                        "chosen": {
                            "replica_id": "replica-a",
                            "center_id": "center-a",
                        },
                        "reason": "数据与计算中心一致，避免跨域传输",
                        "scores": [],
                        "rejects": [],
                    }
                ],
            },
        )
        on_stage("submit", {"status": "started", "mode": "composition"})
        on_stage(
            "submit",
            {
                "status": "finished",
                "mode": "composition",
                "process_id": "process-1",
                "submit_status": "SUBMITTED",
            },
        )
        return plan, {
            "process_id": "process-1",
            "status": "SUBMITTED",
            "status_url": "/api/piflow/v1/xdc/execution/process-1/status",
            "download_url": "/api/piflow/v1/xdc/execution/process-1/download",
        }

    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_finalize_and_execute_pre_bind",
        finish,
    )
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_summarize",
        lambda value, detail=False: {"plan_id": value.plan_id},
    )

    events = _collect_events(
        xdc_session_service.stream_xdc_task_bind_and_execute(
            task_id=task_id,
            user_id="user-1",
        )
    )

    selected = next(
        event
        for event in events
        if event.get("type") == "replica" and event.get("status") == "selected"
    )
    assert selected["reason"] == "数据与计算中心一致，避免跨域传输"
    assert selected["summary"] == (
        "选择副本 replica-a，因为数据与计算中心一致，避免跨域传输。"
    )
    assert memory_repository.tasks[task_id]["status"] == "EXECUTING"
    assert memory_repository.tasks[task_id]["process_id"] == "process-1"
    assert events[-1]["result"]["execution"]["status_url"] == (
        f"/api/piflow/v1/xdc/tasks/{task_id}/execution/status"
    )
    assert events[-1]["result"]["execution"]["process_status_url"] == (
        "/api/piflow/v1/xdc/execution/process-1/status"
    )
    assert memory_repository.items[
        f"{task_id}:replica:dataset-a:selected"
    ]["payload"]["reason"] == "数据与计算中心一致，避免跨域传输"
    assert events[-1]["type"] == "done"

    duplicate = _collect_events(
        xdc_session_service.stream_xdc_task_bind_and_execute(
            task_id=task_id,
            user_id="user-1",
        )
    )
    assert duplicate == [
        {
            "type": "error",
            "code": "TASK_STATE_CONFLICT",
            "message": "任务状态不是 PLANNED，不能绑定执行: EXECUTING",
        }
    ]


def test_execution_success_adds_result_card_and_allows_next_task(
    monkeypatch, memory_repository
):
    task_id = "task-1"
    memory_repository.tasks[task_id] = {
        "task_id": task_id,
        "session_id": "session-1",
        "status": "EXECUTING",
        "plan_revision": 1,
        "mode": "composition",
        "process_id": "process-1",
    }
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "get_cross_dag_execution_status",
        lambda **kwargs: {
            "process_id": "process-1",
            "status": "SUCCESS",
            "terminal": True,
            "downloadable": True,
            "result_file": {
                "file_name": "result.tar",
                "download_url": "/api/piflow/v1/xdc/execution/process-1/download",
            },
        },
    )

    result = xdc_session_service.get_xdc_task_execution_status(
        task_id=task_id,
        user_id="user-1",
    )

    assert result["status"] == "SUCCESS"
    assert memory_repository.tasks[task_id]["status"] == "COMPLETED"
    assert memory_repository.items[f"{task_id}:result-card"]["payload"][
        "file_name"
    ] == "result.tar"

    # A completed task no longer occupies the session's single active slot.
    monkeypatch.setattr(
        xdc_session_service,
        "plan_cross_dag_pre_bind",
        lambda user_request, *, plan_id, on_stage: _pre_bind(plan_id),
    )
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_summarize_pre_bind",
        lambda value, detail=False: {"plan_id": value.plan_id},
    )
    events = _collect_events(
        xdc_session_service.stream_xdc_session_pre_bind(
            session_id="session-1",
            user_request="继续处理另一批资料",
            user_id="user-1",
            parent_task_id=task_id,
        )
    )
    assert events[-1]["type"] == "done"
    assert len(memory_repository.tasks) == 2


def test_task_detail_is_user_scoped(memory_repository):
    memory_repository.tasks["task-private"] = {
        "task_id": "task-private",
        "session_id": "session-1",
        "status": "COMPLETED",
        "plan_revision": 1,
    }

    with pytest.raises(xdc_session_service.XdcTaskNotFound):
        xdc_session_service.get_xdc_task_detail(
            task_id="task-private",
            user_id="user-2",
        )


def test_session_list_serializes_database_times_as_explicit_utc(monkeypatch):
    monkeypatch.setattr(
        xdc_session_service.repository,
        "list_sessions",
        lambda **kwargs: {
            "items": [
                {
                    "session_id": "session-1",
                    "create_time": datetime(2026, 8, 26, 8, 11, 6, 549785),
                    "update_time": datetime(
                        2026,
                        8,
                        26,
                        16,
                        36,
                        53,
                        649511,
                        tzinfo=timezone(timedelta(hours=8)),
                    ),
                }
            ],
            "pagination": {"pageNum": 1, "pageSize": 20, "total": 1},
        },
    )

    result = xdc_session_service.list_xdc_sessions(user_id="user-1")

    assert result["items"][0]["create_time"] == "2026-08-26T08:11:06.549Z"
    assert result["items"][0]["update_time"] == "2026-08-26T08:36:53.649Z"


def test_unavailable_plan_is_terminal_and_does_not_block_session(
    monkeypatch, memory_repository
):
    def unavailable(user_request, *, plan_id, on_stage):
        plan = _pre_bind(plan_id)
        plan.mode = "unavailable"
        plan.satisfaction.mode = "unavailable"
        plan.satisfaction.reason = "平台当前没有可用数据"
        return plan

    monkeypatch.setattr(
        xdc_session_service,
        "plan_cross_dag_pre_bind",
        unavailable,
    )
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_summarize_pre_bind",
        lambda value, detail=False: {
            "plan_id": value.plan_id,
            "mode": value.mode,
            "can_continue": False,
        },
    )

    first = _collect_events(
        xdc_session_service.stream_xdc_session_pre_bind(
            session_id="session-1",
            user_request="查找平台没有的数据",
            user_id="user-1",
        )
    )
    first_task_id = first[0]["task_id"]

    assert first[-1]["type"] == "done"
    assert memory_repository.tasks[first_task_id]["status"] == "UNAVAILABLE"
    assert memory_repository.items[f"{first_task_id}:plan-card"][
        "item_status"
    ] == "unavailable"

    second = _collect_events(
        xdc_session_service.stream_xdc_session_pre_bind(
            session_id="session-1",
            user_request="继续查询另一份资料",
            user_id="user-1",
        )
    )
    assert second[-1]["type"] == "done"
    assert len(memory_repository.tasks) == 2


@pytest.mark.parametrize("selected_dataset_id", ["dataset-a", None])
def test_direct_bind_submits_process_and_keeps_unified_session_contract(
    monkeypatch, memory_repository, selected_dataset_id
):
    pre_bind = _pre_bind("xdc-direct-plan-1")
    pre_bind.mode = "direct"
    pre_bind.satisfaction.mode = "direct"
    pre_bind.satisfaction.coverages = [
        DatasetCoverage(
            dataset_id="dataset-a",
            name="地震目录",
            facets=[
                FacetCoverage(
                    key="field",
                    label="学科领域",
                    mode="match_all",
                    required=["地球科学"],
                    covered=["地球科学"],
                )
            ],
        )
    ]
    task_id = "task-direct-1"
    memory_repository.tasks[task_id] = {
        "task_id": task_id,
        "session_id": "session-1",
        "status": "PLANNED",
        "plan_revision": 1,
        "mode": "direct",
    }
    memory_repository.save_snapshot(
        task_id=task_id,
        revision=1,
        snapshot_type="PRE_BIND_INTERNAL",
        payload=xdc_session_service.encode_pre_bind_plan(pre_bind),
    )
    plan = SimpleNamespace(
        plan_id=pre_bind.plan_id,
        mode="direct",
        to_json=lambda: {"plan_id": pre_bind.plan_id, "mode": "direct"},
    )

    def finish_direct(value, *, user_id, on_stage, selected_dataset_id):
        assert selected_dataset_id == "dataset-a"
        on_stage("access", {"status": "started"})
        on_stage(
            "access",
            {
                "status": "finished",
                "dataset_id": "dataset-a",
                "replica": "replica-a",
                "direct_access": {
                    "replica_decision": {
                        "dataset_id": "dataset-a",
                        "node_id": "dataset-a",
                        "chosen": {
                            "replica_id": "replica-a",
                            "center_id": "center-a",
                        },
                        "reason": "same center, no cross-center transfer",
                    }
                },
            },
        )
        on_stage("submit", {"status": "started", "mode": "direct"})
        on_stage(
            "submit",
            {
                "status": "finished",
                "mode": "direct",
                "process_id": "process-direct-1",
                "submit_status": "SUBMITTED",
            },
        )
        return plan, {
            "process_id": "process-direct-1",
            "status": "SUBMITTED",
            "result_node_id": "direct-dataset-source",
            "result_output_name": "output",
            "status_url": (
                "/api/piflow/v1/xdc/execution/process-direct-1/status"
                "?result_node_id=direct-dataset-source&result_output_name=output"
            ),
            "download_url": (
                "/api/piflow/v1/xdc/execution/process-direct-1/download"
                "?result_node_id=direct-dataset-source&result_output_name=output"
            ),
        }

    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_finalize_and_execute_direct_pre_bind",
        finish_direct,
    )
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_finalize_and_execute_pre_bind",
        lambda *args, **kwargs: pytest.fail("composition helper must not handle direct"),
    )
    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "_summarize_direct_session",
        lambda value, detail=False: {
            "plan_id": value.plan_id,
            "mode": "direct",
            "sources": [{"dataset_id": "dataset-a"}],
            "dag": {"nodes": [{"id": "direct-dataset-source"}], "edges": []},
        },
    )

    events = _collect_events(
        xdc_session_service.stream_xdc_task_bind_and_execute(
            task_id=task_id,
            user_id="user-1",
            selected_dataset_id=selected_dataset_id,
        )
    )

    result = events[-1]["result"]
    assert memory_repository.tasks[task_id]["status"] == "EXECUTING"
    assert memory_repository.tasks[task_id]["process_id"] == "process-direct-1"
    assert f"{task_id}:result-card" not in memory_repository.items
    assert result["plan"]["sources"][0]["dataset_id"] == "dataset-a"
    assert result["plan"]["dag"]["nodes"][0]["id"] == (
        "direct-dataset-source"
    )
    assert result["execution"]["status_url"] == (
        f"/api/piflow/v1/xdc/tasks/{task_id}/execution/status"
        "?result_node_id=direct-dataset-source&result_output_name=output"
    )
    assert result["execution"]["process_status_url"].startswith(
        "/api/piflow/v1/xdc/execution/process-direct-1/status?"
    )

def test_direct_bind_rejects_non_candidate_before_claiming_task(
    memory_repository,
):
    pre_bind = _pre_bind("xdc-direct-plan-invalid")
    pre_bind.mode = "direct"
    pre_bind.satisfaction.mode = "direct"
    pre_bind.satisfaction.coverages = [
        DatasetCoverage(
            dataset_id="dataset-a",
            name="地震目录",
            facets=[
                FacetCoverage(
                    key="field",
                    label="学科领域",
                    mode="match_all",
                    required=["地球科学"],
                    covered=["地球科学"],
                )
            ],
        )
    ]
    task_id = "task-direct-selection-invalid"
    memory_repository.tasks[task_id] = {
        "task_id": task_id,
        "session_id": "session-1",
        "status": "PLANNED",
        "plan_revision": 1,
        "mode": "direct",
    }
    memory_repository.save_snapshot(
        task_id=task_id,
        revision=1,
        snapshot_type="PRE_BIND_INTERNAL",
        payload=xdc_session_service.encode_pre_bind_plan(pre_bind),
    )

    events = _collect_events(
        xdc_session_service.stream_xdc_task_bind_and_execute(
            task_id=task_id,
            user_id="user-1",
            selected_dataset_id="dataset-not-candidate",
        )
    )

    assert events[0]["type"] == "error"
    assert events[0]["code"] == "INVALID_DATASET_SELECTION"
    assert memory_repository.tasks[task_id]["status"] == "PLANNED"


def test_direct_status_restores_result_selector_after_refresh(
    monkeypatch, memory_repository
):
    task_id = "task-direct-1"
    memory_repository.tasks[task_id] = {
        "task_id": task_id,
        "session_id": "session-1",
        "status": "EXECUTING",
        "plan_revision": 1,
        "mode": "direct",
        "process_id": "process-direct-1",
    }
    memory_repository.save_snapshot(
        task_id=task_id,
        revision=1,
        snapshot_type="EXECUTION",
        payload={
            "process_id": "process-direct-1",
            "result_node_id": "direct-dataset-source",
            "result_output_name": "output",
        },
    )
    captured = {}

    def status(**kwargs):
        captured.update(kwargs)
        return {
            "process_id": "process-direct-1",
            "status": "SUCCESS",
            "terminal": True,
            "downloadable": True,
            "result_file": {
                "file_name": "earthquake.csv",
                "download_url": (
                    "/api/piflow/v1/xdc/execution/process-direct-1/download"
                    "?result_node_id=direct-dataset-source"
                    "&result_output_name=output"
                ),
            },
        }

    monkeypatch.setattr(
        xdc_session_service.cross_dag_service,
        "get_cross_dag_execution_status",
        status,
    )

    result = xdc_session_service.get_xdc_task_execution_status(
        task_id=task_id,
        user_id="user-1",
    )

    assert captured["result_node_id"] == "direct-dataset-source"
    assert captured["result_output_name"] == "output"
    assert result["result_node_id"] == "direct-dataset-source"
    assert result["result_output_name"] == "output"
    assert memory_repository.tasks[task_id]["status"] == "COMPLETED"
    assert memory_repository.items[f"{task_id}:result-card"]["payload"][
        "file_name"
    ] == "earthquake.csv"
