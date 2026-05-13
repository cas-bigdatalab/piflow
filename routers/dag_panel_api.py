from fastapi import APIRouter, Depends

from security.auth_dependency import (
    get_current_user,
)
from services.dag_panel_service import get_user_dag_tasks

router = APIRouter()


@router.get("/dag/task/getTasks")
async def get_tasks(
    current_user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
):
    result = get_user_dag_tasks(
        create_user_id=current_user["user_id"],
        page=page,
        page_size=page_size,
        keyword=keyword,
    )

    return {
        "message": "success",
        "result": result,
    }