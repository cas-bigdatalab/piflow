"""Discovery coverage is request-scoped and independent of cache warmth."""
import asyncio
from dataclasses import replace

import pytest

from ..contracts import Limits, Server
from ..execution import Execution
from .test_dataset_qa import Backend, definition


def gateway_for(backend):
    gateway = backend.gateway()
    gateway.servers = {
        "data": Server("data", "Dataset search and details"),
        "compute": Server("compute", "Arithmetic computation"),
    }
    return gateway


@pytest.mark.parametrize("warm", [(), ("compute",), ("data", "compute")])
def test_unique_related_service_is_prepared_even_with_unrelated_warm_cache(warm):
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        async with gateway.session() as previous:
            for name in warm:
                await previous.load(name)
        async with gateway.session() as tools:
            await tools.prepare("search observations")
            assert next(iter(tools.loaded.values())).name == "search"
            assert tools.discovery_status() == {"checked_servers": ["data"], "pending": [],
                "unavailable_servers": [], "complete": True}
            assert backend.lists.count("data") == 1
            assert backend.lists.count("compute") == int("compute" in warm)
            assert not backend.calls
    asyncio.run(run())


def test_unknown_service_relevance_keeps_navigation_without_fanout():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        async with gateway.session() as tools:
            await tools.prepare("unmatched request")
            assert not tools.loaded and not backend.lists
            status = tools.discovery_status()
            assert status["pending"] == [{"server": "data"}, {"server": "compute"}]
            assert not status["complete"]
            assert all(row["name"] for row in tools.list_servers()["items"])
            assert all(row["discovered"] is False for row in tools.list_servers()["items"])
    asyncio.run(run())


def test_unrelated_loading_does_not_prove_requested_capability_was_checked():
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        async with gateway.session() as tools:
            tools.request_query = "search observations"
            await tools.load("compute")
            assert tools.loaded
            assert tools.discovery_status()["pending"] == [{"server": "data"}]
            assert not tools.discovery_status()["complete"]
    asyncio.run(run())


def test_cached_catalogue_without_disclosed_definitions_is_not_coverage():
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        async with gateway.session() as previous:
            await previous.load("data")
        async with gateway.session() as tools:
            tools.request_query = "search observations"
            assert tools.cached_tools("data")
            assert tools.discovery_status()["pending"] == [{"server": "data", "next_offset": 0}]
            tools.prime(tools.request_query)
            assert tools.discovery_status()["complete"]
    asyncio.run(run())


def test_relevant_unseen_page_is_not_hidden_by_first_page_or_group():
    async def run():
        backend = Backend()
        backend.catalog["data"] = [definition("search_"+str(index)) for index in range(7)]
        gateway = gateway_for(backend)
        async with gateway.session() as tools:
            tools.request_query = "search"
            first = await tools.load("data", limit=2)
            assert first["next_offset"] == 2
            assert tools.discovery_status()["pending"] == [{"server": "data", "next_offset": 2}]
            await tools.load("data", offset=2, limit=5)
            assert tools.discovery_status()["complete"]
    asyncio.run(run())


def test_discovery_offset_matches_load_order_with_rejected_definitions():
    async def run():
        backend = Backend()
        backend.catalog["data"] = [
            definition("search_records_details", {"x": {"type": "not_a_json_type"}}),
            definition("search"),
        ]
        gateway = gateway_for(backend)
        async with gateway.session() as tools:
            tools.request_query = "search records details"
            first = await tools.load("data", limit=1)
            assert first["items"][0]["error"] == "invalid_schema"
            pending = tools.discovery_status()["pending"]
            assert pending == [{"server": "data", "next_offset": first["next_offset"]}]
            await tools.load("data", offset=pending[0]["next_offset"], limit=1)
            assert [tool.name for tool in tools.loaded.values()] == ["search"]
            assert tools.discovery_status()["pending"] == []
            assert tools.discovery_status()["unavailable_servers"] == ["data"]
    asyncio.run(run())


def test_evicted_but_previously_disclosed_schemas_remain_reviewed():
    async def run():
        backend = Backend()
        backend.catalog["data"] = [definition("search_"+str(index)) for index in range(3)]
        gateway = gateway_for(backend)
        gateway.limits = Limits(max_tools=1)
        async with gateway.session() as tools:
            tools.request_query = "search"
            for index in range(3):
                await tools.load("data", offset=index, limit=1)
            assert len(tools.loaded) == 1
            assert tools.discovery_status()["complete"]
    asyncio.run(run())


def test_rejected_schema_budget_does_not_claim_reviewed():
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        gateway.limits = Limits(schema_chars=1)
        async with gateway.session() as tools:
            tools.request_query = "search"
            await tools.load("data")
            assert not tools.loaded
            assert not tools.discovery_status()["complete"]
    asyncio.run(run())


def test_changed_tool_contract_requires_new_disclosure():
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        async with gateway.session() as tools:
            tools.request_query = "search"
            await tools.load("data")
            assert tools.discovery_status()["complete"]
            identity, stamp, catalogue, errors = gateway.cache["data"]
            changed = replace(catalogue[0], description="search with new semantics", _definition=None)
            gateway.cache["data"] = (identity, stamp, [changed, *catalogue[1:]], errors)
            assert not tools.discovery_status()["complete"]
            await tools.load("data")
            assert tools.discovery_status()["complete"]
    asyncio.run(run())


def test_unavailable_service_is_not_evidence_of_absent_capability():
    async def run():
        backend = Backend()
        gateway = gateway_for(backend)
        factory = gateway.client_factory
        def broken(target, **kwargs):
            client = factory(target, **kwargs)
            async def unavailable():
                raise ValueError("unavailable catalogue")
            client.list_tools = unavailable
            return client
        gateway.client_factory = broken
        async with gateway.session() as tools:
            await tools.prepare("search")
            assert tools.discovery_status() == {"checked_servers": [], "pending": [],
                "unavailable_servers": ["data"], "complete": False}
    asyncio.run(run())


def test_repeated_lookup_recovery_is_once_and_does_not_allocate_more_budget():
    execution = Execution()
    value = {"data": {"items": []}}
    assert execution.observe("one", value, "find_artifacts")
    assert not execution.observe("two", value, "find_artifacts")
    execution.calls, execution.stalled = 6, 2
    assert execution.recover_discovery({"pending": [{"server": "data"}]})
    assert execution.calls == 6 and execution.stalled == 0
    assert "find_artifacts" not in execution.actions({})
    assert {"load_mcp_tools", "read_result"} <= execution.actions({})
    assert not execution.recover_discovery({"pending": [{"server": "data"}]})


def test_discovery_recovery_never_reopens_execution_or_invents_capabilities():
    execution = Execution()
    assert not execution.recover_discovery({"pending": []})
    execution.cards[("call", "receipt")] = {"result_id": "result"}
    assert not execution.recover_discovery({"pending": [{"server": "data"}]})
    assert not execution.recover_discovery({"pending": []}, available=True)


def test_warm_catalogue_can_recover_repeated_lookup_with_existing_call_budget():
    execution = Execution()
    value = {"data": {"items": []}}
    execution.observe("one", value, "find_artifacts")
    execution.observe("two", value, "find_artifacts")
    execution.calls, execution.stalled = 4, 2
    assert execution.recover_discovery({"pending": [], "complete": True}, available=True)
    assert execution.calls == 4 and execution.stalled == 0
    assert "find_artifacts" not in execution.actions({})
    assert "respond_from_context" in execution.actions({})
    assert not execution.recover_discovery({"pending": []}, available=True)


@pytest.mark.parametrize("state", ["pending", "checked", "unavailable"])
def test_bounded_discovery_status_preserves_complete_coverage_and_whole_identities(state):
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        gateway.servers = {"server-"+str(index): Server("data", "Dataset search")
            for index in range(11)}
        async with gateway.session() as tools:
            if state == "checked":
                for server in tools.servers:
                    await tools.load(server)
            elif state == "unavailable":
                tools.discovery_errors.update({server: RuntimeError("offline") for server in tools.servers})
            full = tools.discovery_status()
            bounded = tools.discovery_status(limit=8)
            assert bounded["complete"] == full["complete"] == (state == "checked")
            assert bounded["details_tool"] == "list_mcp_servers"
            for key, total in (("checked_servers", "checked_total"), ("pending", "pending_total"),
                    ("unavailable_servers", "unavailable_total")):
                assert bounded[key] == full[key][:8]
                assert bounded[total] == len(full[key])
            assert sum(bounded[key] for key in ("checked_total", "pending_total", "unavailable_total")) == 11
            assert len(tools.list_servers(offset=8)["items"]) == 3
    asyncio.run(run())
