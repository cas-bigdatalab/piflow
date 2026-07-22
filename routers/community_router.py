from fastapi import APIRouter, Depends, HTTPException, Query

from security.auth_dependency import get_current_user
from services.community_service import (
    get_community_skill_by_id,
    get_community_skill_by_name,
    install_community_skill,
    list_community_skills,
    remove_community_skill,
)

router = APIRouter()


@router.get("/community/skills/list")
async def get_community_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    language: str = Query(""),
    disciplinary_field: str = Query(""),
    current_user=Depends(get_current_user),
):
    try:
        result = list_community_skills(
            page=page,
            page_size=page_size,
            keyword=keyword,
            language=language,
            disciplinary_field=disciplinary_field,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/community/skills/detail/name/{skill_name}")
async def get_skill_detail_by_name(
    skill_name: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_community_skill_by_name(skill_name)
        if result.get("code") != 200:
            raise HTTPException(status_code=result.get("code", 502), detail=result.get("message", "unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/community/skills/detail/id/{skill_id}")
async def get_skill_detail_by_id(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = get_community_skill_by_id(skill_id)
        if result.get("code") != 200:
            raise HTTPException(status_code=result.get("code", 502), detail=result.get("message", "unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/community/skills/install/{skill_id}")
async def install_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    try:
        user_id = current_user.get("user_id")
        result = install_community_skill(skill_id, user_id=user_id)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "install failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/community/skills/remove/{skill_id}")
async def remove_skill(
    skill_id: str,
    current_user=Depends(get_current_user),
):
    try:
        result = remove_community_skill(skill_id)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("message", "remove failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
