from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any

from infra.config_loader import get_settings
from infra.config_loader import resolve_workspace_root
from tools.excutor.excutor_utils import resolve_dag_definition_skills

_PROCESS_REGISTRY: dict[str, Any] = {}
_PROCESS_REGISTRY_LOCK = threading.Lock()


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

    resolve_dag_json = resolve_dag_definition_skills(definition_json)
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
