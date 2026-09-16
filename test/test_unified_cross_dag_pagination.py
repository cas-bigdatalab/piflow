"""Preserve native session counts when adapting nested pagination for /agents."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from scientific_agents.unified.adapters.cross_dag import BASE, CrossDagAdapter
from scientific_agents.unified.schemas import PREFIX


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
                      "pagination": {"total": total, "pageNum": page, "pageSize": size},
                      "total": total, "pageNum": page, "pageSize": size}
    assert native_response == before


@pytest.mark.parametrize("origin", ["", "https://old-host.example"])
def test_native_links_are_rewritten_in_history_and_stream_without_changing_action(origin):
    path = "/tasks/task-1/bind-and-execute/stream?detail=true#execute"
    view = {"next_action": {"method": "POST", "url": origin + BASE + path,
                            "body": {"detail": True, "selected_dataset_id": "dataset-1"}},
            "status_url": BASE + "/tasks/task-1/execution/status",
            "process_status_url": BASE + "/execution/process-1/status",
            "download_url": BASE + "/execution/process-1/download?result_node_id=n%201&result_output_name=out",
            "dataset": {"url": BASE + "/do-not-rewrite-dataset-url"},
            "external": {"next_action": {"url": "https://example.org/external"}}}
    source = {"type": "done", "result": {"items": [{"payload": view}]}}
    before = deepcopy(source)
    adapter = CrossDagAdapter(SimpleNamespace(request=SimpleNamespace(base_url="https://public.example/")))

    async def stream():
        yield None
        yield source

    async def collect():
        return [event async for event in adapter.convert(stream())]

    converted = adapter.links(source)
    assert asyncio.run(collect()) == [None, converted]
    result = converted["result"]["items"][0]["payload"]
    assert result["next_action"] == {**view["next_action"], "url": "https://public.example" + PREFIX + path}
    for key in ("status_url", "process_status_url", "download_url"):
        assert result[key] == "https://public.example" + view[key].replace(BASE, PREFIX, 1)
    assert result["dataset"] == view["dataset"]
    assert result["external"] == view["external"]
    assert source == before
