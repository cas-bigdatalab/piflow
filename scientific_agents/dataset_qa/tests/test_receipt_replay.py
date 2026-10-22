"""A cached success is evidence, never an implicit recovery of later work."""
import asyncio

import pytest

from ..contracts import QAError
from ..operations import Operations
from ..service import DatasetQA
from .test_dataset_qa import collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, goals, payload, text


CAPABILITY = {"server": "service", "name": "retrieve"}


def succeeded(operations, operation_id, key="good", result_id="good-result"):
    operations.start(operation_id, key, CAPABILITY, retry_safe=True, invocation=key)
    operations.finish(operation_id, key, result_id=result_id)
    return operations.get(operation_id)["attempts"][-1]


@pytest.mark.parametrize("code,state", [
    ("invalid_parameters", "pending"), ("tool_failed", "failed"), ("execution_unknown", "unknown"),
])
@pytest.mark.parametrize("fresh_key", [False, True])
def test_old_success_replay_never_resolves_later_unfinished_attempt(code, state, fresh_key):
    operations = Operations()
    key = operations.register("Requested outcome", CAPABILITY, planned=True)
    receipt = succeeded(operations, key)
    operations.start(key, "later", CAPABILITY, retry_safe=True, invocation="later")
    operations.finish(key, "later", error=QAError(code, "Later work did not complete"))

    replay_key = "remapped-good" if fresh_key else "good"
    if fresh_key:
        operations.reuse(key, replay_key, receipt)
    operations.finish(key, replay_key, result_id="good-result")

    assert operations.get(key)["state"]==state
    assert operations.delivery_ids()==["good-result"]
    assert operations.error(["good-result"]) is not None
    assert not any(attempt["state"]=="running" for attempt in operations.get(key)["attempts"])


def test_first_exact_reuse_completes_a_new_goal_without_execution():
    operations = Operations()
    auxiliary = operations.register("Supporting lookup", CAPABILITY, required=False)
    succeeded(operations, auxiliary)
    requested = operations.register("Requested outcome", CAPABILITY, planned=True)
    receipt = operations.receipt("good", requested)
    assert receipt is not None

    operations.reuse(requested, "selected-good", receipt)
    operations.finish(requested, "selected-good", result_id="good-result")

    item = operations.get(requested)
    assert item["state"]=="succeeded" and len(item["attempts"])==1
    assert item["attempts"][0]["reused"] and item["attempts"][0]["dispatched"] is False
    assert operations.error(["good-result"]) is None


def test_rejected_parameters_do_not_prevent_first_evidence_reuse_for_a_new_goal():
    operations = Operations()
    auxiliary = operations.register("Supporting lookup", CAPABILITY, required=False)
    succeeded(operations, auxiliary)
    requested = operations.register("Requested outcome", CAPABILITY, planned=True)
    operations.start(requested, "invalid", CAPABILITY, retry_safe=True)
    operations.finish(requested, "invalid", error=QAError("invalid_parameters", "Correct the input"))

    operations.reuse(requested, "selected-good", operations.receipt("good", requested))
    operations.finish(requested, "selected-good", result_id="good-result")

    assert operations.get(requested)["state"]=="succeeded"
    assert operations.error(["good-result"]) is None


def test_real_new_execution_can_recover_a_previously_failed_attempt():
    operations = Operations()
    key = operations.register("Requested outcome", CAPABILITY, planned=True)
    succeeded(operations, key)
    operations.start(key, "failed", CAPABILITY, retry_safe=True, invocation="remaining-source")
    operations.finish(key, "failed", error=QAError("tool_failed", "Remaining source unavailable"))

    operations.start(key, "retry", CAPABILITY, retry_safe=True, invocation="remaining-source")
    operations.finish(key, "retry", result_id="recovered-result")

    assert operations.get(key)["state"]=="succeeded"
    assert operations.delivery_ids()==["good-result", "recovered-result"]
    assert operations.error(operations.delivery_ids()) is None


def test_missing_success_receipt_is_still_rejected():
    operations = Operations()
    key = operations.register("Requested outcome", CAPABILITY, planned=True)
    with pytest.raises(QAError, match="缺少"):
        operations.finish(key, "invented", result_id="invented-result")
    assert operations.get(key)["state"]=="pending"


def test_success_replay_after_failed_variant_delivers_partial_without_false_completion(engine):
    async def run():
        backend = configured()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def call(name, arguments, **options):
                backend.protocol_error = arguments.get("query")=="unavailable"
                return await execute(name, arguments, **options)

            connection.call_tool = call
            return connection

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = BareDialogue(load(), goals({"description": "Retrieve both necessary sources", "tool": "search"},
            calls=[remote("search", query="available"), remote("search", query="unavailable")]),
            remote("search", query="available"), text())
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        try:
            values = await collect(service, sid, "Retrieve both necessary sources")
            assert values[-1]["status"]=="FAILED" and values[-1]["code"]=="tool_failed"
            assert backend.calls==[("data", "search", {"query": "available"}),
                ("data", "search", {"query": "unavailable"})]
            assert len(result_cards(values))==1
            ledger = payload(service, sid, values)
            assert ledger["operations"][0]["state"]=="failed"
            assert len(ledger["operations"][0]["attempts"])==2
            assert "部分" in "".join(value.get("text", "") for value in values)
        finally:
            await service.close()
    asyncio.run(run())
