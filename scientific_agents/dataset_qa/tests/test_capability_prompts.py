"""Shared prompts retain reference/evidence safeguards without domain policy."""
import pytest

from ...agent_profiles import AgentProfile, DATASET_QA_PROFILE, ToolScope
from ..prompts import ANSWER_RULES, DECISION_RULES, answer_prompt, system_prompt


@pytest.mark.parametrize("profile", [DATASET_QA_PROFILE,
    AgentProfile("records", "Record assistant", tool_scope=(ToolScope("source", groups=("records",)),))])
def test_final_stage_is_shorter_and_keeps_scope_without_planning_instructions(profile):
    execution, final = system_prompt(profile), answer_prompt(profile)
    assert len(final) < len(execution)
    assert "remember.plan" in execution
    for instruction in ("remember.plan", "remember.goals", "remember.continuation", "load_mcp_tools", "resolve_resource"):
        assert instruction not in final
    assert "without internal planning or another tool call" in final
    if profile != DATASET_QA_PROFILE:
        assert profile.label in execution and profile.label in final
        assert "configured capabilities" in execution and "configured capabilities" in final


def test_execution_preserves_reference_precedence_ordinals_and_confirmed_choices():
    for safeguard in (
        "current request overrides old conditions", "request_source", "resolve wording conflicts first",
        "request_objects", "Explicit choices precede old focus", "unless another referent competes",
        "relevant published candidate list", "second means array index 1", "supplied handles",
        "Summaries cannot establish/override references", "__qa_object", "remember.focus",
        "null clears unresolved old focus", "confirmed selections separately",
        "viewing another object does not discard them", "selected_total", "read_result without result_id",
    ):
        assert safeguard in DECISION_RULES


def test_execution_preserves_goal_evidence_continuation_and_terminal_guards():
    for safeguard in (
        "Variants/pages share outcomes", "independent outcomes stay separate", "Goals persist",
        "__qa_supporting", "delivery_pending is unconfirmed, not auxiliary",
        "Associate late goals with sufficient receipts", "deliver_results confirmations",
        "do not rerun MCP", "independent samples",
        "Never confirm unfinished work", "Only MCP receipts prove execution",
        "Never drop outstanding goals", "remember.continuation to continue or new",
        "Similar tools imply no continuation", "pending handles belong only to that continuation",
        "one terminal action", "respond_from_context cannot accompany new MCP execution",
        "do not use the whole request as an exact resource name or execute the research itself",
    ):
        assert safeguard in DECISION_RULES


def test_final_answer_preserves_external_fact_delivery_and_named_object_guards():
    for safeguard in (
        "Do not invent identifiers, names, facts or execution results", "Do not expose backend errors",
        "Respect request_source and request_objects", "explicit current choices precede old focus",
        "ordinals only within the relevant published candidate list", "summaries cannot establish or override references",
        "An unavailable resource lookup does not establish that a file is absent",
        "Do not claim unperformed work succeeded", "delivery_manifest", "answer_evidence",
        "delivery_links", "do not relabel a CSV as JSONL", "runtime attaches these clickable links",
        "do not copy their URLs", "delivery_next_offset", "truncated preview omits saved evidence",
        "not a count of verified relevant resources", "candidate, not verified suitability",
        "titles and identifiers alone do not establish those facts", "use its own supplied name verbatim",
        "record_path", "name_paths", "Do not substitute identifiers, source/provider labels",
    ):
        assert safeguard in ANSWER_RULES


def test_global_prompts_have_no_catalogue_specific_keyword_or_quantity_policy():
    for prompt in (system_prompt(), answer_prompt()):
        for policy in ("six actually returned", "four completed keywords", "at most four distinct phrases",
                "__qa_task.original_keywords", "search_corpus_datasets", "query_pubchem_compounds"):
            assert policy not in prompt
