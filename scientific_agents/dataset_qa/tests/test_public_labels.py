"""Friendly unavailable responses preserve intent without internal task names."""
import asyncio
import json

import pytest

from ..capabilities import OBJECT, TASK
from ..contracts import Limits, QAError
from ..operations import Operations
from ..responses import notice, response_labels, response_operations
from ..service import DatasetQA
from .assertions import assert_handled
from .test_bounded_discovery import SearchBackend, discover, native, page
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, text


def test_changed_description_uses_pre_diagnostic_intent_without_mutating_receipts():
    operations = Operations()
    key = operations.register("查看数据集的内容", {"server": "source", "name": "inspect"})
    labels = {key: "查看数据集的内容"}
    operations.get(key).update(description="PRIVATE_BACKEND_TRACE", state="failed")
    public = response_labels(operations, labels)
    assert public.notice([])=="暂时还无法提供：查看数据集的内容。"
    assert public.get(key)["description"]==labels[key]
    assert operations.get(key)["description"]=="PRIVATE_BACKEND_TRACE"


@pytest.mark.parametrize("label", [None, "数据预览", "质量报告"])
def test_late_second_operation_never_exposes_an_internal_number(label):
    operations = Operations()
    first = operations.register("定位数据集", {"server": "source", "name": "locate"}, required=False)
    second = operations.register("PRIVATE_BACKEND_TRACE", {"server": "source", "name": "inspect"})
    operations.get(second)["state"] = "failed"
    if label:
        operations.get(second)["public_label"] = label
    labels = {first: "定位数据集"}
    public = response_labels(operations, labels)
    value = public.notice([])
    assert "待处理事项" not in value and "PRIVATE_BACKEND_TRACE" not in value
    assert value==(f"暂时还无法提供：{label}。" if label else "")
    writer = response_operations(operations, labels)
    assert writer["items"][1]["description"]==(label or "")


@pytest.mark.parametrize("diagnostic", ["该数据集不支持预览", "unsupported preview", "PRIVATE_BACKEND_TRACE /srv/secret.py"])
def test_opaque_rejection_does_not_guess_recoverability_or_echo_diagnostics(diagnostic):
    reply = notice(QAError("tool_failed", "MCP工具返回错误", detail=[diagnostic]), subject="数据预览")
    assert "数据预览" in reply
    assert not any(value in reply for value in ("稍后", "调整查询范围", "永久", "PRIVATE", diagnostic))
    assert "选择其他数据集" in reply


@pytest.mark.parametrize("label", ["数据预览", "文件结构", "质量报告"])
@pytest.mark.parametrize("corrections", [0, 2])
def test_unavailable_capability_has_named_feedback_without_extra_explanation_calls(engine, label, corrections):
    async def run():
        backend = SearchBackend(lambda query, number: page(range(5) if number==1 else [5], 6))
        backend.catalogue[2].meta["piflow"]["qa"]["label"] = label
        backend.errors_at = {index: "Unsupported content; PRIVATE_BACKEND_TRACE /srv/secret.py" for index in range(3, 4+corrections)}
        preview = native("directory", **{OBJECT: "candidate:1", TASK: {"complete_request": True}})
        dialogue = BareDialogue(discover(), text(), *([preview]*(corrections+1)))
        service = DatasetQA(engine, dialogue, backend.gateway(Limits(max_corrections=corrections)))
        sid = session(service)
        try:
            await collect(service, sid, "Find chemical engineering datasets", "seed")
            request = "查看第一个数据集的内容"
            events = await collect(service, sid, request, "preview")
            task = assert_handled(service, sid, events[-1], "tool_failed")
            reply = "".join(event.get("text", "") for event in events if event["type"]=="message")
            assert reply==f"本次没有取得可展示的{label}。您可以选择其他数据集，或指定其他希望了解的信息。"
            assert not result_cards(events)
            assert len(dialogue.inputs)==3+corrections and len(backend.calls)==3+corrections
            assert backend.calls[-1]==("directory", {"reference": "0"})
            assert events==await collect(service, sid, request, "preview")
            history = json.dumps(await service.get_session("alice", sid), ensure_ascii=False)
            assert reply in history
            assert all(value not in history for value in ("PRIVATE_BACKEND_TRACE", "待处理事项", "/srv/secret.py"))
            payload = json.loads(task["payload"])
            assert "PRIVATE_BACKEND_TRACE" in json.dumps(payload["operations"][0]["attempts"])
        finally:
            await service.close()
    asyncio.run(run())
