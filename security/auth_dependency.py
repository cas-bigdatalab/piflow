from fastapi import Depends, HTTPException

from fastapi.security import OAuth2PasswordBearer

from security.jwt_handler import verify_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = verify_token(token)

        return {
            "user_id": payload["user_id"],
            "username": payload["username"],
            "is_admin": payload["is_admin"],
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token无效",
        )