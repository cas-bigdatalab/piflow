"""Independent receipts and conservative, source-backed delivery projections."""
from copy import deepcopy

import pytest

from ..context import public_result
from ..contracts import QAError
from ..operations import Operation, Operations
from ..results import collection_paths, combine_results


def ledger(*keys):
    operations = Operations()
    operations.declare([Operation(id=key, description="Outcome "+key) for key in keys])
    return operations


def succeed(operations, key, result_id, *, presentation=None, target=None, safe=True):
    operations.get(key)["target"] = target
    operations.start(key, result_id, {"server": "service", "name": "resource"},
        retry_safe=safe, invocation="invocation-"+result_id, presentation=presentation)
    operations.finish(key, result_id, result_id=result_id)


@pytest.mark.parametrize("code,state", [
    ("invalid_parameters", "pending"), ("tool_failed", "failed"), ("execution_unknown", "unknown"),
])
def test_later_failed_attempt_keeps_successful_delivery_without_claiming_completion(code, state):
    operations = ledger("find")
    succeed(operations, "find", "good")
    successful = deepcopy(operations.get("find")["attempts"][0])
    operations.start("find", "later", {"server": "service", "name": "resource"}, retry_safe=True)
    operations.finish("find", "later", error=QAError(code, "Specific failure"))

    assert operations.get("find")["state"]==state
    assert operations.get("find")["attempts"][0]==successful
    assert operations.delivery_ids()==["good"]
    operations.validate_delivery(["good"], partial=True)
    assert operations.error(["good"]) is not None
    notice = operations.notice(["good"])
    assert "已取得部分信息" in notice and "尚有内容未完成" in notice
    assert "已为您完成" not in notice


def test_supporting_and_historical_results_do_not_gain_delivery_ownership():
    operations = ledger("requested", "supporting")
    operations.get("supporting")["required"] = False
    succeed(operations, "requested", "requested-result")
    succeed(operations, "supporting", "supporting-result")
    assert operations.delivery_ids()==["requested-result"]
    for result_id in ("supporting-result", "history-result"):
        with pytest.raises(QAError, match="交付结果必须"):
            operations.validate_delivery([result_id], partial=True)


def test_answer_evidence_and_artifact_selection_stay_distinct():
    operations = ledger("artifact", "answer")
    operations.get("answer")["output"] = "answer"
    succeed(operations, "artifact", "card")
    succeed(operations, "answer", "evidence")
    assert operations.delivery_ids()==["card"]
    assert operations.delivery_ids("answer")==["evidence"]
    operations.validate_delivery(["card"])
    assert operations.error(["card"]) is None


def cards_and_receipts(*, kind="object", path="", declared=True):
    operations = ledger("a", "b")
    cards = []
    descriptor = {"family": "service/resource", "kind": kind, "path": path} if declared else None
    for key in ("a", "b"):
        row = {"id": key, "title": "Resource "+key}
        data = {"items": [row]} if kind=="collection" else {"data": row} if path else row
        cards.append({"result_id": key, "view_type": "data", "title": "Resource", "data": data})
        succeed(operations, key, key, presentation=descriptor,
            target={"result_id": "candidates", "path": "/items/"+str(len(cards)-1), "kind": "object"})
    return cards, operations


@pytest.mark.parametrize("kind,path", [("object", ""), ("object", "/data"), ("collection", "/items")])
def test_declared_homogeneous_artifacts_from_distinct_targets_share_one_existing_card(kind, path):
    cards, operations = cards_and_receipts(kind=kind, path=path)
    originals = deepcopy(cards)
    paths = collection_paths(cards, operations)
    combined = combine_results(cards, paths, "delivery", "")
    public = public_result(combined)
    assert set(public)=={"result_id", "view_type", "title", "data"}
    assert public["data"]["items"]==[
        {"id": "a", "title": "Resource a"}, {"id": "b", "title": "Resource b"}]
    assert cards==originals
    assert set(operations.delivery_ids())=={"a", "b"}


def test_declared_family_preserves_optional_fields_and_exact_record_deduplication():
    cards, operations = cards_and_receipts(kind="collection", path="/items")
    cards[1]["data"]["items"].insert(0, deepcopy(cards[0]["data"]["items"][0]))
    cards[1]["data"]["items"][1]["size"] = 3
    first = {"type": "text", "text": "Shared source note"}
    cards[0]["content"] = [first]
    cards[1]["content"] = [deepcopy(first)]
    combined = combine_results(cards, collection_paths(cards, operations), "delivery", "")
    assert len(combined["data"])==2 and combined["data"][1]["size"]==3
    assert combined["content"]==[first]
    assert len(operations.result_ids(operations.get("a")))==1


@pytest.mark.parametrize("difference", ["family", "kind", "view", "tool", "unsafe", "missing", "scalar", "path", "descriptor"])
def test_declared_presentations_do_not_combine_unproven_or_heterogeneous_artifacts(difference):
    cards, operations = cards_and_receipts()
    attempt = operations.get("b")["attempts"][0]
    if difference=="family":
        attempt["presentation"]["family"] = "different/family"
    elif difference=="kind":
        attempt["presentation"]["kind"] = "collection"
        cards[1]["data"] = [cards[1]["data"]]
    elif difference=="view":
        cards[1]["view_type"] = "directory"
    elif difference=="tool":
        attempt["tool"]["name"] = "unrelated"
    elif difference=="unsafe":
        attempt["retry_safe"] = False
    elif difference=="missing":
        attempt["state"] = "unknown"
    elif difference=="scalar":
        cards[1]["data"] = "not an object"
    elif difference=="path":
        attempt["presentation"]["path"] = "/absent"
    else:
        attempt["presentation"] = {"family": "service/resource", "kind": "unknown", "path": ""}
    with pytest.raises(QAError) as raised:
        collection_paths(cards, operations)
    assert raised.value.code=="invalid_delivery"


def test_legacy_receipts_keep_the_original_conservative_collection_contract():
    cards, operations = cards_and_receipts(kind="collection", path="/items", declared=False)
    with pytest.raises(QAError, match="不能自动合并"):
        collection_paths(cards, operations)
    operations.get("b")["target"] = operations.get("a")["target"]
    assert collection_paths(cards, operations)=={"a": "/items", "b": "/items"}
    cards[1]["data"] = {"items": [{"url": "https://example.invalid/file"}]}
    with pytest.raises(QAError, match="不能自动合并"):
        collection_paths(cards, operations)


def test_object_projection_requires_a_declaration_not_a_legacy_merge_pointer():
    cards, operations = cards_and_receipts(declared=False)
    with pytest.raises(QAError, match="对象列表"):
        collection_paths(cards, operations)
    with pytest.raises(QAError, match="数组"):
        combine_results(cards, "", "delivery", "")


def test_empty_declared_collections_remain_a_valid_noninvented_result():
    cards, operations = cards_and_receipts(kind="collection", path="/items")
    for card in cards:
        card["data"]["items"] = []
    combined = combine_results(cards, collection_paths(cards, operations), "delivery", "")
    assert public_result(combined)["data"]=={"items": []}


def test_presentation_snapshots_are_owned_by_the_execution_receipt():
    operations = ledger("a")
    descriptor = {"family": "service/resource", "kind": "object", "path": ""}
    succeed(operations, "a", "a", presentation=descriptor)
    descriptor["path"] = "/mutated"
    assert operations.get("a")["attempts"][0]["presentation"]["path"]==""
