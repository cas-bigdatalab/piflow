from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from schemas.auth_schema import LoginRequest

from services.auth_service import login
from security.jwt_handler import verify_token

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


@router.get("/verify-token")
async def verify_token_api(
    token: str | None = Query(default=None, description="待验证的 JWT Token"),
):
    """Return whether the supplied token is valid."""
    if not token:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "message": "Token无效", "valid": False},
        )

    try:
        payload = verify_token(token)
        payload["user_id"]
        payload["user_name"]
        payload["is_admin"]
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "message": "Token无效", "valid": False},
        )

    return {"code": 200, "message": "Token有效", "valid": True}
