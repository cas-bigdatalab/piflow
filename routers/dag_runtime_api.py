from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, logger

from security.auth_dependency import get_current_user
from services.dag_runtime_service import (
    get_dag_task_identity_by_process_id,
    get_dag_run_detail,
    get_dag_run_executions,
    get_dag_run_progress,
    get_dag_runtime_process_status_counts,
    get_dag_runtime_processes,
    get_stop_log_paths_by_job_id,
    is_dag_task_owned_by_user,
    run_dag_task,
    stop_dag_run,
)

router = APIRouter()


@router.post("/dag/runtime/run")
async def run_dag_runtime_api(
    current_user=Depends(get_current_user),
    dag_task_id: str = Body(..., description="任务id"),
):
    try:
        if not is_dag_task_owned_by_user(
            dag_task_id=dag_task_id,
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to run this dag task")
        result = run_dag_task(
            create_user_id=current_user["user_id"],
            dag_task_id=dag_task_id,
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/execution/detail")
async def get_dag_runtime_execution_detail_api(
    process_id: str,
    current_user=Depends(get_current_user),
):
    try:
        identity = get_dag_task_identity_by_process_id(process_id=process_id)
        if identity is None:
            raise HTTPException(status_code=404, detail=f"piflow run not found: {process_id}")
        if not is_dag_task_owned_by_user(
            dag_task_id=identity["dag_task_id"],
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to access this dag run")
        result = get_dag_run_detail(process_id=process_id)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/execution/progress")
async def get_dag_runtime_execution_progress_api(
    process_id: str,
    current_user=Depends(get_current_user),
):
    try:
        identity = get_dag_task_identity_by_process_id(process_id=process_id)
        if identity is None:
            raise HTTPException(status_code=404, detail=f"piflow run not found: {process_id}")
        if not is_dag_task_owned_by_user(
            dag_task_id=identity["dag_task_id"],
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to access this dag run")
        result = get_dag_run_progress(process_id=process_id)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/executions")
async def get_dag_runtime_executions_api(
    current_user=Depends(get_current_user),
    dag_task_id: str = "",
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
):
    try:
        if not dag_task_id:
            raise HTTPException(status_code=400, detail="dag_task_id is required")
        if not is_dag_task_owned_by_user(
            dag_task_id=dag_task_id,
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to access this dag task")
        result = get_dag_run_executions(
            dag_task_id=dag_task_id,
            page=page,
            page_size=page_size,
            status=status,
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/processes")
async def get_dag_runtime_processes_api(
    current_user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    dag_task_id: str | None = None,
    running_only: bool | None = None,
    keyword: str | None = None,
):
    try:
        result = get_dag_runtime_processes(
            page=page,
            page_size=page_size,
            status=status,
            dag_task_id=dag_task_id,
            running_only=running_only,
            keyword=keyword,
            user_id=current_user["user_id"],
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/processes/status-counts")
async def get_dag_runtime_process_status_counts_api(
    current_user=Depends(get_current_user),
    dag_task_id: str | None = None,
    keyword: str | None = None,
):
    try:
        if dag_task_id and not is_dag_task_owned_by_user(
            dag_task_id=dag_task_id,
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to access this dag task")
        result = get_dag_runtime_process_status_counts(
            dag_task_id=dag_task_id,
            keyword=keyword,
            user_id=current_user["user_id"],
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dag/runtime/stop")
async def stop_dag_runtime_api(
    current_user=Depends(get_current_user),
    process_id: str = Body(..., description="运行实例ID"),
):
    try:
        identity = get_dag_task_identity_by_process_id(process_id=process_id)
        if identity is None:
            raise HTTPException(status_code=404, detail=f"piflow run not found: {process_id}")
        if not is_dag_task_owned_by_user(
            dag_task_id=identity["dag_task_id"],
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to stop this dag run")
        result = stop_dag_run(process_id=process_id, run_progress=identity)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/stop/log-paths")
async def get_dag_runtime_stop_log_paths_api(
    job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_stop_log_paths_by_job_id(job_id=job_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"piflow stop job not found: {job_id}")
        if not is_dag_task_owned_by_user(
            dag_task_id=result["dag_task_id"],
            user_id=current_user["user_id"],
        ):
            raise HTTPException(status_code=403, detail="no permission to access this stop log")
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
