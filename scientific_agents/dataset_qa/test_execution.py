"""Regressions for convergence, real streaming finalization and rich artifacts."""
import asyncio
import base64
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest

from .context import encode, project, public_result
from .contracts import Limits, Options, QAError, Server
from .mcp import MCPGateway
from .results import ToolResult, evidence
from .service import DatasetQA
from .test_dataset_qa import Backend, Dialogue, action, collect, engine, load, remote, result_cards, session
from ..unified.adapters.dataset_qa import DatasetQAAdapter


@pytest.mark.parametrize("hints,expected_calls", [
    ({"readOnlyHint": True, "idempotentHint": True}, 1),
    ({"readOnlyHint": True}, 1),
    ({}, 1),
])
def test_repeated_calls_converge_and_keep_one_card(engine, hints, expected_calls):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].annotations = hints
        dialogue = Dialogue(load(), *[remote("search", query="气象", count=2) for _ in range(3)],
            AIMessageChunk(content="已取得两个数据集，更多结果尚未获取。"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert len(backend.calls)==expected_calls
        assert sum(v["type"]=="result" for v in values)==1
        assert values[-1]["status"]=="COMPLETED"
        assert "code" not in values[-1]  # No-gain closure does not invalidate completed goals.
        assert dialogue.inputs[-1][1]==[]
        assert "已取得两个数据集" in "".join(v["text"] for v in values if v["type"]=="message")
        assert sum(v.get("stage")=="execute" for v in values)==1
        assert values==await collect(service, sid)  # Reconnect never dispatches again.
        assert len(backend.calls)==expected_calls
    asyncio.run(run())


def test_cache_is_canonical_per_turn_and_never_hides_fresh_sampling(engine):
    from .test_operations import batch, goal
    async def run():
        backend = Backend()
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        backend.catalog["data"][3].annotations = {"readOnlyHint": True, "idempotentHint": False}
        dialogue = Dialogue(load(), batch(["search"], remote("search", query="气象", count=2),
            operations=[goal("search"), goal("sample", output="answer"), goal("again", output="answer")]),
            batch(["search"], remote("search", count=2, query="气象")),
            batch(["sample"], remote("sample", reference="a", count=1)),
            batch(["again"], remote("sample", count=1, reference="a")))
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED"
        assert [c[1] for c in backend.calls]==["search", "sample", "sample"]
        cards = service.store.results("alice", sid, values[-1]["task_id"])
        assert len(cards)==3 and cards[1]["data"]!=cards[2]["data"]
        assert result_cards(values)==[public_result(cards[0])]
        dialogue.responses = [load(), remote("search", query="气象", count=2)]
        await collect(service, sid, rid="fresh-turn")
        assert len(backend.calls)==4
    asyncio.run(run())


def test_pagination_and_changed_parameters_are_not_duplicates(engine):
    async def run():
        backend = Backend()
        backend.catalog["data"][0].inputSchema["properties"]["offset"] = {"type": "integer"}
        backend.catalog["data"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        original = backend.client
        def factory(*args, **kwargs):
            client = original(*args, **kwargs)
            call = client.call_tool
            async def execute(name, arguments, **options):
                backend.items = [{"id": str(arguments.get("offset", arguments.get("query"))), "title": "New evidence"}]
                return await call(name, arguments, **options)
            client.call_tool = execute
            return client
        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = Dialogue(load(), *[remote("search", offset=i) for i in range(4)],
            remote("search", query="另一领域"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        values = await collect(service, sid)
        assert values[-1]["status"]=="COMPLETED"
        assert len(backend.calls)==5 and sum(v["type"]=="result" for v in values)==1
        assert len(service.store.results("alice", sid, values[-1]["task_id"]))==5
        assert len(result_cards(values))==1
    asyncio.run(run())


def test_call_budget_pairs_skipped_parallel_calls_before_finalizing(engine):
    async def run():
        backend = Backend()
        parallel = AIMessageChunk(content="", tool_calls=[
            {"name": "", "args": {"x": i, "y": 2}, "id": str(i)} for i in range(3)])

        def batch(messages, definitions):
            alias = next(v["function"]["name"] for v in definitions if v["function"]["name"].endswith("_multiply"))
            return parallel.model_copy(update={"tool_calls": [{**c, "name": alias} for c in parallel.tool_calls]})

        dialogue = Dialogue(load("compute"), batch, AIMessageChunk(content="当前完成一项计算。"))
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_calls=2)))
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and len(backend.calls)==1
        messages, definitions = dialogue.inputs[-1]
        assert definitions==[]
        paired = [m for m in messages if isinstance(m, ToolMessage) and m.name!="deliver_results"][-3:]
        assert [m.tool_call_id for m in paired]==["0", "1", "2"]
        assert all(json.loads(m.content)["executed"] is False for m in paired[1:])
        assert values[-1]["code"]=="step_limit"
    asyncio.run(run())


def test_repeated_discovery_is_bounded_and_final_failure_keeps_original_reason(engine):
    async def run():
        backend = Backend()
        dialogue = Dialogue(*[action("list_mcp_servers") for _ in range(3)], RuntimeError("offline"))
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert values[-1]["status"]=="FAILED" and not backend.connections
        assert values[-1]["code"]=="no_progress"
        assert dialogue.inputs[-1][1]==[]
        assert any("停止" in v.get("text", "") for v in values)
    asyncio.run(run())


def test_parallel_duplicates_reuse_receipts_and_keep_all_call_pairs(engine):
    async def run():
        backend = Backend()

        def batch(messages, definitions):
            alias = next(v["function"]["name"] for v in definitions if v["function"]["name"].endswith("_multiply"))
            return AIMessageChunk(content="", tool_calls=[
                {"name": alias, "args": {"x": 2, "y": 3}, "id": str(i)} for i in range(8)])

        dialogue = Dialogue(load("compute"), batch)
        service = DatasetQA(engine, dialogue, backend.gateway())
        values = await collect(service, session(service))
        assert len(backend.calls)==1 and sum(v["type"]=="result" for v in values)==1
        assert values[-1]["status"]=="COMPLETED"
        paired = [m for m in dialogue.inputs[-2][0] if isinstance(m, ToolMessage) and m.name!="deliver_results"][-8:]
        assert [m.tool_call_id for m in paired]==[str(i) for i in range(8)]
        assert all(json.loads(m.content)["executed"] is False for m in paired[1:])
    asyncio.run(run())


def test_unavailable_service_is_not_reconnected_repeatedly_in_one_turn(engine):
    async def run():
        backend = Backend()
        attempted = []

        class Unavailable:
            async def __aenter__(self):
                attempted.append("connect")
                raise OSError("offline")

            async def __aexit__(self, *args):
                pass

        gateway = backend.gateway()
        gateway.client_factory = lambda *args, **kwargs: Unavailable()
        dialogue = Dialogue(load(), load(), load())
        service = DatasetQA(engine, dialogue, gateway)
        values = await collect(service, session(service))
        assert attempted==["connect"] and not backend.calls
        assert values[-1]["code"]=="mcp_unavailable"
        assert len(dialogue.inputs)==3  # Other configured services may still be usable; repeated discovery is bounded.
    asyncio.run(run())


def test_budget_final_answer_streams_before_completion(engine):
    async def run():
        backend, gate = Backend(), asyncio.Event()

        class Streaming(Dialogue):
            async def respond(self, messages, definitions):
                self.inputs.append((messages, definitions))
                if definitions:
                    yield action("list_mcp_servers")
                else:
                    yield AIMessageChunk(content="最终答复首段")
                    await gate.wait()
                    yield AIMessageChunk(content="和尾段")

        dialogue = Streaming()
        service = DatasetQA(engine, dialogue, backend.gateway(limits=Limits(max_rounds=1)))
        sid = session(service)
        stream = service.stream("alice", sid, "继续", "turn", Options())

        async def first_final_text():
            async for value in stream:
                if value and "最终答复首段" in value.get("text", ""):
                    return value

        first = await asyncio.wait_for(first_final_text(), 2)
        assert not gate.is_set() and service.store.task("alice", sid, first["task_id"])["status"]=="RUNNING"
        gate.set()
        rest = [v async for v in stream if v is not None]
        assert any(v.get("text")=="和尾段" for v in rest)
        assert rest[-1]["status"]=="FAILED" and dialogue.inputs[-1][1]==[]
    asyncio.run(run())


def test_status_returns_to_execute_while_model_uses_tool_evidence(engine):
    async def run():
        backend, waiting, gate = Backend(), asyncio.Event(), asyncio.Event()

        class Waiting(Dialogue):
            async def respond(self, messages, definitions):
                if len(self.inputs)==2:
                    waiting.set()
                    await gate.wait()
                async for chunk in super().respond(messages, definitions):
                    yield chunk

        service = DatasetQA(engine, Waiting(load(), remote("search")), backend.gateway())
        sid = session(service)
        reader = asyncio.create_task(collect(service, sid))
        await asyncio.wait_for(waiting.wait(), 2)
        tid = service.store.session("alice", sid)["active_task_id"]
        assert service.store.task("alice", sid, tid)["stage"]=="execute"
        gate.set()
        assert (await reader)[-1]["status"]=="COMPLETED"
    asyncio.run(run())


def rich_output():
    binary = base64.b64encode(b"artifact-bytes"*10000).decode("ascii")
    url = "https://example.invalid/image.png?signature="+"s"*40000
    table = {"columns": [{"name": "value", "type": "integer"}], "rows": [[i] for i in range(10000)]}
    return SimpleNamespace(structured_content=table, content=[
        SimpleNamespace(type="text", text=encode(table)),  # MCP JSON mirror.
        SimpleNamespace(type="text", text="图像与采样表格来自本次操作。"),
        SimpleNamespace(type="image", data=binary, mimeType="image/png"),
        SimpleNamespace(type="resource_link", uri=url, name="preview", mimeType="image/png"),
        SimpleNamespace(type="resource", resource={"uri": "mcp://sample.csv", "mimeType": "text/csv", "blob": "YSxiCjEsMg=="}),
    ], is_error=False), binary, url


def test_rich_output_is_complete_in_sse_history_results_and_replay(engine):
    async def run():
        output, binary, url = rich_output()
        backend = Backend()
        original = backend.client

        def factory(*args, **kwargs):
            client = original(*args, **kwargs)

            async def result(*args, **kwargs):
                return output
            client.call_tool = result
            return client

        gateway = backend.gateway()
        gateway.client_factory = factory
        dialogue = Dialogue(load(), remote("preview", reference="a"))
        service = DatasetQA(engine, dialogue, gateway)
        sid = session(service)
        values = await collect(service, sid)
        card = result_cards(values)[0]
        assert card["data"]["items"]==[output.structured_content] and len(card["content"])==4
        assert [b["type"] for b in card["content"]]==["text", "image", "image", "file"]
        assert card["content"][1]["base64"]==binary and card["content"][2]["url"]==url
        assert base64.b64decode(card["content"][1]["base64"])==b"artifact-bytes"*10000
        assert "truncated" not in card
        assert binary not in encode([m.content for m in dialogue.inputs[-1][0]])
        assert len(dialogue.inputs[-1][0][-1].content)<10000
        history = await service.get_session("alice", sid)
        saved = next(i["payload"] for i in history["items"] if i["item_type"]=="RESULT_CARD")
        adapter = DatasetQAAdapter(SimpleNamespace(user="alice",
            extension=SimpleNamespace(session_services={"dataset_qa": service})))
        queried = await adapter.get_results(sid, values[-1]["task_id"])
        assert saved==queried["items"][0]==public_result(card)
        assert values==await collect(service, sid)
    asyncio.run(run())


def test_rich_output_limit_counts_all_blocks_and_does_not_cut_artifacts():
    output, binary, url = rich_output()
    with pytest.raises(QAError, match="超过"):
        ToolResult.from_mcp(output, len(encode(output.structured_content).encode())+10)
    result = ToolResult.from_mcp(output, 2_000_000)
    card = {"result_id": "saved", "view_type": "tool_result", "title": "结果", **result.payload()}
    assert public_result(card)["content"][1]["base64"]==binary
    assert public_result(card)["content"][2]["url"]==url
    model = evidence(card, 1000)
    assert binary not in encode(model) and url not in encode(model)
    assert len(encode(model))<1500 and model["result_id"]=="saved"
    projected, cut = project({"url": url}, 1000)
    assert cut and "url" not in projected


def test_standard_mcp_content_variants_and_mirror_deduplication():
    result = ToolResult.from_mcp(SimpleNamespace(structuredContent={"count": 0}, content=[
        {"type": "text", "text": '{"count":0}'},
        {"type": "resource", "resource": {"uri": "mcp://note", "text": "说明", "mimeType": "text/plain"}},
        {"type": "audio", "data": "YWJj", "mimeType": "audio/wav"},
        {"type": "resource_link", "uri": "https://example.invalid/file.csv", "name": "file", "mimeType": "text/csv"},
    ]), 10000)
    assert result.data=={"count": 0}
    assert [b["type"] for b in result.content]==["text", "audio", "file"]
    assert not any("id" in b for b in result.content)
    assert ToolResult.from_mcp(SimpleNamespace(content=[{"type": "text", "text": "hello"}]), 100).payload()=={"data": "hello"}


def test_real_fastmcp_preserves_structured_data_and_image_together():
    from fastmcp import FastMCP
    from fastmcp.tools.tool import ToolResult as MCPToolResult
    from mcp.types import ImageContent, TextContent
    mcp = FastMCP("rich-result-test")
    png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    @mcp.tool
    def report() -> MCPToolResult:
        return MCPToolResult(content=[TextContent(type="text", text='{"rows":[[0]]}'),
            ImageContent(type="image", data=png, mimeType="image/png")], structured_content={"rows": [[0]]})

    async def run():
        async with MCPGateway({"local": Server(mcp)}).session() as tools:
            alias = (await tools.load("local"))["items"][0]["name"]
            _, result = await tools.call(alias, {})
            assert result.data=={"rows": [[0]]} and len(result.content)==1
            assert result.content[0]["base64"]==png
    asyncio.run(run())
