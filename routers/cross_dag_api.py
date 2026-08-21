"""跨域规划接口。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from runtime.cross_dag.schema import CrossDagError
from security.auth_dependency import get_current_user
from services.cross_dag_service import (
    CrossDagExecutionNotFound,
    CrossDagExecutionNotReady,
    bind_and_execute_cross_dag_pre_bind,
    compile_cross_dag_plan,
    create_cross_dag_plan,
    create_cross_dag_pre_bind_plan,
    execute_cross_dag_plan,
    get_cross_dag_execution_status,
    get_cross_dag_plan,
    handoff_check_cross_dag_plan,
    list_cross_dag_context,
    prepare_cross_dag_result_download,
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


@router.post("/xdc/plan/pre-bind")
async def create_cross_dag_pre_bind_plan_api(
    current_user=Depends(get_current_user),
    user_request: str = Body(..., embed=True, description="用户自然语言任务"),
    detail: bool = Body(False, embed=True, description="是否附带完整规划详情"),
):
    """生成逻辑 DAG 和候选副本，停在副本绑定之前。"""
    try:
        result = create_cross_dag_pre_bind_plan(
            user_request=user_request,
            user_id=current_user["user_id"],
            detail=detail,
        )
        return {"message": "success", "result": result, "code": 200}
    except CrossDagError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/bind-and-execute")
async def bind_and_execute_cross_dag_pre_bind_api(
    current_user=Depends(get_current_user),
    plan_id: str = Body(..., embed=True, description="预绑定规划 ID"),
    detail: bool = Body(False, embed=True, description="是否附带完整规划详情"),
):
    """完成副本绑定、DAG 划分和嵌套校验，并立即提交执行。"""
    try:
        result = bind_and_execute_cross_dag_pre_bind(
            plan_id=plan_id,
            user_id=current_user["user_id"],
            detail=detail,
        )
        return {"message": "success", "result": result, "code": 200}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
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


@router.get("/xdc/execution/{process_id}/status")
async def get_cross_dag_execution_status_api(
    process_id: str,
    current_user=Depends(get_current_user),
    result_node_id: str = Query("", description="可选：指定结果节点 ID"),
    result_output_name: str = Query("", description="可选：指定结果输出端口"),
):
    """查询跨域根任务状态；前端可轮询，SUCCESS 后返回下载信息。"""
    try:
        result = get_cross_dag_execution_status(
            process_id=process_id,
            user_id=current_user["user_id"],
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
        return {"message": "success", "result": result, "code": 200}
    except CrossDagExecutionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"查询远端执行状态失败: {e}")


@router.get("/xdc/execution/{process_id}/download")
async def download_cross_dag_execution_result_api(
    process_id: str,
    current_user=Depends(get_current_user),
    result_node_id: str = Query("", description="可选：指定结果节点 ID"),
    result_output_name: str = Query("", description="可选：指定结果输出端口"),
):
    """下载执行成功后的最终产物。响应体为文件二进制。"""
    try:
        result = prepare_cross_dag_result_download(
            process_id=process_id,
            user_id=current_user["user_id"],
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
        return FileResponse(
            path=result.path,
            filename=result.file_name,
            media_type=result.media_type,
            headers={"Cache-Control": "no-store", "X-XDC-Process-ID": process_id},
            background=BackgroundTask(_remove_download_temp_file, result.path),
        )
    except CrossDagExecutionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CrossDagExecutionNotReady as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载远端执行结果失败: {e}")


def _remove_download_temp_file(path: Path) -> None:
    path.unlink(missing_ok=True)
