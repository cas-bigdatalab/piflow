"""Session-level demo replay; planning, RPC and the database are local fakes."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from runtime.cross_dag import run_store
from runtime.cross_dag.schema import (
    BindResult, CrossDagPlan, DatasetCoverage, FacetCoverage, SegmentGraph,
)
from services import cross_dag_demo_cache as cache, cross_dag_service as service
from services import xdc_session_service as sessions
from test_xdc_session_service import memory_repository, _collect_events, _pre_bind


@pytest.fixture
def demo_runtime(monkeypatch, tmp_path, memory_repository):
    import piflow_engine.cn.piflow.remote.client as remote

    config = json.loads(cache.CONFIG.read_text(encoding="utf-8"))
    config_path = tmp_path / "demo.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(cache, "CONFIG", config_path)
    monkeypatch.setattr(cache, "resolve_workspace_root", lambda: tmp_path)
    monkeypatch.setattr(service, "resolve_workspace_root", lambda: tmp_path)
    records, payloads = {}, {}
    counts = dict(plan=0, execute=0, rpc=0, download=0)
    state = SimpleNamespace(status="SUCCESS", fail_download=False)
    monkeypatch.setattr(run_store, "save_cross_dag_execution", lambda **kw: records.update({kw["process_id"]: kw}))
    monkeypatch.setattr(run_store, "get_cross_dag_execution", records.get)
    monkeypatch.setattr(run_store, "update_cross_dag_execution_status", lambda *a, **kw: None)

    class Remote:
        def __init__(self, target):
            assert target == "remote:1234"  # Cached handles must never reach RPC.
            counts["rpc"] += 1

        def get_run_status(self, run_id):
            return SimpleNamespace(status=state.status, message="")

        def get_run_result_meta(self, *, run_id, **kwargs):
            return SimpleNamespace(file_name="result.csv", file_size=len(payloads[run_id]), mime_type="text/csv")

        def download_result(self, *, run_id, target_path, **kwargs):
            counts["download"] += 1
            if state.fail_download:
                raise OSError("remote download unavailable")
            Path(target_path).write_bytes(payloads[run_id])

        def close(self):
            pass

    monkeypatch.setattr(remote, "RemoteExecutionClient", Remote)

    def plan(request, *, plan_id, on_stage):
        counts["plan"] += 1
        value = _pre_bind(plan_id)
        value.intent.user_request = request
        if request in [config["requests"][name] for name in ("earthquake", "chemistry")]:
            value.mode = "direct"
            value.satisfaction.mode = "direct"
            value.satisfaction.coverages = [
                DatasetCoverage(dataset_id=name, facets=[FacetCoverage("topic", "topic", "cover_all")])
                for name in ("dataset-a", "dataset-b")
            ]
        return value

    def finish(pre_bind, *, user_id, on_stage, selected_dataset_id=""):
        counts["execute"] += 1
        value = CrossDagPlan(
            plan_id=pre_bind.plan_id, mode=pre_bind.mode, intent=pre_bind.intent,
            logical_dag=pre_bind.logical_dag, validation=pre_bind.validation,
            bind_result=BindResult(), segment_graph=SegmentGraph(),
            nested_dsl={"task_id": pre_bind.plan_id},
        )
        process_id = f"remote-{counts['execute']}"
        records[process_id] = dict(process_id=process_id, user_id=user_id, plan_id=value.plan_id,
                                   execution_center_id="center", remote_grpc_target="remote:1234")
        payloads[process_id] = f"first artifact,{selected_dataset_id},{counts['execute']}".encode()
        return value, dict(process_id=process_id, status="SUBMITTED", result_node_id="save", result_output_name="output")

    monkeypatch.setattr(sessions, "plan_cross_dag_pre_bind", plan)
    monkeypatch.setattr(service, "_finalize_and_execute_pre_bind", finish)
    monkeypatch.setattr(service, "_finalize_and_execute_direct_pre_bind", finish)
    for name in ("_summarize_pre_bind", "_summarize", "_summarize_direct_session"):
        monkeypatch.setattr(service, name, lambda plan, detail=False: {
            "plan_id": plan.plan_id, "mode": plan.mode, "dag": {"task_id": plan.plan_id},
        })

    def start(name="earth_bundle", *, request=None):
        events = _collect_events(sessions.stream_xdc_session_pre_bind(
            session_id="session-1", user_id="user-1", user_request=request or config["requests"][name]))
        assert events[-1]["type"] == "done", events
        return events[-1]["result"]

    def bind(task_id, selection=None):
        events = _collect_events(sessions.stream_xdc_task_bind_and_execute(
            task_id=task_id, user_id="user-1", selected_dataset_id=selection))
        assert events[-1]["type"] == "done", events
        return events[-1]["result"]

    def poll(task_id):
        return sessions.get_xdc_task_execution_status(task_id=task_id, user_id="user-1")

    return SimpleNamespace(config=config, config_path=config_path, records=records, counts=counts,
                           state=state, start=start, bind=bind, poll=poll, memory=memory_repository)


@pytest.mark.parametrize("name", sorted(cache.DEMO_IDS))
def test_first_run_then_replay_new_task_and_download(demo_runtime, name):
    env = demo_runtime
    first = env.start(name)
    assert not first.get("cache_hit")
    first_bound = env.bind(first["task_id"])
    first_status = env.poll(first["task_id"])
    assert first_status["downloadable"]
    assert env.counts["download"] == 1  # Capture happens automatically on successful polling.
    baseline = dict(env.counts)

    second = env.start(name)
    second_bound = env.bind(second["task_id"])
    assert second["cache_hit"] and second_bound["execution"]["cache_hit"]
    assert second["plan_id"] != first["plan_id"]
    assert second_bound["execution"]["process_id"] != first_bound["execution"]["process_id"]
    assert second_bound["plan"]["dag"]["task_id"] == second["plan_id"]
    assert first["plan_id"] not in json.dumps(second_bound)
    assert env.memory.tasks[second["task_id"]]["status"] == "COMPLETED"
    detail = sessions.get_xdc_task_detail(task_id=second["task_id"], user_id="user-1")
    assert "result" in detail["snapshots"]
    assert any(item["item_type"] == "RESULT_CARD" for item in detail["items"])
    process_id = second_bound["execution"]["process_id"]
    downloaded = service.prepare_cross_dag_result_download(process_id=process_id, user_id="user-1")
    expected = b"first artifact,dataset-a,1" if name in {"earthquake", "chemistry"} else b"first artifact,,1"
    assert downloaded.path.read_bytes() == expected
    downloaded.path.unlink()  # Same cleanup as the existing FileResponse.
    assert env.poll(second["task_id"])["downloadable"]
    assert env.counts == baseline  # No model/planning, execution, metadata RPC or remote download.
    with pytest.raises(PermissionError):
        service.prepare_cross_dag_result_download(process_id=process_id, user_id="other-user")
    with pytest.raises(PermissionError):
        service.get_cross_dag_execution_status(process_id=process_id, user_id="other-user")
    wrong_output = service.get_cross_dag_execution_status(
        process_id=process_id, user_id="user-1", result_node_id="other-output")
    assert not wrong_output["downloadable"]
    env.start(name)  # Completed cache tasks do not block a new turn.


def test_only_exact_demo_prompts_and_disable(demo_runtime):
    env = demo_runtime
    for prompt in env.config["requests"].values():
        assert cache.for_request(prompt)
        assert cache.for_request("\n " + prompt + "\n")
        assert cache.for_request(prompt + "请增加清洗步骤") is None
    assert cache.for_request(env.config["requests"]["surface_area"].replace("30", "50")) is None
    for _ in range(2):
        value = env.start(request="这是另一个新请求")
        env.bind(value["task_id"])
        env.poll(value["task_id"])
    assert env.counts["plan"] == env.counts["execute"] == 2
    assert env.counts["download"] == 0
    env.config["enabled"] = False
    env.config_path.write_text(json.dumps(env.config), encoding="utf-8")
    assert cache.for_request(env.config["requests"]["earthquake"]) is None


def test_direct_choices_keep_separate_results(demo_runtime):
    env = demo_runtime
    for selection in ["dataset-a", "dataset-b", "dataset-a", "dataset-b"]:
        value = env.start("chemistry")
        bound = env.bind(value["task_id"], selection)
        env.poll(value["task_id"])
        if bound["execution"].get("cache_hit"):
            artifact = service.prepare_cross_dag_result_download(
                process_id=bound["execution"]["process_id"], user_id="user-1")
            assert selection.encode() in artifact.path.read_bytes()
    assert env.counts["plan"] == 1
    assert env.counts["execute"] == env.counts["download"] == 2


@pytest.mark.parametrize("status,fail_download", [("FAILED", False), ("SUCCESS", True)])
def test_failed_execution_or_download_never_published(demo_runtime, status, fail_download):
    env = demo_runtime
    env.state.status, env.state.fail_download = status, fail_download
    first = env.start()
    env.bind(first["task_id"])
    observed = env.poll(first["task_id"])
    assert observed["status"] == status  # Cache failure never changes the real result.
    assert not list(cache._root().glob("entries/*/*/results/*.json"))
    env.state.status, env.state.fail_download = "SUCCESS", False
    next_task = env.start()
    assert next_task["cache_hit"]  # Valid plan is reusable even if its first execution failed.
    env.bind(next_task["task_id"])
    env.poll(next_task["task_id"])
    assert env.counts["execute"] == 2
    assert list(cache._root().glob("entries/*/*/results/*.json"))


def test_corrupt_file_falls_back_and_clear_preserves_old_downloads(demo_runtime):
    env = demo_runtime
    first = env.start()
    env.bind(first["task_id"])
    env.poll(first["task_id"])
    artifact = next(cache._root().glob("objects/*/artifact"))
    artifact.write_bytes(b"corrupted")
    second = env.start()
    rebound = env.bind(second["task_id"])
    assert not rebound["execution"].get("cache_hit")
    env.poll(second["task_id"])
    third = env.start()
    cached = env.bind(third["task_id"])["execution"]
    assert cached["cache_hit"]
    assert cache.clear("earth_bundle") > 0
    # An old real task must not republish an index after clearing.
    env.poll(second["task_id"])
    assert not list(cache._root().glob("entries/*/*/results/*.json"))
    env.config["enabled"] = False
    env.config_path.write_text(json.dumps(env.config), encoding="utf-8")
    old_download = service.prepare_cross_dag_result_download(process_id=cached["process_id"], user_id="user-1")
    assert old_download.path.read_bytes() == b"first artifact,,2"
    assert not env.start().get("cache_hit")


def test_plan_persistence_first_valid_wins_and_corrupt_falls_back(demo_runtime):
    prompt = demo_runtime.config["requests"]["earth_bundle"]
    store = cache.for_request(prompt)
    plan = _pre_bind("old-id")
    plan.validation.error("bad plan")
    store.save_plan(plan, {})
    assert store.load_plan("new-id") is None
    plan.validation.errors.clear()
    plan.mode = "unavailable"
    store.save_plan(plan, {})
    assert store.load_plan("new-id") is None
    plan.mode = "composition"
    store.save_plan(plan, {"plan_id": "old-id", "conclusion": "first"})
    store.save_plan(plan, {"plan_id": "old-id", "conclusion": "second"})
    # Fresh instance, as after a process restart; no in-memory plan state required.
    restored, view = cache.for_request(prompt).load_plan("new-id", detail=True)
    assert restored.plan_id == restored.logical_dag.task_id == "new-id"
    assert view["conclusion"] == "first"
    assert "detail" in view
    assert "detail" not in store.load_plan("other-id")[1]
    (store.folder / "plan.json").write_text("broken", encoding="utf-8")
    assert store.load_plan("new-id") is None


def test_alternative_output_does_not_poison_result_cache(demo_runtime):
    env = demo_runtime
    first = env.start()
    env.bind(first["task_id"])
    sessions.get_xdc_task_execution_status(task_id=first["task_id"], user_id="user-1", result_node_id="another")
    assert env.counts["download"] == 0


def test_repoll_does_not_overwrite_first_success(demo_runtime):
    env = demo_runtime
    first = env.start()
    bound = env.bind(first["task_id"])
    env.poll(first["task_id"])
    baseline = env.counts["download"]
    # Re-polling the original successful run must not overwrite or download again.
    env.poll(first["task_id"])
    assert env.counts["download"] == baseline
    assert not bound["execution"].get("cache_hit")
