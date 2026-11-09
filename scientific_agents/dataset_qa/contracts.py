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
    max_parallel_reads: int = 4
    max_stalled_calls: int = 2
    max_corrections: int = 2
    transport_retries: int = 1
    retry_delay: float = 0.25
    schema_chars: int = 16000
    context_chars: int = 262144
    working_chars: int = 40000
    context_tokens: int = 73728  # Local total ceiling, including output; not a provider capability claim.
    input_tokens: int = 65536
    context_soft_tokens: int = 49152
    tokenizer_path: str | None = None  # Optional matching local tokenizer.json; never downloaded at request time.
    output_tokens: int = 4096
    result_chars: int = 8000
    result_bytes: int = 2_000_000
    timeout: float = 660
    connect_timeout: float = 10
    model_timeout: float = 60
    turn_timeout: float = 480
    wait_notice: float = 30
    summary_timeout: float = 30
    summary_input_chars: int = 10000
    summary_output_tokens: int = 1024
    summary_chars: int = 6000
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
