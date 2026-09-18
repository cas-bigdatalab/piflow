"""Directory matching must tolerate wording without inventing sites or variables."""
from copy import deepcopy

import pytest

from scientific_agents.forecast.matching import candidates, area_suggestions, matches_target


@pytest.fixture
def catalogue():
    return [dict(id=f"{site}-{variable}", area=area, aliases=[], station_id=site,
                 source_name="高原观测数据", location={"name": area, "address": "示例省示例市观测园"},
                 variable=variable, variable_aliases=aliases,
                 hazard_type="rainfall" if variable == "rain" else "unspecified", hazard_aliases=[])
            for site, area in [("ST001", "青海西宁市共和县光伏观测站"), ("ST002", "青海西宁市东部观测站")]
            for variable, aliases in [("rain", ["降水", "降水量"]), ("temperature", ["气温", "空气温度"])]]


def test_short_place_has_one_eligible_candidate_and_keeps_variable(catalogue):
    scope = dict(requested_area="青海西宁共和县", requested_variable="降水")
    assert not candidates(catalogue, scope)
    assert [c["id"] for c in area_suggestions(catalogue, scope)] == ["ST001-rain"]


@pytest.mark.parametrize("name", ["高原观测数据", "示例省示例市观测园"])
def test_source_and_location_names_keep_all_matching_sites(catalogue, name):
    assert len(candidates(catalogue, dict(requested_area=name, requested_variable="降水"))) == 2


@pytest.mark.parametrize("query", ["降水变化", "降水的变化趋势", "降水预测情况", "降水量趋势"])
def test_target_presentation_words(catalogue, query):
    assert matches_target(catalogue[0], query)
    assert not matches_target(catalogue[1], query)


def test_unknown_places_variables_and_other_device_numbers_are_not_substituted(catalogue):
    for scope in [dict(requested_area="北京市", requested_variable="降水"),
                  dict(requested_area="ST003", requested_variable="降水"),
                  dict(requested_area="共和县", requested_variable="海水盐度")]:
        assert not candidates(catalogue, scope)
        assert not area_suggestions(catalogue, scope)
    assert [c["id"] for c in candidates(catalogue, dict(requested_area="ST001", requested_variable="降水"))] == ["ST001-rain"]


def test_variable_typo_is_only_a_candidate(catalogue):
    scope = dict(requested_area="共和县", requested_variable="temperatur")
    assert not candidates(catalogue, scope)
    assert [c["id"] for c in area_suggestions(catalogue, scope)] == ["ST001-temperature"]


def test_risk_capability_does_not_hide_explicit_target(catalogue):
    before = deepcopy(catalogue)
    assert len(candidates(catalogue, dict(requested_variable="气温", requested_hazard="rainfall"))) == 2
    assert len(candidates(catalogue, dict(requested_hazard="rainfall"))) == 2
    assert not candidates(catalogue, dict(requested_hazard="unknown_risk"))
    assert catalogue == before


def test_physical_variable_distinctions_are_not_erased(catalogue):
    assert not matches_target(catalogue[1], "最高气温")
    depth = dict(variable="soil_10cm", variable_aliases=["10cm土壤温度"])
    assert not matches_target(depth, "20cm土壤温度")
    assert not area_suggestions([dict(catalogue[0], **depth)], dict(requested_variable="20cm土壤温度"))
    minimum = dict(catalogue[0], variable="minimum_temperature", variable_aliases=["最低气温"])
    assert not area_suggestions([minimum], dict(requested_variable="maximum_temperature"))


def test_full_candidate_count_is_independent_of_display_limit(catalogue):
    cases = [dict(catalogue[0], id=f"rain-{i}") for i in range(8)]
    scope = dict(requested_area="青海西宁共和县", requested_variable="rain")
    assert len(area_suggestions(cases, scope, limit=1)) == 1
    assert len(area_suggestions(cases, scope)) == 5
    assert len(area_suggestions(cases, scope, limit=None)) == 8
