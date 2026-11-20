"""Empty artifact acknowledgements use complete receipts, never guessed causes."""
import asyncio
from copy import deepcopy

import pytest

from ..operations import Operations
from ..responses import delivery_status, empty_delivery_summary
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, engine, result_cards, session
from .test_decisions import goals, payload, text
from .test_independent_outcomes import ContractDialogue, native
from .test_resource_index import Backend, POLICY, node


@pytest.fixture
def receipt_set():
    operations, cards = Operations(), []
    for name, data, presentation in [("详情", {"description": "Full detail", "optional": []}, None),
            ("条目", {"records": []}, {"kind": "collection", "path": "/records"})]:
        identifier = operations.register(name, {"server": "arbitrary", "name": name})
        operations.start(identifier, identifier, presentation=presentation)
        operations.finish(identifier, identifier, result_id=identifier)
        cards.append({"result_id": identifier, "data": data})
    return operations, cards


def render(operations, cards, *, delivered=None):
    delivered = [card["result_id"] for card in cards] if delivered is None else delivered
    facts = delivery_status(operations, delivered, cards=cards)
    return empty_delivery_summary(operations, facts, cards, delivered)


def test_empty_declared_primary_collection_keeps_other_provided_labels(receipt_set):
    operations, cards = receipt_set
    assert render(operations, cards) == "已为您提供：详情；条目。\n\n条目：本次查询未返回条目。"
    assert cards[0]["data"]["description"] == "Full detail"


@pytest.mark.parametrize("case", ["undeclared", "wrong_path", "non_list", "nonempty", "missing_card",
    "analysis", "unfinished", "not_delivered", "search"])
def test_unknown_nonempty_or_interpretive_results_never_trigger_empty_ack(receipt_set, case):
    operations, cards = receipt_set
    item = operations.items[1]
    if case == "undeclared":
        item["attempts"][0].pop("presentation")
    elif case == "wrong_path":
        item["attempts"][0]["presentation"]["path"] = "/not_returned"
    elif case == "non_list":
        cards[1]["data"]["records"] = None
    elif case == "nonempty":
        cards[1].update(data={"records": [{"value": 1}], "optional": []}, truncated=True)
    elif case == "missing_card":
        cards.pop()
    elif case == "analysis":
        operations.items[0]["output"] = "answer"
    elif case == "unfinished":
        operations.items[0]["state"] = "pending"
    elif case == "not_delivered":
        assert not render(operations, cards, delivered=[cards[0]["result_id"]])
        return
    elif case == "search":
        item["search"] = {"done": True}
    assert not render(operations, cards)


@pytest.mark.parametrize("earlier", [{"records": [{"value": 1}]}, {"optional": []}])
def test_last_empty_page_does_not_make_the_whole_goal_empty(receipt_set, earlier):
    operations, cards = receipt_set
    item = operations.items[1]
    operations.start(item["id"], "page-2", presentation={"kind": "collection", "path": "/records"})
    operations.finish(item["id"], "page-2", result_id="second-page")
    cards[1]["data"] = earlier
    cards.append({"result_id": "second-page", "data": {"records": []}})
    assert not render(operations, cards)


@pytest.mark.parametrize("count", [None, False, -1, "0", 1])
def test_directory_unknown_or_nonempty_count_is_not_zero(receipt_set, count):
    operations, cards = receipt_set
    operations.items[1]["attempts"][0].pop("presentation")
    cards[1]["directory_receipt"] = {"entry_count": count}
    assert not render(operations, cards)


@pytest.mark.parametrize("mode", ["empty", "analysis", "nonempty", "invalid_status", "missing_path", "ambiguous_path"])
def test_actual_directory_receipt_drives_ack_without_changing_cards_or_analysis(engine, mode):
    async def run():
        backend = Backend()
        original = backend.client
        directory_data = {"code": 200, "data": {"nodes": []}}
        if mode == "nonempty":
            directory_data["data"]["nodes"] = [node("known-file", "values.json", True)]
        elif mode == "invalid_status":
            directory_data["code"] = 501
        elif mode == "missing_path":
            directory_data = {"code": 200, "optional": []}
        elif mode == "ambiguous_path":
            directory_data["nodes"] = []

        def client(*args, **kwargs):
            connection = original(*args, **kwargs)
            dispatch = connection.call_tool

            async def call(name, arguments, **options):
                response = await dispatch(name, arguments, **options)
                if name == "list_tree":
                    response.structured_content = deepcopy(directory_data)
                elif name == "dataset_info":
                    response.structured_content.update(description="完整详情仍在卡片中", size="2 files",
                        download_url="https://example.invalid/details.json")
                return response
            connection.call_tool = call
            return connection

        backend.client = client
        final_calls = []

        def finish(messages, definitions):
            if definitions:
                return action("deliver_results")
            final_calls.append(True)
            return text("按请求解释已取得的详情；这份观察不能建立其他事实。")

        dialogue = ContractDialogue(goals(
            {"description": "详情", "tool": "dataset_info", "output": "answer" if mode == "analysis" else "result"},
            {"description": "目录结构", "tool": "list_tree"}, calls=[
                native("dataset_info", dataset="one"), native("list_tree", dataset="one")]), *[finish] * 5)
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        request = "请查看 dataset=one 的详情和目录结构" + ("，并分析详情的意义" if mode == "analysis" else "")
        try:
            events = await collect(service, sid, request, "empty-delivery")
            assert_completed(service, sid, events[-1])
            public = result_cards(events)
            assert len(public) == (1 if mode == "analysis" else 2)
            assert all(set(card) == {"result_id", "view_type", "title", "data"} for card in public)
            saved = service.store.results("alice", sid, events[-1]["task_id"])
            directory = next(card for card in saved if "directory_receipt" in card)
            if mode in {"invalid_status", "missing_path", "ambiguous_path"}:
                assert "entry_count" not in directory["directory_receipt"]
            else:
                assert directory["directory_receipt"]["entry_count"] == int(mode == "nonempty")
            assert directory["data"] == directory_data
            reply = "".join(event.get("text", "") for event in events if event["type"] == "message")
            if mode == "empty":
                assert final_calls == [] and all(definitions for _, definitions in dialogue.inputs)
                assert reply.startswith("已为您提供：详情；目录结构。\n\n目录结构：本次查询未返回条目。")
                assert "https://example.invalid/details.json" in reply
                assert "完整详情仍在卡片中" in str(public)
                assert "delivery" in payload(service, sid, events)
                assert await collect(service, sid, request, "empty-delivery") == events
            else:
                assert final_calls == [True] and "按请求解释" in reply
        finally:
            await service.close()
    asyncio.run(run())


def test_saved_empty_result_interpretation_keeps_the_context_answer_path(engine):
    async def run():
        backend = Backend()
        backend.tree[("one", None)] = []
        dialogue = ContractDialogue(native("list_tree", True, dataset="one"))
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        try:
            first = await collect(service, sid, "查看 dataset=one 的目录", "first")
            assert_completed(service, sid, first[-1])
            card, = result_cards(first)
            previous_calls, previous_rounds = len(backend.calls), len(dialogue.inputs)
            dialogue.responses = [action("respond_from_context", mode="evidence",
                result_ids=[card["result_id"]], reason="Interpret the saved observation"),
                text("这次查询返回空列表；这个观察不能确定其他范围的内容。")]
            events = await collect(service, sid, "解释这个结果能说明什么", "interpret")
            assert_completed(service, sid, events[-1])
            assert not result_cards(events) and len(backend.calls) == previous_calls
            assert len(dialogue.inputs) == previous_rounds + 2 and dialogue.inputs[-1][1] == []
            assert "response_basis" in payload(service, sid, events)
            assert "这个观察不能确定" in "".join(event.get("text", "") for event in events)
        finally:
            await service.close()
    asyncio.run(run())
