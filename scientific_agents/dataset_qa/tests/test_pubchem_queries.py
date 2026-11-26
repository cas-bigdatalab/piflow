"""PubChem capability contracts: modes, exact predicates, columns and bounded I/O."""
import asyncio
from copy import deepcopy
import csv
import io
import json
import os
import time

from fastmcp import Client
import pytest
import requests

from mcp_servers.corpus_mcp import mcp
from services import corpus_connector_service as backend
from ..artifacts import execution_metadata
from .test_file_pipeline import SECRET, files, query_args, run_export, run_query


def records(files):
    return [json.loads(line) for line in next(files.root.glob("*/*/data.jsonl")).read_text(encoding="utf-8").splitlines()]


def test_selected_columns_filter_with_unpublished_fields_and_keep_missing_outputs(files):
    files.rows[0].update(MolecularFormula="C2H6", TPSA=0, Complexity=2.5, Charge=0)
    files.rows[1].update(MolecularFormula="C3H8", Complexity=3, Charge=0)
    args = query_args(properties=["MolecularFormula", "TPSA"], limit=1200)
    value = run_query(args)
    assert value["resource"]["fields"] == ["CID", "SMILES", "MolecularFormula", "TPSA"]
    assert files.requests[1][0].endswith("/property/SMILES,MolecularFormula,TPSA,MolecularWeight,XLogP/JSON")
    rows = records(files)
    assert rows == [{"CID": 1, "SMILES": "CC", "MolecularFormula": "C2H6", "TPSA": 0.0},
        {"CID": 2, "SMILES": "CCC", "MolecularFormula": "C3H8", "TPSA": None}]
    assert value["statistics"]["missing_output_fields"] == {"TPSA": 1}
    assert value["record_count"] == 2 and value["target_met"] is False
    output = run_export(value["resource"])
    table = list(csv.DictReader(io.StringIO(next(files.root.glob("*/*/data.csv")).read_text(encoding="utf-8"))))
    assert list(table[0]) == value["resource"]["fields"] and table[1]["TPSA"] == ""
    assert output["statistics"] == value["statistics"]


@pytest.mark.parametrize("field,minimum,maximum", [("TPSA", 0, 80), ("Complexity", 0, 300), ("Charge", -1, 1)])
def test_new_filter_boundaries_and_missing_values(files, field, minimum, maximum):
    for row, value in zip(files.rows, (minimum, maximum, maximum+1)):
        row[field] = value
    value = run_query(query_args(filters=[{"field": field, "minimum": minimum, "maximum": maximum}], properties=[field]))
    assert [row["CID"] for row in records(files)] == [1, 2]
    assert value["statistics"]["exclusion_reasons"] == {"outside_"+field: 1, "missing_"+field: 1}
    if field == "Charge":
        assert all(type(row[field]) is int for row in records(files))


@pytest.mark.parametrize("changes", [
    {"search_type": "invalid"}, {"smiles": None}, {"smiles": " "}, {"smarts": "C"},
    {"search_type": "substructure", "smarts": "C"},
    {"search_type": "superstructure", "smiles": None, "smarts": "C"},
    {"search_type": "property"}, {"search_type": "property", "smiles": None, "filters": []},
    {"search_type": "substructure", "similarity_threshold": 90},
    {"filters": False}, {"filters": [{"field": [], "minimum": 1}]}, {"filters": [{"field": "Charge", "minimum": 0.5}]},
    {"filters": [{"field": "Charge", "minimum": True}]},
    {"filters": [{"field": "MolecularFormula", "minimum": 1}]},
    {"filters": [{"field": "TPSA"}]}, {"filters": [{"field": "XLogP", "minimum": 2, "maximum": 1}]},
    {"filters": [{"field": "TPSA", "minimum": 100}, {"field": "TPSA", "maximum": 80}]},
    {"properties": ["unsupported"]}, {"properties": "TPSA"}, {"limit": True}, {"limit": 20001},
])
def test_invalid_parameters_do_not_query_or_publish(files, changes):
    with pytest.raises(ValueError):
        run_query(query_args(**changes))
    assert not files.requests and not files.writes


@pytest.mark.parametrize("mode,input_name,structure,route", [
    ("similarity", "smiles", "CC", "fastsimilarity_2d/smiles"),
    ("substructure", "smiles", "c1ccccc1", "fastsubstructure/smiles"),
    ("substructure", "smarts", "[#6]1:[#6]:[#6]:[#6]:[#6]:[#6]:1", "fastsubstructure/smarts"),
    ("superstructure", "smiles", "CCO", "fastsuperstructure/smiles"),
])
def test_structure_modes_preserve_input_and_official_semantics(files, monkeypatch, mode, input_name, structure, route):
    request = backend._pubchem_request
    calls = []
    def dispatch(client, path, data, params, root, deadline):
        calls.append((path, data, params))
        if "/compound/fast" in path:
            return {"IdentifierList": {"CID": [1, 2]}}
        return request(client, path, data, params, root, deadline)
    monkeypatch.setattr(backend, "_pubchem_request", dispatch)
    args = query_args(search_type=mode, smiles=None, **{input_name: structure}) if input_name == "smarts" else query_args(search_type=mode, smiles=structure)
    value = run_query(args)
    assert value["record_count"] == 2
    assert calls[0][0] == "/compound/"+route+"/cids/JSON"
    assert calls[0][1] == {input_name: structure}
    assert ("Threshold" in calls[0][2]) == (mode == "similarity")


def test_property_search_pages_snapshot_rechecks_filters_and_stops_at_accepted_count(files, monkeypatch):
    pages, batches = [], []
    def search(client, params, root, deadline):
        pages.append(deepcopy(params))
        offset = params["retstart"]
        return {"esearchresult": {"count": "450", "idlist": [str(n) for n in range(offset+1, min(offset+201, 451))],
            "querykey": "1", "webenv": "snapshot"}}
    def fetch(client, route, data, params, root, deadline):
        batch = list(map(int, data["cid"].split(",")))
        batches.append(batch)
        return {"PropertyTable": {"Properties": [{"CID": cid, "SMILES": "CC", "MolecularWeight": 200,
            "XLogP": 1 if cid % 2 == 0 else 8} for cid in batch]}}
    monkeypatch.setattr(backend, "_entrez_request", search)
    monkeypatch.setattr(backend, "_pubchem_request", fetch)
    args = query_args(search_type="property", smiles=None, limit=120)
    result = run_query(args)
    assert result["record_count"] == 120 and result["target_met"] is True
    assert result["coverage"] == "partial" and result["stop_reason"] == "target_reached"
    assert result["statistics"]["checked"] == 240 and result["statistics"]["excluded"] == 120
    assert result["statistics"]["source_candidates"] == 450
    assert pages[0]["term"] == "100:500[MW] AND -1:5[LOGP]"
    assert pages[1]["term"] == "#1" and pages[1]["WebEnv"] == "snapshot" and pages[1]["retstart"] == 200
    assert len(pages) == len(batches) == 2


@pytest.mark.parametrize("empty", [False, True])
def test_property_one_sided_filter_is_exact_without_inventing_bounds(files, monkeypatch, empty):
    queries = []
    def search(client, params, root, deadline):
        queries.append(params)
        return {"esearchresult": {"count": "0" if empty else "4", "idlist": [] if empty else ["1", "2", "3", "4"]}}
    monkeypatch.setattr(backend, "_entrez_request", search)
    value = run_query(query_args(search_type="property", smiles=None, filters=[{"field": "XLogP", "maximum": 0}]))
    assert queries[0]["term"] == "all[filt]"
    assert value["coverage"] == "complete" and value["stop_reason"] == "candidates_exhausted"
    assert value["record_count"] == (0 if empty else 1)
    if not empty:
        assert records(files)[0]["CID"] == 1


@pytest.mark.parametrize("page", [
    {"error": "unavailable"}, {"esearchresult": {"count": "0", "idlist": [], "errorlist": {"fieldsnotfound": ["MW"]}}},
    {"esearchresult": {"count": "4", "idlist": ["1", "2"]}},
    {"esearchresult": {"count": "1", "idlist": ["0"]}},
    {"esearchresult": {"count": "0", "idlist": [], "errorlist": ["unavailable"]}},
    {"esearchresult": {"count": "201", "idlist": [str(n) for n in range(1, 201)]}},
])
def test_incomplete_property_search_is_not_reported_as_zero_matches(files, monkeypatch, page):
    monkeypatch.setattr(backend, "_entrez_request", lambda *args: page)
    result = run_query(query_args(search_type="property", smiles=None))
    assert result["coverage"] == "partial" and result["stop_reason"] == "source_interrupted"
    assert result["status"] == "unavailable" and result["resource"] is None


def test_property_candidate_cap_and_duplicate_ids(files, monkeypatch):
    monkeypatch.setattr(backend, "_CANDIDATE_LIMIT", 5)
    monkeypatch.setattr(backend, "_entrez_request", lambda *args: {
        "esearchresult": {"count": "100", "idlist": ["1", "2", "2", "3", "4"]}})
    result = run_query(query_args(search_type="property", smiles=None, limit=None))
    assert result["record_count"] == 2 and result["coverage"] == "partial"
    assert result["stop_reason"] == "candidate_limit" and result["statistics"]["duplicate_candidates"] == 1


def test_legacy_signed_mcp_call_and_new_options_cannot_bypass_signature(files):
    async def run():
        old = {k: v for k, v in query_args().items() if k not in {"search_type", "smarts", "properties"}}
        meta = execution_metadata("user_a", "legacy", old, 120, secret=SECRET)
        async with Client(mcp) as client:
            result = await client.call_tool("query_pubchem_compounds", old, meta=meta)
            assert result.structured_content["resource"]["fields"] == list(backend._COMPOUND_FIELDS)
            store = backend._ResultFiles(meta["piflow_execution"], old)
            assert store.resolve(result.structured_content["resource"]["source_ref"]) == backend._digest(["pubchem-v1", "legacy", old])
            for changes in [{"search_type": "substructure"}, {"properties": ["TPSA"]}, {"smarts": "C"}]:
                altered = await client.call_tool("query_pubchem_compounds", {**old, **changes}, meta=meta, raise_on_error=False)
                assert altered.is_error
        assert len(files.requests) == 2
    asyncio.run(run())


def test_requested_columns_participate_in_replay_identity(files):
    first = run_query(query_args(properties=["MolecularWeight", "TPSA"]))
    second = run_query(query_args(properties=["MolecularFormula", "Charge"]))
    assert first["resource"]["source_ref"] != second["resource"]["source_ref"]
    assert run_query(query_args(properties=["MolecularWeight", "TPSA"]))["resource"] == first["resource"]
    assert len(files.requests) == 4


@pytest.mark.parametrize("mode", ["substructure", "superstructure", "property"])
def test_new_modes_cross_real_mcp_schema_and_signed_parameters(files, monkeypatch, mode):
    original = backend._pubchem_request
    def request(client, route, data, params, root, deadline):
        if "/compound/fast" in route:
            return {"IdentifierList": {"CID": [1, 2]}}
        return original(client, route, data, params, root, deadline)
    monkeypatch.setattr(backend, "_pubchem_request", request)
    monkeypatch.setattr(backend, "_entrez_request", lambda *args: {"esearchresult": {"count": "2", "idlist": ["1", "2"]}})
    args = query_args(search_type=mode, properties=["MolecularFormula", "TPSA", "Charge"])
    if mode != "superstructure":
        args["smiles"] = None
    if mode == "substructure":
        args["smarts"] = "[#6]"
    async def run():
        async with Client(mcp) as client:
            value = await client.call_tool("query_pubchem_compounds", args,
                meta=execution_metadata("user_a", "new-mode", args, 120, secret=SECRET))
            assert not value.is_error and value.structured_content["record_count"] == 2
            assert value.structured_content["query"] == args
            assert value.structured_content["resource"]["fields"] == ["CID", "SMILES", *args["properties"]]
    asyncio.run(run())


@pytest.mark.parametrize("status,body,empty", [
    (404, {"Fault": {"Code": "PUGREST.NotFound"}}, True),
    (404, {"detail": "Not Found"}, False), (400, {"Fault": {"Code": "PUGREST.BadRequest"}}, False),
])
def test_http_not_found_is_empty_only_for_structured_structure_search(tmp_path, status, body, empty):
    class Response:
        status_code = status
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def iter_content(self, _): yield json.dumps(body).encode()
        def raise_for_status(self): raise requests.HTTPError(str(status))
    class Session:
        def post(self, *args, **kwargs): return Response()
    call = lambda route: backend._pubchem_request(Session(), route, {}, {}, tmp_path, time.time()+10)
    if empty:
        assert call("/compound/fastsimilarity_2d/smiles/cids/JSON") == {"IdentifierList": {"CID": []}}
    else:
        with pytest.raises(requests.HTTPError):
            call("/compound/fastsimilarity_2d/smiles/cids/JSON")
    with pytest.raises(requests.HTTPError):
        call("/compound/cid/property/SMILES/JSON")


def test_schema_catalogue_is_shared_and_tool_count_unchanged():
    async def run():
        async with Client(mcp) as client:
            tools = await client.list_tools()
        query = next(t for t in tools if t.name == "query_pubchem_compounds")
        schema = query.inputSchema
        assert set(schema["properties"]["filters"]["anyOf"][0]["items"]["properties"]["field"]["enum"]) == backend._FILTER_FIELDS
        assert set(schema["properties"]["properties"]["anyOf"][0]["items"]["enum"]) == set(backend.PUBCHEM_PROPERTIES)
        assert {t.name for t in tools if "pubchem" in t.name} == {"query_pubchem_compounds"}
    asyncio.run(run())


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_PUBCHEM") != "1", reason="Opt-in real PubChem mode checks")
@pytest.mark.parametrize("changes", [
    {"search_type": "substructure", "smiles": None, "smarts": "c1ccccc1"},
    {"search_type": "superstructure"},
    {"search_type": "property", "smiles": None, "limit": 201, "filters": [
        {"field": "MolecularWeight", "minimum": 180, "maximum": 181},
        {"field": "TPSA", "minimum": 60, "maximum": 70}, {"field": "Charge", "minimum": 0, "maximum": 0}]},
])
def test_live_pubchem_additional_modes(tmp_path, monkeypatch, changes):
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("DATASET_QA_ARTIFACT_SIGNING_KEY", SECRET)
    monkeypatch.setenv("DATASET_QA_ARTIFACT_BASE_URL", "https://testserver/api/piflow/v1/mcp")
    args = query_args(**{"filters": None, "limit": 3, "properties": list(backend.PUBCHEM_PROPERTIES), **changes})
    started = time.perf_counter()
    result = run_query(args)
    assert result["record_count"] == args["limit"] and result["target_met"] is True, {k: result[k] for k in ("record_count", "status", "stop_reason")}
    rows = [json.loads(line) for line in next(tmp_path.glob("*/*/data.jsonl")).read_text(encoding="utf-8").splitlines()]
    assert all(set(row) == {"CID", "SMILES", *backend.PUBCHEM_PROPERTIES} for row in rows)
    assert all(type(row["Charge"]) is int for row in rows)
    for rule in args["filters"] or []:
        assert all(rule["minimum"] <= row[rule["field"]] <= rule["maximum"] for row in rows)
    print({"mode": args["search_type"], "rows": result["record_count"], "seconds": round(time.perf_counter()-started, 2),
        "coverage": result["coverage"], "stop": result["stop_reason"]})
