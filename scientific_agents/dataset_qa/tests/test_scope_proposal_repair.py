"""Scope-only repair keeps submitted values without accepting unverified work."""
import asyncio
import json

from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, goals, payload, seed, text
from .test_independent_outcomes import ContractDialogue, batch, native, outcomes, read_backend
from .test_resource_index import Backend, POLICY


def test_incomplete_scope_repair_keeps_original_calls_until_all_outcomes_are_declared(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)

            def complete_scope(messages, definitions):
                feedback = json.loads(messages[-1].content)["runtime_feedback"]["detail"]
                assert feedback["retained_proposal"] is True
                assert len(backend.calls) == 1
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                return outcomes()(messages, definitions)

            dialogue.responses = [batch(native("inspect"), native("preview")),
                goals({"description": "数据集详情", "tool": "inspect"}), complete_scope, text()]
            events = await collect(service, sid, "查看详情和目录", "incomplete-scope")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) - baseline == 4
            assert backend.calls[1:] == [("data", "inspect", {"reference": "resource-1"}),
                ("data", "preview", {"reference": "resource-1"})]
            assert len(result_cards(events)) == 2
            assert len(payload(service, sid, events)["operations"]) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_scope_only_repair_revalidates_original_parent_and_requires_explicit_parameter_replacement(engine):
    async def run():
        # Exercise original explicit-null input compatibility at runtime.
        backend, dialogue = Backend(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        async def no_background_index(*args, **kwargs):
            return None
        service.resources.observe = no_background_index
        sid = session(service)
        declared = goals({"description": "Details", "tool": "dataset_info"},
            {"description": "Directory", "tool": "list_tree"})

        def replace_parameters(messages, definitions):
            feedback = json.loads(messages[-1].content)["runtime_feedback"]["detail"]
            assert feedback["origin"] == "directory_parent" and feedback["dispatched"] is False
            assert not backend.calls  # Retention must not normalize the string into null.
            assert not json.loads(messages[1].content).get("operations", {}).get("items")
            return goals({"description": "Details", "tool": "dataset_info"},
                {"description": "Directory", "tool": "list_tree"}, calls=[
                    native("dataset_info", dataset="one"),
                    native("list_tree", dataset="one", folder=None)])(messages, definitions)

        dialogue.responses = [batch(native("dataset_info", dataset="one"),
            native("list_tree", dataset="one", folder="None")), declared, replace_parameters, text()]
        try:
            events = await collect(service, sid, "Show details and root directory for dataset=one", "bad-parent")
            assert_completed(service, sid, events[-1])
            assert backend.calls == [("dataset_info", {"dataset": "one"}),
                ("list_tree", {"dataset": "one", "folder": None})]
            assert len(result_cards(events)) == 2
            assert len(dialogue.inputs) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_retained_focus_and_new_request_decision_survive_scope_only_repair(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        backend.items.append({"id": "resource-2", "title": "Other dataset"})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "Sample first dataset", "tool": "sample", "object": "candidate:1"}),
                action("request_input", missing="Sample quantity", question="How many records?")]
            waiting = await collect(service, sid, "Sample the first dataset", "waiting")
            assert waiting[-1]["status"] == "WAITING_INPUT"

            def original(messages, definitions):
                reply = batch(native("inspect"), native("preview"))(messages, definitions)
                meaning = action("remember", continuation="new", focus="candidate:2")
                return reply.model_copy(update={"tool_calls": [*meaning.tool_calls, *reply.tool_calls]})

            dialogue.responses = [original, outcomes(), text()]
            events = await collect(service, sid, "Instead show the second dataset's details and directory", "new-scope")
            assert_completed(service, sid, events[-1])
            ledger = payload(service, sid, events)
            assert ledger["resume"] is False
            assert len(ledger["operations"]) == 2
            assert all(item["target"]["path"] == "/items/1" for item in ledger["operations"])
            assert backend.calls[1:] == [("data", "inspect", {"reference": "resource-2"}),
                ("data", "preview", {"reference": "resource-2"})]
            assert payload(service, sid, waiting)["operations"][0]["state"] == "pending"
            assert "scope_proposal" not in ledger
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_replacement_discards_retained_calls_and_next_turn_starts_without_them(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [batch(native("inspect"), native("preview")), native("inspect", True), text()]
            events = await collect(service, sid, "Show details; inspect the directory only if necessary", "replace")
            assert_completed(service, sid, events[-1])
            assert backend.calls[1:] == [("data", "inspect", {"reference": "resource-1"})]

            def execute_new_goal(messages, definitions):
                assert len(backend.calls) == 2
                operations = json.loads(messages[1].content)["operations"]["items"]
                assert len(operations) == 1 and operations[0]["state"] == "pending"
                return native("preview")(messages, definitions)

            dialogue.responses = [goals({"description": "Directory", "tool": "preview"}), execute_new_goal, text()]
            following = await collect(service, sid, "Now show the directory", "new-turn")
            assert_completed(service, sid, following[-1])
            assert backend.calls[2:] == [("data", "preview", {"reference": "resource-1"})]
        finally:
            await service.close()
    asyncio.run(run())
