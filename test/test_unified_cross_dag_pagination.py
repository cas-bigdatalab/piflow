"""Preserve native session counts when adapting nested pagination for /agents."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from scientific_agents.unified.adapters.cross_dag import BASE, CrossDagAdapter


@pytest.mark.parametrize("total,page,size", [(0, 1, 20), (3, 1, 20), (45, 2, 20),
                                             (45, 3, 20), (45, 4, 20)])
def test_session_pagination_preserves_total_and_session_fields(total, page, size):
    start = (page - 1) * size
    items = [{"session_id": f"s-{i}", "title": f"Session {i}", "status": "ACTIVE",
              "create_time": "2026-09-16T10:00:00+08:00", "update_time": "2026-09-16T11:00:00+08:00",
              "task_count": 2, "latest_task_id": f"t-{i}", "latest_task_status": "COMPLETED",
              "latest_task_stage": "done"} for i in range(start, min(start + size, total))]
    native_response = {"code": 200, "message": "success", "result": {
        "items": items, "pagination": {"total": total, "pageNum": page, "pageSize": size}}}
    before = deepcopy(native_response)
    native = SimpleNamespace(json=AsyncMock(return_value=native_response))

    result = asyncio.run(CrossDagAdapter(native).list_sessions(page, size))

    native.json.assert_awaited_once_with("GET", BASE + "/sessions", None,
                                        {"pageNum": page, "pageSize": size})
    assert result == {"items": [{**row, "agent_id": "cross_dag"} for row in items],
                      "total": total, "pageNum": page, "pageSize": size}
    assert native_response == before
