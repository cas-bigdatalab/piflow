from __future__ import annotations

from typing import Any

from services.dag_panel_service import get_panel_dag_json
from runtime.piflow_adapter import submit_frontend_dag
from runtime.piflow_run_query import get_piflow_run_detail


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
