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


@pytest.fixture
def temperature_catalogue():
    return [dict(id=f"{site}-{variable}", area=area, aliases=[], station_id=site,
                 variable=variable, variable_aliases=aliases)
            for site, area in [("ST001", "示例市南部观测站"), ("ST002", "示例市北部观测站")]
            for variable, aliases in [("air_temperature", ["气温", "空气温度", "temperature"]),
                                      ("soil_temperature", ["土壤温度"])]]


@pytest.mark.parametrize("query", ["air_temperature", "temperature", "气温变化"])
def test_exact_target_is_preserved_when_place_is_approximate(temperature_catalogue, query):
    before = deepcopy(temperature_catalogue)
    scope = dict(requested_area="示例南部", requested_variable=query)
    assert not candidates(temperature_catalogue, scope)
    assert [c["id"] for c in area_suggestions(temperature_catalogue, scope)] == ["ST001-air_temperature"]
    assert temperature_catalogue == before


def test_exact_target_keeps_multiple_eligible_sites(temperature_catalogue):
    scope = dict(requested_area="示例观侧网", requested_variable="air_temperature")
    cases = [dict(c, source_name="示例观测网") for c in temperature_catalogue]
    assert not candidates(cases, scope)
    assert {c["id"] for c in area_suggestions(cases, scope, limit=None)} == {
        "ST001-air_temperature", "ST002-air_temperature"}


def test_unknown_target_can_still_use_approximate_variable(temperature_catalogue):
    scope = dict(requested_area="示例南部", requested_variable="air_temperatur")
    assert not candidates(temperature_catalogue, scope)
    assert area_suggestions(temperature_catalogue, scope)[0]["id"] == "ST001-air_temperature"


@pytest.mark.parametrize("place", ["ST001", "示例市南部观测站"])
def test_exact_place_is_not_replaced_to_find_exact_target(temperature_catalogue, place):
    cases = [c for c in temperature_catalogue if c["id"] != "ST001-air_temperature"]
    # A similarly named site has the requested variable; the named site does not.
    cases = [dict(c, area="示例市南部观测点") if c["station_id"] == "ST002" else c for c in cases]
    scope = dict(requested_area=place, requested_variable="air_temperature")
    assert not candidates(cases, scope)
    assert not area_suggestions(cases, scope)
