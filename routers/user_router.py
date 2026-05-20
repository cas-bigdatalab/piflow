from fastapi import (
    APIRouter,
    HTTPException,
)

from schemas.user_schema import (
    RegisterUserRequest,
)

from services.user_service import (
    register_user,
)

router = APIRouter()


@router.post("/register")
async def register_api(
    req: RegisterUserRequest,
):
    try:
        result = register_user(
            username=req.username,
            password=req.password,
            nickname=req.nickname,
        )

        return {
            "message": "注册成功",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="注册失败",
        )