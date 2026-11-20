"""Search continuation preserves provenance and distinguishes retrieval from replay."""
from copy import deepcopy

import pytest

from ..contracts import QAError
from ..search import SearchProfile, SearchRun, ordered_keywords


@pytest.mark.parametrize("user_request,original,substring,rewrite", [
    ("Find river flow measurements", "river flow", "river", "hydrology"),
    ("查找海洋观测站数据", "海洋观测站", "海洋", "marine monitoring"),
    ("Find ＲＮＡ expression records", "RNA expression", "rna", "transcriptomics"),
])
def test_initial_keyword_prioritization_does_not_mutate_declared_provenance(user_request, original, substring, rewrite):
    submitted = [original, rewrite, substring]
    words, originals = ordered_keywords(submitted, [original], user_request)
    assert originals == [original]
    assert words == [original, substring, rewrite]
    saved = {"original_keywords": originals, "keywords": words}
    before = deepcopy(saved)
    assert ordered_keywords(submitted, [original], user_request, previous=saved) == (words, originals)
    assert saved == before and submitted == [original, rewrite, substring]


@pytest.mark.parametrize("user_request,original,rewrite", [
    ("Find mountain observatory records", "mountain observatory", "observatory"),
    ("查找海洋观测站数据", "海洋观测站", "海洋"),
])
@pytest.mark.parametrize("explicit", [False, True])
def test_later_request_substring_is_a_rewrite_of_the_frozen_extraction(user_request, original, rewrite, explicit):
    previous = {"original_keywords": [original], "keywords": [original]}
    before = deepcopy(previous)
    words, originals = ordered_keywords([rewrite], [original] if explicit else None,
        user_request, previous=previous)
    assert words==[original, rewrite] and originals==[original]
    assert previous==before


def test_continuation_preserves_accepted_spelling_and_order_after_context_changes():
    previous = {"original_keywords": ["RNA-seq", "proteomics"], "keywords": ["RNA-seq", "proteomics"]}
    words, originals = ordered_keywords(["protein abundance"], ["PROTEOMICS", "rna-SEQ"],
        "Continue proteomics", previous=previous)
    assert originals==["RNA-seq", "proteomics"]
    assert words==["RNA-seq", "proteomics", "protein abundance"]


def test_continuation_cannot_replace_the_original_subject_even_if_new_text_contains_it():
    previous = {"original_keywords": ["ocean"], "keywords": ["ocean"]}
    before = deepcopy(previous)
    with pytest.raises(QAError, match="原词已确定"):
        ordered_keywords(["weather"], ["weather"], "Find weather records", previous=previous)
    assert previous==before


@pytest.mark.parametrize("count", [0, 1, 5, 6])
@pytest.mark.parametrize("initial_size", [1, 2, 4])
def test_partial_and_complete_queues_reach_the_same_bounded_result(count, initial_size):
    words = ["ocean", "marine", "sea", "pelagic"]
    descriptor = SearchProfile(query="term", page="page", page_size="size", total="/total", identity=["/id"])
    arguments = {"term": words[0], "page": 1, "size": 5}
    search = SearchRun.create(descriptor, arguments, words[:initial_size])
    search.state["original_keywords"] = words[:1]
    calls = []
    while not search.state["done"]:
        if search.needs_keywords:
            before = search.progress
            queue, originals = ordered_keywords(words, None, "Continue", previous=search.state)
            search.extend(arguments, queue)
            assert search.progress==before  # Adding work has not retrieved anything.
            assert originals==words[:1]
        call = search.arguments()
        assert call is not None
        calls.append((call["term"], call["page"]))
        start = (call["page"]-1)*call["size"]
        rows = [{"id": index} for index in range(start, min(start+call["size"], count))]
        before = search.progress
        search.record({"items": rows, "total": count}, "/items", f"result-{len(calls)}")
        assert search.progress!=before

    assert not search.needs_keywords and search.arguments() is None
    assert search.view()["unique_count"]==count
    if count>=6:
        assert calls==[("ocean", 1), ("ocean", 2)]
        assert search.state["stop"]=="enough"
    else:
        # Duplicate rows across distinct completed keywords still advance the
        # policy; they never inflate the actual unique candidate count.
        assert calls==[(word, 1) for word in words]
        assert search.state["completed"]==words and search.state["stop"]=="exhausted"


def test_exhausted_queue_replay_is_not_progress_and_resume_needs_no_new_operation():
    descriptor = SearchProfile(query="term", identity=["/id"])
    search = SearchRun.create(descriptor, {"term": "alpha"}, ["alpha"])
    search.record({"items": [{"id": 1}]}, "/items", "result-1")
    resumed = SearchRun(deepcopy(search.state))
    before = resumed.progress
    assert resumed.needs_keywords and resumed.arguments() is None
    resumed.extend({"term": "ALPHA"}, [" alpha "])
    assert resumed.progress==before and resumed.needs_keywords
    resumed.extend({"term": "beta"}, ["beta"])
    assert resumed.progress==before and not resumed.needs_keywords
    resumed.record({"items": [{"id": 1}]}, "/items", "result-2")
    assert resumed.progress!=before and resumed.view()["unique_count"]==1


def test_rejected_page_and_filter_change_cannot_claim_retrieval_progress():
    search = SearchRun.create(SearchProfile(query="term"), {"term": "alpha", "scope": "a"}, ["alpha"])
    before = deepcopy(search.state)
    progress = search.progress
    with pytest.raises(QAError):
        search.record({"items": "unavailable"}, "/items", "invalid")
    with pytest.raises(QAError):
        search.extend({"term": "beta", "scope": "b"}, ["beta"])
    assert search.state==before and search.progress==progress


@pytest.mark.parametrize("original, changed", [(0, False), (1, True), ([0], [False]), ({"value": 1}, {"value": True})])
def test_frozen_filters_preserve_numeric_and_boolean_types(original, changed):
    search = SearchRun.create(SearchProfile(query="term"), {"term": "alpha", "filter": original}, ["alpha"])
    before = deepcopy(search.state)
    with pytest.raises(QAError):
        search.extend({"term": "beta", "filter": changed}, ["beta"])
    assert search.state == before

