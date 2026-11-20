"""Exercise complete decision traces with competing historical file evidence."""
import asyncio
import json

from langchain_core.messages import ToolMessage

from ..service import DatasetQA
from .test_artifact_catalogue import register
from .test_dataset_qa import action, collect, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, configured, payload, text
from .test_independent_outcomes import ContractDialogue


def test_new_search_recovers_from_saved_file_loop_without_using_its_evidence(engine):
    async def run():
        backend = configured()
        def read(messages, definitions):
            value = next(json.loads(m.content) for m in reversed(messages)
                if isinstance(m, ToolMessage) and m.name == "find_artifacts")
            return action("read_result", result_id=value["result_id"], path="/items")
        def recover(messages, definitions):
            assert "find_artifacts" not in {d["function"]["name"] for d in definitions}
            assert json.loads(messages[1].content)["discovery_state"]["pending"]
            return load()
        def final(messages, definitions):
            assert not definitions
            raw = " ".join(str(m.content) for m in messages)
            assert "pubchem-compounds.jsonl" not in raw and "dataset.csv" not in raw
            return text("已为您找到相关数据集。")
        dialogue = ContractDialogue(action("find_artifacts"), read,
            action("find_artifacts", format="csv"), action("find_artifacts", query="absent-a"),
            action("find_artifacts", query="absent-b"), action("find_artifacts", query="absent-c"),
            recover, remote("search", query="观测站"), action("deliver_results"), final)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            register(service.artifacts, "csv", name="dataset.csv")
            register(service.artifacts, "jsonl", name="pubchem-compounds.jsonl", format="jsonl")
            sid = session(service)
            events = await collect(service, sid, "我想找共和县光伏观测站相关的数据集")
            assert not payload(service, sid, events).get("error")
            assert len(backend.calls) == 1 and backend.calls[0][1] == "search"
            assert len(result_cards(events)) == 1
            initial = json.loads(dialogue.inputs[0][0][1].content)
            assert not initial.get("available_artifacts") and "artifact_catalog" in initial
            assert events == await collect(service, sid, "我想找共和县光伏观测站相关的数据集")
            assert len(backend.calls) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_no_business_evidence_cannot_turn_catalogue_into_final_search_explanation(engine):
    async def run():
        backend = configured()
        # An adversarial model repeats an action after runtime removed it.
        dialogue = BareDialogue(*[action("find_artifacts", query="absent") for _ in range(6)])
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            register(service.artifacts, "old", name="old.csv")
            sid = session(service)
            events = await collect(service, sid, "查找新数据")
            assert not backend.calls and not result_cards(events)
            assert all(definitions for _, definitions in dialogue.inputs)
            reply = "".join(e.get("text", "") for e in events)
            assert "缩小范围" not in reply and "old.csv" not in reply
        finally:
            await service.close()
    asyncio.run(run())
