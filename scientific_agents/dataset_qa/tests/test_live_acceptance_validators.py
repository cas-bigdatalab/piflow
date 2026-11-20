"""Acceptance judges actual execution; rejected drafts remain recovery diagnostics."""
import pytest

from ..contracts import QAError
from .test_model_sequence_live import (
    AcceptanceFailure, verify_combined_model_identifiers, verify_combined_retrieval,
)


REFERENCE = "observed-source"
DETAIL = "get_corpus_dataset_detail"
DIRECTORY = "get_corpus_dataset_directory"


@pytest.fixture
def combined():
    calls = [(DETAIL, {"cstr": REFERENCE}), (DIRECTORY, {"cstr": REFERENCE})]
    saved = {"operations": [{"capability": {"name": name}, "state": "succeeded",
        "attempts": [{"state": "succeeded", "result_id": name}]} for name, _ in calls]}
    events = [{"type": "result", "items": [{"result_id": name} for name, _ in calls]},
        {"type": "done", "status": "COMPLETED"}]
    outputs = {DETAIL: {"cstr": REFERENCE}, DIRECTORY: {"data": [{"id": "observed-node"}]}}
    return {"calls": calls, "saved": saved, "events": events, "reference": REFERENCE,
        "outputs": outputs, "failures": {}}


@pytest.mark.parametrize("origin", ["native", "plan"])
def test_rejected_identifier_draft_does_not_fail_correct_actual_execution(combined, origin):
    arguments = {"cstr": "invented-source", "file_id": "root"}
    draft = {"name": DIRECTORY, "public_arguments": arguments} if origin == "native" else {
        "name": "remember", "public_arguments": {"plan": {"steps": [{"tool": DIRECTORY, "arguments": arguments}]}}}
    diagnostics = verify_combined_model_identifiers([{"tool_calls": [draft]}], REFERENCE)
    assert diagnostics["violation_count"] == 2
    assert {item["field"] for item in diagnostics["violations"]} == {"cstr", "file_id"}
    assert {item["origin"] for item in diagnostics["violations"]} == {origin}
    assert verify_combined_retrieval(**combined)["delivered_cards"] == 2


@pytest.mark.parametrize("field,value", [("cstr", "invented-source"), ("file_id", "root")])
def test_invalid_dispatched_identifiers_still_fail_acceptance(combined, field, value):
    combined["calls"][1][1][field] = value
    with pytest.raises(AcceptanceFailure, match="grounded CSTR|guessed file identifier"):
        verify_combined_retrieval(**combined)


@pytest.mark.parametrize("failure", ["zero_calls", "missing_delivery", "no_progress"])
def test_missing_execution_or_incomplete_outcome_still_fails_acceptance(combined, failure):
    if failure == "zero_calls":
        combined["calls"] = []
    elif failure == "missing_delivery":
        combined["events"][0]["items"] = []
    else:
        combined["saved"]["error"] = {"error_code": "no_progress"}
    with pytest.raises(AcceptanceFailure):
        verify_combined_retrieval(**combined)


def test_recovered_draft_allows_only_evidenced_unsupported_partial(combined):
    diagnostics = verify_combined_model_identifiers([{"tool_calls": [
        {"name": DIRECTORY, "public_arguments": {"file_id": "root"}}]}], REFERENCE)
    assert diagnostics["violation_count"] == 1
    combined["saved"]["operations"][1].update(state="failed", attempts=[])
    combined["saved"]["error"] = {"error_code": "tool_failed"}
    combined["events"][0]["items"] = [{"result_id": DETAIL}]
    combined["events"][-1]["outcome"] = "partial"
    combined["outputs"].pop(DIRECTORY)
    combined["failures"][DIRECTORY] = QAError("tool_failed", "Directory unavailable", 502,
        detail={"message": "Unsupported source operation"})
    assert verify_combined_retrieval(**combined, directory="unsupported")["delivered_cards"] == 1
    combined["failures"] = {}
    with pytest.raises(AcceptanceFailure, match="explicitly unsupported upstream"):
        verify_combined_retrieval(**combined, directory="unsupported")
