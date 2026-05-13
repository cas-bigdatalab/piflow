from pydantic import BaseModel


class RegisterUserRequest(BaseModel):
    username: str
    password: str
    nickname: str | None = None