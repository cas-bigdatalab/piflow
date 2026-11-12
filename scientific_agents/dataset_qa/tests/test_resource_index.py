"""Directory index isolation, bounded traversal and immutable reference bridges."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
import threading

from langchain_core.messages import AIMessageChunk, ToolMessage
import pytest
from sqlalchemy import update

from ..capabilities import OBJECT, TASK, profile
from ..contracts import QAError, Server
from ..mcp import MCPGateway, Tool
from ..resource_index.model import DirectorySpec, IndexPolicy, source_identity
from ..resource_index.store import IndexStore, ROOT
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import action, collect, definition, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, text

SPEC = dict(identity=["dataset"], parent="folder", nodes=["/nodes", "/data/nodes"],
    node_id="/key", name="/filename", is_file="/leaf", download_url="/url", status=["/code"])
DIRECTORY = dict(bind={"dataset": ["/identity"]}, directory=SPEC, atomic=True)
READ = dict(bind={"url": ["/url"]}, atomic=True, target_kind="file")
# Successful traversal waits for completion, not a sub-second scheduling SLA.
# Timeout/cancellation cases below supply their own deliberately short bounds.
POLICY = IndexPolicy(poll_seconds=0.02, lookup_wait=3, request_timeout=1, lease_seconds=4)


def node(key, name, leaf=False):
    return {"key": key, "filename": name, "leaf": leaf,
        "url": "https://example.invalid/"+key+".jsonl" if leaf else None}


def directory_tool():
    return Tool("arbitrary", "list_tree", "List directory", {"type": "object", "properties": {
        "dataset": {"type": "string"}, "folder": {"type": ["string", "null"], "default": None}},
        "required": ["dataset"]}, {"readOnlyHint": True, "idempotentHint": True}, {"piflow": {"qa": DIRECTORY}})


def seed(store, dataset="one", rows=None, user="alice"):
    return store.observe(user, directory_tool(), source_identity(Server("source")), {"dataset": dataset, "folder": None},
        {"nodes": rows if rows is not None else [node("folder", "nested")]}, {"identity": dataset, "title": "Dataset "+dataset})


SOURCES = {"arbitrary": source_identity(Server("source"))}


class Backend:
    def __init__(self):
        self.calls, self.gate, self.error = [], None, False
        self.tree = {("one", None): [node("folder", "nested")],
            ("one", "folder"): [node("deeper", "inside")],
            ("one", "deeper"): [node("records", "measurements.jsonl", True)]}
        directory = directory_tool()
        self.tools = [definition(directory.name, directory.schema["properties"], ["dataset"], directory.annotations),
            definition("read_file", {"url": {"type": "string"}, "size": {"type": "integer", "default": 3}}, ["url"], directory.annotations),
            definition("dataset_info", {"dataset": {"type": "string"}}, ["dataset"], directory.annotations)]
        for tool, descriptor in zip(self.tools, [DIRECTORY, READ, {"bind": {"dataset": ["/identity"]}, "atomic": True}]):
            tool.meta = {"piflow": {"qa": descriptor, "view_type": "directory" if tool.name=="list_tree" else "table"}}

    def gateway(self):
        return MCPGateway({"arbitrary": Server("source")}, client_factory=self.client)

    def client(self, target, **kwargs):
        owner = self

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def list_tools(self):
                return owner.tools

            async def call_tool(self, name, arguments, **kwargs):
                owner.calls.append((name, deepcopy(arguments)))
                if name=="list_tree":
                    if owner.gate:
                        await owner.gate.wait()
                    if owner.error:
                        return SimpleNamespace(is_error=True, content=[])
                    data = {"code": 200, "data": {"nodes": owner.tree[(arguments["dataset"], arguments.get("folder"))]}}
                elif name=="read_file":
                    data = {"schema": [{"name": "value", "type": "number"}], "data": [{"value": 2}], "url": arguments["url"]}
                else:
                    data = {"identity": arguments["dataset"], "description": "Metadata"}
                return SimpleNamespace(is_error=False, structured_content=data)
        return Client()


async def populate(service, backend):
    await service.resources.observe("alice", directory_tool(), {"dataset": "one", "folder": None},
        {"nodes": backend.tree[("one", None)]}, {"identity": "one", "title": "Dataset one"})
    result = await service.resources.lookup("alice", "measurements.jsonl")
    assert result["complete"] and len(result["items"])==1
    return result["items"][0]["scope"]


def test_declared_envelopes_and_business_status():
    spec = DirectorySpec(**SPEC)
    row = node("x", "a.json", True)
    assert spec.rows({"nodes": [row]})[0]["raw"]==row
    assert spec.rows({"data": {"nodes": [row]}})[0]["pointer"]=="/data/nodes/0"
    for bad in [{"code": 500, "nodes": []}, {"nodes": [], "data": {"nodes": []}}, {"data": []},
                {"nodes": [{"key": "x", "filename": "a", "leaf": "true"}]}]:
        with pytest.raises(QAError):
            spec.rows(bad)


def test_store_is_persistent_user_and_source_scoped(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    key = seed(store, rows=[node("x", "same.json", True)])
    other = IndexStore(engine, store.lock, POLICY)
    assert other.lookup("alice", SOURCES, "same.json")["complete"]
    assert not other.lookup("bob", SOURCES, "same.json")["items"]
    assert not other.lookup("alice", {"arbitrary": "changed"}, "same.json")["items"]
    with pytest.raises(QAError):
        other.scope("bob", key, SOURCES)
    assert len(other.scopes_for("alice", SOURCES, record={"identity": "one"}))==1
    assert not other.scopes_for("alice", SOURCES, record={"identity": None})


def test_partial_matches_never_prove_uniqueness(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    seed(store, rows=[node("x", "same.json", True), node("dir", "more")])
    assert not store.lookup("alice", SOURCES, "same.json")["complete"]
    job = store.claim(SOURCES)
    store.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node("y", "same.json", True)]}))
    result = store.lookup("alice", SOURCES, "same.json")
    assert result["complete"] and len(result["items"])==2


def test_leases_bound_workers_and_recover_expired_claims(engine):
    store = IndexStore(engine, threading.RLock(), replace(POLICY, workers=1))
    seed(store)
    seed(store, "two")
    first = store.claim(SOURCES)
    second_store = IndexStore(engine, store.lock, replace(POLICY, workers=1))
    assert second_store.claim(SOURCES) is None
    with store.transaction() as conn:
        conn.execute(update(store.slots).values(lease=0))
        conn.execute(update(store.scopes).values(lease=0))
    replacement = second_store.claim(SOURCES)
    assert replacement and replacement["owner"]!=first["owner"]
    store.finish(first, [])  # Late worker cannot overwrite a replacement.
    assert second_store.claim(SOURCES) is None
    second_store.release(replacement)
    assert second_store.claim(SOURCES)


def test_cycles_limits_and_failed_refresh_do_not_erase_snapshot(engine):
    store = IndexStore(engine, threading.RLock(), replace(POLICY, max_nodes=4))
    key = seed(store, rows=[node("old", "old.json", True)])
    store.refresh("alice", key, SOURCES, full=True)
    job = store.claim(SOURCES)
    store.finish(job, error="tool_failed")
    result = store.lookup("alice", SOURCES, "old.json")
    assert len(result["items"])==1 and not result["complete"]
    store.refresh("alice", key, SOURCES, full=True)
    job = store.claim(SOURCES)
    with pytest.raises(QAError):
        store.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node(str(i), str(i)) for i in range(5)]}))
    store.finish(job, error="index_limit")
    assert store.lookup("alice", SOURCES, "old.json")["items"]


def test_background_walk_does_not_change_conversation_and_refresh_is_on_demand(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=POLICY)
        sid = session(service)
        before = service.store.session("alice", sid)
        key = await populate(service, backend)
        assert service.store.session("alice", sid)==before
        assert service.store.results("alice", sid)==[]
        assert [args["folder"] for _, args in backend.calls]==["folder", "deeper"]
        await service.resources.lookup("alice", "measurements.jsonl")
        assert len(backend.calls)==2
        with service.resources.store.transaction() as conn:
            conn.execute(update(service.resources.store.nodes).where(service.resources.store.nodes.c.kind=="file").values(observed=0))
        result = await service.resources.lookup("alice", "measurements.jsonl")
        assert result["items"][0]["fresh"]
        assert backend.calls[-1]==("list_tree", {"dataset": "one", "folder": "deeper"})
        await service.resources.lookup("alice", "measurements.jsonl", scope_id=key, refresh=True)
        assert any(args.get("folder") is None for _, args in backend.calls)
        await service.close()
    asyncio.run(run())


def resolved_call(messages, definitions):
    result = next(json.loads(message.content) for message in reversed(messages)
        if isinstance(message, ToolMessage) and message.name=="resolve_resource")
    assert result["status"]=="resolved"
    return remote("read_file", **{OBJECT: result["object"], TASK: {"complete_request": True}})(messages, definitions)


def locate(name, **arguments):
    return AIMessageChunk(content="", tool_calls=[{"name": "resolve_resource", "args": {"name": name, **arguments}, "id": "locate"}])


def test_new_session_resolves_nested_file_and_preserves_public_contract(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load("arbitrary"), locate("measurements.jsonl"), resolved_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        await populate(service, backend)
        sid = session(service)
        values = await collect(service, sid, "查看measurements.jsonl的schema")
        assert_completed(service, None, values[-1])
        cards = result_cards(values)
        assert len(cards)==1 and set(cards[0])=={"result_id", "view_type", "title", "data"}
        assert cards[0]["data"]["items"][0]["schema"]==[{"name": "value", "type": "number"}]
        assert backend.calls[-1]==("read_file", {"url": "https://example.invalid/records.jsonl", "size": 3})
        history = await service.get_session("alice", sid)
        assert all(item["item_type"]!="REFERENCE_EVIDENCE" for item in history["items"])
        assert len(service.store.results("alice", sid))==1
        assert len(service.store.result_refs("alice", sid, 0, 20)[0])==1
        context = json.loads(service.store.session("alice", sid)["context"])
        assert context["references"]["current"]["result_id"].startswith("resource-")
        assert "candidates" not in context["references"] and not context["references"].get("selected")
        dialogue.responses = [remote("dataset_info", **{TASK: {"complete_request": True}}), text()]
        again = await collect(service, sid, "这个文件所属数据集的详情", "next")
        assert_completed(service, None, again[-1])
        assert backend.calls[-1]==("dataset_info", {"dataset": "one"})
        await service.close()
    asyncio.run(run())


def test_resolution_timeout_does_not_expose_preparation_or_read_arbitrary_match(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        dialogue = BareDialogue(locate("same.json"),
            action("respond_from_context", mode="conversation", reason="索引仍在创建，需要用户等待"), text("本次没有取得该文件的内容。"))
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=replace(POLICY, lookup_wait=0.02))
        seed(service.resources.store, rows=[node("x", "same.json", True), node("dir", "more")])
        sid = session(service)
        values = await collect(service, sid, "看same.json的schema")
        assert_completed(service, None, values[-1])
        result = next(json.loads(m.content) for m in dialogue.inputs[1][0] if isinstance(m, ToolMessage))
        assert result["status"]=="unavailable" and "object" not in result
        final_context = json.loads(dialogue.inputs[-1][0][1].content)
        assert "reason" not in final_context["response_basis"]
        assert final_context["resource_requests"][0]["status"]=="unavailable"
        public = json.dumps(values, ensure_ascii=False)
        assert not any(term in public for term in ["索引", "后台", "等待", "building"])
        assert not result_cards(values)
        assert all(name!="read_file" for name, _ in backend.calls)
        await service.close()
    asyncio.run(run())


def test_file_request_waits_internally_then_continues_without_another_user_turn(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        dialogue = BareDialogue(load("arbitrary"), locate("measurements.jsonl"), resolved_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=replace(POLICY,
            lookup_wait=2, request_timeout=3, lease_seconds=8))
        seed(service.resources.store)
        sid = session(service)
        events = []

        async def consume():
            from ..contracts import Options
            async for event in service.stream("alice", sid, "查看measurements.jsonl的schema", "wait", Options()):
                if event is not None:
                    events.append(event)

        task = asyncio.create_task(consume())
        try:
            for _ in range(100):
                if backend.calls:
                    break
                await asyncio.sleep(0.005)
            assert backend.calls and not task.done()
            await asyncio.sleep(0.05)
            assert len(dialogue.inputs)==2  # No model polling or premature final reply.
            assert not any(event["type"] in {"result", "message"} for event in events)
            backend.gate.set()
            await asyncio.wait_for(task, 2)
            assert_completed(service, None, events[-1])
            assert len(result_cards(events))==1
            assert [name for name, _ in backend.calls]==["list_tree", "list_tree", "read_file"]
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await service.close()
    asyncio.run(run())


def test_waiters_share_background_work_and_cancellation_is_prompt(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=replace(POLICY,
            lookup_wait=30, request_timeout=3, lease_seconds=8))
        seed(service.resources.store)
        cancelled = asyncio.create_task(service.resources.lookup("alice", "measurements.jsonl"))
        surviving = asyncio.create_task(service.resources.lookup("alice", "measurements.jsonl"))
        try:
            for _ in range(100):
                if backend.calls:
                    break
                await asyncio.sleep(0.005)
            cancelled.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(cancelled, 0.5)
            assert not surviving.done()
            backend.gate.set()
            assert (await asyncio.wait_for(surviving, 2))["complete"]
            assert len(backend.calls)==2
        finally:
            for task in (cancelled, surviving):
                task.cancel()
            await asyncio.gather(cancelled, surviving, return_exceptions=True)
            await service.close()
    asyncio.run(run())


def test_successful_directory_result_triggers_walk_during_answer_generation(engine):
    async def run():
        backend = Backend()
        expanded = asyncio.Event()
        original = backend.client

        def client(*args, **kwargs):
            instance = original(*args, **kwargs)
            call = instance.call_tool

            async def record(name, arguments, **options):
                output = await call(name, arguments, **options)
                if name=="list_tree" and arguments.get("folder"):
                    expanded.set()
                return output
            instance.call_tool = record
            return instance

        class WaitingAnswer(BareDialogue):
            async def respond(self, messages, definitions):
                if not definitions:
                    await asyncio.wait_for(expanded.wait(), 1)
                async for chunk in super().respond(messages, definitions):
                    yield chunk

        gateway = backend.gateway()
        gateway.client_factory = client
        dialogue = WaitingAnswer(load("arbitrary"), remote("list_tree", dataset="one", **{TASK: {"complete_request": True}}), text())
        service = DatasetQA(engine, dialogue, gateway, index_policy=POLICY)
        try:
            result = await collect(service, session(service), "查看one目录")
            assert_completed(service, None, result[-1])
            assert expanded.is_set() and service.active_mcp_calls==0
            assert len(result_cards(result))==1
        finally:
            await service.close()
    asyncio.run(run())


def test_directory_foreground_shape_and_background_are_independent(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load("arbitrary"), remote("list_tree", dataset="one", **{TASK: {"complete_request": True}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        values = await collect(service, sid, "查看one的目录")
        assert_completed(service, None, values[-1])
        card, = result_cards(values)
        assert card["data"]["items"]==[{"code": 200, "data": {"nodes": backend.tree[("one", None)]}}]
        assert len(service.store.results("alice", sid))==1
        result = await service.resources.lookup("alice", "measurements.jsonl")
        assert result["complete"]
        assert len(service.store.results("alice", sid))==1
        await service.close()
    asyncio.run(run())


def test_ambiguous_names_require_choice_then_resume_in_chosen_dataset(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(locate("shared.json"), action("request_input", missing="同名文件所属数据集",
            question="要查看哪个数据集中的 shared.json？", options=["Dataset one", "Dataset two"]))
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        seed(service.resources.store, rows=[node("a", "shared.json", True)])
        seed(service.resources.store, "two", [node("b", "shared.json", True)])
        sid = session(service)
        first = await collect(service, sid, "查看shared.json的schema")
        assert service.store.task("alice", sid, first[-1]["task_id"])["status"]=="WAITING_INPUT"
        observation = next(json.loads(m.content) for m in dialogue.inputs[1][0] if isinstance(m, ToolMessage))
        assert observation["status"]=="ambiguous" and "object" not in observation
        dialogue.responses = [action("remember", continuation="continue"), load("arbitrary"),
            locate("shared.json", dataset="Dataset two"), resolved_call, text()]
        second = await collect(service, sid, "Dataset two", "choice")
        assert_completed(service, None, second[-1])
        assert backend.calls==[("read_file", {"url": "https://example.invalid/b.jsonl", "size": 3})]
        await service.close()
    asyncio.run(run())


def test_current_scope_prevents_cross_dataset_fallback(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load("arbitrary"), locate("shared.json"), resolved_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        seed(service.resources.store, rows=[node("a", "shared.json", True)])
        seed(service.resources.store, "two", [node("b", "other.json", True)])
        sid = session(service)
        await collect(service, sid, "看shared.json")
        dialogue.responses = [locate("other.json"), action("respond_from_context", mode="conversation", reason="当前数据集无此文件"), text()]
        await collect(service, sid, "看other.json", "other")
        observation = next(json.loads(m.content) for m in dialogue.inputs[-2][0] if isinstance(m, ToolMessage))
        assert observation["status"]=="not_found" and not observation["items"]
        assert len(backend.calls)==1
        await service.close()
    asyncio.run(run())


def test_index_restart_continues_pending_work_and_shuts_down_cleanly(engine):
    async def run():
        backend = Backend()
        backend.gate = asyncio.Event()
        first = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=POLICY)
        seed(first.resources.store)
        first.resources.start()
        for _ in range(100):
            if backend.calls:
                break
            await asyncio.sleep(0.005)
        assert backend.calls
        await first.close()
        assert not first.resources.workers
        backend.gate.set()
        second = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=POLICY)
        result = await second.resources.lookup("alice", "measurements.jsonl")
        assert result["complete"] and len(result["items"])==1
        await second.close()
    asyncio.run(run())


def test_schema_errors_do_not_retry_or_break_foreground_and_lookup_is_bounded(engine):
    async def run():
        backend = Backend()
        backend.error = True
        service = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=replace(POLICY, lookup_wait=0.03))
        seed(service.resources.store)
        result = await service.resources.lookup("alice", "unknown.json")
        assert not result["complete"]
        first_count = len(backend.calls)
        assert first_count==1
        await service.resources.lookup("alice", "unknown.json")
        assert len(backend.calls)==first_count
        assert not service.store.results("alice", session(service))
        await service.close()
    asyncio.run(run())


def test_rename_and_cycles_use_node_relationships_not_path_prefixes(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    key = seed(store, rows=[node("folder", "a/b")])
    job = store.claim(SOURCES)
    store.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node("x", "sample.json", True)]}))
    assert store.lookup("alice", SOURCES, "a/b/sample.json")["complete"]
    seed(store, rows=[node("folder", "renamed")])
    assert not store.lookup("alice", SOURCES, "sample.json")["complete"]
    job = store.claim(SOURCES)
    with pytest.raises(QAError):
        store.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node("folder", "cycle")]}))
    store.finish(job, error="invalid_schema")
    assert store.scope("alice", key, SOURCES)["state"]=="partial"


def test_foreground_observation_wins_over_late_background_response(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    key = seed(store)
    job = store.claim(SOURCES)
    store.observe("alice", directory_tool(), SOURCES["arbitrary"], {"dataset": "one", "folder": "folder"},
        {"nodes": [node("new", "new.json", True)]}, {"identity": "one"})
    store.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node("old", "old.json", True)]}))
    assert store.lookup("alice", SOURCES, "new.json")["complete"]
    assert not store.lookup("alice", SOURCES, "old.json")["items"]
    assert store.scope("alice", key, SOURCES)["owner"] is None


def test_live_profiles_bind_urls_without_changing_native_schema():
    file = Tool("piflow-corpus", "read_corpus_file_records", "File content", {
        "type": "object", "properties": {"download_url": {"type": "string"}, "size": {"type": "integer", "default": 5}},
        "required": ["download_url"]}, {}, {})
    from ..capabilities import inputs
    assert profile(file).target_kind=="file"
    assert inputs(file, {}, {"downloadUrl": "https://host/a.jsonl"})=={"download_url": "https://host/a.jsonl", "size": 5}
    assert file.schema["required"]==["download_url"]


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("tool,helper,expected", [
    ("get_corpus_file_schema", "get_file_schema", {"schema": {"properties": {"value": {"type": "integer"}}}}),
    ("read_corpus_file_records", "get_file_records", {"data": [{"value": 1}], "returnedCount": 1}),
])
def test_real_mcp_nested_directory_to_file_content(engine, monkeypatch, wrapped, tool, helper, expected):
    from mcp_servers import corpus_mcp

    calls = []

    def directory(cstr, file_id=None):
        calls.append(("directory", cstr, file_id))
        data = {"code": 200, "data": [{"fileId": "nested" if file_id is None else "nested/data.jsonl",
            "name": "nested" if file_id is None else "data.jsonl", "isFile": file_id is not None,
            "downloadUrl": None if file_id is None else "https://example.invalid/data.jsonl"}]}
        return {"mode": "directory", "data": data} if wrapped else data

    def content(download_url, **arguments):
        calls.append(("file", download_url, arguments))
        return deepcopy(expected)

    monkeypatch.setattr(corpus_mcp, "get_dataset_directory", directory)
    monkeypatch.setattr(corpus_mcp, helper, content)

    async def run():
        dialogue = BareDialogue(load("piflow-corpus", query="get_corpus_dataset_directory"),
            remote("get_corpus_dataset_directory", cstr="sample-id", **{TASK: {"complete_request": True}}), text())
        service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(corpus_mcp.mcp)}), index_policy=POLICY)
        first = await collect(service, session(service), "查看sample-id的数据目录")
        assert_completed(service, None, first[-1])
        assert result_cards(first)[0]["data"]["items"][0]==directory("sample-id")
        await service.resources.lookup("alice", "data.jsonl")

        def read(messages, definitions):
            value = next(json.loads(m.content) for m in reversed(messages) if isinstance(m, ToolMessage) and m.name=="resolve_resource")
            assert value["status"]=="resolved"
            return remote(tool, **{OBJECT: value["object"], TASK: {"complete_request": True}})(messages, definitions)

        dialogue.responses = [load("piflow-corpus", query=tool), locate("data.jsonl"), read, text()]
        result = await collect(service, session(service, request="new-session"), "查看data.jsonl的schema" if helper=="get_file_schema" else "查看data.jsonl的样例")
        assert_completed(service, None, result[-1])
        assert calls[-1]==("file", "https://example.invalid/data.jsonl", {} if helper=="get_file_schema" else {"size": 5})
        assert result_cards(result)[0]["data"]["items"][0]==expected
        await service.close()
    asyncio.run(run())


def test_refresh_does_not_mutate_saved_references_or_repeat_within_turn(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load("arbitrary"), locate("measurements.jsonl"), resolved_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        await populate(service, backend)
        sid = session(service)
        await collect(service, sid, "看measurements.jsonl")
        old_ref = json.loads(service.store.session("alice", sid)["context"])["references"]["current"]
        saved = service.store.selected_results("alice", sid, [old_ref["result_id"]])[0]
        backend.tree[("one", "deeper")][0]["url"] = "https://example.invalid/renewed.jsonl"
        with service.resources.store.transaction() as conn:
            conn.execute(update(service.resources.store.nodes).where(service.resources.store.nodes.c.kind=="file").values(observed=0))
        dialogue.responses = [locate("measurements.jsonl"), locate("measurements.jsonl"), resolved_call, text()]
        second = await collect(service, sid, "再看measurements.jsonl", "again")
        assert_completed(service, None, second[-1])
        assert service.store.selected_results("alice", sid, [old_ref["result_id"]])[0]==saved
        assert backend.calls[-1]==("read_file", {"url": "https://example.invalid/renewed.jsonl", "size": 3})
        observations = [json.loads(m.content) for m in dialogue.inputs[-2][0] if isinstance(m, ToolMessage) and m.name=="resolve_resource"]
        assert len(observations)==2 and observations[0]["object"]==observations[1]["object"]
        assert observations[1]["repeated"] is True
        await service.close()
    asyncio.run(run())


def test_no_download_location_does_not_invent_a_readable_file(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(locate("empty.json"), action("respond_from_context", mode="conversation", reason="目录没有提供文件访问地址"), text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        seed(service.resources.store, rows=[{**node("empty", "empty.json", True), "url": None}])
        await collect(service, session(service), "看empty.json的schema")
        result = next(json.loads(m.content) for m in dialogue.inputs[1][0] if isinstance(m, ToolMessage))
        assert result["status"]=="unavailable" and "object" not in result
        assert not backend.calls
        await service.close()
    asyncio.run(run())


def test_background_yields_to_foreground_but_necessary_lookup_is_prioritized(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    key = seed(store)
    assert store.claim(SOURCES, foreground=True) is None
    store.prioritize("alice", key, SOURCES)
    job = store.claim(SOURCES, foreground=True)
    assert job and job["scope"]["id"]==key
    store.release(job)


def test_later_grounded_dataset_metadata_can_resolve_a_cross_session_name(engine):
    store = IndexStore(engine, threading.RLock(), POLICY)
    rows = {"nodes": [node("file", "data.jsonl", True)]}
    key = store.observe("alice", directory_tool(), SOURCES["arbitrary"], {"dataset": "one"}, rows, None)
    assert store.scopes_for("alice", SOURCES, record={"identity": "one"})[0]["id"]==key
    store.observe("alice", directory_tool(), SOURCES["arbitrary"], {"dataset": "one"}, rows,
        {"identity": "one", "title": "Grounded dataset name"})
    assert store.scopes_for("alice", SOURCES, dataset="Grounded dataset name")[0]["id"]==key


def test_unsafe_directory_capability_is_not_scheduled(engine):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, BareDialogue(), backend.gateway(), index_policy=POLICY)
        tool = replace(directory_tool(), annotations={"readOnlyHint": True, "idempotentHint": False})
        assert await service.resources.observe("alice", tool, {"dataset": "one"}, {"nodes": [node("folder", "nested")]}, None) is None
        assert not service.resources.workers and not backend.calls
        assert not (await service.resources.lookup("alice", "data.jsonl"))["scopes"]
        await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("name", ["观察结果.csv", "simulation.hdf5", "unknown-format.bin"])
def test_directory_index_is_independent_of_file_format_and_domain(engine, name):
    store = IndexStore(engine, threading.RLock(), POLICY)
    seed(store, rows=[{**node("stable-file-id", name, True), "url": "https://example.invalid/"+name}])
    result = store.lookup("alice", SOURCES, name)
    assert result["complete"] and result["items"][0]["name"]==name


def test_non_directory_success_does_not_trigger_index(engine):
    async def run():
        backend = Backend()
        dialogue = BareDialogue(load("arbitrary"), remote("dataset_info", dataset="one", **{TASK: {"complete_request": True}}), text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        try:
            result = await collect(service, session(service), "查询one的数据集详情")
            assert_completed(service, None, result[-1])
            assert not service.resources.store.scopes_for("alice", SOURCES)
            assert not service.resources.workers
            assert [name for name, _ in backend.calls]==["dataset_info"]
        finally:
            await service.close()
    asyncio.run(run())


def test_missing_location_can_be_prepared_and_consumed_in_the_same_request(engine):
    async def run():
        from ..capabilities import SUPPORTING

        backend = Backend()
        dialogue = BareDialogue(locate("measurements.jsonl"), load("arbitrary"),
            remote("list_tree", dataset="one", **{SUPPORTING: True, TASK: {"complete_request": False}}),
            locate("measurements.jsonl"), resolved_call, text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        try:
            result = await collect(service, session(service), "查看one数据集的measurements.jsonl文件schema")
            assert_completed(service, None, result[-1])
            cards = result_cards(result)
            assert len(cards)==1 and cards[0]["view_type"]=="table"
            assert [name for name, _ in backend.calls].count("read_file")==1
            observations = [json.loads(m.content) for m in dialogue.inputs[-2][0]
                if isinstance(m, ToolMessage) and m.name=="resolve_resource"]
            assert [value["status"] for value in observations]==["needs_directory", "resolved"]
        finally:
            await service.close()
    asyncio.run(run())


def test_job_fencing_uses_the_claimed_snapshot_even_if_wall_clock_moves_back(engine, monkeypatch):
    from ..resource_index import store as persistence

    index = IndexStore(engine, threading.RLock(), POLICY)
    with monkeypatch.context() as clock:
        clock.setattr(persistence.time, "time", lambda: 1000.0)
        seed(index)
        clock.setattr(persistence.time, "time", lambda: 999.0)
        job = index.claim(SOURCES)
        index.finish(job, DirectorySpec(**SPEC).rows({"nodes": [node("file", "file.json", True)]}))
        assert index.lookup("alice", SOURCES, "file.json")["complete"]
        assert index.claim(SOURCES) is None
