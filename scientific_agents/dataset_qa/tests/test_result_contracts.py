"""Result contracts apply to actual values in every execution mode and domain."""
import asyncio
from copy import deepcopy
from types import SimpleNamespace

import pytest

from ..capabilities import TASK
from ..contracts import QAError, Server
from ..mcp import MCPGateway
from ..planning import Check, ResultContract
from ..service import DatasetQA
from .test_dataset_qa import action, collect, definition, engine, remote, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_planning import approve


@pytest.mark.parametrize("expected,actual,valid", [
    ("compact", "compact", True), ("compact", "expanded", False),
    (1, 1.0, True), (1, True, False), (True, 1, False), (1, "1", False),
    (1.2, 1.3, False), (None, None, True),
    ({"a": [1, False], "b": "x"}, {"b": "x", "a": [1.0, False]}, True),
    ([1, 2], [2, 1], False),
])
def test_json_value_equality_preserves_type_and_structure(expected, actual, valid):
    contract = ResultContract(kind="records", argument_paths={"option": "/value"})
    if valid:
        contract.validate_arguments({"value": actual}, {"option": expected})
    else:
        with pytest.raises(QAError) as raised:
            contract.validate_arguments({"value": actual}, {"option": expected})
        assert raised.value.code == "invalid_result"
    if not isinstance(expected, (dict, list)):
        assert Check(path="/value", test="equals", value=expected).matches({"value": actual}) is valid


def test_missing_result_field_is_distinct_from_explicit_null():
    contract = ResultContract(kind="records", argument_paths={"option": "/value"},
        unavailable_when=[Check(path="/available", test="equals", value=False)])
    with pytest.raises(QAError):
        contract.validate_arguments({}, {"option": None})
    contract.validate_arguments({}, {})
    contract.validate_arguments({"available": False}, {"option": "compact"})


class RenderingBackend:
    def __init__(self, mismatch):
        self.mismatch, self.calls = mismatch, []
        options = definition("options", annotations={"readOnlyHint": True, "idempotentHint": True})
        options.meta = {"piflow": {"qa": {"result": {"kind": "options"}}}}
        render = definition("render", {"dialect": {"type": "string", "default": "compact"}},
            annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True})
        render.meta = {"piflow": {"qa": {"atomic": True,
            "result": {"kind": "rendered", "argument_paths": {"dialect": "/output/dialect"}}}}}
        self.catalogue = [options, render]

    def client(self, *args, **kwargs):
        backend = self
        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def list_tools(self):
                return backend.catalogue

            async def call_tool(self, name, arguments, **kwargs):
                backend.calls.append((name, deepcopy(arguments)))
                value = arguments.get("dialect", "compact")
                data = {"dialect": "compact"} if name == "options" else {
                    "output": {"dialect": "expanded" if backend.mismatch else value}}
                return SimpleNamespace(structured_content=data, is_error=False)
        return Client()

    def gateway(self):
        return MCPGateway({"renderer": Server("renderer")}, client_factory=self.client)


@pytest.mark.parametrize("mode", ["direct", "planned", "dependency"])
@pytest.mark.parametrize("mismatch", [False, True])
def test_direct_and_planned_calls_share_actual_output_validation(engine, mode, mismatch):
    backend = RenderingBackend(mismatch)
    steps = []
    if mode == "direct":
        steps = [remote("render", **{TASK: {"complete_request": True}})]
    else:
        plan = {"outcomes": [{"key": "result", "description": "Rendered records", "kind": "rendered"}],
            "steps": [{"key": "render", "tool": "render", "produces": ["result"]}]}
        if mode == "dependency":
            plan["steps"].insert(0, {"key": "options", "tool": "options"})
            plan["steps"][1]["inputs"] = {"dialect": {"step": "options", "path": "/dialect"}}
        steps = [action("remember", plan=plan), approve]
    if not mismatch:
        steps.append(text())

    async def run():
        dialogue = BareDialogue(*steps)
        service = DatasetQA(engine, dialogue, backend.gateway())
        try:
            sid = session(service)
            events = await collect(service, sid, "Render records in the selected dialect")
            saved = payload(service, sid, events)
            if mismatch:
                assert saved["error"]["error_code"] == "invalid_result"
                assert not result_cards(events)
                assert saved["operations"][-1]["state"] == "failed"
                reply = "".join(item.get("text", "") for item in events if item["type"] == "message")
                assert not any(word in reply for word in ("invalid_result", "执行失败", "Traceback"))
            else:
                assert saved.get("error") is None
                assert result_cards(events)[0]["data"]["items"][0]["output"]["dialect"] == "compact"
            assert len(backend.calls) == (2 if mode == "dependency" else 1)
            assert backend.calls[-1][1]["dialect"] == "compact"
            assert not dialogue.responses
        finally:
            await service.close()
    asyncio.run(run())


def test_gateway_applies_parameter_default_without_an_agent():
    async def run():
        backend = RenderingBackend(True)
        async with backend.gateway().session() as tools:
            await tools.load("renderer")
            tool = next(item for item in tools.loaded.values() if item.name == "render")
            with pytest.raises(QAError) as raised:
                await tools.call(tool.alias, {})
            assert raised.value.code == "invalid_result"
            assert backend.calls == [("render", {})]
    asyncio.run(run())
