from __future__ import annotations

from pydantic import BaseModel, Field


class BatchDagSubmitRequest(BaseModel):
    definition_id: str
    input_dir: str
    max_parallel: int = Field(default=5, ge=1)
    retry_count: int = Field(default=1, ge=0)
    stop_on_failure: bool = False
    output_dir: str | None = None
