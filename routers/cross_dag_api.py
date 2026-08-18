"""跨域规划接口。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from runtime.cross_dag.schema import CrossDagError
from security.auth_dependency import get_current_user
from services.cross_dag_service import (
    compile_cross_dag_plan,
    create_cross_dag_plan,
    execute_cross_dag_plan,
    get_cross_dag_plan,
    handoff_check_cross_dag_plan,
    list_cross_dag_context,
    stream_cross_dag_plan,
)
from services.cross_dag_trace import trace_cross_dag_plan

router = APIRouter()


@router.get("/xdc/context")
async def get_cross_dag_context_api(current_user=Depends(get_current_user)):
    """中心清单 + 已注册数据集。用于确认环境是否就绪。"""
    try:
        return {"message": "success", "result": list_cross_dag_context(), "code": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/plan")
async def create_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    user_request: str = Body(..., embed=True, description="用户自然语言任务"),
    detail: bool = Body(False, embed=True, description="附带内部完整数据，排障用"),
):
    """只规划不执行，返回需求理解、覆盖情况与方案（直接获取或 DAG）。"""
    try:
        result = create_cross_dag_plan(
            user_request=user_request,
            user_id=current_user["user_id"],
            detail=detail,
        )
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/trace")
async def trace_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    user_request: str = Body(..., embed=True, description="用户自然语言任务"),
):
    """全过程可观测：跑一遍真实链路，返回每个环节的输入、输出、耗时。"""
    try:
        result = trace_cross_dag_plan(
            user_request=user_request,
            user_id=current_user["user_id"],
        )
        return {"message": "success", "result": result, "code": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/compile")
async def compile_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    planning_json: dict = Body(..., description="规划态 DAG JSON"),
    dataset_ids: list[str] | None = Body(None, description="留空则从 dataset:// 引用自动扫描"),
    detail: bool = Body(False, description="附带内部完整数据，排障用"),
):
    """跳过 LLM，直接编译规划态 JSON。"""
    try:
        result = compile_cross_dag_plan(
            planning_json=planning_json,
            user_id=current_user["user_id"],
            dataset_ids=dataset_ids,
            detail=detail,
        )
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/plan/stream")
async def stream_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    user_request: str = Body(..., embed=True, description="用户自然语言任务"),
    detail: bool = Body(False, embed=True, description="附带内部完整数据，排障用"),
):
    """SSE 逐阶段推送规划过程，done 事件带最终方案。"""

    async def event_source():
        try:
            async for event in stream_cross_dag_plan(
                user_request=user_request,
                user_id=current_user["user_id"],
                detail=detail,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/xdc/plan/{plan_id}")
async def get_cross_dag_plan_api(
    plan_id: str,
    current_user=Depends(get_current_user),
    detail: bool = Query(False, description="附带内部完整数据，排障用"),
):
    try:
        result = get_cross_dag_plan(plan_id, detail=detail)
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/handoff")
async def handoff_check_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    plan_id: str = Body(..., embed=True, description="规划 ID"),
):
    """执行引擎对接自检：嵌套 DSL 每一层都过一遍引擎的转换与构图。"""
    try:
        result = handoff_check_cross_dag_plan(plan_id)
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/execute")
async def execute_cross_dag_plan_api(
    current_user=Depends(get_current_user),
    plan_id: str = Body(..., embed=True, description="规划 ID"),
):
    """把规划好的嵌套 DSL 交给现有执行引擎。"""
    try:
        result = execute_cross_dag_plan(
            plan_id=plan_id,
            user_id=current_user["user_id"],
        )
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
