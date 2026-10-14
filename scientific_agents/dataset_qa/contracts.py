"""Transport options and generic runtime limits; no business tool catalogue."""
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Options(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    selected_dataset_id: str | None = Field(default=None, max_length=500)
    result_id: str | None = Field(default=None, max_length=180)
    expected_version: int | None = Field(default=None, ge=0)
    after_event_seq: int = Field(default=0, ge=0)


@dataclass(frozen=True)
class Limits:
    max_tools: int = 8
    max_rounds: int = 12
    max_calls: int = 24
    max_stalled_calls: int = 2
    schema_chars: int = 16000
    context_chars: int = 32000
    result_chars: int = 8000
    result_bytes: int = 2_000_000
    timeout: float = 660
    connect_timeout: float = 30
    cache_seconds: float = 300
    heartbeat_seconds: float = 15


@dataclass(frozen=True)
class Server:
    target: Any
    description: str = ""
    timeout: float | None = None


class QAError(Exception):
    def __init__(self, code, message, status=422, detail=None):
        super().__init__(message)
        self.code, self.status = code, status
        self.detail = detail
