"""Original subject wording precedes rewrites across domains and turns."""
import asyncio

import pytest

from ..contracts import QAError
from ..search import ordered_keywords
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import SearchBackend, discover, outcome, page
from .test_dataset_qa import action, collect, engine, session
from .test_decisions import BareDialogue, text


@pytest.mark.parametrize("user_request,originals,rewrites", [
    ("我想找化学化工相关的数据集", ["化学", "化工"], ["chemistry", "chemical engineering"]),
    ("找天文和气象数据", ["天文", "气象"], ["astronomy", "meteorology"]),
    ("Find gene expression and proteomics datasets", ["gene expression", "proteomics"], ["transcriptomics", "protein abundance"]),
])
def test_original_phrases_are_grounded_and_scheduled_before_rewrites(user_request, originals, rewrites):
    words, sources = ordered_keywords([*rewrites, *reversed(originals)], originals, user_request)
    assert words==originals+rewrites and sources==originals


@pytest.mark.parametrize("originals", [["chemistry"], ["catalysis"], None])
def test_translations_or_ungrounded_subjects_cannot_claim_to_be_original(originals):
    with pytest.raises(QAError, match="原请求"):
        ordered_keywords(["chemistry", "chemical engineering"], originals, "我想找化学化工数据")


def test_extracted_and_rewritten_phrases_share_one_four_keyword_budget():
    with pytest.raises(QAError, match="合计最多四个"):
        ordered_keywords(["beta", "gamma", "delta", "epsilon"], ["alpha"], "Find alpha data")


def test_normalized_duplicates_keep_the_original_spelling_and_no_extra_query():
    words, originals = ordered_keywords(["rna-SEQ", "gene expression"], ["RNA-seq"], "Find RNA-seq data")
    assert words==["RNA-seq", "gene expression"] and originals==["RNA-seq"]


def test_current_request_precedes_explicit_user_history():
    words, _ = ordered_keywords(["physical science", "chemistry", "physics"], ["chemistry", "physics"],
        "Find physics data", ["Find chemistry data"])
    assert words==["physics", "chemistry", "physical science"]


def test_older_calls_infer_originals_only_from_actual_user_text():
    assert ordered_keywords(["chemistry", "化学"], None, "找化学数据")[0]==["化学", "chemistry"]


def test_current_request_words_cannot_be_mislabelled_as_later_rewrites():
    words, originals = ordered_keywords(["chemistry", "化工", "化学"], ["化学"], "找化学化工数据")
    assert words==["化学", "化工", "chemistry"] and originals==["化学", "化工"]


def test_extensions_preserve_the_original_subject_after_source_history_is_trimmed():
    previous = {"original_keywords": ["化学"], "keywords": ["化学"]}
    words, originals = ordered_keywords(["chemistry"], None, "继续", previous=previous)
    assert words==["化学", "chemistry"] and originals==["化学"]
    with pytest.raises(QAError, match="原词已确定"):
        ordered_keywords(["chemical engineering"], ["化工"], "化学化工", previous=previous)


def test_real_service_orders_original_queries_even_if_model_lists_translations_first(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        words = ["chemistry", "chemical engineering", "化工", "化学"]
        dialogue = BareDialogue(discover(keywords=words, originals=["化学", "化工"]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "我想找化学化工相关的数据集")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==["化学", "化工", "chemistry", "chemical engineering"]
            assert len(dialogue.inputs)==2
            search = outcome(service, sid, events)["operations"][0]["search"]
            assert search["original_keywords"]==["化学", "化工"]
            assert search["done"] and len(search["completed"])==4
        finally:
            await service.close()
    asyncio.run(run())


def test_original_query_meeting_threshold_skips_every_rewrite(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        words = ["chemistry", "chemical engineering", "化学", "化工"]
        dialogue = BareDialogue(discover(keywords=words, originals=["化学", "化工"]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "我想找化学化工相关的数据集")
            assert_completed(service, sid, events[-1])
            assert [(args["phrase"], args["page_number"]) for _, args in backend.calls]==[("化学", 1), ("化学", 2)]
            assert len(dialogue.inputs)==2
        finally:
            await service.close()
    asyncio.run(run())


def test_ungrounded_original_is_corrected_before_any_mcp_dispatch(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        wrong = discover(keywords=["chemistry", "chemical engineering"], originals=["chemistry"])
        correct = discover(keywords=["化学", "化工", "chemistry", "chemical engineering"], originals=["化学", "化工"])
        dialogue = BareDialogue(wrong, correct, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "我想找化学化工相关的数据集")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==["化学", "化工", "chemistry", "chemical engineering"]
            assert len(dialogue.inputs)==3 and len(outcome(service, sid, events)["operations"])==1
        finally:
            await service.close()
    asyncio.run(run())


def test_followup_grounds_subject_in_user_history_without_reusing_old_results(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))
        plan = discover(keywords=["化学", "化工", "chemistry", "chemical engineering"], originals=["化学", "化工"])
        dialogue = BareDialogue(plan, text(), plan, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "我想找化学化工相关的数据集", "first")
            second = await collect(service, sid, "再帮我找一批", "second")
            assert_completed(service, sid, first[-1])
            assert_completed(service, sid, second[-1])
            assert [args["phrase"] for _, args in backend.calls]==["化学", "化工", "chemistry", "chemical engineering"]*2
            assert len(dialogue.inputs)==4
        finally:
            await service.close()
    asyncio.run(run())


def test_older_call_without_control_fields_cannot_search_a_translation_first(engine):
    async def run():
        backend = SearchBackend(lambda query, number: page([], 0))

        def old_call(messages, definitions):
            alias = next(value["function"]["name"] for value in definitions if value["function"]["name"].endswith("_find_assets"))
            return action(alias, phrase="chemistry")

        plan = discover(keywords=["化学", "化工", "chemistry", "chemical engineering"], originals=["化学", "化工"])
        dialogue = BareDialogue(old_call, plan, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "我想找化学化工相关的数据集")
            assert_completed(service, sid, events[-1])
            assert [args["phrase"] for _, args in backend.calls]==["化学", "化工", "chemistry", "chemical engineering"]
            assert len(dialogue.inputs)==3
        finally:
            await service.close()
    asyncio.run(run())
