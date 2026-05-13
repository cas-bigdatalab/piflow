from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth_schema import LoginRequest

from services.auth_service import login

router = APIRouter()


@router.post("/login")
async def login_api(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    result = login(
        username=form_data.username,
        password=form_data.password,
    )

    if not result:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )

    return result