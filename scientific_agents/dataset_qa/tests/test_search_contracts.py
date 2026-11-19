"""Capability-specific discovery and identity survive delivery and old state."""
import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

from jsonschema import Draft202012Validator
from pydantic import ValidationError
import pytest

from ..capabilities import GOAL, TASK, definition, profile
from ..context import encode
from ..contracts import QAError
from ..execution import Execution
from ..mcp import Tool
from ..operations import Operation, Operations
from ..results import collection_paths, combine_results, evidence_group
from ..search import SearchPolicy, SearchProfile, SearchRun, TaskDirective, ordered_keywords, record_key
from ..service import DatasetQA
from .assertions import assert_completed
from .test_bounded_discovery import SearchBackend, discover, native, outcome, page
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import BareDialogue, text


def capability(search=None, **extra):
    return Tool("records", "lookup", "Retrieve records", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        {"readOnlyHint": True, "idempotentHint": True},
        {"piflow": {"qa": {"collection": "/items", "search": {"query": "query", **(search or {})}, **extra}}})


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2", None, 1001])
def test_invalid_explicit_policy_is_rejected_instead_of_using_legacy_defaults(value):
    with pytest.raises(QAError) as caught:
        profile(capability({"policy": {"candidate_stop": value}}))
    assert caught.value.code=="invalid_schema"


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "2", None, 17])
def test_keyword_policy_is_bounded_and_strict(value):
    with pytest.raises(ValidationError):
        SearchPolicy(keyword_limit=value)


def test_advertised_keyword_limit_matches_parser_ordering_and_search_execution():
    policy = SearchPolicy(candidate_stop=3, keyword_limit=5)
    tool = capability({"policy": policy.model_dump()})
    descriptor = profile(tool).search
    words = ["alpha", "beta", "gamma", "delta", "epsilon"]
    arguments = {"query": "alpha", TASK: {"complete_request": True,
        "keywords": words, "original_keywords": ["alpha"]}}
    schema = definition(tool)["function"]["parameters"]
    Draft202012Validator(schema).validate(arguments)
    directive = TaskDirective.model_validate(arguments[TASK], context={"search_policy": descriptor.policy})
    with pytest.raises(ValidationError):
        TaskDirective.model_validate(arguments[TASK])  # Old callers retain four.
    keywords, _ = ordered_keywords(directive.keywords, directive.original_keywords, "Find alpha",
        policy=descriptor.policy)
    search = SearchRun.create(descriptor, {"query": "alpha"}, keywords)
    search.record({"items": [{"id": n} for n in range(3)]}, "/items", "first")
    assert search.state["stop"]=="enough" and search.view()["unique_count"]==3
    assert search.view()["minimum"]==3 and search.view()["remaining_keywords"]==0
    guidance = schema["properties"][TASK]["properties"]["keywords"]["description"]
    assert "3 actually returned" in guidance and "5 completed keywords" in guidance
    assert "original phrases FIRST" in guidance and "exact lookup first" in guidance
    assert "does not implicitly request details" in guidance


def test_saved_policy_wins_over_changed_capability_and_old_snapshots_keep_six_four():
    descriptor = SearchProfile(query="query", policy=SearchPolicy(candidate_stop=2, keyword_limit=2))
    search = SearchRun.create(descriptor, {"query": "alpha"}, ["alpha", "beta"])
    search.state["original_keywords"] = ["alpha"]
    with pytest.raises(QAError):
        ordered_keywords(["gamma"], None, "Continue", previous=search.state,
            policy=SearchPolicy(keyword_limit=5))
    resumed = SearchRun(deepcopy(search.state))
    resumed.record({"items": [{"id": 1}, {"id": 2}]}, "/items", "first")
    assert resumed.state["stop"]=="enough" and resumed.minimum==2

    legacy = deepcopy(search.state)
    legacy["profile"].pop("policy")
    legacy["profile"].pop("identity_mode")
    resumed = SearchRun(legacy)
    words, _ = ordered_keywords(["gamma", "delta"], None, "Continue", previous=legacy,
        policy=SearchPolicy(keyword_limit=2))
    resumed.extend({"query": "alpha"}, words)
    assert resumed.minimum==6 and resumed.maximum_keywords==4
    for index in range(4):
        resumed.record({"items": []}, "/items", str(index))
    assert resumed.state["done"] and resumed.state["stop"]=="exhausted"
    assert resumed.view()["unique_count"]==0


@pytest.mark.parametrize("count", [0, 1, 5])
def test_legacy_exhaustion_is_complete_below_early_stop_threshold(count):
    search = SearchRun.create(SearchProfile(query="query", identity=["/id"]),
        {"query": "alpha"}, ["alpha", "beta", "gamma", "delta"])
    for index in range(4):
        search.record({"items": [{"id": n} for n in range(count)]}, "/items", str(index))
    assert search.view()["done"] and search.view()["stop"]=="exhausted"
    assert search.view()["unique_count"]==count


def receipts(cards, descriptor):
    operations = Operations()
    operations.declare([Operation(id="lookup", description="Find records")])
    for card in cards:
        rid = card["result_id"]
        operations.start("lookup", rid, {"server": "records", "name": "lookup"},
            retry_safe=True, presentation=descriptor)
        operations.finish("lookup", rid, result_id=rid)
    return operations


def test_composite_identity_matches_progress_and_delivered_rows_without_partial_keys():
    first = [{"source": "a", "id": 1, "name": "first"},
        {"source": "b", "id": 1, "name": "second"},
        {"source": "a", "name": "missing one"}]
    second = [{"source": "a", "id": 1, "name": "changed description"},
        {"source": "a", "name": "missing two"}, {"name": "missing one", "source": "a"}]
    descriptor = SearchProfile(query="query", identity=["/source", "/id"], identity_mode="composite")
    search = SearchRun.create(descriptor, {"query": "alpha"}, ["alpha", "beta"])
    cards = [{"result_id": rid, "view_type": "data", "title": "Records", "data": {"items": rows}}
        for rid, rows in [("first", first), ("second", second)]]
    original = deepcopy(cards)
    for card in cards:
        search.record(card["data"], "/items", card["result_id"])
    presentation = {"family": "records/lookup", "kind": "collection", "path": "/items",
        "identity": descriptor.identity, "identity_mode": descriptor.identity_mode}
    operations = receipts(cards, presentation)
    lineage = {}
    combined = combine_results(cards, collection_paths(cards, operations), "combined", "Records", lineage)
    assert search.view()["unique_count"]==len(combined["data"])==4
    assert [row["name"] for row in combined["data"]]==["first", "second", "missing one", "missing two"]
    assert lineage["3"]=={"result_id": "second", "path": "/items/1"}
    assert cards==original


def test_legacy_identity_paths_remain_alternatives_and_composite_missing_fields_use_full_rows():
    first, second = {"source": "a", "id": 1}, {"source": "a", "id": 2}
    assert record_key(first, ["/source", "/id"])==record_key(second, ["/source", "/id"])
    assert record_key({"id": 1}, ["/source", "/id"])==record_key(first, ["/absent", "/id"])
    for invalid in [None, "", True, {}, []]:
        left, right = {"source": "a", "id": invalid, "value": 1}, {"source": "a", "id": invalid, "value": 2}
        assert record_key(left, ["/source", "/id"], identity_mode="composite")!=record_key(
            right, ["/source", "/id"], identity_mode="composite")
    left = {"source": "a", "measurement": {"value": 1, "unit": "m"}}
    right = {"measurement": {"unit": "m", "value": 1}, "source": "a"}
    assert record_key(left, ["/source", "/id"], identity_mode="composite")==record_key(
        right, ["/source", "/id"], identity_mode="composite")


@pytest.mark.parametrize("identity", [[], ["/id"], ["/id", "/id"]])
def test_composite_identity_requires_distinct_declared_components(identity):
    with pytest.raises(QAError):
        profile(capability({"identity": identity, "identity_mode": "composite"}))


def test_declared_naming_paths_reach_only_bounded_evidence_and_stay_whole():
    tool = capability(name_paths=["/metadata/display_name"])
    assert profile(tool).name_paths==["/metadata/display_name"]
    with pytest.raises(QAError):
        profile(capability(name_paths=["metadata/display_name"]))
    cards = [{"result_id": "first", "view_type": "data", "title": "Records",
        "data": {"items": [{"metadata": {"display_name": "Actual name"}}]}}]
    original = deepcopy(cards)
    descriptor = {"family": "records/lookup", "kind": "collection", "path": "/items",
        "name_paths": profile(tool).name_paths}
    operations = receipts(cards, descriptor)
    expected = {"record_path": "/items", "kind": "collection", "name_paths": ["/metadata/display_name"]}
    assert evidence_group(cards, operations, 1000)["items"][0]["naming"]==expected
    for budget in [4, 64, 128, 256, 512]:
        value = evidence_group(cards, operations, budget)
        assert len(encode(value))<=budget
        for entry in value.get("items", []):
            assert entry["result_id"]=="first"
            assert "naming" not in entry or entry["naming"]==expected
    assert cards==original


def test_native_discovery_uses_its_five_keyword_policy_end_to_end(engine):
    async def run():
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        backend = SearchBackend(lambda query, number: page([1] if query=="epsilon" else [], 1))
        backend.catalogue[0].meta["piflow"]["qa"]["search"]["policy"] = {
            "candidate_stop": 3, "keyword_limit": 5}
        dialogue = BareDialogue(discover(keywords=words, originals=["alpha"]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find alpha records")
            assert_completed(service, sid, events[-1])
            assert [arguments["phrase"] for _, arguments in backend.calls]==words
            assert len(dialogue.inputs)==2
            saved = outcome(service, sid, events)["operations"][0]["search"]
            assert saved["profile"]["policy"]=={"candidate_stop": 3, "keyword_limit": 5}
            assert saved["done"] and saved["stop"]=="exhausted" and len(saved["records"])==1
            card, = result_cards(events)
            assert len(card["data"]["items"])==1
        finally:
            await service.close()
    asyncio.run(run())


def test_composite_native_search_delivers_same_unique_count_and_names_as_progress(engine):
    async def run():
        rows = {
            1: [{"source": "a", "id": 1, "metadata": {"display_name": "First"}},
                {"source": "b", "id": 1, "metadata": {"display_name": "Second"}}],
            2: [{"source": "a", "id": 1, "metadata": {"display_name": "Revised first"}},
                {"source": "a", "id": 2, "metadata": {"display_name": "Third"}}],
        }
        backend = SearchBackend(lambda query, number: {"items": rows[number], "pagination": {"total": 50}})
        metadata = backend.catalogue[0].meta["piflow"]["qa"]
        metadata["name_paths"] = ["/metadata/display_name"]
        metadata["search"].update(identity=["/source", "/id"], identity_mode="composite",
            policy={"candidate_stop": 3, "keyword_limit": 2})
        dialogue = BareDialogue(discover(keywords=["alpha", "beta"], originals=["alpha"]), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            events = await collect(service, sid, "Find alpha records")
            assert_completed(service, sid, events[-1])
            assert [arguments["page_number"] for _, arguments in backend.calls]==[1, 2]
            saved = outcome(service, sid, events)["operations"][0]["search"]
            assert saved["stop"]=="enough" and len(saved["records"])==3
            card, = result_cards(events)
            assert [row["metadata"]["display_name"] for row in card["data"]["items"]]==["First", "Second", "Third"]
            final = json.loads(dialogue.inputs[-1][0][-1].content)
            assert any(entry.get("naming", {}).get("name_paths")==["/metadata/display_name"]
                for entry in final["answer_evidence"])
        finally:
            await service.close()
    asyncio.run(run())


def test_continued_search_uses_saved_policy_after_capability_metadata_changes(engine):
    async def run():
        words = ["alpha", "beta", "gamma", "delta", "epsilon"]
        backend = SearchBackend(lambda query, number: page([query], 1))
        descriptor = backend.catalogue[0].meta["piflow"]["qa"]["search"]
        descriptor["policy"] = {"candidate_stop": 8, "keyword_limit": 5}
        first = DatasetQA(engine, BareDialogue(discover(keywords=["alpha"], originals=["alpha"]),
            action("request_input", missing="scope", question="Keep the same subject scope?")), backend.gateway())
        sid = session(first)
        try:
            waiting = await collect(first, sid, "Find alpha records", "start")
            assert waiting[-1]["status"]=="WAITING_INPUT"
            saved = outcome(first, sid, waiting)["operations"][0]["search"]
            assert saved["completed"]==["alpha"] and not saved["done"]
        finally:
            await first.close()

        # A fresh gateway really discovers the changed declaration. The old
        # search must keep both its accepted keyword budget and stopping rule.
        descriptor["policy"] = {"candidate_stop": 1, "keyword_limit": 2}

        def continue_search(messages, definitions):
            tool = next(item["function"] for item in definitions
                if item["function"]["name"].endswith("_find_assets"))
            task = tool["parameters"]["properties"][TASK]
            array = task["properties"]["keywords"]
            assert array["maxItems"]==4  # Five saved slots, with alpha already completed.
            current, = json.loads(messages[1].content)["operations"]["items"]
            assert current["search"]["minimum"] == 8
            return native("find_assets", **{GOAL: current["id"], TASK: {"keywords": words[1:]}})(messages, definitions)

        dialogue = BareDialogue(action("remember", continuation="continue"), continue_search, text())
        resumed = DatasetQA(engine, dialogue, backend.gateway())
        try:
            events = await collect(resumed, sid, "Continue the same alpha scope", "continue")
            assert_completed(resumed, sid, events[-1])
            assert backend.lists==2
            assert [arguments["phrase"] for _, arguments in backend.calls]==words
            assert len(dialogue.inputs)==3  # No policy repair/model round or repeated retrieval.
            saved = outcome(resumed, sid, events)["operations"][0]["search"]
            assert saved["profile"]["policy"]=={"candidate_stop": 8, "keyword_limit": 5}
            assert saved["done"] and saved["stop"]=="exhausted" and len(saved["records"])==5
            card, = result_cards(events)
            assert [row["id"] for row in card["data"]["items"]]==words
        finally:
            await resumed.close()
    asyncio.run(run())


@pytest.mark.parametrize("second_policy", [
    {"candidate_stop": 8, "keyword_limit": 5},
    {"candidate_stop": 3, "keyword_limit": 3},
])
def test_multiple_saved_searches_advertise_compatible_schema_and_enforce_selected_policy(second_policy):
    tool = capability({"policy": {"candidate_stop": 1, "keyword_limit": 2}})
    execution = Execution()
    saved_policies = [{"candidate_stop": 8, "keyword_limit": 5}, second_policy]
    goal_ids = []
    for index, policy in enumerate(saved_policies):
        goal = execution.operations.register(f"Independent search {index}",
            {"server": tool.server, "name": tool.name}, planned=True)
        saved = SearchRun.create(SearchProfile(query="query", policy=SearchPolicy(**policy)),
            {"query": "alpha"}, ["alpha"])
        execution.operations.get(goal)["search"] = saved.state
        goal_ids.append(goal)
    tools = SimpleNamespace(loaded={tool.alias: tool})
    native = definition(tool)
    original = deepcopy(native)
    displayed, = DatasetQA._definitions([native], tools, execution)
    schema = displayed["function"]["parameters"]
    task = schema["properties"][TASK]
    array = next(item for item in task["properties"]["keywords"]["anyOf"] if item.get("type")=="array")
    assert array["maxItems"]==5  # Both saved policies fit despite live maxItems=2.
    choices = json.loads(schema["properties"][GOAL]["description"].partition(": ")[2])
    assert {choice["id"]: choice["search_policy"] for choice in choices}==dict(zip(goal_ids, saved_policies))
    if saved_policies[0]==second_policy:
        assert "8 actually returned unique candidates" in task["properties"]["keywords"]["description"]
    else:
        assert "selected goal" in task["properties"]["keywords"]["description"]
        assert "shared maxItems only accommodates" in task["properties"]["keywords"]["description"]

    words = ["alpha", "beta", "gamma", "delta", "epsilon"]
    directive = {"complete_request": True, "keywords": words, "original_keywords": ["alpha"]}
    for goal, policy in zip(goal_ids, saved_policies):
        # The model gets one envelope; the selected operation remains the
        # authority. No model request, capability discovery or MCP call is needed.
        Draft202012Validator(schema).validate({"query": "alpha", GOAL: goal, TASK: directive})
        effective = DatasetQA._task_policy(tool, execution.operations, goal)
        assert effective.model_dump()==policy
        if policy["keyword_limit"]==5:
            assert TaskDirective.model_validate(directive, context={"search_policy": effective}).keywords==words
        else:
            with pytest.raises(ValidationError):
                TaskDirective.model_validate(directive, context={"search_policy": effective})
            search = SearchRun(execution.operations.get(goal)["search"])
            before = deepcopy(search.state)
            with pytest.raises(QAError):
                search.extend({"query": "alpha"}, words)
            assert search.state==before
    assert native==original and profile(tool).search.policy.keyword_limit==2
