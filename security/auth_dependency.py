from fastapi import Depends, HTTPException

from fastapi.security import OAuth2PasswordBearer

from security.jwt_handler import verify_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/piflow/v1/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = verify_token(token)

        return {
            "user_id": payload["user_id"],
            "user_name": payload["user_name"],
            "is_admin": payload["is_admin"],
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token无效",
        )


def get_current_user_with_token(
    token: str = Depends(oauth2_scheme),
):
    """Validate the current user and retain the raw bearer token for forwarding."""
    try:
        payload = verify_token(token)

        return {
            "user_id": payload["user_id"],
            "user_name": payload["user_name"],
            "is_admin": payload["is_admin"],
            "access_token": token,
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token无效",
        )
