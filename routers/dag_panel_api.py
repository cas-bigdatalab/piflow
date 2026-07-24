from fastapi import APIRouter, Depends, Body, File, UploadFile

from schemas.dag.DagDefinition import DagDefinition
from security.auth_dependency import (
    get_current_user,
)
from services.dag_panel_service import get_user_dag_tasks, save_dag_panel, get_panel_dag_json, \
    get_skill_info_by_id, get_dag_skills_by_condition, create_dag_task, update_dag_task, remove_dag_task, \
    get_dag_json_by_message_id, remove_local_skill, enable_local_skill, upload_skill_package
from runtime.dag_manager import get_skill_type_counts

router = APIRouter()


@router.get("/dag/task/getTasks")
async def get_tasks(
    current_user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
):
    try:
        result = get_user_dag_tasks(
            create_user_id=current_user["user_id"],
            page=page,
            page_size=page_size,
            keyword=keyword,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/task/createTask")
async def create_task(
    current_user=Depends(get_current_user),
    description: str = Body(None, description="任务描述"),
    message_id: str = Body(None, description="消息id（只有大模型生成的任务才有，否则为空）"),
    task_name: str = Body(None, description="任务名称"),
):
    try:
        result = create_dag_task(
            create_user_id=current_user["user_id"],
            description=description,
            message_id=message_id,
            task_name=task_name,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/task/updateTask")
async def update_task(
    current_user=Depends(get_current_user),
    dag_name: str = Body(None, description="任务名称"),
    dag_task_id: str = Body(None, description="任务id"),
    description: str = Body(None, description="任务描述"),
    message_id: str = Body(None, description="消息id（只有大模型生成的任务才有，否则为空）"),
):
    try:
        result = update_dag_task(
            create_user_id=current_user["user_id"],
            dag_name=dag_name,
            dag_task_id=dag_task_id,
            description=description,
            message_id=message_id,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/task/deleteTask")
async def delete_task(
    current_user=Depends(get_current_user),
    dag_task_id: str = Body(None, description="任务id"),
):
    try:
        result = remove_dag_task(
            create_user_id=current_user["user_id"],
            dag_task_id=dag_task_id,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/panel/save")
async def save_dag_panel_api(
    definition_json: DagDefinition,
    current_user=Depends(get_current_user),
):
    try:
        result = save_dag_panel(
            definition_json=definition_json.model_dump(),
            create_user_id=current_user["user_id"],
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }

@router.post("/dag/panel/getDSLJson")
async def get_dag_Json_api(
    dag_task_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_panel_dag_json(
            create_user_id=current_user["user_id"],
            dag_task_id=dag_task_id,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }

@router.get("/dag/skill/getSkillInfo")
async def get_skill_info_api(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_skill_info_by_id(skill_id)

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.get("/dag/skill/listSkills")
async def list_skills_api(
    current_user=Depends(get_current_user),
    page: int = None,
    page_size: int = None,
    keyword: str = None,
    skill_type: str = None,
    version: str = None,
    disciplinary_field: str = None,
    publisher: str = None,
):
    try:
        result = get_dag_skills_by_condition(
            page=page,
            page_size=page_size,
            keyword=keyword,
            skill_type=skill_type,
            version=version,
            disciplinary_field=disciplinary_field,
            publisher=publisher,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.get("/dag/panel/getDSLJsonByMessageId")
async def get_json_by_message_id(
    message_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_dag_json_by_message_id(
            create_user_id=current_user["user_id"],
            message_id=message_id,
        )

        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.get("/dag/skill/getSkillTypeCounts")
async def get_skill_type_counts_api():
    try:
        data = get_skill_type_counts()
        return {
            "code": 200,
            "data": data,
            "total": len(data),
        }
    except Exception as e:
        return {
            "code": 500,
            "message": str(e),
        }


@router.post("/dag/skill/removeLocalSkill")
async def remove_local_skill_api(
    skill_id: str = Body(..., description="dag_skills表中的skill_id"),
    current_user=Depends(get_current_user),
):
    try:
        result = remove_local_skill(skill_id)
        if not result.get("success"):
            return {
                "message": result.get("message", "remove failed"),
                "result": None,
                "code": 500,
            }
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/skill/enableLocalSkill")
async def enable_local_skill_api(
    skill_id: str = Body(..., description="dag_skills表中的skill_id"),
    current_user=Depends(get_current_user),
):
    try:
        result = enable_local_skill(skill_id)
        if not result.get("success"):
            return {
                "message": result.get("message", "enable failed"),
                "result": None,
                "code": 500,
            }
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }


@router.post("/dag/skill/uploadPackage")
async def upload_skill_package_api(
    file: UploadFile = File(..., description="skill zip压缩包"),
    current_user=Depends(get_current_user),
):
    try:
        file_bytes = await file.read()
        result = upload_skill_package(file_bytes, file.filename or "upload.zip")
        if not result.get("success"):
            return {
                "message": result.get("message", "upload failed"),
                "result": None,
                "code": 500,
            }
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except Exception as e:
        return {
            "message": str(e),
            "result": None,
            "code": 500,
        }
