"""Opt-in real decisions after a controlled, incomplete first search proposal.

Only the initial proposal is scripted to cover delivery roles that a fresh
model may not choose during happy-path acceptance. Continuation, scope review,
delivery and the next-turn inspection use the real model without intervention.
MCP data is simulated; reports contain no credentials or provider endpoints.
"""
import asyncio
import json
import os
from pathlib import Path
import time

import pytest

from ..capabilities import TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import SearchBackend, native, outcome, page
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import goals
from .test_model_sequence_live import ObservedDialogue, final_answer, safe_exception


class SearchEntryDialogue(ObservedDialogue):
    def __init__(self, phrase, scope):
        super().__init__()
        self.entry = native("find_assets", phrase=phrase, **{TASK: {
            "complete_request": False, "keywords": [phrase], "original_keywords": [phrase]}})
        if scope == "declared":
            self.entry = goals({"description": "Find " + phrase, "tool": "find_assets"}, calls=[self.entry])

    async def respond(self, messages, definitions):
        if self.entry is not None:
            proposal, self.entry = self.entry, None
            yield proposal(messages, definitions)
            return
        async for chunk in super().respond(messages, definitions):
            yield chunk


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_SEQUENCE") != "1", reason="Opt-in real model after scripted entry")
@pytest.mark.parametrize("scope", ["inferred", "declared"])
@pytest.mark.parametrize("phrase,utterance,followup", [
    ("lake water quality", "Find datasets about lake water quality", "Show this dataset's details"),
    ("高原气象观测", "我想找高原气象观测相关的数据集", "看下这个数据集的详情"),
])
def test_real_model_completes_incomplete_search_then_inspects_same_object(engine, tmp_path, scope, phrase, utterance, followup):
    report = {"scripted_initial_proposal": True, "subsequent_decisions": "real model",
        "upstream": "simulated", "scope": scope, "phrase": phrase, "correct": False, "turns": []}

    async def run():
        # One original match, no extra matches from variants. The runtime must
        # finish the keyword budget and still deliver the one actual candidate.
        backend = SearchBackend(lambda word, number: page(["observed-asset"] if word == phrase else [], 1 if word == phrase else 0))
        dialogue = SearchEntryDialogue(phrase, scope)
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            for label, message in (("search", utterance), ("detail", followup)):
                first_call, first_round = len(backend.calls), len(dialogue.rounds)
                started = time.perf_counter()
                row = {"turn": label, "correct": False}
                report["turns"].append(row)
                try:
                    events = await collect(service, sid, message, label)
                    row["answer"] = final_answer(events)
                    assert_completed(service, sid, events[-1])
                    operation, = outcome(service, sid, events)["operations"]
                    calls = backend.calls[first_call:]
                    if label == "search":
                        assert [name for name, _ in calls] == ["find_assets"] * 4
                        assert operation["search"]["done"] and len(operation["search"]["records"]) == 1
                        assert operation["search"]["original_keywords"] == [phrase]
                    else:
                        assert calls == [("inspect", {"reference": "observed-asset"})]
                        assert operation["capability"]["name"] == "inspect"
                    assert len(result_cards(events)) == 1
                    # The same bounds as the free-running sequence suite:
                    # keyword decisions may be incremental; inspection needs
                    # no new search, so it has the tighter decision budget.
                    assert len(dialogue.rounds) - first_round <= (6 if label == "search" else 4)
                    row["correct"] = True
                finally:
                    row.update(seconds=round(time.perf_counter()-started, 3),
                        model_calls=len(dialogue.rounds)-first_round, model_trace=dialogue.rounds[first_round:],
                        mcp_calls=backend.calls[first_call:])
            report["correct"] = True
        finally:
            await service.close()

    failure = None
    try:
        asyncio.run(run())
    except Exception as exc:
        failure = type(exc).__name__
        report["exception"] = safe_exception(exc)
    finally:
        directory = Path(os.getenv("DATASET_QA_LIVE_REPORT_DIR") or tmp_path)
        directory.mkdir(parents=True, exist_ok=True)
        suffix = "en" if phrase.isascii() else "zh"
        (directory / f"search-phase-{scope}-{suffix}.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if failure:
        pytest.fail("Continuation acceptance did not complete; see sanitized report (" + failure + ").", pytrace=False)
