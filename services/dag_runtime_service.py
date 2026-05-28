from __future__ import annotations

from typing import Any

from services.dag_panel_service import get_panel_dag_json
from runtime.piflow_adapter import stop_registered_process, submit_frontend_dag
from runtime.piflow_run_query import (
    get_piflow_run_detail,
    get_piflow_run_progress,
    list_piflow_processes,
    list_piflow_runs_by_task_id,
)


def run_dag_task(
    *,
    create_user_id: str,
    dag_task_id: str,
    workspace_root: str | None = None,
    python_home: str | None = None,
) -> dict[str, Any]:
    definition_json = get_panel_dag_json(
        create_user_id=create_user_id,
        dag_task_id=dag_task_id,
    )
    if definition_json is None:
        raise ValueError(f"dag definition not found: {dag_task_id}")

    process = submit_frontend_dag(
        definition_json=definition_json,
        workspace_root=workspace_root,
        python_home=python_home,
    )

    return {
        "dag_task_id": dag_task_id,
        "process_id": process.pid(),
        "status": "SUBMITTED",
    }


def get_dag_run_detail(
    *,
    process_id: str,
) -> dict[str, Any]:
    result = get_piflow_run_detail(process_id)
    if result is None:
        raise ValueError(f"piflow run not found: {process_id}")
    return result


def get_dag_run_progress(
    *,
    process_id: str,
) -> dict[str, Any]:
    result = get_piflow_run_progress(process_id)
    if result is None:
        raise ValueError(f"piflow run not found: {process_id}")
    return result


def get_dag_run_executions(
    *,
    dag_task_id: str,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    return list_piflow_runs_by_task_id(
        dag_task_id,
        page=page,
        page_size=page_size,
        status=status,
    )


def get_dag_runtime_processes(
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    dag_task_id: str | None = None,
    running_only: bool | None = None,
    keyword: str | None = None,
) -> dict[str, Any]:
    if page < 1:
        raise ValueError("page must be >= 1")
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    return list_piflow_processes(
        page=page,
        page_size=page_size,
        status=status,
        dag_task_id=dag_task_id,
        running_only=running_only,
        keyword=keyword,
    )


def stop_dag_run(
    *,
    process_id: str,
) -> dict[str, Any]:
    run = get_piflow_run_progress(process_id)
    if run is None:
        raise ValueError(f"piflow run not found: {process_id}")

    if run.get("finished_at") is not None:
        return {
            "process_id": process_id,
            "status": run.get("status"),
            "message": "process already finished",
        }

    stopped = stop_registered_process(process_id)
    if not stopped:
        raise ValueError(f"running process not found in local registry: {process_id}")

    return {
        "process_id": process_id,
        "status": "CANCELLED",
        "message": "stop requested",
    }
