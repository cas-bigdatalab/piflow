from fastapi import APIRouter
from fastapi import Body, Depends
from fastapi import HTTPException, Query

from enums.workflow_template_enums import TEMPLATE_TAG_VALUES
from schemas.workflow_template_schema import WorkflowTemplateCreateRequest
from services.workflow_template_service import save_workflow_template
from security.auth_dependency import get_current_user
from services.workflow_template_service import list_workflow_templates_by_params
from services.workflow_template_service import get_workflow_template_fields_info
from services.workflow_template_service import get_workflow_template_detail_info
from services.workflow_template_service import remove_workflow_template
from services.workflow_template_service import run_workflow_template

router = APIRouter()

@router.post("/workflow_templates/create_template")
async def create_workflow_template(
    req: WorkflowTemplateCreateRequest,
    current_user=Depends(get_current_user),
):
    try:
        result = save_workflow_template(
            user_id=current_user["user_id"],
            user_name=current_user["user_name"],
            template_name=req.template_name,
            dag_task_id=req.dag_task_id,
            description=req.description,
            template_json=req.template_json,
            disciplinary_field=req.disciplinary_field,
            tags=req.tags,
            version=req.version,
            db_id=req.db_id
        )
        return {
            "code": 200,
            "message": "workflow template created",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow_templates/run")
async def run_workflow_template_api(
    current_user=Depends(get_current_user),
    template_id: str = Body(..., description="流水线模板id"),
):
    try:
        result = run_workflow_template(
            user_id=current_user["user_id"],
            template_id=template_id,
        )
        return {
            "message": "success",
            "result": result,
            "code": 200,
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow_templates/list")
async def list_workflow_templates(
    page: int = Query(None, ge=1),
    page_size: int = Query(None, le=100),
    keyword: str = Query(""),
    disciplinary_field: str = Query(""),
    publisher: str = Query(""),
    current_user=Depends(get_current_user),
):
    try:
        result = list_workflow_templates_by_params(
            page=page,
            page_size=page_size,
            keyword=keyword,
            disciplinary_field=disciplinary_field,
            publisher=publisher,
            user_id=current_user["user_id"],
        )
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow_templates/fields")
async def get_workflow_template_fields(
    current_user=Depends(get_current_user),
):
    try:
        result = get_workflow_template_fields_info(user_id=current_user["user_id"])
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow_templates/detail/{template_id}")
async def get_workflow_template_detail(
    template_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_workflow_template_detail_info(template_id, user_id=current_user["user_id"])
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflow_templates/delete/{template_id}")
async def delete_workflow_template(
    template_id: str,
    current_user=Depends(get_current_user),
):
    try:
        deleted = remove_workflow_template(template_id, current_user["user_id"])
        return {
            "code": 200,
            "message": "workflow template deleted or not exists",
            "data": {"template_id": template_id, "deleted": deleted}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow_templates/get_tags")
async def get_workflow_template_tags(
    current_user=Depends(get_current_user),
):
    try:
        result = TEMPLATE_TAG_VALUES
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))