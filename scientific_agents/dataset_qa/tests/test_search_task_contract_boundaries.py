"""Search mode stays explicit even when outcome scope is already supplied."""
import asyncio
import json

from jsonschema import Draft202012Validator
import pytest

from ..capabilities import GOAL, OBJECT, SUPPORTING, TASK
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import KEYWORDS, SearchBackend, native, outcome, page
from .test_dataset_qa import action, collect, engine, remote, session
from .test_decisions import BareDialogue, text
from .test_planning import approve
from .test_runtime_transitions import keyword_extension, search_plan


@pytest.mark.parametrize("scope", ["supporting", "declared_goal"])
def test_search_scope_cannot_silently_choose_discovery_instead_of_exact_lookup(engine, scope):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        arguments = {"phrase": "asset-1"}
        if scope == "supporting":
            arguments[SUPPORTING] = True

        def omit_mode(messages, definitions):
            schema = next(item["function"]["parameters"] for item in definitions
                if item["function"]["name"].endswith("_find_assets"))
            assert not Draft202012Validator(schema).is_valid(arguments)
            return remote("find_assets", **arguments)(messages, definitions)

        def supply_exact_mode(messages, definitions):
            assert backend.calls == []
            operations = json.loads(messages[1].content).get("operations", {}).get("items", [])
            assert len(operations) == int(scope == "declared_goal")
            return native("find_assets", **arguments, **{TASK: {
                "complete_request": False, "keywords": None, "original_keywords": None}})(messages, definitions)

        responses = []
        if scope == "declared_goal":
            responses.append(action("remember", goals=[{
                "description": "Find asset-1", "tool": "find_assets"}]))
        responses.extend([omit_mode, supply_exact_mode])
        if scope == "supporting":
            responses.append(native("inspect", **{
                OBJECT: "object:1", TASK: {"complete_request": True}}))
        dialogue = BareDialogue(*responses, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            request = "Inspect asset-1 using a supporting exact lookup" if scope == "supporting" else "Find asset-1 only"
            events = await collect(service, sid, request)
            assert_completed(service, sid, events[-1])
            expected = ["find_assets", "inspect"] if scope == "supporting" else ["find_assets"]
            assert [name for name, _ in backend.calls] == expected
            search = next(item for item in outcome(service, sid, events)["operations"]
                if item["capability"]["name"] == "find_assets")
            assert "search" not in search
            assert search["required"] is (scope == "declared_goal")
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_plan_keyword_checkpoint_matches_narrow_schema_and_restores_saved_parameters(engine):
    async def run():
        backend = SearchBackend(lambda word, number: page(["asset-1"], 1))
        spec = search_plan()
        spec["steps"][0]["arguments"]["per_page"] = 2

        def continue_search(messages, definitions):
            context = json.loads(messages[1].content)
            guidance = context["execution_decision"]["guidance"]
            assert "supply only __qa_goal" in guidance
            assert "__qa_task={keywords:[...]}" in guidance
            assert "do not include complete_request or business arguments" in guidance
            tool = next(item["function"] for item in definitions if item["function"]["name"].endswith("_find_assets"))
            schema = tool["parameters"]
            assert set(schema["properties"]) == {GOAL, TASK}
            assert set(schema["properties"][TASK]["properties"]) == {"keywords"}
            assert len(backend.calls) == 1
            return keyword_extension(messages, definitions)

        dialogue = BareDialogue(action("remember", plan=spec), approve, continue_search, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find chemical engineering datasets")
            assert_completed(service, sid, events[-1])
            saved = outcome(service, sid, events)
            assert saved["plan"]["revision"] == saved["plan"]["reviewed"] == 1
            operation, = saved["operations"]
            assert operation["search"]["original_keywords"] == KEYWORDS[:1]
            assert operation["search"]["completed"] == KEYWORDS
            assert [args["phrase"] for _, args in backend.calls] == KEYWORDS
            assert all(args["per_page"] == 2 and args["page_number"] == 1 for _, args in backend.calls)
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())
