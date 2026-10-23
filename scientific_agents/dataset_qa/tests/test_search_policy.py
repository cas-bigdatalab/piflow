"""Policy boundaries are about distinct queries and actual source records."""
from copy import deepcopy

from pydantic import ValidationError
import pytest

from ..contracts import QAError
from ..search import SearchProfile, SearchRun, TaskDirective


PROFILE = SearchProfile(query="term", page="page", page_size="size", total="/total", identity=["/id"])


def begin(keywords=("alpha", "beta", "gamma", "delta")):
    return SearchRun.create(PROFILE, {"term": keywords[0], "size": 5, "page": 1}, keywords)


@pytest.mark.parametrize("words", [["alpha", " ALPHA "], ["Ａｌｐｈａ", "alpha"], ["  "], ["x"*2001]])
def test_keyword_plan_rejects_empty_repeated_and_oversized_phrases(words):
    with pytest.raises(ValidationError):
        TaskDirective(complete_request=True, keywords=words)


def test_fifth_keyword_is_rejected_without_mutating_the_saved_plan():
    search = begin()
    saved = deepcopy(search.state)
    with pytest.raises(QAError):
        search.extend({"term": "epsilon", "size": 5, "page": 1}, ["epsilon"])
    assert search.state==saved


def test_whitespace_variant_is_not_another_query_and_keeps_original_wire_text():
    search = begin(("Alpha topic",))
    search.extend({"term": " ALPHA   topic ", "size": 5, "page": 1}, [])
    assert search.state["keywords"]==["Alpha topic"]
    assert search.arguments()["term"]=="Alpha topic"


def test_rows_with_stable_ids_are_deduplicated_despite_changed_descriptions():
    search = begin()
    search.record({"items": [{"id": n, "description": "first"} for n in range(5)], "total": 99}, "/items", "first")
    search.record({"items": [{"id": n, "description": "changed"} for n in range(3)], "total": 99}, "/items", "second")
    assert len(search.state["records"])==5
    assert search.arguments()=={"term": "beta", "size": 5, "page": 1}
    assert search.state["completed"]==["alpha"]


def test_a_large_total_without_rows_never_satisfies_the_result_count():
    search = begin()
    for index in range(4):
        search.record({"items": [], "total": 1000000}, "/items", str(index))
    assert search.state["done"] and search.state["stop"]=="exhausted"
    assert not search.state["records"]


def test_missing_total_uses_full_pages_and_stops_at_six_actual_records():
    search = begin()
    search.record({"items": [{"id": n} for n in range(5)]}, "/items", "first")
    assert search.arguments()["page"]==2
    search.record({"items": [{"id": 5}]}, "/items", "second")
    assert search.arguments() is None
    assert search.state["stop"]=="enough"
    assert search.state["completed"]==["alpha"]


def test_opaque_filters_and_unannounced_filter_changes_do_not_execute():
    descriptor = SearchProfile(query="term", opaque_filters=["classification"])
    with pytest.raises(QAError):
        SearchRun.create(descriptor, {"term": "alpha", "classification": "guessed category"}, ["alpha"])
    search = begin()
    before = deepcopy(search.state)
    with pytest.raises(QAError):
        search.extend({"term": "beta", "size": 5, "author": "unrequested", "page": 1}, ["beta"])
    assert search.state==before


@pytest.mark.parametrize("data", [{}, {"items": None}, {"items": {}}, {"items": ["not a record"]}])
def test_invalid_payload_is_not_an_empty_success(data):
    search = begin()
    before = deepcopy(search.state)
    with pytest.raises(QAError) as caught:
        search.record(data, "/items", "invalid")
    assert caught.value.code=="invalid_result"
    assert search.state==before
