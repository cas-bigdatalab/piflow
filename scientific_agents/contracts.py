"""Shared conversation input contract; independent of any specific agent."""
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TurnInput(StrictModel):
    message: str = Field(min_length=1, max_length=12000)
    thread_id: str = Field(min_length=1, max_length=160,
                          validation_alias=AliasChoices("session_id", "thread_id"))
    user_id: str = Field(default="local", min_length=1, max_length=160)
    message_id: int | None = None
    request_id: str | None = Field(default=None, max_length=160)
    attachments: list[str] = Field(default_factory=list)
    expected_version: int | None = None
