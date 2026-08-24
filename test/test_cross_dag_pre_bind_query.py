from __future__ import annotations

import pytest

from repositories import xdc_session_repository
from runtime.cross_dag.schema import CrossDagError
from services import cross_dag_service


def test_get_pre_bind_plan_uses_persisted_frontend_view(monkeypatch):
    expected = {
        "plan_id": "xdc-persisted",
        "stage": "pre_bind",
        "binding_status": "PENDING",
        "mode": "composition",
    }

    monkeypatch.setattr(
        xdc_session_repository,
        "get_pre_bind_view_by_plan_id",
        lambda **kwargs: {"payload_json": expected},
    )
    monkeypatch.setattr(cross_dag_service, "_PRE_BIND_CACHE", {})

    result = cross_dag_service.get_cross_dag_pre_bind_plan(
        "xdc-persisted",
        user_id="user-1",
    )

    assert result == expected


def test_get_pre_bind_plan_reports_missing_plan(monkeypatch):
    monkeypatch.setattr(
        xdc_session_repository,
        "get_pre_bind_view_by_plan_id",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(cross_dag_service, "_PRE_BIND_CACHE", {})

    with pytest.raises(CrossDagError, match="xdc-missing"):
        cross_dag_service.get_cross_dag_pre_bind_plan(
            "xdc-missing",
            user_id="user-1",
        )
