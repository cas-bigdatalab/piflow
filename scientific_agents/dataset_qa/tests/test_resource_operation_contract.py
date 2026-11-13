"""Operation semantics, representation binding and export receipt verification."""
import asyncio
from copy import deepcopy
import json

import pytest

from ..capabilities import inputs, validate_export, validate_intent
from ..contracts import QAError
from ..mcp import Tool, ToolSession
from ..service import DatasetQA
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import BareDialogue, payload, text
from .test_file_pipeline import files
from .test_followup_resource_execution import competing_gateway, export_action, retrieve, warm


def converter(operations=("export",)):
    return Tool("provider", "write_records", "Convert a resource", {
        "type": "object", "properties": {"ref": {"type": "string"},
            "representation": {"type": "string", "enum": ["csv", "jsonl"]}},
        "required": ["ref", "representation"]}, {}, {"piflow": {"qa": {
            "bind": {"ref": ["/source_ref"]}, "artifact": {"consume": "ref"},
            "routing": {"group": "records", "operations": list(operations), "outputs": ["csv", "jsonl"]},
            "result": {"kind": "file", "argument_paths": {"representation": "/resource/format"}}}}})


def test_format_contract_uses_declared_mapping_not_a_parameter_name():
    tool = converter()
    validate_intent(tool, {"operation": "export", "output_format": "CSV"}, {"representation": "csv"})
    with pytest.raises(QAError):
        validate_intent(tool, {"operation": "export", "output_format": "csv"}, {"representation": "jsonl"})
    assert inputs(tool, {"representation": "csv"}, {"source_ref": "actual-reference"})["ref"] == "actual-reference"


def test_same_output_format_does_not_make_filter_a_pure_exporter():
    with pytest.raises(QAError) as error:
        validate_intent(converter(("filter",)), {"operation": "export", "output_format": "csv"})
    assert error.value.code == "invalid_parameters"
    validate_intent(converter(("filter",)), {"operation": "filter", "output_format": "csv"}, {"representation": "csv"})


def test_workspace_binding_cannot_substitute_an_opaque_resource_reference():
    tool = Tool("provider", "process_local", "Local processing", {
        "type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, {},
        {"piflow": {"qa": {"bind": {"path": ["/workspace_path"]}}}})
    with pytest.raises(QAError):
        inputs(tool, {"path": "invented.csv"}, {"source_ref": "owned-reference"})
    assert inputs(tool, {}, {"workspace_path": "dataset/real.csv"}) == {"path": "dataset/real.csv"}


@pytest.mark.parametrize("count", [0, 1000])
def test_export_receipt_preserves_empty_and_nonempty_record_sets(count):
    source = {"resource": {"record_count": count, "source_ref": "original"}}
    validate_export(converter(), {"resource": {"record_count": count}, "parent_source_ref": "original"}, source)
    for changed in ({"resource": {"record_count": count+1}, "parent_source_ref": "original"},
            {"resource": {"record_count": count}, "parent_source_ref": "other"}, {}):
        with pytest.raises(QAError) as error:
            validate_export(converter(), changed, source)
        assert error.value.code == "invalid_result" and error.value.detail["dispatched"] is True


@pytest.mark.parametrize("mismatch", ["count", "parent"])
def test_invalid_export_is_not_published_or_retried_as_a_new_search(engine, files, monkeypatch, mismatch):
    original_call = ToolSession.call
    calls = []

    async def changed(tools, alias, arguments, **kwargs):
        tool, output = await original_call(tools, alias, arguments, **kwargs)
        calls.append(tool.name)
        if tool.name == "export_dataset":
            if mismatch == "count":
                output.data["record_count"] = output.data["resource"]["record_count"] = 1
            else:
                output.data["parent_source_ref"] = "unrelated-reference"
        return tool, output

    monkeypatch.setattr(ToolSession, "call", changed)

    async def run():
        gateway, _ = competing_gateway()
        await warm(gateway)
        service = DatasetQA(engine, BareDialogue(), gateway)
        try:
            sid = session(service)
            await retrieve(service, sid)
            before = deepcopy(service.artifacts.recent("alice"))
            def export(messages, definitions):
                handle = json.loads(messages[1].content)["published_artifacts"]["items"][0]["handle"]
                return export_action(definitions, handle)
            service.dialogue = BareDialogue(export, text())
            events = await collect(service, sid, "把这些记录保存成 CSV", rid="mismatched-export")
            assert payload(service, sid, events)["error"]["error_code"] == "invalid_result"
            assert not result_cards(events)
            assert calls == ["query_pubchem_compounds", "export_dataset"]
            assert service.artifacts.recent("alice") == before
        finally:
            await service.close()
    asyncio.run(run())
