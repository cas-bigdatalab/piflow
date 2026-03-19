import pytest

from runtime.skill_loader import SkillLoader
from tools.core.registry import registry


EXPECTED_OPERATOR_TOOLS = {
    "gully_slop_operator.emit_operator",
    "geotrans_main_operator.emit_operator",
    "hydro_susceptibility_operator.emit_operator",
    "overlap_dam_select_operator.emit_operator",
    "result_storage_operator.emit_operator",
}

EXPECTED_ORCHESTRATOR_PLAN_TOOL = "flow_orchestrator.plan_analysis"
EXPECTED_ORCHESTRATOR_TOOL = "flow_orchestrator.build_flow"
EXPECTED_ORCHESTRATOR_BUILD_WITH_SOURCES_TOOL = "flow_orchestrator.build_flow_with_selected_sources"
EXPECTED_ORCHESTRATOR_JSON_TOOL = "flow_orchestrator.build_flow_json"
EXPECTED_ORCHESTRATOR_SESSION_TOOL = "flow_orchestrator.prepare_dam_analysis_session"
EXPECTED_ORCHESTRATOR_EXEC_TOOL = "flow_orchestrator.execute_flow_from_temp"
EXPECTED_FLOW_RUN_TOOL = "flow_run.run_flow"
EXPECTED_SYNERGY_SEARCH_TOOL = "synergy_datasource_search.process"


def _mock_dataset_stop(name: str, index: int) -> dict:
    return {
        "customizedProperties": {},
        "dataSourceId": f"mock-ds-{index}",
        "dataCenter": "http://124.16.184.77:7801",
        "registerId": f"mock-register-{index}",
        "sourceType": "COLLABORATIVE_NETWORK",
        "webAddress": "http://124.16.184.77:7801",
        "name": name,
        "uuid": "723c59c7-a8c7-4a9c-8cc7-6c980a9798dd",
        "bundle": "cn.piflow.bundle.hdfs.HdfsPathToDf",
        "properties": {},
    }


@pytest.mark.asyncio
async def test_operator_skills_registered_and_callable():
    registry.clear()
    SkillLoader().load()

    names = {rec.spec.name for rec in registry.list_records()}
    assert EXPECTED_OPERATOR_TOOLS.issubset(names)
    assert EXPECTED_ORCHESTRATOR_PLAN_TOOL in names
    assert EXPECTED_ORCHESTRATOR_TOOL in names
    assert EXPECTED_ORCHESTRATOR_BUILD_WITH_SOURCES_TOOL in names
    assert EXPECTED_ORCHESTRATOR_JSON_TOOL in names
    assert EXPECTED_ORCHESTRATOR_SESSION_TOOL in names
    assert EXPECTED_ORCHESTRATOR_EXEC_TOOL in names
    assert EXPECTED_FLOW_RUN_TOOL in names
    assert EXPECTED_SYNERGY_SEARCH_TOOL in names

    for tool_name in EXPECTED_OPERATOR_TOOLS:
        result = await registry.call_internal(tool_name, {})
        assert result.success is True
        assert isinstance(result.output, dict)
        assert "operator_name" in result.output
        assert "stop" in result.output


@pytest.mark.asyncio
async def test_three_stage_orchestration_chain():
    registry.clear()
    SkillLoader().load()

    plan = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_PLAN_TOOL,
        {"selected_operators": ["overlap_dam_select"]},
    )
    assert plan.success is True
    assert plan.output["selection_mode"] == "explicit"
    assert "overlap_dam_select" in plan.output["selected_operators"]
    assert len(plan.output["required_sources"]) == 5

    selected_sources = [
        _mock_dataset_stop(source_name, idx)
        for idx, source_name in enumerate(plan.output["required_sources"], start=1)
    ]

    assembled = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_BUILD_WITH_SOURCES_TOOL,
        {
            "selected_operators": ["overlap_dam_select"],
            "selected_dataset_stops": selected_sources,
        },
    )
    assert assembled.success is True
    assert len(assembled.output["flow"]["stops"]) == 10
    assert len(assembled.output["flow"]["paths"]) == 9
    assert assembled.output["meta"]["missing_required_sources"] == []
    assert assembled.output["flow_session_id"]
    assert isinstance(assembled.output.get("run_payload"), dict)
    assert "dag_preview_json_text" in assembled.output

    run_kwargs = assembled.output["run_payload"]
    execution = await registry.call_internal(EXPECTED_FLOW_RUN_TOOL, run_kwargs)
    assert execution.success is True
    assert execution.output["status"] in {"submitted_placeholder", "submitted_remote"}
    assert execution.output["process_id"]


@pytest.mark.asyncio
async def test_flow_orchestrator_no_fallback_when_invalid_or_no_match():
    registry.clear()
    SkillLoader().load()

    no_match = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_TOOL,
        {"user_request": "火星天气预报"},
    )
    assert no_match.success is True
    assert no_match.output["meta"]["selection_mode"] == "none"
    assert len(no_match.output["flow"]["stops"]) == 0
    assert len(no_match.output["flow"]["paths"]) == 0

    invalid_selected = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_TOOL,
        {"selected_operators": ["不存在算子"]},
    )
    assert invalid_selected.success is True
    assert invalid_selected.output["meta"]["selection_mode"] == "none"
    assert "不存在算子" in invalid_selected.output["meta"]["invalid_operators"]


@pytest.mark.asyncio
async def test_build_flow_with_selected_sources_rejects_name_string_input():
    registry.clear()
    SkillLoader().load()

    selected_names = "2019年中国榆林市30m数字高程数据集,2019年中国榆林市沟道信息,地貌信息熵"
    result = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_BUILD_WITH_SOURCES_TOOL,
        {
            "selected_operators": ["hydro_susceptibility"],
            "selected_dataset_stops": selected_names,
        },
    )
    assert result.success is False
    assert "selected_dataset_stops must be a non-empty list of full datasource stop JSON objects" in str(result.error)


@pytest.mark.asyncio
async def test_build_flow_with_selected_sources_rejects_incomplete_source_json():
    registry.clear()
    SkillLoader().load()

    result = await registry.call_internal(
        EXPECTED_ORCHESTRATOR_BUILD_WITH_SOURCES_TOOL,
        {
            "selected_operators": ["gully_slop"],
            "selected_dataset_stops": [{"name": "2019年中国榆林市沟道信息"}],
        },
    )
    assert result.success is False
    assert "selected_dataset_stops must be full datasource stop JSON objects" in str(result.error)
