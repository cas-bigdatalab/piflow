from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from runtime.schedule.models import ScheduleJob, ScheduleRun
from runtime.schedule.service import (
    _merge_schedule_times,
    create_schedule_job,
    delete_schedule_job,
    get_schedule_job,
    get_schedule_run,
    list_schedule_jobs,
    list_schedule_runs,
    pause_schedule_job,
    preview_trigger_config,
    start_schedule_job,
    stop_schedule_job,
    update_schedule_job,
)
from schemas.schedule.schedule_schema import (
    CreateScheduleRequest,
    TriggerConfigRequest,
    UpdateScheduleRequest,
)
from security.auth_dependency import get_current_user

router = APIRouter()


def _job_to_dict(job: ScheduleJob) -> dict:
    return {
        "schedule_job_id": job.schedule_job_id,
        "schedule_name": job.schedule_name,
        "dag_task_id": job.dag_task_id,
        "definition_id": job.definition_id,
        "owner_id": job.owner_id,
        "trigger_type": job.trigger_type,
        "cron_expression": job.cron_expression,
        "interval_seconds": job.interval_seconds,
        "start_time": job.start_time,
        "end_time": job.end_time,
        "timezone": job.timezone,
        "misfire_policy": job.misfire_policy,
        "max_running_instances": job.max_running_instances,
        "concurrency_policy": job.concurrency_policy,
        "status": job.status,
        "next_fire_time": job.next_fire_time,
        "last_fire_time": job.last_fire_time,
        "payload_json": job.payload_json,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def _run_to_dict(run: ScheduleRun) -> dict:
    return {
        "schedule_run_id": run.schedule_run_id,
        "schedule_job_id": run.schedule_job_id,
        "dag_task_id": run.dag_task_id,
        "definition_id": run.definition_id,
        "owner_id": run.owner_id,
        "planned_fire_time": run.planned_fire_time,
        "actual_fire_time": run.actual_fire_time,
        "process_id": run.process_id,
        "status": run.status,
        "attempt": run.attempt,
        "dispatch_owner": run.dispatch_owner,
        "dispatch_lease_until": run.dispatch_lease_until,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


@router.post("/schedules/create")
async def create_schedule_api(
    req: CreateScheduleRequest,
    current_user=Depends(get_current_user),
):
    try:
        start_time, end_time = _merge_schedule_times(
            trigger_type=req.trigger_type,
            start_date=req.start_date,
            execute_time=req.execute_time,
            end_date=req.end_date,
        )
        job = create_schedule_job(
            owner_id=current_user["user_id"],
            schedule_name=req.schedule_name,
            dag_task_id=req.dag_task_id,
            definition_id=req.definition_id,
            trigger_type=req.trigger_type,
            timezone=req.timezone,
            cron_expression=req.cron_expression,
            interval_seconds=req.interval_seconds,
            start_time=start_time,
            end_time=end_time,
            misfire_policy=req.misfire_policy,
            max_running_instances=req.max_running_instances,
            concurrency_policy=req.concurrency_policy,
            payload_json=req.payload_json,
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/list")
async def list_schedules_api(
    current_user=Depends(get_current_user),
    status: str | None = None,
    dag_task_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    try:
        result = list_schedule_jobs(
            owner_id=current_user["user_id"],
            status=status,
            dag_task_id=dag_task_id,
            page=page,
            page_size=page_size,
        )
        result["items"] = [_job_to_dict(item) for item in result["items"]]
        return {"message": "success", "result": result, "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/job/get")
async def get_schedule_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        job = get_schedule_job(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
        )
        if job is None:
            raise HTTPException(status_code=404, detail=f"schedule not found: {schedule_job_id}")
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/job/update")
async def update_schedule_api(
    schedule_job_id: str,
    req: UpdateScheduleRequest,
    current_user=Depends(get_current_user),
):
    try:
        start_time, end_time = _merge_schedule_times(
            trigger_type=None,
            start_date=req.start_date,
            execute_time=req.execute_time,
            end_date=req.end_date,
            timezone_name=req.timezone or "Asia/Shanghai",
        )
        job = update_schedule_job(
            schedule_job_id,
            owner_id=current_user["user_id"],
            schedule_name=req.schedule_name,
            cron_expression=req.cron_expression,
            start_time=start_time,
            end_time=end_time,
            timezone=req.timezone,
            misfire_policy=req.misfire_policy,
            max_running_instances=req.max_running_instances,
            concurrency_policy=req.concurrency_policy,
            payload_json=req.payload_json,
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/job/start")
async def start_schedule_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        job = start_schedule_job(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/job/pause")
async def pause_schedule_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        job = pause_schedule_job(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/job/stop")
async def stop_schedule_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        job = stop_schedule_job(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/job/delete")
async def delete_schedule_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
):
    try:
        job = delete_schedule_job(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
        )
        return {"message": "success", "result": _job_to_dict(job), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/runs/list")
async def list_schedule_runs_api(
    schedule_job_id: str,
    current_user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
):
    try:
        result = list_schedule_runs(
            schedule_job_id=schedule_job_id,
            owner_id=current_user["user_id"],
            page=page,
            page_size=page_size,
        )
        result["items"] = [_run_to_dict(item) for item in result["items"]]
        return {"message": "success", "result": result, "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/runs/get")
async def get_schedule_run_api(
    schedule_run_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_schedule_run(
            schedule_run_id=schedule_run_id,
            owner_id=current_user["user_id"],
        )
        if result is None:
            raise HTTPException(status_code=404, detail=f"schedule run not found: {schedule_run_id}")
        return {"message": "success", "result": result, "code": 200}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/trigger/preview")
async def preview_trigger_config_api(
    req: TriggerConfigRequest,
    current_user=Depends(get_current_user),
):
    """前端触发模式配置预览：把 UI 选择转成底层 trigger_type + cron/interval。

    前端拿返回值填到 CreateScheduleRequest 对应字段调创建接口。
    """
    try:
        result = preview_trigger_config(req)
        return {"message": "success", "result": result.model_dump(), "code": 200}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
