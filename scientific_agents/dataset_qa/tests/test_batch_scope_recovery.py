"""Whole-turn scope repair preserves independent outcomes and saved work."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from ..capabilities import SUPPORTING, TASK
from ..service import DatasetQA
from .assertions import assert_completed, assert_handled
from .test_dataset_qa import collect, engine, remote, result_cards, session
from .test_decisions import BareDialogue, goals, payload, seed, text
from .test_independent_outcomes import ContractDialogue, batch, native, outcomes, read_backend


@pytest.mark.parametrize("complete", [(True, True), (True, False), (False, False)])
@pytest.mark.parametrize("execution_failure", [False, True])
def test_scope_only_repair_preserves_typed_calls_and_one_execution_repair(engine, complete, execution_failure):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        backend.catalog["data"][2].inputSchema["properties"]["section"] = {"type": ["string", "null"], "enum": [None, "top"]}
        original_client = backend.client
        failed = False

        def client(*args, **kwargs):
            connection = original_client(*args, **kwargs)
            execute = connection.call_tool

            async def dispatch(name, arguments, **options):
                nonlocal failed
                result = await execute(name, arguments, **options)
                if execution_failure and name == "preview" and not failed:
                    failed = True
                    return SimpleNamespace(is_error=True,
                        content=[SimpleNamespace(type="text", text="Directory temporarily unavailable")])
                return result

            connection.call_tool = dispatch
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)
            detail_args, directory_args = {"reference": "resource-1"}, {"reference": "resource-1", "section": None}

            def repair_scope(messages, definitions):
                feedback = json.loads(messages[-1].content)["runtime_feedback"]
                detail = feedback["detail"]
                assert detail["decision"] == "declare_outcomes"
                assert detail["phase"] == "scope_admission" and detail["dispatched"] is False
                assert {name.rsplit("_", 1)[-1] for name in detail["tools"]} == {"inspect", "preview"}
                assert detail["retained_proposal"] is True
                assert "remember.goals ONLY" in detail["guidance"]
                assert len(backend.calls) == 1
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                return outcomes()(messages, definitions)

            def repair_execution(messages, definitions):
                operations = json.loads(messages[1].content)["operations"]["items"]
                assert len(operations) == 2
                assert all(not item.get("supporting") and not item.get("delivery_pending") for item in operations)
                assert len(backend.calls) == 3
                # The successful independent result is retained, not re-executed.
                assert next(item for item in operations if item["description"] == "数据集详情")["state"] == "succeeded"
                return native("preview", False, **directory_args)(messages, definitions)

            dialogue.responses = [batch(native("inspect", complete[0], **detail_args),
                native("preview", complete[1], **directory_args)), repair_scope,
                *([repair_execution] if execution_failure else []), text()]
            events = await collect(service, sid, "看下这个数据集的详情以及目录结构", "scope-repair")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) - baseline == 3 + int(execution_failure)
            assert backend.calls[1:] == [("data", "inspect", detail_args), ("data", "preview", directory_args),
                *([("data", "preview", directory_args)] if execution_failure else [])]
            assert len(result_cards(events)) == 2
            ledger = payload(service, sid, events)
            assert not ledger.get("plan")
            assert len(ledger["operations"]) == 2
            assert all(item["required"] and item["state"] == "succeeded" for item in ledger["operations"])
            assert service.gateway.limits.max_corrections == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_whole_turn_outcome_can_coemit_an_explicit_auxiliary_call(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            baseline = len(dialogue.inputs)
            dialogue.responses = [batch(native("inspect", True, reference="resource-1"),
                remote("preview", reference="resource-1", **{SUPPORTING: True, TASK: {"complete_request": False}})), text()]
            events = await collect(service, sid, "查看详情；如有帮助，可用目录作为辅助信息", "supporting-read")
            assert_completed(service, sid, events[-1])
            assert len(dialogue.inputs) - baseline == 2
            assert len(backend.calls) == 3 and len(result_cards(events)) == 1
            required = [item for item in payload(service, sid, events)["operations"] if item["required"]]
            assert len(required) == 1 and required[0]["capability"]["name"] == "inspect"
        finally:
            await service.close()
    asyncio.run(run())


def test_changing_shortcut_flags_still_requires_scope_before_dispatch(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)

            def declare_before_reads(messages, definitions):
                assert not json.loads(messages[1].content).get("operations", {}).get("items")
                assert len(backend.calls) == 1
                assert json.loads(messages[-1].content)["runtime_feedback"]["detail"]["decision"] == "declare_outcomes"
                return outcomes()(messages, definitions)

            dialogue.responses = [batch(native("inspect", True), native("preview", True)),
                batch(native("inspect"), native("preview")), declare_before_reads, text()]
            events = await collect(service, sid, "查看详情和目录", "late-explicit-scope")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 3 and len(result_cards(events)) == 2
            required = [item for item in payload(service, sid, events)["operations"] if item["required"]]
            assert len(required) == 2 and all(item["planned"] for item in required)
            assert all(not attempt.get("reused") for item in required for attempt in item["attempts"])
        finally:
            await service.close()
    asyncio.run(run())


def test_auxiliary_role_does_not_bypass_whole_batch_target_validation(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            invalid = batch(native("inspect", True, reference="resource-1"),
                remote("preview", reference="invented-resource", **{SUPPORTING: True, TASK: {"complete_request": False}}))
            dialogue.responses = [invalid] * 3
            events = await collect(service, sid, "查看详情，可用目录作为辅助", "invalid-auxiliary-target")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert len(backend.calls) == 1 and not result_cards(events)
            assert not payload(service, sid, events).get("operations")
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("already_declared", [False, True])
def test_false_batch_requires_scope_for_every_requested_capability(engine, already_declared):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            partial_scope = {"description": "数据集详情", "tool": "inspect"}

            def repair_missing_scope(messages, definitions):
                feedback = json.loads(messages[-1].content)["runtime_feedback"]
                assert feedback["detail"]["decision"] == "declare_outcomes"
                assert feedback["detail"]["phase"] == "scope_admission"
                assert len(backend.calls) == 1
                operations = json.loads(messages[1].content).get("operations", {}).get("items", [])
                assert len(operations) == int(already_declared)
                assert all(item["state"] == "pending" and not item["result_ids"] for item in operations)
                return outcomes()(messages, definitions)

            reads = [native("inspect"), native("preview")]
            dialogue.responses = ([goals(partial_scope), batch(*reads)] if already_declared else [
                goals(partial_scope, calls=reads)]) + [repair_missing_scope, text()]
            events = await collect(service, sid, "查看详情和目录", "missing-scope")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 3 and len(result_cards(events)) == 2
            assert all(item["required"] for item in payload(service, sid, events)["operations"])
        finally:
            await service.close()
    asyncio.run(run())


def test_explicit_legacy_batch_keeps_its_existing_scope_contract(engine):
    from .test_dataset_qa import action

    async def run():
        backend, dialogue = read_backend(), BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)

            def legacy_batch(messages, definitions):
                calls = batch(native("inspect"), native("preview"))(messages, definitions)
                meaning = action("remember", operations=[
                    {"id": "detail", "description": "数据集详情", "direct": True},
                    {"id": "directory", "description": "目录结构", "direct": True}],
                    calls=["detail", "directory"])
                return calls.model_copy(update={"tool_calls": [*meaning.tool_calls, *calls.tool_calls]})

            dialogue.responses = [legacy_batch, text()]
            events = await collect(service, sid, "查看详情和目录", "legacy-scope")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 3 and len(result_cards(events)) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_multiple_calls_may_serve_one_explicit_goal(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        backend.catalog["data"][1].inputSchema["properties"]["section"] = {
            "type": "string", "enum": ["summary", "license"]}
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals({"description": "Read the dataset's summary and license", "tool": "inspect"},
                calls=[native("inspect", section="summary"), native("inspect", section="license")]), text()]
            events = await collect(service, sid, "查看数据集详情中的摘要和许可", "shared-goal")
            assert_completed(service, sid, events[-1])
            assert len(backend.calls) == 3
            operation, = payload(service, sid, events)["operations"]
            assert operation["required"] and operation["state"] == "succeeded"
            assert len(operation["attempts"]) == 2
            assert len({attempt["result_id"] for attempt in operation["attempts"]}) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_upstream_supporting_business_field_is_not_a_qa_role(engine):
    async def run():
        backend, dialogue = read_backend(), ContractDialogue()
        # Reserved-looking upstream fields disable the QA wrapper; their
        # values cannot silently turn a business call into auxiliary evidence.
        backend.catalog["data"][2].inputSchema["properties"][SUPPORTING] = {"type": "boolean"}
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            invalid = batch(native("inspect", True), remote("preview", reference="resource-1", **{SUPPORTING: True}))
            dialogue.responses = [invalid] * 3
            events = await collect(service, sid, "查看详情和目录", "business-field-collision")
            assert_handled(service, sid, events[-1], "invalid_parameters")
            assert len(backend.calls) == 1 and not result_cards(events)
            assert not payload(service, sid, events).get("operations")
        finally:
            await service.close()
    asyncio.run(run())
