"""Current advertised contracts, without legacy bookkeeping inserted by tests."""
import asyncio
import json

from jsonschema import Draft202012Validator
from langchain_core.messages import AIMessageChunk
import pytest

from ..capabilities import TASK
from ..contracts import QAError
from ..operations import Operations
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import action, collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, configured, for_goal, goals, payload, seed, text


class ContractDialogue(BareDialogue):
    async def respond(self, messages, definitions):
        schemas = {value["function"]["name"]: value["function"]["parameters"] for value in definitions}
        async for reply in super().respond(messages, definitions):
            for call in reply.tool_calls:
                assert call["name"] in schemas
                Draft202012Validator(schemas[call["name"]]).validate(call["args"])
            yield reply


def read_backend():
    backend = configured()
    backend.items = [{"id": "resource-1", "title": "Observation dataset"}]
    for definition, label, view in zip(backend.catalog["data"][1:3],
            ("数据集详情", "目录结构"), ("detail", "table")):
        definition.annotations = {"readOnlyHint": True, "idempotentHint": True}
        definition.meta["piflow"].update(view_type=view)
        definition.meta["piflow"]["qa"].update(atomic=True, label=label)
    return backend


def native(name, complete=False, **arguments):
    return remote(name, **arguments, **{TASK: {"complete_request": complete}})


def batch(*calls):
    def reply(messages, definitions):
        return AIMessageChunk(content="", tool_calls=[
            {**call(messages, definitions).tool_calls[0], "id": "read-"+str(index)}
            for index, call in enumerate(calls)])
    return reply


def outcomes(*, calls=()):
    return goals({"description": "数据集详情", "tool": "inspect"},
        {"description": "目录结构", "tool": "preview"}, calls=calls)


def confirm_receipts(messages, definitions):
    schema = next(value["function"]["parameters"] for value in definitions
        if value["function"]["name"] == "deliver_results")
    choices = schema["properties"]["confirmations"]["items"]["properties"]["goal"]
    entries = json.loads(choices["description"].split(" Choices: ", 1)[1])
    assert len(entries) == 2
    return action("deliver_results", confirmations=[
        {"goal": entry["goal"], "result_ids": entry["result_ids"]} for entry in entries])


@pytest.mark.parametrize("complete", [False, True])
@pytest.mark.parametrize("supply_identifier", [False, True])
def test_two_reads_of_the_only_candidate_finish_without_a_plan_or_extra_model_rounds(engine, complete, supply_identifier):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)
            args = {"reference": "resource-1"} if supply_identifier else {}
            dialogue.responses = [outcomes(calls=[native("inspect", complete, **args),
                native("preview", complete, **args)]), text("已整理好数据集详情和目录结构。")]
            events = await collect(service, sid, "看下这个数据集的详情以及目录结构", "two-reads")
            assert_completed(service, sid, events[-1])
            assert backend.calls[1:] == [("data", "inspect", {"reference": "resource-1"}),
                ("data", "preview", {"reference": "resource-1"})]
            assert len(dialogue.inputs) - baseline == 2
            assert dialogue.inputs[-1][1] == []
            assert len(result_cards(events)) == 2
            assert {card["view_type"] for card in result_cards(events)} == {"detail", "table"}
            assert all(set(card) == {"result_id", "view_type", "title", "data"} for card in result_cards(events))
            ledger = payload(service, sid, events)
            assert not ledger.get("plan")
            assert len(ledger["operations"]) == 2
            assert all(item["state"] == "succeeded" and item["required"] for item in ledger["operations"])
            replay = await collect(service, sid, "看下这个数据集的详情以及目录结构", "two-reads")
            assert result_cards(replay) == result_cards(events)
            assert len(backend.calls) == 3
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("repair", ["confirmation", "replay"])
@pytest.mark.parametrize("sequential", [False, True])
def test_late_outcomes_confirm_both_receipts_without_another_mcp_call(engine, repair, sequential):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            confirmation = confirm_receipts if repair == "confirmation" else batch(native("inspect", True), native("preview", True))
            reads = [native("inspect"), native("preview")] if sequential else [batch(native("inspect"), native("preview"))]
            dialogue.responses = [*reads,
                action("deliver_results"), outcomes(), confirmation, text("两项内容已整理好。")]
            events = await collect(service, sid, "查看详情和目录结构", "late-outcomes")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 3
            assert all(arguments == {"reference": "resource-1"} for _, _, arguments in backend.calls[1:])
            assert len(result_cards(events)) == 2
            ledger = payload(service, sid, events)
            required = [item for item in ledger["operations"] if item["required"]]
            assert len(required) == 2
            assert all(attempt.get("confirmation" if repair == "confirmation" else "reused")
                for item in required for attempt in item["attempts"])
        finally:
            await service.close()
    asyncio.run(run())


def test_reference_provenance_cannot_choose_one_of_two_unconfirmed_outcomes():
    operations = Operations()
    detail = operations.register("Read details", {"server": "data", "name": "inspect"}, required=False)
    operations.get(detail).update(inferred=True, state="succeeded", attempts=[
        {"key": "read-detail", "state": "succeeded", "result_id": "details"}])
    directory = operations.register("Read directory", {"server": "data", "name": "preview"},
        target={"result_id": "details", "path": "", "kind": "object"}, required=False)
    operations.get(directory).update(inferred=True, state="succeeded", attempts=[
        {"key": "read-directory", "state": "succeeded", "result_id": "directory"}])

    with pytest.raises(QAError) as caught:
        DatasetQA._infer_delivery_goal(operations)

    assert caught.value.code == "invalid_delivery"
    assert len(caught.value.detail["candidates"]) == 2
    assert not operations.required


def test_explicit_supporting_result_does_not_become_a_second_outcome():
    operations = Operations()
    support = operations.register("Resolve object", {"server": "data", "name": "inspect"}, required=False)
    operations.get(support).update(state="succeeded", attempts=[
        {"key": "resolve", "state": "succeeded", "result_id": "resolved-object"}])
    requested = operations.register("Read directory", {"server": "data", "name": "preview"},
        target={"result_id": "resolved-object", "path": "", "kind": "object"}, required=False)
    operations.get(requested).update(inferred=True, state="succeeded", attempts=[
        {"key": "read-directory", "state": "succeeded", "result_id": "directory"}])

    DatasetQA._infer_delivery_goal(operations)

    assert [item["id"] for item in operations.required] == [requested]
    assert operations.delivery_ids() == ["directory"]


@pytest.mark.parametrize("case", ["ambiguous", "hidden_candidate", "unknown_id", "competing_selection", "cleared_focus"])
def test_implicit_binding_does_not_guess_a_target(engine, case):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        if case in {"ambiguous", "hidden_candidate"}:
            backend.items.append({"id": "resource-2", "title": "Another dataset" if case == "ambiguous" else "x" * 12000})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            context = json.loads(service.store.session("alice", sid)["context"])
            if case == "competing_selection":
                from .test_references import stored
                other = stored(service, sid, "selected-source", {"id": "other"})
                context["references"]["selected"] = [{"result_id": other["result_id"], "path": "", "kind": "object"}]
                from sqlalchemy import update
                from ..persistence import dumps
                with engine.begin() as conn:
                    conn.execute(update(service.store.sessions).where(service.store.sessions.c.id == sid)
                        .values(context=dumps(context)))
            args = {"reference": "invented-resource"} if case == "unknown_id" else {}
            call = native("inspect", True, **args)
            if case == "cleared_focus":
                original = call
                def call(messages, definitions):
                    return AIMessageChunk(content="", tool_calls=[action("remember", focus=None).tool_calls[0],
                        original(messages, definitions).tool_calls[0]])
            dialogue.responses = [call] * 3
            events = await collect(service, sid, "查看这个数据集的详情", "ambiguous-target")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert not [call for call in backend.calls if call[1] == "inspect"]
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("empty_directory", [False, True])
def test_real_corpus_mcp_contracts_preserve_two_cards_and_the_directory_table(engine, monkeypatch, empty_directory):
    from mcp_servers import corpus_mcp
    from ..contracts import Server
    from ..mcp import MCPGateway

    calls = []
    item = {"cstr": "dataset-alpha", "title": "Observation dataset"}
    nodes = [] if empty_directory else [{"name": "measurements.jsonl", "fileId": "file-1", "isFile": True,
        "downloadUrl": "https://example.invalid/measurements.jsonl"}]
    directory = {"code": 200, "data": nodes, "message": "OK"}

    def search(**kwargs):
        calls.append(("search", kwargs))
        return {"items": [item], "pagination": {"total": 1}}

    def detail(cstr):
        calls.append(("detail", cstr))
        assert cstr == item["cstr"]
        return {**item, "description": "Station measurements", "format": "jsonl"}

    def listing(cstr, file_id=None):
        calls.append(("directory", cstr, file_id))
        assert cstr == item["cstr"] and file_id is None
        return directory

    monkeypatch.setattr(corpus_mcp, "list_dataset_details", search)
    monkeypatch.setattr(corpus_mcp, "get_dataset_detail_by_cstr", detail)
    monkeypatch.setattr(corpus_mcp, "get_dataset_directory", listing)

    async def run():
        dialogue = ContractDialogue(action("load_mcp_tools", server="piflow-corpus", group="corpus", limit=8),
            remote("search_corpus_datasets", query=item["title"], **{TASK: {
                "complete_request": True, "keywords": None, "original_keywords": None}}), text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(corpus_mcp.mcp)}))
        sid = session(service)
        try:
            first = await collect(service, sid, "Find Observation dataset", "find-one")
            assert_completed(service, sid, first[-1])
            baseline = len(dialogue.inputs)
            dialogue.responses = [goals(
                {"description": "数据集详情", "tool": "get_corpus_dataset_detail"},
                {"description": "目录结构", "tool": "get_corpus_dataset_directory"},
                calls=[native("get_corpus_dataset_detail"), native("get_corpus_dataset_directory")]),
                text("详情和目录已整理好。" if nodes else "详情已整理好，本次目录返回的条目为 0。")]
            events = await collect(service, sid, "看下这个数据集的详情以及目录结构", "two-corpus-reads")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) - baseline == 2
            assert len(calls) == 3
            assert {value[0] for value in calls} == {"search", "detail", "directory"}
            cards = result_cards(events)
            assert len(cards) == 2
            tree = next(card for card in cards if card["view_type"] == "table")
            assert tree["data"] == {"items": [directory]}
            assert all(set(card) == {"result_id", "view_type", "title", "data"} for card in cards)
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("content_available", [True, False])
def test_summary_unavailable_still_identifies_the_delivered_content(engine, content_available):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        if not content_available:
            backend.catalog["data"][2].meta["piflow"]["qa"]["result"] = {
                "kind": "tree", "unavailable_when": [{"path": "/available", "test": "equals", "value": False}]}
            original = backend.client
            def client(*args, **kwargs):
                connection = original(*args, **kwargs)
                execute = connection.call_tool
                async def dispatch(name, arguments, **options):
                    result = await execute(name, arguments, **options)
                    if name == "preview":
                        result.structured_content = {"available": False}
                    return result
                connection.call_tool = dispatch
                return connection
            backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [outcomes(calls=[native("inspect"), native("preview")]),
                QAError("model_timeout", "private provider diagnostic")]
            events = await collect(service, sid, "查看详情和目录结构", "answer-fallback")
            assert_completed(service, sid, events[-1])
            answer = "".join(event.get("text", "") for event in events if event["type"] == "message")
            assert "数据集详情" in answer and "目录结构" in answer
            if not content_available:
                assert "已为您提供：数据集详情。" in answer and "本次尚未提供：目录结构。" in answer
            assert not any(word in answer for word in ("private", "错误", "失败", "其余内容"))
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("scope", ["focus", "pinned_source", "matching_identifier", "conflicting_identifier"])
def test_implicit_binding_respects_current_scope_and_verifies_identifiers(engine, scope):
    from sqlalchemy import update
    from ..persistence import dumps
    from .test_references import stored

    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        if scope == "matching_identifier":
            backend.items.append({"id": "resource-2", "title": "Second dataset"})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            candidate = await seed(service, dialogue, sid)
            if scope != "matching_identifier":
                old = stored(service, sid, "old-focus", {"id": "old-object"})
                state = json.loads(service.store.session("alice", sid)["context"])
                state["references"]["current"] = {"result_id": old["result_id"], "path": "", "kind": "object"}
                with engine.begin() as conn:
                    conn.execute(update(service.store.sessions).where(service.store.sessions.c.id == sid).values(context=dumps(state)))
            args = {"reference": "resource-2"} if scope == "matching_identifier" else {
                "reference": "resource-1"} if scope == "conflicting_identifier" else {}
            params = {"result_id": candidate["result_id"]} if scope == "pinned_source" else {}
            dialogue.responses = [native("inspect", True, **args)] * 3 if scope == "conflicting_identifier" else [
                native("inspect", True, **args), text()]
            events = await collect(service, sid, "查看这个数据集的详情", "scoped-read", **params)
            if scope == "conflicting_identifier":
                assert_handled(service, sid, events[-1], "invalid_parameters")
                assert len(backend.calls) == 1
            else:
                assert_completed(service, sid, events[-1])
                expected = "old-object" if scope == "focus" else "resource-2" if scope == "matching_identifier" else "resource-1"
                assert backend.calls[-1] == ("data", "inspect", {"reference": expected})
        finally:
            await service.close()
    asyncio.run(run())


def test_contradictory_whole_request_batch_is_rejected_before_any_business_dispatch(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            # The declaration covers only one of two calls claiming completion.
            reply = goals({"description": "数据集详情", "tool": "inspect"},
                calls=[native("inspect", True), native("preview", True)])
            dialogue.responses = [reply] * 3
            events = await collect(service, sid, "查看这个数据集的详情", "conflicting-batch")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert len(backend.calls) == 1
            assert not payload(service, sid, events).get("operations")
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("unavailable", [{"preview"}, {"inspect", "preview"}])
def test_partial_read_closure_names_content_without_reexecution_or_diagnostics(engine, unavailable):
    from types import SimpleNamespace

    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        original = backend.client
        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool
            async def dispatch(name, arguments, **options):
                result = await execute(name, arguments, **options)
                if name in unavailable:
                    return SimpleNamespace(is_error=True, content=[SimpleNamespace(type="text", text="PRIVATE backend traceback")])
                return result
            connection.call_tool = dispatch
            return connection
        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)
            dialogue.responses = [outcomes(calls=[native("inspect"), native("preview")]), action("deliver_results")]
            events = await collect(service, sid, "查看详情和目录结构", "partial-reads")
            assert_handled(service, sid, events[-1], "tool_failed")
            assert len(dialogue.inputs) - baseline == 2  # One scope decision, no explanation-only call.
            assert len(backend.calls) == 3
            assert len(result_cards(events)) == 2 - len(unavailable)
            answer = "".join(event.get("text", "") for event in events if event["type"] == "message")
            assert "数据集详情" in answer and "目录结构" in answer
            if len(unavailable) == 1:
                assert "已为您提供：数据集详情" in answer and "本次尚未提供：目录结构" in answer
            assert not any(word in answer for word in ("PRIVATE", "traceback", "错误", "失败", "op1", "op2"))
            replay = await collect(service, sid, "查看详情和目录结构", "partial-reads")
            assert replay == events
            assert len(backend.calls) == 3
        finally:
            await service.close()
    asyncio.run(run())


def test_late_bound_target_still_enforces_its_outcome_format_before_dispatch(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        backend.items.append({"id": "resource-2", "title": "Second dataset"})
        tool = backend.catalog["data"][1]
        tool.inputSchema["properties"]["format"] = {"type": "string", "enum": ["csv", "jsonl"]}
        tool.meta["piflow"]["qa"].update(artifact={}, result={"kind": "export", "argument_paths": {"format": "/resource/format"}})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            wrong = goals({"description": "CSV records", "tool": "inspect", "output_format": "csv"},
                {"description": "Directory", "tool": "preview", "object": "candidate:1"},
                calls=[native("inspect", True, reference="resource-2", format="jsonl"),
                    native("preview", True, reference="resource-1")])
            dialogue.responses = [wrong] * 3
            events = await collect(service, sid, "Export the second dataset to CSV and show the first directory", "format-conflict")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert len(backend.calls) == 1  # Format mismatch stops the entire contradictory batch.
        finally:
            await service.close()
    asyncio.run(run())


def test_supplied_goal_selection_binds_two_previously_unresolved_targets(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        backend.items.append({"id": "resource-2", "title": "Second dataset"})
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "First details", "tool": "inspect"},
                {"description": "Second details", "tool": "inspect"}),
                batch(for_goal("First details", native("inspect", reference="resource-1")),
                    for_goal("Second details", native("inspect", reference="resource-2"))), text()]
            events = await collect(service, sid, "Show both datasets' details", "two-objects")
            assert_completed(service, sid, events[-1])
            assert backend.calls[1:] == [("data", "inspect", {"reference": "resource-1"}),
                ("data", "inspect", {"reference": "resource-2"})]
            rows = payload(service, sid, events)["operations"]
            assert [row["target"]["path"] for row in rows] == ["/items/0", "/items/1"]
        finally:
            await service.close()
    asyncio.run(run())
