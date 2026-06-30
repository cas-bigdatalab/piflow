from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any

from infra.config_loader import get_settings
from infra.config_loader import resolve_workspace_root
from runtime.workspace_manager import WorkspaceManager
from tools.excutor.excutor_utils import resolve_dag_definition_skills

_PROCESS_REGISTRY: dict[str, Any] = {}
_PROCESS_REGISTRY_LOCK = threading.Lock()
_PATH_LIKE_PARAM_SUFFIXES = ("_path", "_file", "_dir")


def register_running_process(process: Any) -> None:
    with _PROCESS_REGISTRY_LOCK:
        _PROCESS_REGISTRY[process.pid()] = process


def unregister_running_process(process_id: str) -> None:
    with _PROCESS_REGISTRY_LOCK:
        _PROCESS_REGISTRY.pop(process_id, None)


def get_registered_process(process_id: str) -> Any | None:
    with _PROCESS_REGISTRY_LOCK:
        return _PROCESS_REGISTRY.get(process_id)


def stop_registered_process(process_id: str) -> bool:
    process = get_registered_process(process_id)
    if process is None:
        return False
    process.stop()
    return True


def init_piflow_run_tracking_db() -> None:
    """Initialize PiFlow's canonical run tracking tables."""
    from database.postgres import get_connection
    from cn.piflow.runtime.store.postgres.schema import initialize_postgres_schema

    conn = get_connection()
    try:
        initialize_postgres_schema(conn)
    finally:
        conn.close()


def _looks_like_path_param(param_name: str) -> bool:
    normalized = (param_name or "").strip().lower()
    return normalized.endswith(_PATH_LIKE_PARAM_SUFFIXES) or normalized in {
        "path",
        "file_path",
        "input_path",
        "output_path",
        "input_file",
        "output_file",
        "input_dir",
        "output_dir",
    }


def _normalize_manual_runtime_path(
    raw_value: str,
    *,
    param_name: str,
    workspace: WorkspaceManager,
    user_id: str | None,
) -> str:
    value = str(raw_value or "").strip()
    if not value or not _looks_like_path_param(param_name):
        return value

    path_obj = Path(value)
    if path_obj.is_absolute():
        try:
            return str(workspace.resolve_virtual_path(value))
        except ValueError:
            if user_id:
                try:
                    return str(workspace.resolve_user_virtual_path(user_id, value))
                except ValueError as exc:
                    raise ValueError(f"path escapes workspace: {value}") from exc
            raise

    if user_id:
        return str(workspace.resolve_user_virtual_path(user_id, value))
    return str(workspace.resolve_virtual_path(value))


def _normalize_frontend_runtime_paths(
    definition_json: dict[str, Any],
    *,
    workspace_root: str | Path | None,
    user_id: str | None,
) -> dict[str, Any]:
    workspace = WorkspaceManager()
    workspace.root = resolve_workspace_root(workspace_root)
    workspace.artifacts = workspace.root / "artifacts"
    workspace.outputs = workspace.root / "outputs"
    workspace.temp = workspace.root / "temp"
    workspace.logs = workspace.root / "logs"

    normalized_nodes = []
    for node in definition_json.get("nodes", []):
        skill = node.get("skill") or {}
        skill_name = str(skill.get("skill_name") or node.get("skill_name") or "").strip()
        input_params = []
        for param in node.get("input_params", []) or []:
            updated = dict(param)
            if str(updated.get("value_mode", "")).strip() == "manual":
                param_name = str(updated.get("param_name") or "").strip()
                param_value = updated.get("param_value", "")
                if skill_name == "sink_stop" and param_name == "path":
                    updated["param_value"] = _normalize_manual_runtime_path(
                        param_value,
                        param_name="output_path",
                        workspace=workspace,
                        user_id=user_id,
                    )
                else:
                    updated["param_value"] = _normalize_manual_runtime_path(
                        param_value,
                        param_name=param_name,
                        workspace=workspace,
                        user_id=user_id,
                    )
            input_params.append(updated)
        normalized_nodes.append({**node, "input_params": input_params})

    return {**definition_json, "nodes": normalized_nodes}


def submit_frontend_dag(
    definition_json: dict[str, Any],
    *,
    workspace_root: str | Path | None = None,
    user_id: str | None = None,
    python_home: str | None = None,
) -> Any:
    from piflow_engine.cn.piflow.core.flow_bean import FlowBean
    from piflow_engine.cn.piflow.core.frontend_dag_converter import convert_frontend_dag_to_piflow
    from piflow_engine.cn.piflow.core.runner import Runner
    from piflow_engine.cn.piflow.engine.local.constants import (
        RUNNER_CONTEXT_PYTHON_HOME,
        RUNNER_CONTEXT_SANDBOX_BACKEND,
        RUNNER_CONTEXT_WORKSPACE_ROOT,
        RUNNER_CONTEXT_USER_ID,
    )
    from piflow_engine.cn.piflow.runtime.logging import RunLogger
    from piflow_engine.cn.piflow.runtime.run_tracking_listener import RunTrackingListener
    from piflow_engine.cn.piflow.runtime.store.postgres.PostgresRunStore import PostgresRunStore
    from database.postgres import get_connection

    class ClosingRunTrackingListener(RunTrackingListener):
        def __init__(self, *, run_store: PostgresRunStore, run_logger: RunLogger):
            super().__init__(run_store=run_store, run_logger=run_logger)
            self._closing_run_store = run_store

        def on_process_completed(self, ctx) -> None:
            try:
                super().on_process_completed(ctx)
            finally:
                unregister_running_process(ctx.get_process().pid())
                self._closing_run_store.close()

        def on_process_failed(self, ctx, error: Exception) -> None:
            try:
                super().on_process_failed(ctx, error)
            finally:
                unregister_running_process(ctx.get_process().pid())
                self._closing_run_store.close()

        def on_process_aborted(self, ctx) -> None:
            try:
                super().on_process_aborted(ctx)
            finally:
                unregister_running_process(ctx.get_process().pid())
                self._closing_run_store.close()

    normalized_definition = _normalize_frontend_runtime_paths(
        definition_json,
        workspace_root=workspace_root,
        user_id=user_id,
    )
    resolve_dag_json = resolve_dag_definition_skills(normalized_definition)
    piflow_json = convert_frontend_dag_to_piflow(resolve_dag_json)
    flow = FlowBean.from_dict(piflow_json).construct_flow()

    workspace = resolve_workspace_root(workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    sandbox_backend = "docker" if settings.piflow_engine.sandbox_enabled else "local"

    run_store = PostgresRunStore(connection=get_connection())
    run_logger = RunLogger(workspace)
    runner = (
        Runner.create()
        .bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
        .bind(RUNNER_CONTEXT_USER_ID, user_id or "")
        .bind(RUNNER_CONTEXT_PYTHON_HOME, python_home or sys.executable)
        .bind(RUNNER_CONTEXT_SANDBOX_BACKEND, sandbox_backend)
    )
    runner.add_listener(
        ClosingRunTrackingListener(
            run_store=run_store,
            run_logger=run_logger,
        )
    )
    process = runner.start(flow)
    register_running_process(process)
    return process
