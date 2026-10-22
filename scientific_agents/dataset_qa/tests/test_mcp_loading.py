"""Loading budgets, concurrent discovery and isolated read execution regressions."""
import asyncio
from dataclasses import replace

import httpx
import pytest

from .. import mcp
from ..context import encode
from ..contracts import Limits, QAError, Server
from ..mcp import MCPGateway, Tool, checked_tool
from .test_dataset_qa import Backend, definition


def test_concurrent_discovery_and_connection_are_shared_within_a_session():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        factory = gateway.client_factory

        def delayed(*args, **kwargs):
            client = factory(*args, **kwargs)
            connect, discover = client.__class__.__aenter__, client.list_tools

            async def enter(self):
                await asyncio.sleep(0.01)
                return await connect(self)

            async def listing():
                await asyncio.sleep(0.01)
                return await discover()

            client.__class__.__aenter__, client.list_tools = enter, listing
            return client

        gateway.client_factory = delayed
        async with gateway.session() as tools:
            pages = await asyncio.gather(*(tools.load("compute") for _ in range(6)))
            assert all(page == pages[0] for page in pages)
            assert backend.connections == ["compute"]
            assert backend.lists == ["compute"]
        async with gateway.session() as tools:
            clients = await asyncio.gather(*(tools.client("data") for _ in range(6)))
            assert all(client is clients[0] for client in clients)
            assert backend.connections == ["compute", "data"]
    asyncio.run(run())


def test_cancelled_discovery_does_not_poison_waiting_reader():
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        factory = gateway.client_factory
        entered = asyncio.Event()
        attempts = 0

        def delayed(*args, **kwargs):
            client = factory(*args, **kwargs)
            discover = client.list_tools

            async def listing():
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    entered.set()
                    await asyncio.Event().wait()
                return await discover()

            client.list_tools = listing
            return client

        gateway.client_factory = delayed
        async with gateway.session() as tools:
            cancelled = asyncio.create_task(tools.load("compute"))
            await entered.wait()
            waiting = asyncio.create_task(tools.load("compute"))
            cancelled.cancel()
            with pytest.raises(asyncio.CancelledError):
                await cancelled
            assert (await waiting)["items"][0]["tool"] == "multiply"
            assert not tools.discovery_errors
    asyncio.run(run())


def test_schema_budget_includes_definition_list_and_reports_omitted_tools():
    async def run():
        backend = Backend()
        tool = checked_tool(Tool("compute", "multiply", "Tool multiply",
            backend.catalog["compute"][0].inputSchema, {}, {}))
        limit = len(encode(tool.definition()))
        async with backend.gateway(limits=Limits(schema_chars=limit)).session() as tools:
            result = await tools.load("compute")
            assert result["items"][0]["error"] == "schema_too_large"
            assert not tools.definitions()
        async with backend.gateway(limits=Limits(max_tools=2)).session() as tools:
            result = await tools.load("data", limit=4)
            assert len(result["items"]) == 2
            assert {item["tool"] for item in result["not_loaded"]} == {"preview", "sample"}
            assert all(item["error"] == "tool_budget" for item in result["not_loaded"])
    asyncio.run(run())


def test_schema_examples_are_data_not_remote_references():
    async def run():
        backend = Backend()
        backend.catalog["compute"] = [definition("payload", {
            "value": {"type": "object", "default": {"$ref": "https://example.invalid/data"},
                "examples": [{"$dynamicRef": "https://example.invalid/example"}]}})]
        async with backend.gateway().session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            assert tools.validate(alias, {"value": {"$ref": "https://example.invalid/data"}})
    asyncio.run(run())


def test_compiled_input_schema_is_reused_without_revalidation(monkeypatch):
    async def run():
        backend = Backend()
        gateway = backend.gateway()
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]

        def checked_once(schema):
            raise AssertionError("Already checked catalogue schema must not be compiled per call")

        monkeypatch.setattr(mcp, "check_schema", checked_once)
        async with gateway.session() as tools:
            tools.prime("multiply")
            for _ in range(3):
                assert tools.validate(alias, {"x": 2, "y": 3})
            with pytest.raises(QAError) as caught:
                tools.validate(alias, {"x": "invalid", "y": 3})
            assert caught.value.code == "invalid_parameters"
    asyncio.run(run())


@pytest.mark.parametrize("transient,expected", [(True, 2), (False, 1)])
def test_directory_retry_is_safe_bounded_and_transport_only(transient, expected):
    async def run():
        backend = Backend()
        gateway = backend.gateway(limits=replace(Limits(), retry_delay=0))
        factory = gateway.client_factory
        attempts = 0

        def flaky(*args, **kwargs):
            client = factory(*args, **kwargs)
            discover = client.list_tools

            async def listing():
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise httpx.ReadError("response interrupted") if transient else ValueError("bad catalogue")
                return await discover()

            client.list_tools = listing
            return client

        gateway.client_factory = flaky
        async with gateway.session() as tools:
            if transient:
                assert (await tools.load("compute"))["items"][0]["tool"] == "multiply"
            else:
                with pytest.raises(QAError) as caught:
                    await tools.load("compute")
                assert caught.value.code == "mcp_unavailable"
        assert attempts == expected
    asyncio.run(run())


def test_isolated_read_retry_does_not_close_other_inflight_connection():
    async def run():
        backend = Backend()
        backend.catalog["compute"][0].annotations = {"readOnlyHint": True, "idempotentHint": True}
        gateway = backend.gateway(limits=replace(Limits(), retry_delay=0))
        factory = gateway.client_factory
        other_started, retry_finished = asyncio.Event(), asyncio.Event()
        attempts = 0
        closed = []

        def flaky(*args, **kwargs):
            client = factory(*args, **kwargs)
            execute, exit_client = client.call_tool, client.__class__.__aexit__
            client.closed = False

            async def call(name, arguments, **options):
                nonlocal attempts
                if arguments["x"] == 1:
                    attempts += 1
                    if attempts == 1:
                        await other_started.wait()
                        raise httpx.ReadError("one interrupted response")
                    retry_finished.set()
                else:
                    other_started.set()
                    await retry_finished.wait()
                    assert not client.closed, "A sibling retry closed this active connection"
                return await execute(name, arguments, **options)

            async def close(self, *args):
                self.closed = True
                closed.append(self)
                return await exit_client(self, *args)

            client.call_tool, client.__class__.__aexit__ = call, close
            return client

        gateway.client_factory = flaky
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            results = await asyncio.wait_for(asyncio.gather(
                tools.call_isolated(alias, {"x": 1, "y": 3}),
                tools.call_isolated(alias, {"x": 2, "y": 3})), timeout=2)
            assert [result.data for _, result in results] == [3, 6]
            assert backend.lists == ["compute"]
        assert attempts == 2
        assert len(closed) == len(backend.connections) == 4
    asyncio.run(run())


def test_real_mcp_isolated_parallel_reads_and_cancellation_cleanup():
    from fastmcp import FastMCP

    async def run():
        server = FastMCP("isolated-read-regression")
        started, release = asyncio.Event(), asyncio.Event()
        running = set()

        @server.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
        async def inspect(value: int) -> dict:
            running.add(value)
            try:
                if value == 1:
                    started.set()
                    await release.wait()
                else:
                    assert 1 in running, "Independent MCP reads did not overlap"
                return {"value": value}
            finally:
                running.discard(value)

        gateway = MCPGateway({"local": Server(server)})
        async with gateway.session() as tools:
            alias = (await tools.load("local"))["items"][0]["name"]
            first = asyncio.create_task(tools.call_isolated(alias, {"value": 1}))
            await asyncio.wait_for(started.wait(), timeout=2)
            second = await asyncio.wait_for(tools.call_isolated(alias, {"value": 2}), timeout=2)
            assert second[1].data == {"value": 2}
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            assert not running
            # Cancelling one isolated reader cannot close the primary session.
            release.set()
            assert (await tools.call(alias, {"value": 1}))[1].data == {"value": 1}
    asyncio.run(run())


@pytest.mark.parametrize("budget", [0, 1])
def test_unusable_loading_budget_has_explicit_outcome_without_crashing(budget):
    async def run():
        backend = Backend()
        async with backend.gateway(limits=Limits(schema_chars=budget)).session() as tools:
            result = await tools.load("compute")
            assert result["items"][0]["error"] == "schema_too_large"
        async with backend.gateway(limits=Limits(max_tools=0)).session() as tools:
            result = await tools.load("compute")
            assert result["items"][0]["error"] == "tool_budget"
            assert not tools.definitions()
    asyncio.run(run())


@pytest.mark.parametrize("arguments", [None, [], {"value": float("nan")},
    {"value": float("inf")}, {"value": float("-inf")}, {"value": {1, 2}}, {"value": b"bytes"}])
def test_non_json_parameters_are_rejected_before_connection(arguments):
    async def run():
        backend = Backend()
        backend.catalog["compute"] = [definition("payload", {"value": {}})]
        gateway = backend.gateway()
        async with gateway.session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
        async with gateway.session() as tools:
            tools.prime("payload")
            with pytest.raises(QAError) as caught:
                await tools.call_isolated(alias, arguments)
            assert caught.value.code == "invalid_parameters"
            assert not tools.clients and not backend.calls
        assert backend.connections == ["compute"]
    asyncio.run(run())


def test_boolean_does_not_satisfy_numeric_parameters():
    async def run():
        backend = Backend()
        async with backend.gateway().session() as tools:
            alias = (await tools.load("compute"))["items"][0]["name"]
            with pytest.raises(QAError) as caught:
                await tools.call(alias, {"x": True, "y": 3})
            assert caught.value.code == "invalid_parameters"
        assert not backend.calls
    asyncio.run(run())


def test_ranked_page_retains_best_matches_and_can_replace_older_tools():
    async def run():
        backend = Backend()
        async with backend.gateway(limits=Limits(max_tools=2)).session() as tools:
            await tools.load("compute")
            page = await tools.load("data", query="sample", limit=4)
            assert page["items"][0]["tool"] == "sample"
            alias = page["items"][0]["name"]
            assert (await tools.call(alias, {"reference": "a", "count": 1}))[1].data["code"] == 200
            assert len(tools.loaded) == 2
            assert {item["tool"] for item in page["not_loaded"]} == {"inspect", "preview"}
            # A later focused request is a new page and may replace this page.
            page = await tools.load("data", query="inspect", limit=1)
            assert page["items"][0]["tool"] == "inspect"
            assert len(tools.loaded) == 2
    asyncio.run(run())
