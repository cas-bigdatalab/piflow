"""Final prose and deterministic links share delivery facts across truncation."""
import asyncio
import json
import logging

from langchain_core.messages import AIMessageChunk
import pytest

from ..context import encode, project
from ..contracts import QAError
from ..dialogue import Dialogue
from ..responses import delivery_links
from ..service import DatasetQA
from .test_dataset_qa import Backend, engine
from .test_reply_link_delivery import card, save_delivery
from .test_terminal_responses import replies, started


class FinalStream(Dialogue):
    def __init__(self, chunks):
        super().__init__(model=object())
        self.chunks = chunks
        self.calls = self.consumed = 0
        self.closed = False
        self.input = None

    async def respond(self, messages, definitions):
        self.calls += 1
        assert not definitions
        self.input = self.budget(messages, definitions)
        try:
            for chunk in self.chunks:
                self.consumed += 1
                if isinstance(chunk, Exception):
                    raise chunk
                yield chunk
        finally:
            self.closed = True


@pytest.mark.parametrize("mode", ["normal", "character_limit", "length", "max_tokens", "timeout"])
def test_final_links_survive_output_limits_without_another_model_request(engine, caplog, mode):
    caplog.set_level(logging.WARNING, logger="flow.dataset_qa")
    url = "https://files.example/result.csv?signature="+"a"*300
    plain = "已整理 result.csv。"
    if mode == "character_limit":
        chunks = [AIMessageChunk(content="说明。"+"x"*15980),
            AIMessageChunk(content=f"\n[下载](<{url}>)."), AIMessageChunk(content="不应继续消费")]
    elif mode in {"length", "max_tokens"}:
        # A full URL without closing Markdown is still an incomplete link.
        chunks = [AIMessageChunk(content=f"{plain}\n[下载](<{url}"),
            AIMessageChunk(content="", response_metadata={"finish_reason": mode})]
    elif mode == "timeout":
        chunks = [AIMessageChunk(content=f"{plain}\n[下载](<{url[:70]}"),
            QAError("model_timeout", "PRIVATE DIAGNOSTIC", 504)]
    else:
        chunks = [AIMessageChunk(content=plain)]

    async def run():
        store, sid, tid = started(engine)
        csv = card("csv", url, "result.csv")
        csv["data"]["resource"].update(format="csv", record_count=27)
        source = card("source", "https://files.example/source.jsonl", "source.jsonl")
        save_delivery(store, sid, tid, [source, csv], delivered=["csv"])
        dialogue = FinalStream(chunks)
        service = DatasetQA(engine, dialogue, Backend().gateway())
        answer = {"text": ""}

        async def phase(*args):
            pass

        try:
            await service._final_reply("alice", sid, tid,
                dialogue.messages("将这些记录保存为 CSV", {}), answer, phase)
            assert store.finish("alice", sid, tid, "COMPLETED", message=answer["text"])
            _, reply, saved = replies(store, sid, tid)
            assert saved == [reply]
            assert f"(<{url}>)" in reply
            assert source["data"]["downloadUrl"] not in reply
            assert "PRIVATE DIAGNOSTIC" not in reply
            assert dialogue.calls == 1 and dialogue.closed
            if mode == "character_limit":
                assert len(answer["text"]) == 16000
                assert dialogue.consumed == 2
            if mode in {"character_limit", "length", "max_tokens"}:
                assert f"reason={mode}" in caplog.text
            context = json.loads(dialogue.input[1].content)
            manifest = context["delivery_links"]["items"]
            assert len(manifest) == 1 and manifest[0]["result_id"] == "csv"
            assert manifest[0]["label"] == "result.csv"
            assert manifest[0]["format"] == "csv" and manifest[0]["record_count"] == 27
            assert "url" not in manifest[0]
            assert "runtime attaches these clickable links" in dialogue.input[0].content
        finally:
            await service.close()
    asyncio.run(run())


def test_url_is_omitted_whole_by_context_projection_not_clipped():
    url = "https://files.example/"+"signature"*1000
    value, cut = project({"downloadUrl": url}, 100)
    assert cut and url not in encode(value) and "https://" not in encode(value)


def test_delivery_facts_survive_context_budget_and_exclude_urls():
    source = card("csv", "https://files.example/signed.csv")
    links = [{key: value for key, value in link.items() if key!="url"} for link in delivery_links([source])]
    context = {"delivery_links": {"items": links, "total": 1},
        "history": [{"role": "user", "text": "Old optional history "*10000}]}
    dialogue = Dialogue(model=object())
    bounded = dialogue.budget(dialogue.messages("保存为 CSV", context), [])
    assert json.loads(bounded[1].content)["delivery_links"] == context["delivery_links"]
