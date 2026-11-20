"""Opt-in real model + real corpus upstream, with no simulated data or decisions.

Set DATASET_QA_LIVE_CORPUS=1 and normal model credentials. TB_CHAT_URL and
DATASET_QA_LIVE_MODEL_NAME select a test-only model endpoint. Optional
DATASET_QA_LIVE_CORPUS_QUERY changes the search request; comma-separated
DATASET_QA_LIVE_CORPUS_EXPECT sets relevance terms (default: 共和县,光伏).
DATASET_QA_LIVE_REPORT_DIR receives a sanitized report. No fixed dataset ID is used.
The combined node requests details and directory in one follow-up. Set
DATASET_QA_LIVE_CORPUS_DIRECTORY_EXPECT=nonempty|empty|unsupported to assert the
actual source outcome (default nonempty); unsupported must be explicit upstream
evidence, not a guessed capability gap or another retrieval failure.
"""
import asyncio
from copy import deepcopy
import json
import logging
import os
from pathlib import Path
import time

import pytest

from ..contracts import Server
from ..execution import Execution
from ..mcp import MCPGateway, ToolSession
from ..service import DatasetQA
from .test_artifact_download_origin import http_mcp
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import payload
from .test_model_sequence_live import (
    AcceptanceFailure, COMBINED_TURN, ObservedDialogue, final_answer, foreground_marker,
    require, safe_arguments, safe_correction, safe_exception, scrub_text,
    verify_combined_model_identifiers, verify_combined_retrieval,
)


def test_foreground_marker_counts_search_pages_and_excludes_background_calls(engine, monkeypatch):
    from .test_bounded_discovery import KEYWORDS, SearchBackend, discover, page
    from .test_decisions import BareDialogue, text
    foreground, observed = foreground_marker(monkeypatch), []
    original = ToolSession.call

    async def capture(tools, alias, arguments, **kwargs):
        observed.append(foreground.get())
        return await original(tools, alias, arguments, **kwargs)

    monkeypatch.setattr(ToolSession, "call", capture)

    async def run():
        backend = SearchBackend(lambda word, number: page([1], 1))
        service = DatasetQA(engine, BareDialogue(discover(), text()), backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert not payload(service, sid, events).get("error")
            assert observed == [True] * len(KEYWORDS)
            async with service.gateway.session() as tools:
                await tools.load("arbitrary-source")
                alias = next(alias for alias, tool in tools.loaded.items() if tool.name == "find_assets")
                await tools.call(alias, {"phrase": "background", "page_number": 1, "per_page": 5})
            assert observed == [True] * len(KEYWORDS) + [False]
        finally:
            await service.close()
    asyncio.run(run())


def _real_corpus_retrieval(engine, tmp_path, monkeypatch, caplog, *, combined=False):
    from infra.config_loader import get_settings
    settings = get_settings()
    provider = settings.providers[settings.llm.provider]
    if not (os.getenv(provider.api_key_env or "LLM_API_KEY") or os.getenv("LLM_API_KEY")) and os.getenv("API_KEY"):
        monkeypatch.setenv("LLM_API_KEY", os.environ["API_KEY"])
    require(bool(os.getenv(provider.api_key_env or "LLM_API_KEY") or os.getenv("LLM_API_KEY")), "Model credentials are missing")
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    caplog.set_level(logging.CRITICAL)
    query = os.getenv("DATASET_QA_LIVE_CORPUS_QUERY", "我想找共和县光伏观测站相关的数据集")
    terms = [term.strip() for term in os.getenv("DATASET_QA_LIVE_CORPUS_EXPECT", "共和县,光伏").split(",") if term.strip()]
    require(bool(terms), "At least one relevance term is required")
    turns = ([("search", query), COMBINED_TURN] if combined else
        [("search", query), ("detail", "看下这个数据集的详情"), ("directory", "看下目录结构")])
    directory_mode = os.getenv("DATASET_QA_LIVE_CORPUS_DIRECTORY_EXPECT", "nonempty")
    require(directory_mode in {"nonempty", "empty", "unsupported"}, "Unsupported directory expectation configuration")
    active, reports, found, background = {}, [], {}, []
    foreground = foreground_marker(monkeypatch)
    original_call, original_correct = ToolSession.call, Execution.correct

    async def capture(tools, alias, arguments, **kwargs):
        name = tools.loaded[alias].name
        business_call = foreground.get()
        if business_call:
            active["calls"].append((name, deepcopy(arguments)))
        else:
            background.append(name)
        try:
            result = await original_call(tools, alias, arguments, **kwargs)
        except Exception as exc:
            if business_call:
                active["failures"][name] = exc
            raise
        _, output = result
        if business_call:
            active["outputs"][name] = deepcopy(output.data)
        if business_call and name == "search_corpus_datasets" and isinstance(output.data, dict):
            for row in output.data.get("items", []):
                if isinstance(row, dict):
                    raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
                    reference = row.get("cstr") or raw.get("cstr")
                    if isinstance(reference, str) and reference:
                        found[reference] = row
        return result

    def correction(execution, error, limit, **kwargs):
        active["corrections"].append(error.code)
        active["correction_details"].append(safe_correction(error))
        return original_correct(execution, error, limit, **kwargs)

    monkeypatch.setattr(ToolSession, "call", capture)
    monkeypatch.setattr(Execution, "correct", correction)

    def relevant(row):
        records = [row, row.get("raw", {})]
        visible = " ".join(str(record.get(key, "")) for record in records if isinstance(record, dict)
            for key in ("title", "name", "description"))
        return all(term.casefold() in visible.casefold() for term in terms)

    async def run():
        selected = None
        async with http_mcp("/api/piflow/v1/mcp") as base:
            dialogue = ObservedDialogue()
            service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(base + "/")}))
            sid = session(service)
            try:
                for label, utterance in turns:
                    active.update(calls=[], corrections=[], correction_details=[], outputs={}, failures={})
                    first_background = len(background)
                    started, first_round = time.perf_counter(), len(dialogue.rounds)
                    report = {"turn": label, "correct": False}
                    reference = None
                    reports.append(report)
                    try:
                        events = await collect(service, sid, utterance, rid=label)
                        saved = payload(service, sid, events)
                        report["final_answer"] = final_answer(events)
                        report["error_code"] = (saved.get("error") or {}).get("error_code")
                        if label != "detail_directory":
                            require(not saved.get("error"), "Corpus turn did not complete successfully")
                        require(bool(result_cards(events)), "Corpus turn did not deliver a result card")
                        names = [name for name, _ in active["calls"]]
                        if label == "search":
                            require(bool(names) and set(names) == {"search_corpus_datasets"}, "Search ran an unexpected capability")
                            report.update(candidate_count=len(found), relevant_count=sum(map(relevant, found.values())),
                                candidate_titles=[scrub_text(row.get("title", ""), 200) for row in list(found.values())[:12]])
                            require(any(map(relevant, found.values())), "No actual search record matches the configured relevance terms")
                        elif label == "detail_directory":
                            references = {arguments.get("cstr") for _, arguments in active["calls"]}
                            require(len(references) == 1, "Combined retrieval did not share one dataset identity")
                            reference = next(iter(references))
                            require(reference in found and relevant(found[reference]),
                                "Combined source is absent from relevant actual search results")
                            report["combined"] = verify_combined_retrieval(active["calls"], saved, events,
                                reference, active["outputs"], active["failures"], directory=directory_mode)
                        else:
                            expected = "get_corpus_dataset_detail" if label == "detail" else "get_corpus_dataset_directory"
                            require(names == [expected], "Follow-up did not execute exactly the requested retrieval")
                            arguments = active["calls"][0][1]
                            reference = arguments.get("cstr")
                            require(reference in found and relevant(found[reference]), "Follow-up source is absent from relevant actual search results")
                            if label == "detail":
                                selected = reference
                            else:
                                require(reference == selected, "Directory changed the dataset selected for details")
                                require(arguments.get("file_id") is None, "Root directory used an invented file identifier")
                            report["source_grounded"] = True
                        report["correct"] = True
                    except Exception as exc:
                        report["exception"] = safe_exception(exc)
                        if isinstance(exc, AcceptanceFailure):
                            report["failure"] = str(exc)
                        raise
                    finally:
                        if label == "detail_directory":
                            report["draft_identifier_diagnostics"] = verify_combined_model_identifiers(
                                dialogue.rounds[first_round:], reference)
                        report.update(seconds=round(time.perf_counter() - started, 3),
                            model_calls=len(dialogue.rounds) - first_round, model_trace=dialogue.rounds[first_round:],
                            corrections=active["corrections"], mcp_call_count=len(active["calls"]),
                            correction_details=active["correction_details"],
                            background_mcp_call_count=len(background) - first_background,
                            mcp_calls=[{"name": name, "arguments": safe_arguments(args)} for name, args in active["calls"]])
                        print("DATASET_QA_REAL_CORPUS_TURN " + json.dumps({key: report[key] for key in
                            ("turn", "correct", "seconds", "model_calls", "mcp_call_count", "background_mcp_call_count", "corrections")}), flush=True)
            finally:
                await service.close()

    failure = None
    try:
        asyncio.run(run())
    except Exception as exc:
        failure = safe_exception(exc)
    summary = {"real_model": True, "real_corpus_upstream": True, "combined": combined, "correct": failure is None,
        "failure": failure, "background_mcp_call_count": len(background), "turns": reports}
    destination = Path(os.getenv("DATASET_QA_LIVE_REPORT_DIR") or tmp_path)
    destination.mkdir(parents=True, exist_ok=True)
    filename = "real_corpus_combined_retrieval.json" if combined else "real_corpus_retrieval.json"
    (destination / filename).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DATASET_QA_REAL_CORPUS_REPORT " + json.dumps(summary, ensure_ascii=False))
    if failure is not None:
        pytest.fail("Real corpus acceptance failed; see sanitized DATASET_QA_REAL_CORPUS_REPORT.", pytrace=False)


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_CORPUS") != "1", reason="Opt-in real model and external corpus retrieval")
def test_real_corpus_search_detail_directory_keep_grounded_reference(engine, tmp_path, monkeypatch, caplog):
    _real_corpus_retrieval(engine, tmp_path, monkeypatch, caplog)


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_CORPUS") != "1", reason="Opt-in real model and external corpus retrieval")
def test_real_corpus_search_then_combined_detail_directory_keep_grounded_reference(engine, tmp_path, monkeypatch, caplog):
    _real_corpus_retrieval(engine, tmp_path, monkeypatch, caplog, combined=True)
