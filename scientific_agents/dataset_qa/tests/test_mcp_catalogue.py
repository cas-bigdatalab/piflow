"""Invalid capabilities stay local and cannot poison later cached discovery."""
import asyncio
from copy import deepcopy
from dataclasses import replace

import pytest

from ..contracts import QAError, Server
from ..mcp import MCPGateway
from ..service import DatasetQA
from .test_dataset_qa import Backend, action, collect, definition, engine, load, remote, result_cards, session
from .test_decisions import BareDialogue, text


@pytest.mark.parametrize("fault", ["metadata", "schema", "remote_ref", "local_ref", "pointer", "json"])
def test_bad_definition_isolated_before_caching_and_warm_priming(fault, caplog):
    async def run():
        backend = Backend()
        broken = backend.catalog["data"][1]
        if fault=="metadata":
            broken.meta = {"piflow": {"qa": {"bind": {"missing_parameter": ["/id"]}}}}
        elif fault=="schema":
            broken.inputSchema["properties"]["reference"] = {"type": "not-a-type"}
        elif fault=="remote_ref":
            broken.inputSchema["properties"]["reference"] = {"$ref": "https://example.invalid/schema"}
        elif fault=="local_ref":
            broken.inputSchema["properties"]["reference"] = {"$ref": "#/$defs/Missing"}
        elif fault=="pointer":
            broken.meta = {"piflow": {"qa": {"object": "not/a/pointer"}}}
        else:
            broken.meta = {"value": float("nan")}
        gateway = backend.gateway()
        async with gateway.session() as tools:
            page = await tools.load("data", limit=8)
            errors = [item for item in page["items"] if item.get("error")]
            assert errors==[{"name": "inspect", "error": "invalid_schema", "message": errors[0]["message"]}]
            assert all(tool.name!="inspect" for tool in tools.loaded.values())
            alias = next(item["name"] for item in page["items"] if item.get("tool")=="search")
            await tools.call(alias, {"query": "real input"})
        async with gateway.session() as tools:
            tools.prime("multiply")  # The unrelated cold capability must remain usable.
            assert not tools.clients and all(tool.name!="inspect" for tool in tools.loaded.values())
            cached = await tools.load("data", query="inspect", limit=1)
            assert cached["items"][0]["error"]=="invalid_schema" and not tools.clients
            alias = (await tools.load("compute"))["items"][0]["name"]
            assert (await tools.call(alias, {"x": 2, "y": 3}))[1].data==6
        assert backend.lists==["data", "compute"]
        assert [call[1] for call in backend.calls]==["search", "multiply"]
    asyncio.run(run())
    assert sum("MCP definition rejected" in record.message for record in caplog.records)==1


@pytest.mark.parametrize("ref", ["#/$defs/Node", "#node"])
def test_valid_recursive_local_references_remain_callable(ref):
    async def run():
        backend = Backend()
        recursive = definition("recursive", {"node": {"$ref": ref}}, ["node"])
        recursive.inputSchema.update({"$id": "https://example.invalid/root", "$defs": {
            "Node": {"$anchor": "node", "type": "object", "properties": {
                "value": {"type": "integer"}, "next": {"anyOf": [{"$ref": ref}, {"type": "null"}]}},
                "required": ["value"], "additionalProperties": False}}})
        backend.catalog["compute"] = [recursive]
        async with backend.gateway().session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            arguments = {"node": {"value": 1, "next": {"value": 2, "next": None}}}
            assert tools.validate(alias, arguments).name=="recursive"
            await tools.call(alias, arguments)
            assert not tools.definition_errors["compute"]
        assert backend.calls==[("compute", "recursive", arguments)]
    asyncio.run(run())


def test_all_invalid_tools_are_cached_locally_and_recover_after_expiry():
    async def run():
        backend = Backend()
        broken = backend.catalog["compute"][0]
        broken.meta = {"piflow": {"qa": {"bind": {"unknown": ["/id"]}}}}
        gateway = backend.gateway()
        for _ in range(2):
            async with gateway.session() as tools:
                tools.prime("multiply")
                with pytest.raises(QAError) as caught:
                    await tools.load("compute")
                assert caught.value.code=="invalid_schema"
                assert tools.discovery_errors["compute"] is caught.value
                assert (await tools.load("data"))["items"]
        assert backend.lists.count("compute")==1
        broken.meta = {}
        gateway.limits = replace(gateway.limits, cache_seconds=0)
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            assert not tools.definition_errors["compute"]
            assert (await tools.call(alias, {"x": 3, "y": 4}))[1].data==12
        assert backend.lists.count("compute")==2
    asyncio.run(run())


def test_catalogue_and_model_definitions_are_detached_snapshots():
    async def run():
        backend, gateway = Backend(), None
        gateway = backend.gateway()
        async with gateway.session() as tools:
            catalogue = await tools.tools("compute")
            catalogue[0].schema["required"].clear()
            catalogue[0].meta["piflow"] = {"qa": {"bind": {"unknown": ["/id"]}}}
            alias = (await tools.load("compute"))["items"][0]["name"]
            assert tools.loaded[alias].schema["required"]==["x", "y"]
            definitions = tools.definitions()
            definitions[0]["function"]["parameters"]["required"].clear()
            assert tools.definitions()[0]["function"]["parameters"]["required"]==["x", "y"]
            with pytest.raises(QAError) as caught:
                await tools.call(alias, {"x": 2})
            assert caught.value.code=="invalid_parameters"
        async with gateway.session() as tools:
            tools.prime("multiply")
            tool, = tools.loaded.values()
            assert tool.schema["required"]==["x", "y"] and not tool.meta
            assert not tools.clients
        assert backend.catalog["compute"][0].inputSchema["required"]==["x", "y"]
        assert not backend.catalog["compute"][0].meta and not backend.calls
    asyncio.run(run())


@pytest.mark.parametrize("changed_target", [False, True])
@pytest.mark.parametrize("evicted", [False, True])
def test_old_discovery_cannot_overwrite_a_newer_catalogue(changed_target, evicted):
    async def run():
        backend = Backend()
        entered, release = asyncio.Event(), asyncio.Event()
        fetches = 0

        def factory(target, **kwargs):
            client = backend.client(target, **kwargs)

            async def list_tools():
                nonlocal fetches
                fetches += 1
                snapshot = deepcopy(backend.catalog[target])
                if fetches==1:
                    entered.set()
                    await release.wait()
                return snapshot

            client.list_tools = list_tools
            return client

        backend.catalog["old"] = [definition("old_tool")]
        backend.catalog["new"] = [definition("new_tool")]
        gateway = MCPGateway({"service": Server("old")}, client_factory=factory)

        async def old_discovery():
            async with gateway.session() as tools:
                return await tools.load("service")

        older = asyncio.create_task(old_discovery())
        await entered.wait()
        if changed_target:
            gateway.servers["service"] = Server("new")
        else:
            backend.catalog["old"] = backend.catalog["new"]
        async with gateway.session() as tools:
            assert (await tools.load("service"))["items"][0]["tool"]=="new_tool"
        if evicted:
            gateway.limits = replace(gateway.limits, cache_seconds=0)
            async with gateway.session():
                pass
            gateway.limits = replace(gateway.limits, cache_seconds=300)
        release.set()
        assert (await older)["items"][0]["tool"]=="old_tool"
        async with gateway.session() as tools:
            if evicted:
                assert "service" not in gateway.cache  # Older work must not revive an evicted generation.
                await tools.load("service")
            connections = set(tools.clients)
            tools.prime("")
            assert [tool.name for tool in tools.loaded.values()]==["new_tool"]
            assert set(tools.clients)==connections
    asyncio.run(run())


def test_duplicate_names_are_quarantined_without_hiding_other_tools():
    async def run():
        backend = Backend()
        backend.catalog["data"] = [definition("duplicate"), definition("duplicate"), definition("healthy")]
        async with backend.gateway().session() as tools:
            values = await tools.load("data", limit=8)
            assert [tool.name for tool in tools.loaded.values()]==["healthy"]
            assert len([row for row in values["items"] if row.get("error")])==1
    asyncio.run(run())


def test_preflight_validation_has_no_execution_or_connection_side_effects():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
        async with gateway.session() as tools:
            tools.prime("multiply")
            assert tools.validate(alias, {"x": 2, "y": 3}).name=="multiply"
            with pytest.raises(QAError) as caught:
                tools.validate(alias, {"x": "bad", "y": 3})
            assert caught.value.code=="invalid_parameters"
            assert not tools.clients and not backend.calls
            with pytest.raises(QAError):
                await tools.call(alias, {"x": "bad", "y": 3})
            assert not tools.clients and not backend.calls
        assert backend.connections==["compute"] and backend.lists==["compute"]
    asyncio.run(run())


def test_invalid_service_does_not_block_another_service_or_following_turn(engine):
    async def run():
        backend = Backend()
        backend.catalog["compute"][0].meta = {"piflow": {"qa": {"bind": {"unknown": ["/id"]}}}}
        dialogue = BareDialogue(load("compute"), load(), remote("search", query="resources"),
            action("deliver_results"), text())
        service = DatasetQA(engine, dialogue, backend.gateway())
        sid = session(service)
        try:
            first = await collect(service, sid, "Find resources", "first")
            assert first[-1]["status"]=="COMPLETED" and len(result_cards(first))==1
            dialogue.responses = [remote("search", query="another request"), action("deliver_results"), text()]
            second = await collect(service, sid, "Find more resources", "second")
            assert second[-1]["status"]=="COMPLETED" and len(result_cards(second))==1
            assert len(backend.calls)==2 and backend.lists.count("compute")==1
        finally:
            await service.close()
    asyncio.run(run())


def test_real_mcp_metadata_failure_does_not_hide_a_healthy_tool():
    from fastmcp import FastMCP

    async def run():
        mcp, calls = FastMCP("catalogue-isolation"), []

        @mcp.tool(meta={"piflow": {"qa": {"bind": {"missing_parameter": ["/id"]}}}})
        def invalid_tool(identifier: str) -> dict:
            raise AssertionError("Invalid definitions must never execute")

        @mcp.tool
        def healthy_tool(value: int) -> dict:
            calls.append(value)
            return {"value": value}

        gateway = MCPGateway({"local": Server(mcp)})
        async with gateway.session() as tools:
            page = await tools.load("local", limit=8)
            alias = next(row["name"] for row in page["items"] if row.get("tool")=="healthy_tool")
            assert any(row.get("error")=="invalid_schema" for row in page["items"])
            assert (await tools.call(alias, {"value": 7}))[1].data=={"value": 7}
        async with gateway.session() as tools:
            tools.prime("invalid_tool")
            assert [tool.name for tool in tools.loaded.values()]==["healthy_tool"] and not tools.clients
        assert calls==[7]
    asyncio.run(run())
