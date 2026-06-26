from __future__ import annotations

from typing import Any

from services.dag_panel_service import get_panel_dag_json
from runtime.dag_manager import get_dag_task
from runtime.piflow_adapter import stop_registered_process, submit_frontend_dag
from runtime.piflow_run_query import (
    get_piflow_stop_log_paths_by_job_id,
    get_piflow_run_detail,
    get_piflow_run_progress,
    get_piflow_process_status_counts,
    list_piflow_processes,
    list_piflow_runs_by_task_id,
)
from runtime.workspace_manager import WorkspaceManager


def get_dag_task_identity_by_process_id(
    *,
    process_id: str,
) -> dict[str, Any] | None:
    result = get_piflow_run_progress(process_id)
    if result is None:
        return None

    flow_uuid = result.get("flow_uuid") or result.get("dag_task_id")
    return {
        **result,
        "process_id": process_id,
        "dag_task_id": flow_uuid,
        "flow_uuid": flow_uuid,
    }


def is_dag_task_owned_by_user(
    *,
    dag_task_id: str,
    user_id: str,
) -> bool:
    if not dag_task_id or not user_id:
        return False

    dag_task = get_dag_task(dag_task_id)
    if dag_task is None:
        return False

    return dag_task.create_user_id == user_id


def get_stop_log_paths_by_job_id(
    *,
    job_id: str,
) -> dict[str, Any] | None:
    result = get_piflow_stop_log_paths_by_job_id(job_id)
    if result is None:
        return None

    workspace = WorkspaceManager()

    def _to_workspace_relative(raw_path: str | None) -> str | None:
        if not raw_path:
            return None
        return workspace.to_workspace_relative_path(raw_path)

    return {
        "process_id": result.get("process_id"),
        "dag_task_id": result.get("dag_task_id"),
        "flow_uuid": result.get("flow_uuid"),
        "job_id": result.get("job_id"),
        "stop_name": result.get("stop_name"),
        "log_path": _to_workspace_relative(result.get("log_path")),
        "stdout_log_path": _to_workspace_relative(result.get("stdout_log_path")),
        "stderr_log_path": _to_workspace_relative(result.get("stderr_log_path")),
    }


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
        user_id=create_user_id,
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
    user_id: str | None = None,
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
        user_id=user_id,
    )


def get_dag_runtime_process_status_counts(
    *,
    dag_task_id: str | None = None,
    keyword: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    return get_piflow_process_status_counts(
        dag_task_id=dag_task_id,
        keyword=keyword,
        user_id=user_id,
    )


def stop_dag_run(
    *,
    process_id: str,
    run_progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run = run_progress or get_piflow_run_progress(process_id)
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
