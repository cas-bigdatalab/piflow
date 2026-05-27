from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from security.auth_dependency import get_current_user
from services.dag_runtime_service import get_dag_run_detail, run_dag_task

router = APIRouter()


@router.post("/dag/runtime/run")
async def run_dag_runtime_api(
    current_user=Depends(get_current_user),
    dag_task_id: str = Body(..., description="任务id"),
):
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
