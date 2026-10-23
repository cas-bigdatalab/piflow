"""A semantic declaration after execution must preserve grounded receipts."""
import asyncio
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import ToolMessage
import pytest

from .assertions import assert_completed, assert_handled
from ..capabilities import OBJECT, SUPPORTING
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, text


def lookup_backend(name, *, varying=False):
    """Use arbitrary MCP names so the regression cannot depend on search names."""
    backend = configured()
    backend.catalog["data"][0].name = name
    factory = backend.client

    def client(*args, **kwargs):
        connection = factory(*args, **kwargs)
        execute = connection.call_tool

        async def call(tool, arguments, **options):
            if tool == name and varying:
                backend.items = [{"id": arguments["query"], "title": arguments["query"]}]
            value = await execute("search" if tool == name else tool, arguments, **options)
            if tool == name:
                server, _, recorded = backend.calls[-1]
                backend.calls[-1] = (server, tool, recorded)
            return value

        connection.call_tool = call
        return connection

    backend.client = client
    return backend


def confirm_available_receipt(messages, definitions):
    """A scripted model explicitly selects only IDs advertised by the tool."""
    if not definitions:
        return text("Please see the retrieved candidates.")
    schema = next(item["function"]["parameters"] for item in definitions
        if item["function"]["name"] == "deliver_results")
    arguments = {}
    if "confirmations" in schema.get("properties", {}):
        assert "confirmations" in schema["required"]
        properties = schema["properties"]["confirmations"]["items"]["properties"]
        goal_ids = properties["goal"]["enum"]
        result_ids = properties["result_ids"]["items"]["enum"]
        # These tests intentionally have exactly one compatible receipt. They
        # do not select arbitrary evidence when multiple outcomes are possible.
        assert len(goal_ids) == len(result_ids) == 1
        arguments["confirmations"] = [{"goal": goal_ids[0], "result_ids": result_ids}]
    Draft202012Validator(schema).validate(arguments)
    return action("deliver_results", **arguments)


@pytest.mark.parametrize("tool,query", [
    ("catalogue_lookup", "chemical engineering"),
    ("discover_records", "marine heatwaves"),
])
def test_late_goal_after_success_delivers_without_reexecuting_mcp(engine, tool, query):
    async def run():
        backend = lookup_backend(tool)

        # This is the production order: no goal before the native call, a goal
        # declaration once evidence exists, then delivery. The scripted model
        # now explicitly confirms the receipt IDs exposed by delivery's schema;
        # no helper inserts goals, native invocations or execution receipts.
        dialogue = BareDialogue(action("list_mcp_servers"), load(), remote(tool, query=query),
            goals({"description": "Find related datasets", "tool": tool}),
            *([confirm_available_receipt] * 4))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find datasets for " + query, "late-goal")
            assert backend.calls == [("data", tool, {"query": query})]
            assert_completed(service, sid, events[-1])
            card, = result_cards(events)
            state = payload(service, sid, events)
            required = [item for item in state["operations"] if item.get("required", True)]
            assert required and all(item["state"] == "succeeded" for item in required)
            assert state["delivery_sources"] == [card["result_id"]]
            assert len(dialogue.inputs) <= 6
            observations = [json.loads(message.content) for messages, _ in dialogue.inputs
                for message in messages if isinstance(message, ToolMessage)]
            assert not any(value.get("error") == "invalid_delivery" for value in observations)
        finally:
            await service.close()

    asyncio.run(run())


def test_missing_confirmation_has_one_actionable_correction_without_reexecution(engine):
    async def run():
        backend = lookup_backend("catalogue_lookup")

        def repair(messages, definitions):
            feedback = next(json.loads(message.content) for message in reversed(messages)
                if isinstance(message, ToolMessage) and message.name == "deliver_results")
            assert feedback["error"] in {"invalid_parameters", "invalid_delivery"}
            assert "confirmations" in json.dumps(feedback)
            return confirm_available_receipt(messages, definitions)

        dialogue = BareDialogue(load(), remote("catalogue_lookup", query="resources"),
            goals({"description": "Find related datasets", "tool": "catalogue_lookup"}),
            action("deliver_results"), repair, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related datasets", "confirm-receipt")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == len(result_cards(events)) == 1
            assert len(dialogue.inputs) == 6
            state = payload(service, sid, events)
            assert all(item["state"] == "succeeded" for item in state["operations"])
        finally:
            await service.close()

    asyncio.run(run())


def test_available_receipt_does_not_skip_a_new_requested_query(engine):
    async def run():
        backend = lookup_backend("discover_records", varying=True)

        def refine(messages, definitions):
            state = json.loads(messages[1].content)
            goal = next(item for item in state["operations"]["items"]
                if item["description"] == "Find the refined resources")
            assert goal["state"] == "pending"
            schema = next(item["function"]["parameters"] for item in definitions
                if item["function"]["name"] == "deliver_results")
            assert "confirmations" in schema.get("required", [])
            # Declaring the same capability is not confirmation that this old
            # query meets the goal. A different query must still execute.
            return remote("discover_records", query="refined")(messages, definitions)

        dialogue = BareDialogue(load(), remote("discover_records", query="broad"),
            goals({"description": "Find the refined resources", "tool": "discover_records"}),
            refine, text("Please see the refined candidates."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find relevant refined resources", "new-query")
            assert_completed(service, sid, events[-1])
            assert [arguments["query"] for _, _, arguments in backend.calls] == ["broad", "refined"]
            card, = result_cards(events)
            assert card["data"]["items"][0]["id"] == "refined"
            assert len(dialogue.inputs) == 5
        finally:
            await service.close()

    asyncio.run(run())


def test_partial_confirmation_feedback_preserves_all_uncommitted_choices(engine):
    async def run():
        backend = lookup_backend("catalogue_lookup")
        selected = []

        def partial_confirmation(messages, definitions):
            items = json.loads(messages[1].content)["operations"]["items"]
            for goal in (item for item in items if item["state"] == "pending"):
                owner = next(item for item in items if item["state"] == "succeeded"
                    and item["capability"] == goal["capability"]
                    and item.get("target") == goal.get("target"))
                selected.append({"goal": goal["id"], "result_ids": owner["result_ids"]})
            assert len(selected) == 2
            return action("deliver_results", confirmations=selected[:1])

        def repair(messages, definitions):
            feedback = next(json.loads(message.content) for message in reversed(messages)
                if isinstance(message, ToolMessage) and message.name == "deliver_results")
            assert feedback["error"] == "invalid_delivery"
            assert feedback["detail"]["confirmations"] == selected
            items = json.loads(messages[1].content)["operations"]["items"]
            assert all(item["state"] == "pending" for item in items
                if item["id"] in {value["goal"] for value in selected})
            schema = next(item["function"]["parameters"] for item in definitions
                if item["function"]["name"] == "deliver_results")
            arguments = {"confirmations": feedback["detail"]["confirmations"]}
            Draft202012Validator(schema).validate(arguments)
            return action("deliver_results", **arguments)

        dialogue = BareDialogue(load(), remote("catalogue_lookup", query="resources"),
            remote("inspect", **{OBJECT: "object:1"}),
            goals({"description": "Find related datasets", "tool": "catalogue_lookup"},
                {"description": "Describe the first dataset", "tool": "inspect", "object": "object:1"}),
            partial_confirmation, repair, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related datasets and describe the first", "atomic-confirmations")
            assert_completed(service, sid, events[-1])
            assert [name for _, name, _ in backend.calls] == ["catalogue_lookup", "inspect"]
            assert len(result_cards(events)) == 2
            state = payload(service, sid, events)
            assert state["delivery_sources"] == [value["result_ids"][0] for value in selected]
            assert all(item["state"] == "succeeded" for item in state["operations"])
            assert len(dialogue.inputs) == 7
        finally:
            await service.close()

    asyncio.run(run())


def test_invalid_delivery_reference_does_not_commit_confirmation_before_retry(engine):
    async def run():
        backend = lookup_backend("catalogue_lookup")
        selected = []

        def invalid_reference(messages, definitions):
            reply = confirm_available_receipt(messages, definitions)
            selected.extend(reply.tool_calls[0]["args"]["confirmations"])
            # Persisted/legacy callers can supply references even though new
            # models receive the smaller confirmation-only delivery schema.
            return action("deliver_results", confirmations=selected,
                references={"current": {"result_id": selected[0]["result_ids"][0], "path": "/missing"}})

        def repair(messages, definitions):
            feedback = next(json.loads(message.content) for message in reversed(messages)
                if isinstance(message, ToolMessage) and message.name == "deliver_results")
            assert feedback["error"] == "result_not_found"
            items = json.loads(messages[1].content)["operations"]["items"]
            assert next(item for item in items if item["id"] == selected[0]["goal"])["state"] == "pending"
            reply = confirm_available_receipt(messages, definitions)
            assert reply.tool_calls[0]["args"]["confirmations"] == selected
            return reply

        dialogue = BareDialogue(load(), remote("catalogue_lookup", query="resources"),
            goals({"description": "Find related datasets", "tool": "catalogue_lookup"}),
            invalid_reference, repair, text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related datasets", "invalid-reference")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == len(result_cards(events)) == 1
            assert len(dialogue.inputs) == 6
            state = payload(service, sid, events)
            required = next(item for item in state["operations"] if item["id"] == selected[0]["goal"])
            assert len(required["attempts"]) == 1
            assert required["attempts"][0]["confirmation"] is True
        finally:
            await service.close()

    asyncio.run(run())


@pytest.mark.parametrize("case", ["supporting", "other-capability", "multiple-goals"])
def test_late_goal_never_promotes_unrelated_or_ambiguous_evidence(engine, case):
    async def run():
        backend = lookup_backend("catalogue_lookup")
        arguments = {"query": "available resources"}
        if case == "supporting":
            arguments[SUPPORTING] = True
        declarations = [{"description": "Find requested resources", "tool": "catalogue_lookup"}]
        if case == "other-capability":
            declarations = [{"description": "Sample the requested resource", "tool": "sample"}]
        elif case == "multiple-goals":
            declarations.append({"description": "Find a second independent source", "tool": "catalogue_lookup"})
        dialogue = BareDialogue(load(), remote("catalogue_lookup", **arguments), goals(*declarations),
            action("deliver_results"), action("deliver_results"), action("deliver_results"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Complete the requested operations", "unrelated-evidence")
            assert len(backend.calls) == 1
            assert_handled(service, sid, events[-1])
            required = [item for item in payload(service, sid, events)["operations"]
                if item.get("required", True)]
            assert required and any(item["state"] != "succeeded" for item in required)
            # Recovery may show unconfirmed findings, never count them as
            # satisfying the late goals. Explicit auxiliary receipts stay hidden.
            assert len(result_cards(events))==(0 if case=="supporting" else 1)
            assert events[-1]["outcome"]=="partial"
            assert all(not item["attempts"] for item in required)
        finally:
            await service.close()

    asyncio.run(run())
