"""跨域规划接口。"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from runtime.cross_dag.schema import CrossDagError
from schemas.xdc_session_schema import (
    XdcSessionCreateRequest,
    XdcSessionPreBindRequest,
    XdcTaskBindExecuteRequest,
)
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
    get_cross_dag_pre_bind_plan,
    handoff_check_cross_dag_plan,
    list_cross_dag_context,
    prepare_cross_dag_result_download,
    stream_bind_and_execute_cross_dag_pre_bind,
    stream_cross_dag_plan,
    stream_cross_dag_pre_bind_plan,
)
from services.cross_dag_trace import trace_cross_dag_plan
from services.xdc_session_service import (
    XdcSessionConflict,
    XdcSessionNotFound,
    XdcTaskNotFound,
    create_xdc_session,
    delete_xdc_session,
    get_xdc_session_detail,
    get_xdc_task_detail,
    get_xdc_task_execution_status,
    list_xdc_sessions,
    stream_xdc_session_pre_bind,
    stream_xdc_task_bind_and_execute,
)

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


@router.post("/xdc/plan/pre-bind/stream")
async def stream_cross_dag_pre_bind_plan_api(
    current_user=Depends(get_current_user),
    user_request: str = Body(..., embed=True, description="用户自然语言任务"),
    detail: bool = Body(False, embed=True, description="是否附带完整规划详情"),
):
    """SSE 推送意图识别到绑定前逻辑 DAG 的生成过程。"""

    async def event_source():
        try:
            async for event in stream_cross_dag_pre_bind_plan(
                user_request=user_request,
                user_id=current_user["user_id"],
                detail=detail,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@router.post("/xdc/bind-and-execute/stream")
async def stream_bind_and_execute_cross_dag_pre_bind_api(
    current_user=Depends(get_current_user),
    plan_id: str = Body(..., embed=True, description="预绑定规划 ID"),
    detail: bool = Body(False, embed=True, description="是否附带完整规划详情"),
):
    """SSE 推送副本选择、跨域编译、校验和提交过程。"""

    async def event_source():
        try:
            async for event in stream_bind_and_execute_cross_dag_pre_bind(
                plan_id=plan_id,
                user_id=current_user["user_id"],
                detail=detail,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@router.get("/xdc/plan/pre-bind/{plan_id}")
async def get_cross_dag_pre_bind_plan_api(
    plan_id: str,
    current_user=Depends(get_current_user),
):
    """查询当前用户的副本绑定前方案。"""
    try:
        result = get_cross_dag_pre_bind_plan(
            plan_id,
            user_id=current_user["user_id"],
        )
        return {"message": "success", "result": result, "code": 200}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CrossDagError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/xdc/sessions")
async def create_xdc_session_api(
    request: XdcSessionCreateRequest,
    current_user=Depends(get_current_user),
):
    """创建一个属于当前登录用户的智能取数会话。"""
    try:
        result = create_xdc_session(
            user_id=current_user["user_id"],
            title=request.title,
        )
        return {"message": "success", "result": result, "code": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xdc/sessions")
async def list_xdc_sessions_api(
    current_user=Depends(get_current_user),
    page_num: int = Query(1, alias="pageNum", ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
):
    """分页返回当前用户的会话，供左侧“最近取数”渲染。"""
    try:
        result = list_xdc_sessions(
            user_id=current_user["user_id"],
            page_num=page_num,
            page_size=page_size,
        )
        return {"message": "success", "result": result, "code": 200}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xdc/sessions/{session_id}")
async def get_xdc_session_detail_api(
    session_id: str,
    current_user=Depends(get_current_user),
    after_item_id: int = Query(0, ge=0),
    item_limit: int = Query(1000, ge=1, le=2000),
):
    """恢复一个会话的任务列表和结构化时间线。"""
    try:
        result = get_xdc_session_detail(
            session_id=session_id,
            user_id=current_user["user_id"],
            after_item_id=after_item_id,
            item_limit=item_limit,
        )
        return {"message": "success", "result": result, "code": 200}
    except XdcSessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/xdc/sessions/{session_id}")
async def delete_xdc_session_api(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """软删除一个已无运行中任务的会话。"""
    try:
        result = delete_xdc_session(
            session_id=session_id,
            user_id=current_user["user_id"],
        )
        return {"message": "success", "result": result, "code": 200}
    except XdcSessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except XdcSessionConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xdc/tasks/{task_id}")
async def get_xdc_task_detail_api(
    task_id: str,
    current_user=Depends(get_current_user),
):
    """查询单个任务、过程项和可供前端展示的快照。"""
    try:
        result = get_xdc_task_detail(
            task_id=task_id,
            user_id=current_user["user_id"],
        )
        return {"message": "success", "result": result, "code": 200}
    except XdcTaskNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/xdc/sessions/{session_id}/tasks/plan/pre-bind/stream")
async def stream_xdc_session_pre_bind_api(
    session_id: str,
    request: XdcSessionPreBindRequest,
    current_user=Depends(get_current_user),
):
    """创建会话内任务，动态返回绑定前的规划过程。"""

    async def event_source():
        try:
            async for event in stream_xdc_session_pre_bind(
                session_id=session_id,
                user_request=request.user_request,
                user_id=current_user["user_id"],
                detail=request.detail,
                parent_task_id=request.parent_task_id,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/xdc/tasks/{task_id}/bind-and-execute/stream")
async def stream_xdc_task_bind_and_execute_api(
    task_id: str,
    request: XdcTaskBindExecuteRequest,
    current_user=Depends(get_current_user),
):
    """从数据库恢复预绑定计划，动态返回副本选择直至提交执行。"""

    async def event_source():
        try:
            async for event in stream_xdc_task_bind_and_execute(
                task_id=task_id,
                user_id=current_user["user_id"],
                detail=request.detail,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/xdc/tasks/{task_id}/execution/status")
async def get_xdc_task_execution_status_api(
    task_id: str,
    current_user=Depends(get_current_user),
    result_node_id: str = Query("", description="可选：指定结果节点 ID"),
    result_output_name: str = Query("", description="可选：指定结果输出端口"),
):
    """按会话任务查询执行状态，并把状态和结果同步到会话时间线。"""
    try:
        result = get_xdc_task_execution_status(
            task_id=task_id,
            user_id=current_user["user_id"],
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
        return {"message": "success", "result": result, "code": 200}
    except XdcTaskNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except XdcSessionConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    except CrossDagExecutionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"查询远端执行状态失败: {e}")
