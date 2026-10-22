"""Task-scoped references and explicit input identity provenance."""
from copy import deepcopy
import asyncio
import json

import pytest

from .assertions import assert_completed, assert_handled
from ..capabilities import GOAL, OBJECT, SUPPORTING, adapted, identifiers_from_request, inputs, request_identifiers
from ..context import encode
from ..contracts import QAError
from ..mcp import Tool
from ..references import identifier_in_request, pending_objects, scoped_preview
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, seed, text


def reference(result_id, path=""):
    return {"result_id": result_id, "path": path, "kind": "object"}


def bound_tool(properties=None, binding=None):
    return Tool("unfamiliar-service", "operate", "Read a selected asset", {
        "type": "object", "properties": properties or {"asset_key": {"type": "string"}},
        "required": ["asset_key"], "additionalProperties": False}, {},
        {"piflow": {"qa": {"bind": binding or {"asset_key": ["/identity/key"]}}}})


def test_pending_scope_restores_only_unfinished_requested_objects():
    a, b, c = reference("source-a", "/items/0"), reference("source-b"), reference("source-c")
    payload = {"objects": {"object:1": b, "object:2": a}, "operations": [
        {"target": b, "state": "succeeded"},
        {"target": c, "state": "pending", "required": False},
        {"target": a, "state": "pending"},
        {"target": a, "state": "failed"},
    ]}
    snapshot = deepcopy(payload)
    assert pending_objects(payload)=={"pending:1": a}
    assert payload==snapshot
    assert pending_objects(payload, limit=0)=={}


def test_unbound_pending_goal_restores_intermediate_choices_with_stable_deduplication():
    a, b = reference("source", "/items/0"), reference("source", "/items/1")
    payload = {"objects": {"object:1": a, "object:2": b, "object:3": a},
        "operations": [{"target": a, "state": "pending"}, {"target": None, "state": "pending"}]}
    assert pending_objects(payload)=={"pending:1": a, "pending:2": b}
    assert pending_objects(payload, limit=1)=={"pending:1": a}
    # The child may own object:1 already; restoring the parent cannot overwrite it.
    child = {"object:1": reference("new-source")}
    assert {**child, **pending_objects(payload)}["object:1"]==reference("new-source")


def test_repeated_clarification_keeps_unbound_candidates_from_the_prior_scope():
    a, b = reference("source", "/items/0"), reference("source", "/items/1")
    continued = {"operations": [{"target": None, "state": "pending"}],
        "pending_objects": {"pending:1": a, "pending:2": b}}
    assert pending_objects(continued)=={"pending:1": a, "pending:2": b}


def test_pending_handles_keep_creation_order_after_sorted_json_storage():
    objects = {"object:"+str(index): reference("source", "/items/"+str(index-1)) for index in range(1, 13)}
    payload = {"operations": [{"target": None, "state": "pending"}], "objects": objects}
    assert pending_objects(json.loads(json.dumps(payload, sort_keys=True)))==pending_objects(payload)
    assert pending_objects(payload)["pending:2"]["path"]=="/items/1"


def test_scoped_preview_is_bounded_keeps_id_whole_and_omits_source_bodies():
    records = [{"id": "asset-"+str(index), "title": "Resource "+str(index),
        "secret": "hidden", "body": "large "*1000, "raw": {"data": "raw "*1000}} for index in range(20)]
    card = {"result_id": "source", "data": {"items": records}}
    handles = {"pending:"+str(index+1): reference("source", "/items/"+str(index)) for index in range(20)}
    snapshot = deepcopy(card)
    view = scoped_preview(handles, {"source": card}, limit=700)
    assert len(encode(view))<=700 and view["total"]==20 and view["next_offset"]<20
    assert view["items"][0]["handle"]=="pending:1"
    assert view["items"][0]["value"]["id"]=="asset-0"
    assert "large large" not in encode(view) and '"raw"' not in encode(view)
    assert card==snapshot
    with pytest.raises(QAError, match="当前会话"):
        scoped_preview(handles, {})
    with pytest.raises(QAError, match="完整记录"):
        scoped_preview({"pending:1": reference("source", "/items/0/id")}, {"source": card})


@pytest.mark.parametrize("value,message,expected", [
    ("a", "show dataset", False),
    ("a", "show 'a'", True),
    ("direct-b", "inspect direct-b", True),
    ("direct-b", "inspect direct-b-extra", False),
    ("direct-b", "inspect direct-b2", False),
    ("direct-b", "inspect /corpus/direct-b", False),
    ("direct-b", "inspect direct-b.", True),
    ("direct-b", "inspect direct-b.json", False),
    ("SA-CORPUS-B031", "查看SA-CORPUS-B031的详情", True),
    (12, "inspect 123", False),
    (12, "inspect 12", True),
    (True, "True", False),
    (None, "None", False),
    ([], "[]", False),
    ("", "anything", False),
    (" a ", " a ", False),
])
def test_input_identity_requires_a_complete_value(value, message, expected):
    assert identifier_in_request(value, message)==expected


def test_known_field_assignment_is_evidence_without_whitespace():
    assert identifier_in_request("direct-b", "asset_key:direct-b", "asset_key")
    assert identifier_in_request("direct-b", "ASSET_KEY：direct-b", "asset_key")
    assert not identifier_in_request("direct-b", "not_asset_key:direct-b", "asset_key")
    assert not identifier_in_request("direct-b", "asset_key:direct-b-extra", "asset_key")


def test_explicit_new_identity_is_available_without_weakening_selected_object_validation():
    tool = bound_tool()
    arguments = {"asset_key": "direct-b"}
    assert identifiers_from_request(tool, arguments, "inspect direct-b")
    assert request_identifiers(tool, arguments, "inspect direct-b")==arguments
    assert not identifiers_from_request(tool, arguments, "inspect this")
    # Service may use proven direct input instead of an implicit old current.
    assert inputs(tool, arguments)==arguments
    # Explicit object selection remains authoritative and mismatch is rejected.
    with pytest.raises(QAError, match="不一致"):
        inputs(tool, arguments, {"identity": {"key": "current-a"}})


def test_composite_identity_requires_all_declared_components_from_request():
    tool = bound_tool({"asset_key": {"type": "string"}, "owner": {"type": "string"}},
        {"asset_key": ["/identity/key"], "owner": ["/owner"]})
    arguments = {"asset_key": "entry-1", "owner": "tenant-2"}
    assert not identifiers_from_request(tool, arguments, "inspect entry-1")
    assert request_identifiers(tool, arguments, "inspect entry-1")=={"asset_key": "entry-1"}
    assert identifiers_from_request(tool, arguments, "inspect entry-1 under tenant-2")


@pytest.mark.parametrize("reserved", [GOAL, OBJECT, SUPPORTING])
def test_native_reserved_name_collision_keeps_the_original_parameter(reserved):
    tool = bound_tool({"asset_key": {"type": "string"}, reserved: {"type": "string"}})
    assert not adapted(tool)
    arguments = {"asset_key": "entry-1", reserved: "native-value"}
    assert inputs(tool, arguments)==arguments
    assert tool.definition()["function"]["parameters"]==tool.schema


def test_runtime_goal_selector_is_stripped_only_from_an_adapted_tool():
    tool = bound_tool()
    assert adapted(tool)
    assert GOAL not in tool.definition()["function"]["parameters"]["properties"]
    assert inputs(tool, {"asset_key": "entry-1", GOAL: "provided-goal", SUPPORTING: False})=={"asset_key": "entry-1"}


def continuation(relation, *actions):
    def response(messages, definitions):
        values = [action("remember", continuation=relation)]
        values.extend(item(messages, definitions) if callable(item) else item for item in actions)
        calls = [{**call, "id": "step-"+str(index)}
            for index, call in enumerate(call for value in values for call in value.tool_calls)]
        return values[0].model_copy(update={"tool_calls": calls})
    return response


def test_new_request_does_not_complete_or_deliver_a_pending_same_capability_goal(engine):
    async def run():
        backend = configured()
        backend.items = [{"id": "old-a", "title": "Old A"}]
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}

        def search_a(messages, definitions):
            rows = json.loads(messages[1].content)["operations"]["items"]
            selected = next(item["id"] for item in rows if item["description"]=="Search A")
            return remote("search", query="A", **{GOAL: selected})(messages, definitions)

        dialogue = BareDialogue(load(), goals({"description": "Search A", "tool": "search"},
            {"description": "Search B", "tool": "search"}), search_a,
            action("request_input", missing="Required date filter for B", question="Which year for B?"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            old = await collect(service, sid, "Search A and B; ask me for B's year", "waiting")
            assert old[-1]["status"]=="WAITING_INPUT"
            old_payload = payload(service, sid, old)
            old_source = old_payload["operations"][0]["attempts"][0]["result_id"]
            backend.items = [{"id": "new-c", "title": "New C"}]
            dialogue.responses = [continuation("new", remote("search", query="C")), action("deliver_results"), text()]
            new = await collect(service, sid, "New request: search C instead", "new")
            assert_completed(service, None, new[-1])
            ledger = payload(service, sid, new)
            assert ledger["resume"] is False and len(ledger["operations"])==1
            assert old_source not in ledger["delivery_sources"]
            assert result_cards(new)[0]["data"]["items"]==backend.items
            assert payload(service, sid, old)["operations"][1]["state"]=="pending"
            assert backend.calls==[("data", "search", {"query": "A"}), ("data", "search", {"query": "C"})]
        finally:
            await service.close()
    asyncio.run(run())


def test_unpublished_intermediate_object_survives_clarification_without_retrieval_again(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resource", **{SUPPORTING: True}),
            goals({"description": "Sample the resource", "tool": "sample", "object": "object:1"}),
            action("request_input", missing="Required sample count", question="How many rows?"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            old = await collect(service, sid, "Find a resource, then ask me for sample count", "waiting")
            assert old[-1]["status"]=="WAITING_INPUT" and not result_cards(old)
            assert not json.loads(service.store.session("alice", sid)["context"]).get("references")
            dialogue.responses = [continuation("continue", remote("sample", count=5, **{OBJECT: "pending:1"})), text()]
            resumed = await collect(service, sid, "5 rows", "answer")
            assert_completed(service, None, resumed[-1])
            assert len(result_cards(resumed))==1
            ledger = payload(service, sid, resumed)
            assert ledger["resume"] is True
            assert backend.calls==[("data", "search", {"query": "resource"}),
                ("data", "sample", {"reference": "a", "count": 5})]
            assert ledger["operations"][-1]["description"]=="Sample the resource"
            assert ledger["operations"][-1]["target"]==payload(service, sid, old)["operations"][-1]["target"]
            assert (await service.get_session("alice", sid))["interaction"] is None
        finally:
            await service.close()
    asyncio.run(run())


def test_repeated_clarification_keeps_unpublished_candidates_and_original_receipts(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), remote("search", query="resource", **{SUPPORTING: True}),
            goals({"description": "Sample the chosen resource", "tool": "sample"}),
            action("request_input", missing="Required resource choice", question="Which resource?"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find resources and let me choose one to sample", "ask-first")
            assert first[-1]["status"]=="WAITING_INPUT"
            dialogue.responses = [continuation("continue", action("request_input",
                missing="Resource choice is still unclear", question="Would you like the first or second resource?"))]
            second = await collect(service, sid, "Remind me which choices are available", "ask-again")
            assert second[-1]["status"]=="WAITING_INPUT"
            assert payload(service, sid, second)["pending_objects"]["pending:2"]["path"]=="/items/1"
            dialogue.responses = [continuation("continue", remote("sample", count=2, **{OBJECT: "pending:2"})), text()]
            last = await collect(service, sid, "The second one, two rows", "answer")
            assert_completed(service, None, last[-1])
            assert len(result_cards(last))==1
            assert backend.calls==[("data", "search", {"query": "resource"}),
                ("data", "sample", {"reference": "b", "count": 2})]
            assert payload(service, sid, last)["operations"][-1]["target"]["path"]=="/items/1"
            assert service.store.task("alice", sid, first[-1]["task_id"])["status"]=="COMPLETED"
            assert service.store.task("alice", sid, second[-1]["task_id"])["status"]=="COMPLETED"
        finally:
            await service.close()
    asyncio.run(run())


def test_direct_input_can_switch_implicit_current_without_a_focus_clearing_round(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [remote("inspect", **{OBJECT: "candidate:1"}), action("deliver_results"), text()]
            assert_completed(service, None, (await collect(service, sid, "Inspect first", "focus"))[-1])
            dialogue.responses = [remote("inspect", reference="direct-b"), action("deliver_results"), text()]
            switched = await collect(service, sid, "Inspect direct-b", "switch")
            assert_completed(service, None, switched[-1])
            assert backend.calls[-1]==("data", "inspect", {"reference": "direct-b"})
            assert not any("runtime_feedback" in message.content for messages, _ in dialogue.inputs[-3:] for message in messages)
            dialogue.responses = [remote("sample"), action("deliver_results"), text()]
            sampled = await collect(service, sid, "Sample this", "sample")
            assert_completed(service, None, sampled[-1])
            assert backend.calls[-1]==("data", "sample", {"reference": "direct-b", "count": 5})
        finally:
            await service.close()
    asyncio.run(run())


def test_a_word_substring_cannot_ground_a_guessed_short_object_id(engine):
    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), *[remote("inspect", reference="a") for _ in range(3)])
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "show dataset", "short-id")
            assert_handled(service, None, values[-1], "invalid_parameters")
            assert not backend.calls and not result_cards(values)
        finally:
            await service.close()
    asyncio.run(run())


def test_pending_preview_pages_actual_visible_handles_and_excludes_a_new_task(engine):
    async def run():
        service = DatasetQA(engine, BareDialogue(), configured().gateway())
        sid = session(service)
        parent_payload = {"message": "Choose a resource", "params": {}, "parent_task_id": None,
            "operations": [{"id": "op1", "description": "Sample a resource", "target": None,
                "state": "pending", "output": "result", "attempts": []}]}
        parent, _ = service.store.submit("alice", sid, "waiting", parent_payload, None, service.owner)
        source_id = parent["id"]+":0"
        parent_payload["objects"] = {"object:"+str(index+1): reference(source_id, "/items/"+str(index)) for index in range(20)}
        card = {"result_id": source_id, "view_type": "detail", "title": "Candidates", "data": {
            "items": [{"id": "entry-"+str(index), "title": "Title "+str(index)+"x"*300} for index in range(20)]}}
        context = {"pending": {"task_id": parent["id"], "question": "Which resource?"}}
        service.store.write("alice", sid, parent["id"], card=card, payload=parent_payload, context=context)
        service.store.finish("alice", sid, parent["id"], "WAITING_INPUT")
        child_payload = {"message": "Show more choices", "params": {}, "parent_task_id": parent["id"]}
        child, _ = service.store.submit("alice", sid, "browse", child_payload, None, service.owner)
        try:
            first = await service._builtin("alice", sid, child["id"], "read_result", {"limit": 8}, None, context, child_payload)
            first_rows = first["pending_objects"]["items"]
            offset = first["pending_next_offset"]
            assert 0<len(first_rows)<8 and offset==len(first_rows)
            assert first_rows[0]["handle"]=="pending:1"
            second = await service._builtin("alice", sid, child["id"], "read_result", {"offset": offset, "limit": 8}, None, context, child_payload)
            assert second["pending_objects"]["items"][0]["handle"]=="pending:"+str(offset+1)
            assert second["pending_next_offset"]==offset+len(second["pending_objects"]["items"])
            resumed = {**child_payload, "resume": True, "pending_objects": pending_objects(parent_payload)}
            resumed = json.loads(json.dumps(resumed, sort_keys=True))
            from_payload = await service._builtin("alice", sid, child["id"], "read_result", {"offset": offset, "limit": 8}, None, {}, resumed)
            assert from_payload["pending_objects"]["items"]==second["pending_objects"]["items"]
            independent = await service._builtin("alice", sid, child["id"], "read_result", {}, None, context, {**child_payload, "resume": False})
            assert "pending_objects" not in independent and "pending_next_offset" not in independent
        finally:
            service.store.finish("alice", sid, child["id"], "CANCELLED")
            await service.close()
    asyncio.run(run())
