"""Evidence must trigger a decision before unplanned query variants consume the turn."""
import asyncio
import json

from langchain_core.messages import HumanMessage, ToolMessage

from .assertions import assert_completed, assert_handled
from ..capabilities import OBJECT
from ..contracts import Limits
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, for_goal, goals, payload, text


def read_latest(messages, definitions):
    result_id = next(json.loads(message.content)["result_id"] for message in reversed(messages)
        if isinstance(message, ToolMessage) and json.loads(message.content).get("result_id"))
    return action("read_result", result_id=result_id)


def varying_search_backend():
    """Every query returns new evidence, so duplicate-result detection cannot help."""
    backend = configured()
    factory = backend.client

    def client(*args, **kwargs):
        connection = factory(*args, **kwargs)
        execute = connection.call_tool

        async def call(name, arguments, **options):
            if name == "search":
                backend.items = [{"id": arguments["query"], "title": arguments["query"]}]
            return await execute(name, arguments, **options)

        connection.call_tool = call
        return connection

    backend.client = client
    return backend


def test_log_shaped_query_expansion_requests_a_decision_before_exhausting_rounds(engine):
    async def run():
        backend = varying_search_backend()
        # The reported run used exactly these 12 planning actions. Fresh rows and
        # result reads kept the old no-progress detector from stopping expansion.
        sequence = [action("list_mcp_servers"), load(), remote("search", query="q1"),
            read_latest, remote("search", query="q2"), remote("search", query="q3"),
            read_latest, remote("search", query="q4"), read_latest,
            remote("search", query="q5"), read_latest, remote("search", query="q6")]

        def decide(messages, definitions):
            if not definitions:
                return text("已找到候选资源，请查看检索结果。")
            feedback = []
            for message in messages[2:]:
                if isinstance(message, (HumanMessage, ToolMessage)):
                    try:
                        value = json.loads(message.content)
                    except json.JSONDecodeError:
                        # Ordinary user text is also a HumanMessage. Only
                        # runtime JSON feedback can trigger this model decision.
                        continue
                    if isinstance(value, dict):
                        feedback.append(value.get("runtime_feedback", value))
            if any(value.get("error") == "invalid_parameters" for value in feedback):
                return action("deliver_results")
            response = sequence.pop(0)
            return response(messages, definitions) if callable(response) else response

        dialogue = BareDialogue(*([decide] * 14))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related resources", "bounded-search")
            assert_completed(service, None, events[-1])
            assert len(backend.calls) == 1
            card, = result_cards(events)
            assert len(dialogue.inputs) <= 7
            assert "step_limit" not in json.dumps(events)
            reviews = [json.loads(messages[1].content).get("execution_decision")
                for messages, definitions in dialogue.inputs if definitions]
            reviews = [review for review in reviews if review]
            assert reviews and all(review["phase"] == "review" for review in reviews)
            assert all(review["result_ids"] == [card["result_id"]] for review in reviews)
        finally:
            await service.close()

    asyncio.run(run())


def test_semantic_goal_and_refinement_can_share_the_next_native_response(engine):
    async def run():
        backend = varying_search_backend()
        dialogue = BareDialogue(load(), remote("search", query="broad"), read_latest,
            goals({"description": "Find the relevant refined resources", "tool": "search"},
                calls=[remote("search", query="refined")]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find related resources", "planned-refinement")
            assert_completed(service, None, events[-1])
            assert [arguments["query"] for _, _, arguments in backend.calls] == ["broad", "refined"]
            card, = result_cards(events)
            assert card["data"]["items"][0]["id"] == "refined"
            assert len(dialogue.inputs) == 5
        finally:
            await service.close()

    asyncio.run(run())


def test_native_search_inspection_and_sample_chain_keeps_the_requested_terminal_result(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resources"), read_latest,
            remote("sample", count=2, **{OBJECT: "object:1"}), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find a resource and sample the first one", "chain")
            assert_completed(service, None, events[-1])
            assert [name for _, name, _ in backend.calls] == ["search", "sample"]
            card, = result_cards(events)
            assert card["title"].endswith("sample")
            ledger = payload(service, sid, events)
            assert ledger["operations"][0]["required"] is False
        finally:
            await service.close()

    asyncio.run(run())


def test_budget_closure_does_not_promote_a_prerequisite_to_a_completed_sample(engine):
    async def run():
        backend = configured()
        loaded = {}

        def search(messages, definitions):
            loaded["sample"] = next(definition["function"]["name"] for definition in definitions
                if definition["function"]["name"].endswith("_sample"))
            return remote("search", query="resources")(messages, definitions)

        def pending_goal(messages, definitions):
            # The final decision phase can hide native definitions while the
            # already-discovered capability remains valid semantic goal context.
            return action("remember", goals=[{"description": "Sample the first resource",
                "tool": loaded["sample"], "object": "object:1"}])

        dialogue = BareDialogue(load(), search, pending_goal,
            text("已找到候选资源，但尚未完成采样。"))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=3)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find a resource and sample the first one", "unfinished")
            assert_handled(service, None, events[-1])
            assert not result_cards(events)
            assert [name for _, name, _ in backend.calls] == ["search"]
            ledger = payload(service, sid, events)
            assert not ledger.get("delivery_sources")
            required = [item for item in ledger["operations"] if item.get("required", True)]
            assert len(required) == 1 and required[0]["state"] == "pending"
        finally:
            await service.close()

    asyncio.run(run())


def test_last_planning_round_offers_confirmation_instead_of_new_exploration(engine):
    async def run():
        backend = configured()

        def close(messages, definitions):
            names = {definition["function"]["name"] for definition in definitions}
            assert {"deliver_results", "remember", "request_input"} <= names
            assert not any(name.startswith("mcp_") for name in names)
            assert not {"list_mcp_servers", "load_mcp_tools", "read_result"}.intersection(names)
            return action("deliver_results")

        dialogue = BareDialogue(load(), remote("search", query="resources"), read_latest, close, text())
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=4)))
        try:
            events = await collect(service, session(service), "Find related resources", "last-decision")
            assert_completed(service, None, events[-1])
            assert len(backend.calls) == 1 and len(result_cards(events)) == 1
            assert len(dialogue.inputs) == 5
        finally:
            await service.close()

    asyncio.run(run())


def test_identical_invocation_reuses_receipt_without_forcing_a_refinement_goal(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resources"), read_latest,
            remote("search", query="resources"), action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            events = await collect(service, session(service), "Find related resources", "same-invocation")
            assert_completed(service, None, events[-1])
            assert len(backend.calls) == 1 and len(result_cards(events)) == 1
            observations = [json.loads(message.content) for messages, _ in dialogue.inputs
                for message in messages if isinstance(message, ToolMessage)]
            assert not any(observation.get("error") for observation in observations)
        finally:
            await service.close()

    asyncio.run(run())


def test_last_round_can_execute_an_explicit_pending_goal(engine):
    async def run():
        backend = configured()

        def sample(messages, definitions):
            state = json.loads(messages[1].content)
            assert any(item["state"] == "pending" for item in state["operations"]["items"])
            assert state.get("execution_decision", {}).get("phase") != "finish"
            return remote("sample", count=2, **{OBJECT: "object:1"})(messages, definitions)

        dialogue = BareDialogue(load(), goals(
            {"description": "Find resources", "tool": "search"},
            {"description": "Sample the first resource", "tool": "sample"},
            calls=[remote("search", query="resources")]), read_latest, sample, text())
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=4)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find resources and sample the first one", "last-execution")
            assert_completed(service, None, events[-1])
            assert [name for _, name, _ in backend.calls] == ["search", "sample"]
            assert len(result_cards(events)) == 2
            assert len(dialogue.inputs) == 5
            ledger = payload(service, sid, events)
            assert all(item["state"] == "succeeded" for item in ledger["operations"])
        finally:
            await service.close()

    asyncio.run(run())


def test_rejected_expansion_cannot_itself_confirm_the_users_undeclared_outcomes(engine):
    async def run():
        backend = varying_search_backend()
        dialogue = BareDialogue(load(), remote("search", query="climate"),
            remote("search", query="water"), text("Only the first lookup completed."),
            text("The second requested lookup is still incomplete."))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=4)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find climate resources and water resources", "unconfirmed-pair")
            assert_handled(service, None, events[-1])
            assert [arguments["query"] for _, _, arguments in backend.calls] == ["climate"]
            assert not result_cards(events)
            ledger = payload(service, sid, events)
            assert not ledger.get("delivery_sources")
            assert all(not item.get("required", True) for item in ledger["operations"])
        finally:
            await service.close()

    asyncio.run(run())


def test_rejected_second_query_can_declare_both_outcomes_and_reuse_first_receipt(engine):
    async def run():
        backend = varying_search_backend()

        def declare_pair(messages, definitions):
            state = json.loads(messages[1].content)
            # Refusing another undeclared query must not turn its prerequisite
            # into an assertion that the whole user request has been completed.
            assert all(item.get("delivery_pending") is True for item in state["operations"]["items"])
            assert state["execution_decision"]["phase"] == "review"
            return goals({"description": "Find climate resources", "tool": "search"},
                {"description": "Find water resources", "tool": "search"})(messages, definitions)

        dialogue = BareDialogue(load(), remote("search", query="climate"),
            remote("search", query="water"), declare_pair,
            for_goal("Find climate resources", remote("search", query="climate")),
            for_goal("Find water resources", remote("search", query="water")), text())
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=6)))
        sid = session(service)
        try:
            events = await collect(service, sid, "Find climate resources and water resources", "declared-pair")
            assert_completed(service, None, events[-1])
            assert [arguments["query"] for _, _, arguments in backend.calls] == ["climate", "water"]
            assert len(result_cards(events)) == 2
            ledger = payload(service, sid, events)
            required = [item for item in ledger["operations"] if item.get("required", True)]
            assert len(required) == 2 and all(item["state"] == "succeeded" for item in required)
            assert required[0]["attempts"][0]["reused"] is True
        finally:
            await service.close()

    asyncio.run(run())
