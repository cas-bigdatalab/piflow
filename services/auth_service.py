from repositories.user_repository import (
    get_user_by_username,
)

from security.password_handler import (
    verify_password,
)

from security.jwt_handler import (
    create_access_token,
)


def login(username: str, password: str):
    user = get_user_by_username(username)

    if not user:
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    token = create_access_token({
        "user_id": user["user_id"],
        "username": user["username"],
        "is_admin": user["is_admin"],
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }