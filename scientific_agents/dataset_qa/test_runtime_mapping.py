"""Native decisions exercise semantic ownership and evidence-based convergence."""
import asyncio
import json
from types import SimpleNamespace

from langchain_core.messages import ToolMessage

from .capabilities import GOAL, OBJECT, SUPPORTING
from .contracts import Options
from .execution import Execution
from .mcp import Tool
from .service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, for_goal, goals, payload, seed, text


def test_closed_goals_do_not_publish_an_empty_enum_despite_an_auxiliary_scope():
    tool = Tool("service", "query", "Retrieve resources", {"type": "object", "properties": {}}, {}, {})
    execution = Execution()
    capability = {"server": tool.server, "name": tool.name}
    for description in ("First outcome", "Second outcome"):
        execution.blocked.add(execution.operations.register(description, capability, planned=True))
    execution.operations.register("Auxiliary", capability, required=False)
    tools = SimpleNamespace(loaded={tool.alias: tool})
    assert DatasetQA._definitions([tool.definition()], tools, execution)==[]


def test_native_search_then_detail_delivers_terminal_provenance_not_last_position(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resource"),
            remote("inspect", **{OBJECT: "object:1"}), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Find a resource and show its details")
            assert values[-1]["status"]=="COMPLETED"
            card, = result_cards(values)
            assert card["title"].endswith("inspect")
            assert card["data"]["items"][0]["reference"]=="a"
            assert [call[1] for call in backend.calls]==["search", "inspect"]
        finally:
            await service.close()
    asyncio.run(run())


def test_completed_parent_reference_does_not_require_a_clarification_resume_choice(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            card = await seed(service, dialogue, sid)
            # Use the already completed task as an API reference, not an interrupt.
            parent_id = card["result_id"].rsplit(":", 1)[0]
            before = len(dialogue.inputs)
            dialogue.responses = [remote("search", query="new"), action("deliver_results"), text()]
            values = [event async for event in service.stream("alice", sid, "Find new resources", "new", Options(), parent_id)
                if event is not None]
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            assert payload(service, sid, values)["resume"] is False
            assert len(dialogue.inputs)-before==3
        finally:
            await service.close()
    asyncio.run(run())


def test_reversed_same_capability_goals_keep_semantic_result_ownership(engine):
    async def run():
        backend = configured()
        original = backend.client
        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            call = client.call_tool
            async def execute(name, arguments, **options):
                backend.items = [{"id": arguments["query"], "title": arguments["query"]}]
                return await call(name, arguments, **options)
            client.call_tool = execute
            return client
        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = BareDialogue(load(), goals(
            {"description": "Explain precipitation", "tool": "search", "output": "answer"},
            {"description": "Display runoff", "tool": "search"}),
            for_goal("Display runoff", remote("search", query="runoff")),
            for_goal("Explain precipitation", remote("search", query="precipitation")),
            action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid, "Explain precipitation resources and display runoff resources")
            assert values[-1]["status"]=="COMPLETED"
            assert result_cards(values)[0]["data"]["items"][0]["id"]=="runoff"
            ledger = payload(service, sid, values)
            owner = next(item for item in ledger["operations"] if item["description"]=="Display runoff")
            assert owner["attempts"][0]["result_id"].endswith(":0")
            assert all(GOAL not in args for _, _, args in backend.calls)
        finally:
            await service.close()
    asyncio.run(run())


def test_ambiguous_batch_is_corrected_before_any_mcp_dispatch(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), goals(
            {"description": "Explain A", "tool": "search", "output": "answer"},
            {"description": "Display B", "tool": "search"}, calls=[remote("search", query="B")]),
            for_goal("Display B", remote("search", query="B")),
            for_goal("Explain A", remote("search", query="A")), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Explain A and display B")
            assert values[-1]["status"]=="COMPLETED"
            assert backend.calls==[("data", "search", {"query": "B"}), ("data", "search", {"query": "A"})]
            feedback = [json.loads(m.content) for messages, _ in dialogue.inputs for m in messages
                if isinstance(m, ToolMessage) and json.loads(m.content).get("error")=="invalid_parameters"]
            assert feedback and feedback[0]["detail"]["field"]==GOAL
        finally:
            await service.close()
    asyncio.run(run())


def test_late_goal_declaration_reuses_only_the_matching_invocation(engine):
    async def run():
        backend = configured()
        original = backend.client
        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            call = client.call_tool
            async def execute(name, arguments, **options):
                backend.items = [{"id": arguments["query"], "title": arguments["query"]}]
                return await call(name, arguments, **options)
            client.call_tool = execute
            return client
        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = BareDialogue(load(), remote("search", query="A", **{SUPPORTING: True}),
            remote("search", query="B", **{SUPPORTING: True}), goals(
                {"description": "Explain A", "tool": "search", "output": "answer"},
                {"description": "Display B", "tool": "search"}),
            action("deliver_results"),  # Mere same-capability evidence cannot fulfill both goals.
            for_goal("Display B", remote("search", query="B")),
            for_goal("Explain A", remote("search", query="A")), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid, "Explain A and display B")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==2
            assert result_cards(values)[0]["data"]["items"][0]["id"]=="B"
            ledger = payload(service, sid, values)
            first, second = [item for item in ledger["operations"] if item.get("required")]
            assert first["attempts"][0]["result_id"].endswith(":0")
            assert second["attempts"][0]["result_id"].endswith(":1")
            assert all(attempt.get("reused") for item in (first, second) for attempt in item["attempts"])
        finally:
            await service.close()
    asyncio.run(run())


def test_two_declared_objects_use_one_existing_result_list(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.catalog["data"][1].annotations = {"readOnlyHint": True, "idempotentHint": True}
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "Details of A", "tool": "inspect", "object": "candidate:1"},
                {"description": "Details of B", "tool": "inspect", "object": "candidate:2"}),
                remote("inspect", **{OBJECT: "candidate:2"}),
                remote("inspect", **{OBJECT: "candidate:1"}), text()]
            values = await collect(service, sid, "Show both details", "both")
            assert values[-1]["status"]=="COMPLETED"
            card, = result_cards(values)
            assert set(card)=={"result_id", "view_type", "title", "data"}
            assert {row["reference"] for row in card["data"]["items"]}=={"a", "b"}
            assert dialogue.inputs[-1][1]==[]
            assert len(backend.calls)==3
        finally:
            await service.close()
    asyncio.run(run())


def test_failed_variant_preserves_success_without_claiming_full_completion(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original = backend.client
        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            call = client.call_tool
            async def execute(name, arguments, **options):
                backend.protocol_error = arguments.get("query")=="unavailable"
                return await call(name, arguments, **options)
            client.call_tool = execute
            return client
        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = BareDialogue(load(), goals({"description": "Search two necessary sources", "tool": "search"},
            calls=[remote("search", query="available"), remote("search", query="unavailable")]),
            action("deliver_results"), text("The available source is shown; the other could not be obtained."))
        service = DatasetQA(engine, dialogue, gateway)
        try:
            values = await collect(service, session(service), "Search both sources")
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="tool_failed"
            assert len(result_cards(values))==1 and len(backend.calls)==2
            assert "部分" in "".join(event.get("text", "") for event in values)
        finally:
            await service.close()
    asyncio.run(run())


def test_query_changes_without_new_rows_stop_with_saved_result(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        dialogue = BareDialogue(load(), remote("search", query="one"), remote("search", query="two"),
            remote("search", query="three"), text("These are the available resources."))
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Find related resources")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==3
            assert len(dialogue.inputs)==5 and dialogue.inputs[-1][1]==[]
            assert len(result_cards(values))==1
            assert result_cards(values)[0]["data"]["items"]==backend.items
        finally:
            await service.close()
    asyncio.run(run())


def test_stale_goal_does_not_prevent_another_goal_using_same_tool(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        def check(messages, definitions):
            schema = next(d["function"]["parameters"] for d in definitions if d["function"]["name"].endswith("_search"))
            assert len(schema["properties"][GOAL]["enum"])==1
            return for_goal("Other necessary source", remote("search", query="other"))(messages, definitions)
        dialogue = BareDialogue(load(), goals(
            {"description": "Investigate one source", "tool": "search", "output": "answer"},
            {"description": "Other necessary source", "tool": "search", "output": "answer"}),
            *[for_goal("Investigate one source", remote("search", query=str(i))) for i in range(3)],
            check, action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Investigate both sources")
            assert values[-1]["status"]=="COMPLETED" and len(backend.calls)==4
            assert backend.calls[-1][2]=={"query": "other"}
        finally:
            await service.close()
    asyncio.run(run())
