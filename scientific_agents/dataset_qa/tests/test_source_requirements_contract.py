"""Current selection is checked before reusing owned record resources."""
import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from ..artifacts import validate_source_requirements
from ..capabilities import GOAL, OBJECT, TASK
from ..contracts import QAError, Server
from ..mcp import MCPGateway
from ..planning import SourceRequirements
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import action, collect, definition, engine, result_cards, session
from .test_decisions import BareDialogue, goals, payload, text
from .test_independent_outcomes import ContractDialogue, batch, native
from .test_planning import approve


@pytest.mark.parametrize("actual,expected,accepted", [
    ({}, {"criteria": None, "fields": None}, True),
    ({}, {"criteria": {}, "fields": None}, True),
    ({"query": {}}, {"criteria": {}, "fields": None}, True),
    ({"query": {}}, {"criteria": None, "fields": None}, True),
    ({"query": {"limit": 100, "criterion": "chosen"}}, {"criteria": {"limit": 100}, "fields": None}, True),
    ({"query": {"selection": {"a": 1, "b": 2}}}, {"criteria": {"selection": {"a": 1}}, "fields": None}, False),
    ({"query": {"window": [0, 10], "limit": 250}}, {"criteria": {"window": [0, 10], "limit": 100}, "fields": None}, False),
    ({"query": {"enabled": False}}, {"criteria": {"enabled": 0}, "fields": None}, False),
])
def test_declared_constraints_match_typed_parameters_without_nested_subset_guessing(actual, expected, accepted):
    source = {"resource": {}, "provenance": actual}
    requirement = SourceRequirements(**expected)
    if accepted:
        validate_source_requirements(source, requirement, required=True)
    else:
        with pytest.raises(QAError) as error:
            validate_source_requirements(source, requirement, required=True)
        assert error.value.detail["dispatched"] is False
        assert error.value.detail["source_requirements"] == expected


def test_current_source_only_waives_presence_not_an_existing_requirement():
    source = {"resource": {"fields": ["time", "value"]}, "provenance": {"query": {"limit": 250}}}
    validate_source_requirements(source, None, required=False)
    validate_source_requirements(source, SourceRequirements(criteria=None, fields=None), required=False)
    with pytest.raises(QAError):
        validate_source_requirements(source, None, required=True)
    for expected in ({"criteria": {"limit": 100}, "fields": ["time", "value"]},
                     {"criteria": {"limit": 250}, "fields": ["value"]}):
        with pytest.raises(QAError):
            validate_source_requirements(source, SourceRequirements(**expected), required=False)


class Sources:
    def __init__(self, *, omit_metadata=False):
        self.calls, self.resources = [], {}
        self.omit_metadata = omit_metadata
        self.catalog = [definition("produce", {"criterion": {"type": "string"}, "limit": {"type": "integer", "minimum": 1}},
            ["criterion", "limit"], {"readOnlyHint": True, "idempotentHint": True}),
            definition("export", {"source_ref": {"type": "string"}, "format": {"type": "string", "enum": ["csv"]}},
                ["source_ref", "format"], {"readOnlyHint": False, "idempotentHint": True, "destructiveHint": False})]
        for item in self.catalog:
            descriptor = {"atomic": True, "object": "/resource", "artifact": {"path": "/resource"},
                "result": {"kind": "record_resource", "requires": [{"path": "/resource"}]},
                "routing": {"group": "records", "operations": [item.name], "outputs": ["record_resource", "csv"]}}
            if item.name == "export":
                descriptor["artifact"]["consume"] = "source_ref"
                descriptor["bind"] = {"source_ref": ["/source_ref"]}
                descriptor["result"]["argument_paths"] = {"format": "/resource/format"}
            item.meta = {"piflow": {"qa": descriptor, "view_type": "url"}}

    def gateway(self):
        return MCPGateway({"records": Server("owned-source")}, client_factory=self.client)

    def client(self, *args, **kwargs):
        owner = self
        class Client:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def list_tools(self):
                return owner.catalog
            async def call_tool(self, name, arguments, **kwargs):
                owner.calls.append((name, deepcopy(arguments)))
                if name == "produce":
                    query = deepcopy(arguments)
                    ref = "source-" + sha256(json.dumps(query, sort_keys=True).encode()).hexdigest()
                    value = {"query": query, "record_count": query["limit"], "resource": {
                        "source_ref": ref, "record_count": query["limit"], "format": "jsonl", "fields": ["value"],
                        "name": "records.jsonl", "sha256": sha256(ref.encode()).hexdigest()}}
                else:
                    original = owner.resources[arguments["source_ref"]]
                    value = deepcopy(original)
                    value["parent_source_ref"] = arguments["source_ref"]
                    value["resource"].update(format="csv", name="records.csv",
                        source_ref=arguments["source_ref"]+"-csv", sha256=sha256((arguments["source_ref"]+"csv").encode()).hexdigest())
                if owner.omit_metadata:
                    value.pop("query", None)
                    value["resource"].pop("fields", None)
                owner.resources[value["resource"]["source_ref"]] = deepcopy(value)
                return SimpleNamespace(is_error=False, structured_content=value)
        return Client()


async def produce(service, sid, criterion="original", limit=250, rid="produce"):
    service.dialogue = ContractDialogue(native("produce", True, criterion=criterion, limit=limit), text())
    events = await collect(service, sid, "Create records", rid)
    assert_completed(service, sid, events[-1])
    return result_cards(events)[0]


def exporter(requirements, *, handle=None, goal=None):
    def reply(messages, definitions):
        selected = handle or json.loads(messages[1].content)["published_artifacts"]["items"][0]["handle"]
        alias = next(item["function"]["name"] for item in definitions if item["function"]["name"].endswith("_export"))
        args = {"format": "csv", OBJECT: selected, TASK: {"complete_request": True, "operation": "export",
            "output_format": "csv", "source_requirements": requirements}}
        if goal:
            args[GOAL] = goal
        return action(alias, **args)
    return reply


@pytest.mark.parametrize("weaken_to_null", [False, True])
def test_native_reuse_rejects_changed_conditions_and_cannot_revert_them_to_pass(engine, weaken_to_null):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        current = {"criteria": {"criterion": "changed", "limit": 100}, "fields": ["value"]}
        old = {"criteria": {"criterion": "original", "limit": 250}, "fields": ["value"]}
        if weaken_to_null:
            old = {"criteria": None, "fields": None}
        try:
            await produce(service, sid)
            service.dialogue = ContractDialogue(exporter(current), exporter(old), exporter(old))
            events = await collect(service, sid, "Use changed conditions and 100 records, save CSV", "changed")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert [name for name, _ in backend.calls] == ["produce"]
            assert not result_cards(events)
            operation, = payload(service, sid, events)["operations"]
            assert operation["intent"]["source_requirements"] == current
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("expected", [
    {"criteria": {"criterion": "original", "limit": 250}, "fields": ["value"]},
    {"criteria": None, "fields": None},
    {"criteria": {"limit": 250}, "fields": None},
])
def test_valid_reuse_exports_once_and_the_contract_is_not_sent_to_mcp(engine, expected):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        try:
            await produce(service, sid)
            service.dialogue = ContractDialogue(exporter(expected), text())
            events = await collect(service, sid, "Save these records as CSV", "format")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["produce", "export"]
            assert set(backend.calls[-1][1]) == {"source_ref", "format"}
            assert len(service.dialogue.inputs) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_owned_legacy_resource_without_selection_metadata_allows_explicit_null_format_only_reuse(engine):
    async def run():
        backend = Sources(omit_metadata=True)
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        try:
            await produce(service, sid)
            service.dialogue = ContractDialogue(exporter({"criteria": None, "fields": None}), text())
            events = await collect(service, sid, "Save this existing file as CSV", "legacy-format")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["produce", "export"]
            assert set(backend.calls[-1][1]) == {"source_ref", "format"}
            assert len(service.dialogue.inputs) == 2
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("boolean,numeric", [(True, 1), (False, 0)])
def test_goal_redeclaration_cannot_change_boolean_requirements_into_numbers(engine, boolean, numeric):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        def declaration(value):
            return goals({"description": "Export", "tool": "export", "source_requirements": {
                "criteria": {"enabled": value}, "fields": ["value"]}})
        try:
            await produce(service, sid)
            service.dialogue = ContractDialogue(declaration(boolean), declaration(numeric), declaration(numeric))
            events = await collect(service, sid, "Export the requested records", "typed-goal")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            operation, = payload(service, sid, events)["operations"]
            assert operation["intent"]["source_requirements"]["criteria"]["enabled"] is boolean
            assert [name for name, _ in backend.calls] == ["produce"]
        finally:
            await service.close()
    asyncio.run(run())


def test_rejected_old_source_can_be_replaced_by_a_matching_new_producer_without_losing_requirements(engine):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        expected = {"criteria": {"criterion": "changed", "limit": 100}, "fields": ["value"]}
        try:
            await produce(service, sid)

            def repair(messages, definitions):
                operation, = json.loads(messages[1].content)["operations"]["items"]
                assert operation["intent"]["source_requirements"] == expected
                assert [name for name, _ in backend.calls] == ["produce"]
                return action("remember", plan={"steps": [
                    {"key": "new_source", "tool": "produce", "arguments": expected["criteria"]},
                    {"key": "export", "tool": "export", "goal": operation["id"], "object": "new_source",
                        "description": "Reworded deliverable", "operation": "export", "output_format": "csv",
                        "arguments": {"format": "csv"}}]})

            service.dialogue = ContractDialogue(exporter(expected), action("remember", planning=True), repair, approve, text())
            events = await collect(service, sid, "Change selection and limit to 100, export CSV", "repair-new-source")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["produce", "produce", "export"]
            assert backend.calls[1][1] == expected["criteria"]
            ledger = payload(service, sid, events)
            final = next(step for step in ledger["plan"]["spec"]["steps"] if step["key"] == "export")
            assert final["source_requirements"] == expected
            assert result_cards(events)[0]["data"]["items"][0]["query"] == expected["criteria"]
        finally:
            await service.close()
    asyncio.run(run())


def test_rejected_batch_retains_the_single_export_requirement_without_committing_scope(engine):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        expected = {"criteria": {"criterion": "changed", "limit": 100}, "fields": ["value"]}
        old = {"criteria": {"criterion": "original", "limit": 250}, "fields": ["value"]}
        try:
            await produce(service, sid)

            def first(messages, definitions):
                return goals({"description": "Requested export", "tool": "export", "source_requirements": expected},
                    {"description": "Independent retrieval", "tool": "produce"}, calls=[exporter(expected),
                        native("produce", criterion="independent", limit=5)])(messages, definitions)

            def weaken(messages, definitions):
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                assert [name for name, _ in backend.calls] == ["produce"]
                return exporter(old)(messages, definitions)

            service.dialogue = ContractDialogue(first, weaken, exporter(old))
            events = await collect(service, sid, "Export changed records and fetch independent records", "rollback")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert [name for name, _ in backend.calls] == ["produce"]
            operation, = payload(service, sid, events)["operations"]
            assert operation["intent"]["source_requirements"] == expected
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("coemit_first", [False, True])
def test_two_old_source_exports_bind_distinct_requirements_to_accepted_goal_ids(engine, coemit_first):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        try:
            await produce(service, sid, "first", 250, "first")
            await produce(service, sid, "second", 100, "second")
            entries = {service.artifacts.get("alice", item["handle"])["provenance"]["query"]["criterion"]: item
                for item in service.artifacts.recent("alice")}
            required = {key: {"criteria": {"criterion": key, "limit": count}, "fields": ["value"]}
                for key, count in (("first", 250), ("second", 100))}
            declarations = [{"description": key, "tool": "export", "object": entries[key]["handle"],
                "source_requirements": required[key]} for key in required]

            def declare(messages, definitions):
                assert [name for name, _ in backend.calls] == ["produce", "produce"]
                if coemit_first:
                    assert json.loads(messages[-1].content)["runtime_feedback"]["detail"]["origin"] == "source_requirements_scope"
                    assert not json.loads(messages[1].content).get("operations", {}).get("items")
                return goals(*declarations)(messages, definitions)

            def dispatch(messages, definitions):
                supplied = {item["description"]: item["id"] for item in json.loads(messages[1].content)["operations"]["items"]}
                assert len(supplied) == 2
                return batch(*(exporter(required[key], handle=entries[key]["handle"], goal=supplied[key])
                    for key in required))(messages, definitions)

            first = goals(*declarations, calls=[exporter(required[key], handle=entries[key]["handle"]) for key in required])
            service.dialogue = ContractDialogue(*([first] if coemit_first else []), declare, dispatch, text())
            events = await collect(service, sid, "Save both existing files independently as CSV", "two-exports")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["produce", "produce", "export", "export"]
            operations = payload(service, sid, events)["operations"]
            assert {item["description"]: item["intent"]["source_requirements"] for item in operations} == required
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("declare_preservation", [False, True])
def test_same_turn_query_then_export_needs_no_copied_conditions(engine, declare_preservation):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway())
        sid = session(service)
        workflow = {"steps": [
            {"key": "produce", "tool": "produce", "arguments": {"criterion": "current", "limit": 100}},
            {"key": "export", "tool": "export", "object": "produce", "arguments": {"format": "csv"}}]}
        if declare_preservation:
            workflow["steps"][-1]["source_requirements"] = {"criteria": None, "fields": None}
        service.dialogue = ContractDialogue(action("remember", planning=True), action("remember", plan=workflow), approve, text())
        try:
            events = await collect(service, sid, "Create current records and export CSV", "same-task")
            assert_completed(service, sid, events[-1])
            assert [name for name, _ in backend.calls] == ["produce", "export"]
            final = next(item for item in payload(service, sid, events)["operations"] if item["capability"]["name"] == "export")
            assert final.get("intent", {}).get("source_requirements") == (
                {"criteria": None, "fields": None} if declare_preservation else None)
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("read_source", [False, True])
def test_listing_or_reading_old_artifacts_does_not_make_them_current_production(engine, read_source):
    async def run():
        backend = Sources()
        service = DatasetQA(engine, BareDialogue(), backend.gateway())
        sid = session(service)
        try:
            card = await produce(service, sid)
            view = action("read_result", result_id=card["result_id"]) if read_source else action("find_artifacts")
            service.dialogue = BareDialogue(view, exporter(None), exporter(None), exporter(None))
            events = await collect(service, sid, "Save the previous records as CSV", "old-source-view")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert [name for name, _ in backend.calls] == ["produce"]
            assert not result_cards(events)
            feedback = [json.loads(messages[-1].content)
                for messages, _ in service.dialogue.inputs if messages[-1].type == "tool"]
            assert any(item.get("detail", {}).get("origin") == "source_requirements" for item in feedback)
        finally:
            await service.close()
    asyncio.run(run())
