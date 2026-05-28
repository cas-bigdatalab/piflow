from infra.config_loader import get_settings
from repositories.user_repository import (
    get_user_by_username,
    insert_user,
)

from security.password_handler import (
    hash_password,
)


def register_user(
    username: str,
    password: str,
    nickname: str | None = None,
):
    # 用户名重复检查
    exist_user = get_user_by_username(username)

    if exist_user:
        raise ValueError("用户名已存在")

    # 密码hash
    password_hash = hash_password(password)

    # 存库
    return insert_user(
        username=username,
        password_hash=password_hash,
        nickname=nickname,
    )

def init_default_user():
    settings = get_settings()
    user = settings.default_user

    name = user.name
    password = user.password
    nickname = user.nickname

    exist_user = get_user_by_username(name)

    if exist_user:
        return

    # 密码hash
    password_hash = hash_password(password)

    # 存库
    insert_user(
        username=name,
        password_hash=password_hash,
        nickname=nickname,
    )