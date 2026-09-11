from __future__ import annotations

from typing import Any

from repositories.piflow_batch_store import get_batch
from runtime.piflow_batch_adapter import submit_batch_frontend_dag


def submit_batch_dag(**kwargs: Any) -> dict[str, Any]:
    return submit_batch_frontend_dag(**kwargs)


def get_batch_dag_status(*, batch_id: str, user_id: str) -> dict[str, Any] | None:
    return get_batch(batch_id, user_id)
