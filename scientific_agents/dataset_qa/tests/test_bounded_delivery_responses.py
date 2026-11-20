"""Large delivered artifacts need no speculative interpretation of a preview."""
import asyncio
from copy import deepcopy

import pytest

from ..contracts import Limits
from ..operations import Operations
from ..responses import bounded_delivery_summary, delivery_status
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import goals, text
from .test_independent_outcomes import ContractDialogue, native
from .test_resource_index import Backend, POLICY, node


@pytest.mark.parametrize("case", ["complete", "answer", "search", "pending", "partial", "missing_card",
    "missing_receipt", "not_delivered", "full_view", "support_only", "omitted_preview", "inferred", "implicit"])
def test_bounded_ack_requires_all_requested_results_and_does_not_replace_analysis(case):
    operations = Operations()
    key = operations.register("记录内容", {"server": "arbitrary", "name": "records"}, planned=True)
    operations.start(key, "call")
    operations.finish(key, "call", result_id="saved")
    cards = [{"result_id": "saved", "data": {"records": [{"value": i} for i in range(100)]}}]
    original = deepcopy(cards)
    delivered = ["saved"]
    view = {"final_delivery": [{"result_id": "saved", "model_view_truncated": True}]}
    if case == "answer":
        operations.items[0]["output"] = "answer"
    elif case == "search":
        operations.items[0]["search"] = {"done": True}
    elif case == "inferred":
        operations.items[0]["inferred"] = True
    elif case == "implicit":
        operations.items[0]["planned"] = False
    elif case == "pending":
        operations.items[0]["state"] = "pending"
    elif case == "missing_card":
        cards = []
    elif case == "missing_receipt":
        operations.start(key, "second")
        operations.finish(key, "second", result_id="undisplayed")
    elif case == "not_delivered":
        delivered = []
    elif case == "full_view":
        view["final_delivery"][0]["model_view_truncated"] = False
    elif case == "support_only":
        view = {"answer_evidence": view["final_delivery"]}
    elif case == "omitted_preview":
        view = {"final_delivery": [], "final_delivery_next_offset": 0}
    facts = delivery_status(operations, delivered, cards=cards)
    if case == "partial":
        facts[0]["complete"] = False  # Includes a plan whose desired quantity is not met.
    answer = bounded_delivery_summary(operations, facts, cards, delivered, view)
    assert bool(answer) is (case in {"complete", "omitted_preview"})
    if answer:
        assert "记录内容" in answer and "已为您提供" in answer
    if case != "missing_card":
        assert cards == original


@pytest.mark.parametrize("interpret", [False, True])
def test_full_cards_remain_available_and_explicit_analysis_still_calls_the_model(engine, interpret):
    async def run():
        backend = Backend()
        backend.tree[("one", None)] = [node(str(i), f"record-{i}.json", True) for i in range(80)]
        calls = []

        def finish(messages, definitions):
            calls.append(True)
            return text("按请求解释已提供的记录。")

        dialogue = ContractDialogue(goals({"description": "记录内容", "tool": "list_tree",
            "output": "answer" if interpret else "result"}, calls=[native("list_tree", dataset="one")]),
            finish, finish)
        gateway = backend.gateway()
        gateway.limits = Limits(result_chars=1200)
        service = DatasetQA(engine, dialogue, gateway, index_policy=POLICY)
        sid = session(service)
        try:
            events = await collect(service, sid, "查看 dataset=one 的条目" + ("并解释内容" if interpret else ""))
            assert_completed(service, sid, events[-1])
            cards = result_cards(events)
            saved = service.store.results("alice", sid, events[-1]["task_id"])
            assert saved and len(saved[0]["data"]["data"]["nodes"]) == 80
            if interpret:
                assert calls and not cards
            else:
                assert not calls and len(cards) == 1
                assert cards[0]["data"] == {"items": [saved[0]["data"]]}
                assert "已为您提供" in "".join(event.get("text", "") for event in events)
        finally:
            await service.close()
    asyncio.run(run())
