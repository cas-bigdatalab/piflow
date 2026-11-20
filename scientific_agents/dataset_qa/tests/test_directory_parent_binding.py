"""Parent admission uses typed directory evidence, never names or null aliases."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import update

from ..capabilities import SUPPORTING, profile
from ..context import public_result
from ..contracts import QAError, Server
from ..persistence import Store
from ..references import identifier_in_request
from ..resource_index.model import digest, source_identity
from ..resource_index.resolver import bind_parent, directory_receipt
from ..resource_index.store import IndexStore
from ..service import DatasetQA
from .assertions import assert_completed
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, goals, text
from .test_independent_outcomes import ContractDialogue, batch, native
from .test_resource_index import Backend, POLICY, directory_tool, node, seed


SOURCE = source_identity(Server("source"))


@pytest.fixture
def environment(engine):
    store = Store(engine)
    sid = store.create("alice", "", "parent-test")["id"]
    return SimpleNamespace(store=store,
        gateway=SimpleNamespace(configured_servers=lambda: {"arbitrary": Server("source")}),
        resources=SimpleNamespace(store=None)), sid


def save(service, sid, data, *, arguments=None, tool=None, source=SOURCE, metadata=True):
    tool = tool or directory_tool()
    arguments = arguments or {"dataset": "one"}
    card = {"result_id": "receipt-"+uuid4().hex,
        "view_type": "directory", "title": "Directory", "data": deepcopy(data)}
    if metadata:
        card["directory_receipt"] = directory_receipt(tool, source, arguments)
    with service.store.transaction() as conn:
        service.store._item(conn, sid, "fixture", "TOOL_RESULT", card, result_id=card["result_id"])
    return card


def bind(environment, value, *, message="展开目录", dataset="one", tool=None, user="alice", sid=None):
    service, session = environment
    return asyncio.run(bind_parent(service, user, sid or session, tool or directory_tool(),
        {"dataset": dataset, "folder": value}, message))


@pytest.mark.parametrize("arguments", [{"dataset": "one"}, {"dataset": "one", "folder": None}])
def test_root_preserves_omission_and_null_without_loading_evidence(arguments):
    actual = asyncio.run(bind_parent(None, "alice", "session", directory_tool(), arguments, "根目录"))
    assert actual == arguments and actual is not arguments


@pytest.mark.parametrize("value", ["", "  ", "\n", True, {}, [], 1.5])
def test_invalid_parent_is_rejected_before_any_lookup(environment, value):
    with pytest.raises(QAError) as error:
        bind(environment, value, message=f"folder={value}")
    assert error.value.detail["path"] == ["folder"]
    assert error.value.detail["dispatched"] is False


@pytest.mark.parametrize("value", ["None", "null", "root", "unseen", "nested"])
def test_unseen_strings_are_not_root_aliases_or_identifiers(environment, value):
    service, sid = environment
    save(service, sid, {"nodes": [node("actual-id", value)]})
    with pytest.raises(QAError, match="来源证据"):
        bind(environment, value, message=f"查看 {value} 目录")


def test_parent_feedback_offers_root_arguments_without_rewriting_a_child_request(environment):
    service, sid = environment
    tool = directory_tool()
    arguments = {"dataset": "one", "folder": "unverified-child", "format": "tree"}
    original = deepcopy(arguments)
    with pytest.raises(QAError) as error:
        asyncio.run(bind_parent(service, "alice", sid, tool, arguments, "展开子目录"))
    detail = error.value.detail
    assert arguments == original
    assert detail["dispatched"] is False
    assert detail["root_arguments"] == {"dataset": "one", "format": "tree", "folder": None}
    assert "only for the dataset root" in detail["root_guidance"]
    # The caller must make the choice; merely receiving a root option does not
    # establish the rejected child ID as evidence or silently execute the root.
    with pytest.raises(QAError):
        asyncio.run(bind_parent(service, "alice", sid, tool, arguments, "展开子目录"))
    assert asyncio.run(bind_parent(service, "alice", sid, tool,
        detail["root_arguments"], "根目录")) == detail["root_arguments"]


def test_parent_feedback_does_not_offer_null_against_a_nonnullable_business_schema(environment):
    service, sid = environment
    tool = directory_tool()
    tool = replace(tool, schema={**tool.schema, "properties": {
        **tool.schema["properties"], "folder": {"type": "string"}}})
    with pytest.raises(QAError) as error:
        asyncio.run(bind_parent(service, "alice", sid, tool,
            {"dataset": "one", "folder": "unverified-child"}, "展开子目录"))
    assert "root_arguments" not in error.value.detail


@pytest.mark.parametrize("identity", [{}, {"dataset": None}])
def test_root_feedback_does_not_block_an_explicit_parent_when_identity_is_optional(identity):
    tool = directory_tool()
    tool = replace(tool, schema={**tool.schema, "required": [], "properties": {
        **tool.schema["properties"], "dataset": {"type": ["string", "null"]}}})
    arguments = {**identity, "folder": "verified-child"}
    assert asyncio.run(bind_parent(None, "alice", "session", tool, arguments,
        "folder=verified-child")) == arguments


@pytest.mark.parametrize("message", ["folder=chosen-id", "folder:chosen-id", "folder：'chosen-id'",
    '{"folder": "chosen-id"}', "'folder' = 'chosen-id'", "FOLDER=chosen-id"])
def test_explicit_user_parameter_assignment_is_sufficient(environment, message):
    assert bind(environment, "chosen-id", message=message)["folder"] == "chosen-id"


@pytest.mark.parametrize("message", ["选择 chosen-id 目录", "other=chosen-id", "folder=chosen-id-extra",
    "prefix_folder=chosen-id", "folder=other，chosen-id"])
def test_name_or_partial_assignment_is_not_explicit_id_evidence(environment, message):
    with pytest.raises(QAError):
        bind(environment, "chosen-id", message=message)


def test_labelled_only_keeps_legacy_identifier_recognition():
    assert identifier_in_request("chosen-id", "选择 chosen-id")
    assert not identifier_in_request("chosen-id", "选择 chosen-id", "folder", labelled_only=True)
    assert identifier_in_request("chosen-id", '{"folder":"chosen-id"}', "folder", labelled_only=True)


@pytest.mark.parametrize("identity", ["dir-1", "None", "null", " padded ", 12, 0])
def test_original_directory_identifier_is_preserved_without_an_index(environment, identity):
    service, sid = environment
    tool = directory_tool()
    if type(identity) is int:
        tool = replace(tool, schema={**tool.schema, "properties": {
            **tool.schema["properties"], "folder": {"type": ["integer", "null"]}}})
    card = save(service, sid, {"data": {"nodes": [node(identity, "None")]}}, tool=tool,
        arguments={"dataset": "one", "folder": "ancestor"})
    original = deepcopy(card)
    actual = bind(environment, identity, tool=tool)
    assert actual["folder"] == identity and type(actual["folder"]) is type(identity)
    assert service.store.selected_results("alice", sid, [card["result_id"]])[0] == original
    assert "directory_receipt" not in public_result(card)


@pytest.mark.parametrize("data", [{"nodes": [node("target", "file", True)]},
    {"code": 500, "nodes": [node("target", "folder")]},
    {"nodes": [node("target", "folder")], "data": {"nodes": []}},
    {"nodes": [{"key": "target", "filename": "folder", "leaf": "false"}]}])
def test_files_failed_and_malformed_listings_do_not_ground_parents(environment, data):
    service, sid = environment
    save(service, sid, data)
    with pytest.raises(QAError):
        bind(environment, "target")


@pytest.mark.parametrize("mismatch", ["dataset", "source", "tool", "spec", "type", "session", "user"])
def test_receipts_preserve_source_dataset_contract_and_session_boundaries(environment, mismatch):
    service, sid = environment
    tool, arguments = directory_tool(), {"dataset": "one"}
    source, identity = SOURCE, "target"
    if mismatch == "source":
        source = source_identity(Server("different"))
    if mismatch == "tool":
        tool = replace(tool, name="other_tree")
    if mismatch == "spec":
        tool = replace(tool, meta=deepcopy(tool.meta))
        tool.meta["piflow"]["qa"]["directory"]["nodes"] = ["/nodes"]
    if mismatch == "type":
        identity = 12
    save(service, sid, {"nodes": [node(identity, "folder")]}, source=source, tool=tool, arguments=arguments)
    selected_sid = service.store.create("alice", "", "other-session")["id"] if mismatch == "session" else sid
    with pytest.raises(QAError):
        bind(environment, "12" if mismatch == "type" else "target", sid=selected_sid,
            dataset="two" if mismatch == "dataset" else "one", user="bob" if mismatch == "user" else "alice")


def test_receipts_are_paged_and_stop_when_an_older_match_is_found(environment):
    service, sid = environment
    save(service, sid, {"nodes": [node("target", "folder")]})
    for number in range(9):
        save(service, sid, {"nodes": [node(f"other-{number}", "other")]})
    original, pages = service.store.directory_receipts, []
    def observe(*args, **kwargs):
        value = original(*args, **kwargs)
        pages.append(len(value[0]))
        return value
    service.store.directory_receipts = observe
    assert bind(environment, "target")["folder"] == "target"
    assert pages == [8, 2]


def test_old_session_can_use_a_trusted_existing_index_without_refresh(environment):
    service, sid = environment
    save(service, sid, {"nodes": [node("folder", "nested")]}, metadata=False)
    with pytest.raises(QAError):
        bind(environment, "folder")
    index = service.resources.store = IndexStore(service.store.engine, service.store.lock, POLICY)
    seed(index)
    assert bind(environment, "folder")["folder"] == "folder"
    assert index.lookup("alice", {"arbitrary": SOURCE}, "nested", kind="directory")["pending"]


@pytest.mark.parametrize("mismatch", ["dataset", "source", "tool", "spec", "user", "file"])
def test_index_fallback_is_scoped_and_directory_only(environment, mismatch):
    service, sid = environment
    index = service.resources.store = IndexStore(service.store.engine, service.store.lock, POLICY)
    tool = directory_tool()
    if mismatch == "tool":
        tool = replace(tool, name="other_tree")
    if mismatch == "spec":
        tool = replace(tool, meta=deepcopy(tool.meta))
        tool.meta["piflow"]["qa"]["directory"]["nodes"] = ["/nodes"]
    index.observe("bob" if mismatch == "user" else "alice", tool,
        "changed" if mismatch == "source" else SOURCE,
        {"dataset": "two" if mismatch == "dataset" else "one"},
        {"nodes": [node("target", "folder", mismatch == "file")]}, None)
    with pytest.raises(QAError):
        bind(environment, "target")


def test_index_failure_cannot_invalidate_an_original_directory_receipt(environment):
    service, sid = environment
    save(service, sid, {"nodes": [node("folder", "nested")]})
    def unavailable(*args):
        raise AssertionError("A sufficient receipt must not require the index")
    service.resources.store = SimpleNamespace(directory_parent=unavailable)
    assert bind(environment, "folder")["folder"] == "folder"


def test_supplied_source_snapshot_survives_gateway_configuration_change(environment):
    service, sid = environment
    save(service, sid, {"nodes": [node("folder", "nested")]})
    service.gateway.configured_servers = lambda: {"arbitrary": Server("changed")}
    with pytest.raises(QAError):
        bind(environment, "folder")
    actual = asyncio.run(bind_parent(service, "alice", sid, directory_tool(),
        {"dataset": "one", "folder": "folder"}, "展开目录", source=SOURCE))
    assert actual["folder"] == "folder"


def test_index_hit_does_not_scan_session_receipts(environment):
    service, _ = environment
    service.resources.store = IndexStore(service.store.engine, service.store.lock, POLICY)
    seed(service.resources.store)
    def unexpected(*args, **kwargs):
        raise AssertionError("Exact index evidence should avoid a history scan")
    service.store.directory_receipts = unexpected
    assert bind(environment, "folder")["folder"] == "folder"


@pytest.mark.parametrize("parent", ["None", "", "   "])
@pytest.mark.parametrize("coemit", [False, True])
def test_service_repairs_scope_then_parent_without_repeating_detail_or_exposing_receipt(engine, parent, coemit):
    async def run():
        backend = Backend()
        # Runtime must still accept explicit JSON null from older model clients;
        # the current advertised schema expresses that root value by omission.
        dialogue = BareDialogue()
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        async def unavailable(*args, **kwargs):
            raise RuntimeError("Auxiliary index unavailable")
        service.resources.observe = unavailable
        def declared_calls(folder, *, include_directory=True):
            return goals({"description": "Dataset details", "tool": "dataset_info"},
                {"description": "Directory", "tool": "list_tree"}, calls=[
                    native("dataset_info", False, dataset="one"),
                    *([native("list_tree", False, dataset="one", folder=folder)] if include_directory else [])])
        def repair_scope(messages, definitions):
            feedback = json.loads(messages[-1].content)["runtime_feedback"]
            assert feedback["detail"]["decision"] == "declare_outcomes"
            assert not backend.calls
            return declared_calls(parent, include_directory=coemit)(messages, definitions)
        def repair_parent(messages, definitions):
            feedback = json.loads(messages[-1].content)
            feedback = feedback.get("runtime_feedback", feedback)
            assert feedback["detail"]["origin"] == "directory_parent"
            assert feedback["detail"]["dispatched"] is False
            if coemit:
                assert not backend.calls  # Batch admission rejects before any dispatch.
                return declared_calls(None)(messages, definitions)
            assert backend.calls == [("dataset_info", {"dataset": "one"})]
            return native("list_tree", False, dataset="one", folder=None)(messages, definitions)
        dialogue.responses = [batch(native("dataset_info", True, dataset="one"),
            native("list_tree", True, dataset="one", folder=None)), repair_scope,
            *([] if coemit else [native("list_tree", False, dataset="one", folder=parent)]), repair_parent, text()]
        request = "Show the details and directory for dataset=one"
        try:
            events = await collect(service, sid, request, "parent-repair")
            assert_completed(service, sid, events[-1])
            assert backend.calls == [("dataset_info", {"dataset": "one"}),
                ("list_tree", {"dataset": "one", "folder": None})]
            assert len(result_cards(events)) == 2
            saved = service.store.results("alice", sid)
            assert sum("directory_receipt" in card for card in saved) == 1
            replay = await collect(service, sid, request, "parent-repair")
            history = await service.get_session("alice", sid)
            assert "directory_receipt" not in json.dumps([events, replay, history])
            assert len(backend.calls) == 2
            dialogue.responses = [native("list_tree", True, dataset="one", folder="folder"), text()]
            child = await collect(service, sid, "Expand the nested directory for dataset=one", "child")
            assert_completed(service, sid, child[-1])
            assert backend.calls[-1] == ("list_tree", {"dataset": "one", "folder": "folder"})
            assert len(backend.calls) == 3
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("identity", [{}, {"dataset": None}])
def test_successful_optional_identity_directory_keeps_its_receipt_without_scope_metadata(engine, identity):
    async def run():
        backend = Backend()
        definition = backend.tools[0]
        definition.inputSchema["required"] = []
        definition.inputSchema["properties"]["dataset"] = {"type": ["string", "null"]}
        definition.meta = deepcopy(definition.meta)
        definition.meta["piflow"]["qa"]["bind"] = {}
        original_client = backend.client
        data = {"nodes": [node("folder", "nested")]}
        def client(*args, **kwargs):
            connection = original_client(*args, **kwargs)
            async def dispatch(name, arguments, **options):
                assert name == "list_tree" and arguments.get("dataset") is None
                backend.calls.append((name, deepcopy(arguments)))
                return SimpleNamespace(is_error=False, structured_content=deepcopy(data))
            connection.call_tool = dispatch
            return connection
        backend.client = client
        dialogue = BareDialogue(native("list_tree", True, folder=None, **identity), text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        try:
            events = await collect(service, sid, "Show the default directory", "optional-identity")
            assert_completed(service, sid, events[-1])
            card, = service.store.results("alice", sid)
            assert card["data"] == data and "directory_receipt" not in card
            assert backend.calls == [("list_tree", {"folder": None, **identity})]
            replay = await collect(service, sid, "Show the default directory", "optional-identity")
            assert result_cards(events) == result_cards(replay)
            assert len(backend.calls) == 1
        finally:
            await service.close()
    asyncio.run(run())


def test_actual_session_source_snapshot_is_shared_by_parent_binding_receipts_and_index(engine):
    async def run():
        backend = Backend()
        original_client = backend.client
        def client(*args, **kwargs):
            connection = original_client(*args, **kwargs)
            dispatch = connection.call_tool
            async def change_configuration(name, arguments, **options):
                result = await dispatch(name, arguments, **options)
                # The actual transport retains its ToolSession snapshot while
                # configuration for future sessions changes during the call.
                if name == "list_tree" and arguments.get("folder") is None:
                    service.gateway.servers["arbitrary"] = Server("changed")
                return result
            connection.call_tool = change_configuration
            return connection
        backend.client = client
        dialogue = BareDialogue(
            native("list_tree", False, dataset="one", folder=None, **{SUPPORTING: True}),
            native("list_tree", True, dataset="one", folder="folder"), text())
        service = DatasetQA(engine, dialogue, backend.gateway(), index_policy=POLICY)
        sid = session(service)
        try:
            events = await collect(service, sid, "Show the nested directory in dataset=one", "snapshot")
            assert_completed(service, sid, events[-1])
            assert backend.calls == [("list_tree", {"dataset": "one", "folder": None}),
                ("list_tree", {"dataset": "one", "folder": "folder"})]
            expected = directory_receipt(directory_tool(), SOURCE, {"dataset": "one"})["scope"]
            cards = service.store.results("alice", sid)
            assert len(cards) == 2 and all(card["directory_receipt"]["scope"] == expected for card in cards)
            assert service.resources.store.scopes_for("alice", {"arbitrary": SOURCE})
            assert not service.resources.store.scopes_for("alice", {"arbitrary": source_identity(Server("changed"))})
            # A future session using the new source cannot borrow the old
            # source's identifiers through either the index or the receipts.
            with pytest.raises(QAError, match="来源证据"):
                await bind_parent(service, "alice", sid, directory_tool(),
                    {"dataset": "one", "folder": "folder"}, "Expand nested")
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("identity", [None, True, 1.5, {}, [], "", "   ", "\t\n", "\u3000"])
def test_directory_listing_rejects_invalid_node_identity(identity):
    row = {**node("valid", "folder"), "key": identity}
    with pytest.raises(QAError, match="身份"):
        profile(directory_tool()).directory.rows({"nodes": [row]})


@pytest.mark.parametrize("identity", [None, False, 1.5, {}, [], "", "   ", "\t\n", "\u3000"])
def test_worker_rejects_invalid_old_index_identity_before_any_mcp_call(engine, identity):
    async def run():
        backend = Backend()
        service = DatasetQA(engine, ContractDialogue(), backend.gateway(), index_policy=POLICY)
        index = service.resources.store
        key = seed(index)
        # Older snapshots may predate stricter identifier validation. Do not
        # rely solely on the ingestion path to protect a resumed traversal.
        with index.transaction() as conn:
            conn.execute(update(index.nodes).where(index.nodes.c.scope==key,
                index.nodes.c.key==digest("folder")).values(key=digest(identity), identity=json.dumps(identity)))
        async def finished():
            while index.scope("alice", key, {"arbitrary": SOURCE})["state"] != "partial":
                await asyncio.sleep(0.005)
        try:
            service.resources.start()
            await asyncio.wait_for(finished(), POLICY.lookup_wait)
            assert backend.calls == []
            assert index.lookup("alice", {"arbitrary": SOURCE}, "nested", kind="directory")["pending"] is False
        finally:
            await service.close()
    asyncio.run(run())


@pytest.mark.parametrize("identity", ["None", "null", " padded ", 0])
def test_worker_preserves_valid_identifier_values_without_trimming(engine, identity):
    async def run():
        backend = Backend()
        backend.tools[0].inputSchema["properties"]["folder"] = {"type": ["string", "integer", "null"]}
        backend.tree[("one", identity)] = []
        service = DatasetQA(engine, ContractDialogue(), backend.gateway(), index_policy=POLICY)
        index = service.resources.store
        key = seed(index, rows=[node(identity, "nested")])
        async def finished():
            while index.scope("alice", key, {"arbitrary": SOURCE})["state"] != "complete":
                await asyncio.sleep(0.005)
        try:
            service.resources.start()
            await asyncio.wait_for(finished(), POLICY.lookup_wait)
            assert backend.calls == [("list_tree", {"dataset": "one", "folder": identity})]
            assert type(backend.calls[0][1]["folder"]) is type(identity)
        finally:
            await service.close()
    asyncio.run(run())
