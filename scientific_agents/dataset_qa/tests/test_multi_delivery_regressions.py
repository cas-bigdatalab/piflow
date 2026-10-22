"""Independent user outcomes retain all artifacts through delivery and replay."""
import asyncio

from langchain_core.messages import AIMessageChunk

from ..capabilities import OBJECT
from ..service import DatasetQA
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, for_goal, goals, payload, seed, text


def finish(messages, definitions):
    return action("deliver_results") if definitions else text("The requested results are available.")


def test_heterogeneous_required_artifacts_are_delivered_and_replayed_independently(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.catalog["data"][1].meta["piflow"]["view_type"] = "detail"
        backend.catalog["data"][3].meta["piflow"]["view_type"] = "sample"
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "Show the first dataset details", "tool": "inspect", "object": "candidate:1"},
                {"description": "Sample the second dataset", "tool": "sample", "object": "candidate:2"},
                calls=[remote("inspect", **{OBJECT: "candidate:1"}),
                    remote("sample", count=2, **{OBJECT: "candidate:2"})]),
                *[finish] * 4]
            message = "Show the first dataset details and sample the second dataset"
            values = await collect(service, sid, message, "two-artifacts")
            cards = result_cards(values)
            assert values[-1]["status"] == "COMPLETED"
            assert len(cards) == 2
            assert {card["view_type"] for card in cards} == {"detail", "sample"}
            ledger = payload(service, sid, values)
            ids = [card["result_id"] for card in cards]
            assert ledger["delivery"] == ledger["delivery_sources"] == ids
            assert all(item["state"] == "succeeded" for item in ledger["operations"])
            assert len(backend.calls) == 3
            replay = await collect(service, sid, message, "two-artifacts")
            assert result_cards(replay) == cards
            assert len(backend.calls) == 3
            history = await service.get_session("alice", sid)
            delivered = [item["payload"] for item in history["items"]
                if item["item_type"] == "RESULT_CARD" and item["payload"]["result_id"] in ids]
            assert delivered == cards
        finally:
            await service.close()
    asyncio.run(run())


def test_two_explicit_random_samples_remain_two_artifacts_even_when_content_matches(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def dispatch(name, arguments, **options):
                response = await execute(name, arguments, **options)
                if name == "sample":
                    response.structured_content = {"items": [{"row": "same draw"}]}
                return response
            connection.call_tool = dispatch
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "Draw the first independent sample", "tool": "sample", "object": "candidate:1"},
                {"description": "Draw the second independent sample", "tool": "sample", "object": "candidate:1"}),
                for_goal("Draw the first independent sample", remote("sample", count=1, **{OBJECT: "candidate:1"})),
                for_goal("Draw the second independent sample", remote("sample", count=1, **{OBJECT: "candidate:1"})),
                *[finish] * 4]
            values = await collect(service, sid, "Draw two independent samples from the first dataset", "two-draws")
            cards = result_cards(values)
            assert values[-1]["status"] == "COMPLETED"
            assert len(cards) == 2 and cards[0]["result_id"] != cards[1]["result_id"]
            assert cards[0]["data"] == cards[1]["data"] == {"items": [{"row": "same draw"}]}
            assert len([call for call in backend.calls if call[1] == "sample"]) == 2
            ledger = payload(service, sid, values)
            assert ledger["delivery"] == ledger["delivery_sources"]
            assert len(ledger["delivery"]) == 2
        finally:
            await service.close()
    asyncio.run(run())


def test_failure_of_third_outcome_preserves_both_completed_heterogeneous_artifacts(engine):
    async def run():
        backend, dialogue = configured(), BareDialogue()
        backend.catalog["data"][1].meta["piflow"]["view_type"] = "detail"
        backend.catalog["data"][2].meta["piflow"]["view_type"] = "directory"
        original = backend.client

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            execute = connection.call_tool

            async def dispatch(name, arguments, **options):
                backend.protocol_error = name == "sample"
                try:
                    return await execute(name, arguments, **options)
                finally:
                    backend.protocol_error = False
            connection.call_tool = dispatch
            return connection

        backend.client = client
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            await seed(service, dialogue, sid)
            dialogue.responses = [goals(
                {"description": "Show details", "tool": "inspect", "object": "candidate:1"},
                {"description": "Show preview", "tool": "preview", "object": "candidate:1"},
                {"description": "Obtain sample", "tool": "sample", "object": "candidate:1"},
                calls=[remote("inspect", **{OBJECT: "candidate:1"}),
                    remote("preview", **{OBJECT: "candidate:1"}),
                    remote("sample", count=1, **{OBJECT: "candidate:1"})]), text("Partial results are ready.")]
            values = await collect(service, sid, "Show details, preview and sample the first dataset", "partial-three")
            cards = result_cards(values)
            assert values[-1]["status"] == "FAILED" and values[-1]["code"] == "tool_failed"
            assert len(cards) == 2 and {card["view_type"] for card in cards} == {"detail", "directory"}
            ledger = payload(service, sid, values)
            assert ledger["delivery"] == ledger["delivery_sources"] == [card["result_id"] for card in cards]
            assert [item["state"] for item in ledger["operations"]] == ["succeeded", "succeeded", "failed"]
            message = "".join(value.get("text", "") for value in values if value["type"] == "message")
            assert "Show details" in message and "Show preview" in message and "Obtain sample" in message
            assert len(backend.calls) == 4
        finally:
            await service.close()
    asyncio.run(run())


def test_delivery_position_in_a_batch_does_not_skip_a_later_native_action(engine):
    def deliver_then_search(messages, definitions):
        native = remote("search", query="second field")(messages, definitions)
        return AIMessageChunk(content="", tool_calls=[
            action("deliver_results").tool_calls[0], native.tool_calls[0]])

    async def run():
        backend = configured()
        dialogue = BareDialogue(load(), goals(
            {"description": "Compare two fields", "tool": "search", "output": "answer"},
            calls=[remote("search", query="first field")]), deliver_then_search, *[finish] * 4)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            values = await collect(service, session(service), "Find resources in two fields and compare them", "ordered")
            assert values[-1]["status"] == "COMPLETED"
            assert [call[2]["query"] for call in backend.calls] == ["first field", "second field"]
        finally:
            await service.close()
    asyncio.run(run())
