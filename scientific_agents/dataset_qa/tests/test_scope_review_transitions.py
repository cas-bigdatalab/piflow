"""Receipt-driven scope review across capability names, modes and deployments."""
import asyncio
from copy import deepcopy
import json

import pytest

from ..context import encode
from ..context_budget import navigation_identity
from ..dialogue import Dialogue
from ..execution import Execution
from ..service import DatasetQA
from .assertions import assert_completed
from .test_context_budget import cost
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, text
from .test_execution_decision import goal, receipt, tools, unfinished_search


@pytest.mark.parametrize("name", ["search", "inspect"])
def test_unconfirmed_receipt_only_exposes_scope_and_evidence_decisions(name):
    execution = Execution()
    item = goal(execution, name, required=False, direct=False)
    item["inferred"] = True
    receipt(execution, item)
    before = deepcopy(execution.operations.items)
    assert execution.reviewing_scope and not execution.result_ready
    actions = execution.actions(tools())
    assert {"remember", "deliver_results", "read_result", "request_input"} <= actions
    assert not set(tools()) & actions
    assert not {"find_artifacts", "resolve_resource"} & actions
    assert execution.operations.items == before

    execution.operations.register("Additional requested inspection", {"server": "archive", "name": "inspect"}, planned=True)
    assert not execution.reviewing_scope
    assert "inspect" in execution.actions(tools())


def test_prerequisites_and_unfinished_searches_do_not_enter_scope_review():
    execution = Execution()
    item = goal(execution, required=False)
    receipt(execution, item)
    assert not execution.reviewing_scope  # Explicitly auxiliary, not inferred.
    item["inferred"] = True
    searching = unfinished_search(execution, required=False)
    assert not execution.reviewing_scope
    searching["search"]["done"] = True
    assert execution.reviewing_scope


@pytest.mark.parametrize("mode", ["direct", "planned"])
@pytest.mark.parametrize("count", [1, 2])
def test_result_readiness_depends_on_all_explicit_goals_and_receipts(mode, count):
    execution = Execution()
    for index in range(count):
        item = goal(execution, "inspect" if index else "search", direct=False)
        item[mode] = True
        receipt(execution, item)
    assert execution.result_ready
    item["output"] = "answer"
    assert not execution.result_ready  # Interpretation still needs the model.
    item["output"] = "result"
    item["state"] = "pending"
    assert not execution.result_ready


def test_completed_unconfirmed_retrieval_has_one_scope_decision_and_no_repeat_call(engine):
    async def run():
        backend = configured()

        def review(messages, definitions):
            context = json.loads(messages[1].content)
            assert context["execution_decision"]["phase"] == "review"
            assert not any(item["function"]["name"].startswith("mcp_") for item in definitions)
            memory = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
            assert "plan" not in memory["parameters"]["properties"]
            choices = memory["parameters"]["$defs"]["Goal"]["properties"]["tool"]["enum"]
            assert any(alias.endswith("_inspect") for alias in choices)
            assert "arguments_schema" not in encode(memory)  # No duplicate planning catalogue.
            return action("deliver_results")

        dialogue = BareDialogue(load(), remote("search", query="river observations"), review, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            events = await collect(service, session(service), "Find river observations")
            assert_completed(service, None, events[-1])
            assert len(backend.calls) == 1 and len(dialogue.inputs) == 4
            assert len(result_cards(events)) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_scope_declaration_reopens_only_normal_validated_execution(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="river"),
            goals({"description": "Compare river records with marine records", "tool": "search", "output": "answer"}),
            remote("search", query="marine"), action("deliver_results"), text("Two queried collections are available."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            events = await collect(service, session(service), "Compare river and marine records")
            assert_completed(service, None, events[-1])
            assert [args["query"] for _, _, args in backend.calls] == ["river", "marine"]
            assert len(dialogue.inputs) == 6
            assert dialogue.inputs[-1][1] == []  # Interpretation phase cannot execute tools.
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("review", [False, True])
def test_compacted_directory_keeps_an_available_recovery_tool(engine, review):
    async def run():
        gateway = configured().gateway()
        service = DatasetQA(engine, BareDialogue(), gateway)
        execution = Execution()
        if review:
            item = goal(execution, required=False)
            item["inferred"] = True
            receipt(execution, item)
        try:
            async with gateway.session() as session_tools:
                directory = session_tools.list_servers()
                assert "next_offset" not in directory  # Even a complete page can be compacted.
                context = {"mcp_servers": directory}
                definitions, _ = service._action_definitions(session_tools, execution, {}, context, 0)
                names = {item["function"]["name"] for item in definitions}
                dialogue = Dialogue(model=object())
                thin = {"mcp_servers": navigation_identity(directory)}
                ceiling = cost(dialogue.messages("Find observations", thin), definitions)
                bounded = dialogue._budget(dialogue.messages("Find observations", context), definitions, len, ceiling)
                actual = json.loads(bounded[1].content)["mcp_servers"]
                assert actual["details_tool"] in names
                assert actual["items"] == thin["mcp_servers"]["items"]
                memory = next(item["function"] for item in definitions if item["function"]["name"] == "remember")
                assert "enum" not in memory["parameters"]["$defs"]["Goal"]["properties"]["tool"]
        finally:
            await service.close()
    asyncio.run(run())
