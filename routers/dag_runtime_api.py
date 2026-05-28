from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, logger

from security.auth_dependency import get_current_user
from services.dag_runtime_service import (
    get_dag_run_detail,
    get_dag_run_executions,
    get_dag_run_progress,
    get_dag_runtime_processes,
    run_dag_task,
    stop_dag_run,
)

router = APIRouter()


@router.post("/dag/runtime/run")
async def run_dag_runtime_api(
    current_user=Depends(get_current_user),
    dag_task_id: str = Body(..., description="任务id"),
):
    user_id_temp = current_user["user_id"]
    logger.logger.info(f"get json from dag_task_id:{dag_task_id}")
    logger.logger.info(f"get json from user_id_temp {user_id_temp}")
    print(f"get json from dag_task_id:{dag_task_id}")
    print(f"get json from user_id_temp {user_id_temp}")
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/execution/detail")
async def get_dag_runtime_execution_detail_api(
    process_id: str,
):
    try:
        result = get_dag_run_detail(process_id=process_id)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/execution/progress")
async def get_dag_runtime_execution_progress_api(
    process_id: str,
):
    try:
        result = get_dag_run_progress(process_id=process_id)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dag/runtime/executions")
async def get_dag_runtime_executions_api(
    dag_task_id: str = "",
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
):
    try:
        if not dag_task_id:
            raise HTTPException(status_code=400, detail="dag_task_id is required")
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
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dag/runtime/stop")
async def stop_dag_runtime_api(
    process_id: str = Body(..., description="运行实例ID"),
):
    try:
        result = stop_dag_run(process_id=process_id)
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
