"""Opt-in REAL MODEL acceptance with explicitly SIMULATED upstream data.

PowerShell (credentials must already exist in the process environment)::

    $env:DATASET_QA_LIVE_SEQUENCE = '1'
    python -m pytest scientific_agents/dataset_qa/tests/test_model_sequence_live.py -q -s --tb=short

Uses Dialogue and the configured provider/model by default. API_KEY is accepted
as a test-process-only fallback for LLM_API_KEY. No key or provider URL is read
into a report. DATASET_QA_LIVE_REPORT_DIR optionally receives sanitized JSON.
DATASET_QA_LIVE_REPEATS (default 1) repeats each scenario in fresh sessions.
TB_CHAT_URL optionally overrides the API base URL for this test client only;
DATASET_QA_LIVE_MODEL_NAME optionally overrides its model name. Neither edits
production settings. The existing provider non-thinking options are retained.

Only corpus retrieval and PubChem HTTP response bodies are simulated. Actual
corpus MCP schemas, HTTP transport, planning, validation, runtime, local signed
artifacts, CSV export, and HTTP downloads are exercised. Chemistry fixture rows
are synthetic and provide NO evidence of PubChem accuracy or availability.
No model decision, correction, plan, or continuation is supplied by this test.
For real PubChem upstream I/O use test_workflow_live.py instead.
"""
import asyncio
from copy import deepcopy
import csv
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import time

from fastmcp import Client
import httpx
import pytest

from mcp_servers import corpus_mcp
from services import corpus_connector_service as connector
from ..artifacts import execution_metadata
from ..contracts import Server
from ..dialogue import Dialogue
from ..execution import Execution
from ..mcp import MCPGateway, ToolSession
from ..search import SearchRun, normalize_keyword
from ..service import DatasetQA
from .test_artifact_download_origin import http_mcp
from .test_dataset_qa import collect, engine, result_cards, session
from .test_decisions import payload


STATION = {
    "id": "acceptance-station", "cstr": "ST001-CAMPBELL-B001",
    "title": "共和县光伏观测站campbell仪器观测数据集",
    "description": "模拟验收数据：共和县光伏观测站的气象和辐射观测。",
    "source": "地球系统数值模拟装置", "format": "JSONL", "size": "2 files",
}
SMILES = "CC(=O)OC1=CC=CC=C1C(=O)O"
CATALOG_TURNS = (
    ("search", "我想找共和县光伏观测站相关的数据集"),
    ("detail", "看下这个数据集的详情"),
    ("directory", "看下目录结构"),
)
COMPOUND_TURN = ("compounds_80_1000",
    "我想从 PubChem 找一批和这个分子相似的化合物，用来做后续筛选，"
    f"SMILES 是 {SMILES}。相似度至少 80%，分子量在 100 到 500 之间，"
    "LogP 在 -1 到 5 之间，先帮我找1000 条。并保存为csv文件格式")
CHANGED_TURN = ("compounds_90_100", "其他条件不变，把相似度改成90%，只要100条，并保存为CSV文件。")
SCENARIOS = {
    "catalog_separate": CATALOG_TURNS,
    "compounds_separate": (COMPOUND_TURN, CHANGED_TURN),
    "same_session": (*CATALOG_TURNS, COMPOUND_TURN, CHANGED_TURN),
}


class AcceptanceFailure(Exception):
    """Fixed harness-owned failure text, safe to include in reports."""


def require(condition, message):
    """Avoid pytest rendering raw receipts, signed URLs or provider exceptions."""
    if not condition:
        raise AcceptanceFailure(message)


def scrub_text(value, limit=6000):
    """Keep answer wording/link labels while removing URLs and bearer material."""
    value = str(value)
    secrets = {secret for name, secret in os.environ.items()
        if len(secret) >= 6 and re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", name, re.I)}
    for secret in sorted(secrets, key=len, reverse=True):
        value = value.replace(secret, "<redacted>")
    value = re.sub(r"https?://[^\s<>\]\)]+", "<url>", value)
    value = re.sub(r"\bv[12]\.[A-Za-z0-9_.-]+", "<resource-token>", value)
    value = re.sub(r"\b[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{32,}\b", "<token>", value)
    value = re.sub(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b", "<opaque-id>", value)
    return value[:limit]


def safe_correction(error):
    """Only schema paths/constraints and explicit runtime guidance, never str(error)."""
    result = {"code": scrub_text(error.code, 80)}
    detail = error.detail if isinstance(error.detail, dict) else {}
    for name in ("path", "paths", "constraint", "guidance", "reason", "step", "parameter"):
        item = detail.get(name)
        if isinstance(item, str):
            result[name] = scrub_text(item, 900 if name == "guidance" else 180)
        elif isinstance(item, list):
            result[name] = [part if type(part) is int else scrub_text(part, 120) for part in item[:12]]
    errors = detail.get("errors")
    if isinstance(errors, list):
        result["errors"] = [safe_correction(SimpleCorrection(item)) for item in errors[:3] if isinstance(item, dict)]
    return result


class SimpleCorrection:
    def __init__(self, detail):
        self.code, self.detail = "schema_validation", detail


def final_answer(events):
    text = ""
    for event in events:
        if event.get("type") == "message" and isinstance(event.get("text"), str):
            text = event["text"] if event.get("mode") == "replace" else text + event["text"]
    return scrub_text(text)


def safe_arguments(value):
    """Keep public business constraints and plan structure; redact opaque refs."""
    public = {"query", "smiles", "similarity_threshold", "filters", "limit", "format", "cstr", "file_id",
        "title", "field", "subject", "author", "doi", "sources", "page", "page_size", "minimum", "maximum",
        "server", "group", "offset", "planning", "continuation", "steps", "plan", "arguments", "tool", "key",
        "depends_on", "goals", "description", "output", "outcomes", "produces", "kind", "checks", "requires",
        "__qa_task", "complete_request", "keywords", "original_keywords"}
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            name = key if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,80}", key) else "<non-schema-key>"
            if key == "object":
                result[name] = item if item is None or isinstance(item, str) and re.fullmatch(
                    r"(?:current|(?:candidate|object|selected):[0-9]{1,6})", item) else "<redacted:opaque-handle>"
            else:
                result[name] = safe_arguments(item) if key in public else "<redacted>"
        return result
    if isinstance(value, list):
        return [safe_arguments(item) for item in value[:24]]
    if isinstance(value, str):
        return scrub_text(value, 1000)
    return value


def safe_exception(error, depth=0, seen=None):
    """Expose provider/transport failure identity without exception text or URLs."""
    seen = set() if seen is None else seen
    result = {"type": type(error).__name__}
    if id(error) in seen or depth >= 4:
        result["chain_truncated"] = True
        return result
    seen.add(id(error))
    status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    if type(status) is int and 100 <= status <= 599:
        result["status"] = status
    sensitive_values = [value for name, value in os.environ.items()
        if value and re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", name, re.I)]

    def code(value):
        if type(value) is int:
            return value
        if (isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:-]{0,63}", value)
                and not any(secret in value for secret in sensitive_values)):
            return value
        return None

    for name in ("code", "type", "param", "errno"):
        value = code(getattr(error, name, None))
        if value is not None:
            result["provider_" + name if name == "type" else name] = value
    body = getattr(error, "body", None)
    detail = body.get("error", body) if isinstance(body, dict) else None
    if isinstance(detail, dict):
        result["provider"] = {name: value for name in ("code", "type", "param")
            if (value := code(detail.get(name))) is not None}
    # Known local transport failures need a stable category when no status/code exists.
    message = str(error).casefold()
    phrases = {"event loop is closed": "event_loop_closed", "client has been closed": "client_closed",
        "different event loop": "different_event_loop", "connection refused": "connection_refused",
        "timed out": "timeout", "credentials are missing": "credentials_missing"}
    categories = [category for phrase, category in phrases.items() if phrase in message]
    if categories:
        result["categories"] = categories
    cause = error.__cause__ or error.__context__
    if cause is not None:
        result["cause"] = safe_exception(cause, depth + 1, seen)
    if isinstance(error, BaseExceptionGroup):
        result["children"] = [safe_exception(child, depth + 1, seen) for child in error.exceptions[:3]]
    return result


def type_tree(value, depth=0):
    """Record argument JSON types, never argument string values."""
    if depth >= 7:
        return type(value).__name__
    if isinstance(value, dict):
        return {key if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,80}", key) else "<non-schema-key>":
            type_tree(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        unique = []
        for item in value:
            shape = type_tree(item, depth + 1)
            if shape not in unique:
                unique.append(shape)
        return {"type": "array", "length": len(value), "items": unique}
    return {type(None): "null", str: "string", bool: "boolean", int: "integer", float: "number"}.get(type(value), type(value).__name__)


class ObservedDialogue(Dialogue):
    """Observe real streaming output; pass every model chunk through untouched."""
    def __init__(self):
        super().__init__()
        self.rounds = []

    def _model(self):
        if self.model is None and (os.getenv("TB_CHAT_URL") or os.getenv("DATASET_QA_LIVE_MODEL_NAME")):
            from infra.config_loader import get_settings
            from infra.non_thinking import non_thinking_options
            settings = get_settings()
            provider = settings.providers[settings.llm.provider]
            key = os.getenv(provider.api_key_env or "LLM_API_KEY") or os.getenv("LLM_API_KEY")
            if not key:
                raise RuntimeError("Model credentials are missing")
            model = os.getenv("DATASET_QA_LIVE_MODEL_NAME") or settings.llm.model
            base_url = (os.getenv("TB_CHAT_URL") or provider.base_url).rstrip("/")
            if base_url.endswith("/chat/completions"):
                base_url = base_url[:-len("/chat/completions")]
            self.model = self._create_model(model=model, api_key=key, base_url=base_url,
                temperature=settings.llm.temperature, timeout=self.limits.model_timeout,
                max_retries=1, max_tokens=self.limits.output_tokens,
                **non_thinking_options(provider=settings.llm.provider, model=model, base_url=base_url))
        return super()._model()

    async def respond(self, messages, definitions):
        entry = {"round": len(self.rounds) + 1, "tool_calls": [],
            "definitions_sha256": hashlib.sha256(json.dumps(definitions, sort_keys=True).encode()).hexdigest()}
        self.rounds.append(entry)
        started, merged = time.perf_counter(), None
        try:
            async for chunk in super().respond(messages, definitions):
                merged = chunk if merged is None else merged + chunk
                yield chunk
        except Exception as exc:
            entry["exception"] = safe_exception(exc)
            raise
        finally:
            entry["seconds"] = round(time.perf_counter() - started, 3)
            if merged is not None:
                entry["tool_calls"] = [{"name": call["name"], "argument_types": type_tree(call["args"]),
                    "public_arguments": safe_arguments(call["args"])}
                    for call in merged.tool_calls]
                entry["invalid_tool_calls"] = len(merged.invalid_tool_calls)
                entry["reply_characters"] = len(str(merged.content))


class SimulatedUpstream:
    """Faithful response envelopes, without touching real corpus/PubChem."""
    def __init__(self):
        self.calls = []

    def search(self, *, page_num=1, page_size=5, filters=None):
        self.calls.append("corpus_search")
        filters = filters or {}
        keywords = str(filters.get("keywords") or "").split()
        matches = all(word.casefold() in json.dumps(STATION, ensure_ascii=False).casefold() for word in keywords)
        matches = matches and not any(filters.get(key) for key in ("field", "subject", "author", "doi"))
        matches = matches and (not filters.get("sources") or STATION["source"] in filters["sources"])
        items = [deepcopy(STATION)] if matches else []
        start = (page_num - 1) * page_size
        return {"items": items[start:start + page_size],
            "pagination": {"pageNum": page_num, "pageSize": page_size, "total": len(items)}}

    def detail(self, cstr):
        self.calls.append("corpus_detail")
        if cstr != STATION["cstr"]:
            raise ValueError("Unknown simulated dataset identifier")
        return deepcopy(STATION)

    def directory(self, cstr, *, file_id=None):
        self.calls.append("corpus_directory")
        if cstr != STATION["cstr"] or file_id is not None:
            raise ValueError("Unknown simulated directory identifier")
        return {"code": 200, "data": [
            {"fileId": "fixture-observations", "name": "observations.jsonl", "isFile": True,
                "path": "/observations.jsonl", "downloadUrl": "https://fixtures.invalid/observations.jsonl"},
            {"fileId": "fixture-readme", "name": "README.txt", "isFile": True,
                "path": "/README.txt", "downloadUrl": "https://fixtures.invalid/README.txt"},
        ]}

    def pubchem(self, client, route, data, params, root, deadline):
        if "fastsimilarity_2d" in route:
            self.calls.append("pubchem_similarity")
            # Distinct synthetic candidate sets expose accidental prior-turn reuse.
            cids = list(range(20001, 20181)) if params["Threshold"] >= 90 else list(range(1, 1401))
            return {"IdentifierList": {"CID": [*cids, cids[0]]}}
        if route != "/compound/cid/property/SMILES,MolecularWeight,XLogP/JSON":
            raise ValueError("Unsupported simulated PubChem endpoint")
        self.calls.append("pubchem_properties")
        rows = []
        for cid in map(int, data["cid"].split(",")):
            row = {"CID": cid, "SMILES": SMILES, "MolecularWeight": "501" if cid % 11 == 0 else "180.16"}
            if cid % 13:
                row["XLogP"] = 1.2
            rows.append(row)
        return {"PropertyTable": {"Properties": rows}}


@pytest.fixture
def simulated_upstream(monkeypatch, tmp_path, caplog):
    # All real file side effects are temporary; runtime signing keys stay in memory.
    monkeypatch.setenv("DATASET_QA_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.delenv("DATASET_QA_ARTIFACT_BASE_URL", raising=False)
    monkeypatch.delenv("DATASET_QA_ARTIFACT_SIGNING_KEY", raising=False)
    caplog.set_level(logging.CRITICAL)
    backend = SimulatedUpstream()
    monkeypatch.setattr(corpus_mcp, "list_dataset_details", backend.search)
    monkeypatch.setattr(corpus_mcp, "get_dataset_detail_by_cstr", backend.detail)
    monkeypatch.setattr(corpus_mcp, "get_dataset_directory", backend.directory)
    monkeypatch.setattr(connector, "_pubchem_request", backend.pubchem)

    def unsupported(*args, **kwargs):
        raise ValueError("This optional upstream operation is not simulated in the acceptance fixture")

    # Fail locally if the model incorrectly chooses an unrelated external reader.
    for name in ("get_dataset_sampler", "get_file_schema", "get_file_records"):
        if hasattr(corpus_mcp, name):
            monkeypatch.setattr(corpus_mcp, name, unsupported)
    return backend


def query_arguments(threshold=80, limit=1000):
    # Used only as expected assertions and direct non-model fixture smoke input.
    return {"smiles": SMILES, "similarity_threshold": threshold, "limit": limit,
        "filters": [{"field": "MolecularWeight", "minimum": 100, "maximum": 500},
            {"field": "XLogP", "minimum": -1, "maximum": 5}]}


async def verify_csv(output, base, threshold, limit):
    require(output.get("resource", {}).get("format") == "csv", "Expected a CSV result resource")
    require(output.get("record_count") == limit, "CSV count differs from requested fixture count")
    require(output.get("target_count") == limit and output.get("target_met") is True, "Target-count metadata mismatch")
    require(output.get("query", {}).get("similarity_threshold") == threshold, "CSV inherited stale similarity settings")
    require(output.get("downloadUrl", "").startswith(base + "/artifacts/"), "Download is not the local artifact endpoint")
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(output["downloadUrl"])
        partial = await client.get(output["downloadUrl"], headers={"Range": "bytes=0-15"})
    require(response.status_code == 200 and partial.status_code == 206, "Artifact HTTP or range download failed")
    require("attachment" in response.headers.get("content-disposition", ""), "CSV is not delivered as an attachment")
    require(hashlib.sha256(response.content).hexdigest() == output["resource"]["sha256"], "Downloaded bytes fail integrity check")
    rows = list(csv.DictReader(io.StringIO(response.text)))
    require(len(rows) == limit and len({row["CID"] for row in rows}) == limit, "CSV row count or uniqueness mismatch")
    require(all(100 <= float(row["MolecularWeight"]) <= 500 and -1 <= float(row["XLogP"]) <= 5 for row in rows), "CSV rows violate property constraints")
    require(all((int(row["CID"]) >= 20001) == (threshold >= 90) for row in rows), "CSV contains stale previous-query records")
    return {"format": "csv", "rows": len(rows), "unique_cids": len(rows), "http": [200, 206], "sha256_verified": True}


def verify_search(calls, saved):
    """Accept exact lookup or genuinely completed bounded broad discovery."""
    require(bool(calls) and all(name == "search_corpus_datasets" for name, _ in calls),
        "Search performed an unrelated MCP operation")
    require(all(isinstance(args.get("query"), str) and args["query"].strip() for _, args in calls),
        "Search omitted the requested dataset keywords")
    runs = [item["search"] for item in saved.get("operations", []) if item.get("search")]
    if not runs:
        require(len(calls) == 1, "An exact lookup unexpectedly repeated retrieval")
        return {"mode": "exact", "calls": 1}
    require(len(runs) == 1, "Broad discovery split one requested topic into new search outcomes")
    search = SearchRun(runs[0])
    view = search.view()
    require(view["done"] and view["stop"] in {"enough", "exhausted"}, "Broad discovery did not satisfy its runtime stop policy")
    require(len(runs[0]["keywords"]) <= search.maximum_keywords, "Search exceeded its declared keyword budget")
    # This fixture has one candidate and no additional pages. Multiple useful
    # model-selected keywords are valid; forcing one call would reject a valid
    # four-keyword completion under the actual default broad-search policy.
    requests = [(normalize_keyword(args["query"]), args.get("page", 1)) for _, args in calls]
    require(len(requests) == len(set(requests)) and len(calls) <= search.maximum_keywords,
        "Search repeated a completed page or exceeded the fixture retrieval bound")
    if view["stop"] == "enough":
        require(view["unique_count"] >= search.minimum, "Early search stop lacked enough actual unique candidates")
    else:
        completed = {normalize_keyword(keyword) for keyword in runs[0]["completed"]}
        require(len(completed) == search.maximum_keywords, "Search declared exhaustion before completing the keyword policy")
    return {"mode": "broad", **view}


def test_simulated_upstream_contract_and_artifacts(simulated_upstream):
    """Offline harness smoke: real MCP/storage/export, explicitly no real model."""
    async def run():
        async with http_mcp("/api/piflow/v1/mcp") as base:
            async with Client(base + "/") as client:
                names = {tool.name for tool in await client.list_tools()}
                require({"search_corpus_datasets", "get_corpus_dataset_detail", "get_corpus_dataset_directory",
                    "query_pubchem_compounds", "export_dataset"} <= names, "Missing actual corpus schemas")
                found = await client.call_tool("search_corpus_datasets", {"query": "共和县光伏观测站"})
                require(found.structured_content["items"][0]["cstr"] == STATION["cstr"], "Search fixture shape mismatch")
                for name in ("get_corpus_dataset_detail", "get_corpus_dataset_directory"):
                    require(not (await client.call_tool(name, {"cstr": STATION["cstr"]})).is_error, "Retrieval fixture shape mismatch")
                for threshold, limit in ((80, 1000), (90, 100)):
                    args = query_arguments(threshold, limit)
                    queried = await client.call_tool("query_pubchem_compounds", args,
                        meta=execution_metadata("fixture-owner", str(threshold), args, 120))
                    args = {"source_ref": queried.structured_content["resource"]["source_ref"], "format": "csv"}
                    exported = await client.call_tool("export_dataset", args,
                        meta=execution_metadata("fixture-owner", "export-" + str(threshold), args, 120))
                    await verify_csv(exported.structured_content, base, threshold, limit)
    asyncio.run(run())


@pytest.mark.skipif(os.getenv("DATASET_QA_LIVE_SEQUENCE") != "1", reason="Opt-in real model; simulated corpus/PubChem upstream")
@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_real_model_acceptance_sequence(engine, simulated_upstream, tmp_path, monkeypatch, scenario):
    from infra.config_loader import get_settings
    settings = get_settings()
    provider = settings.providers[settings.llm.provider]
    if not (os.getenv(provider.api_key_env or "LLM_API_KEY") or os.getenv("LLM_API_KEY")) and os.getenv("API_KEY"):
        monkeypatch.setenv("LLM_API_KEY", os.environ["API_KEY"])
    if not (os.getenv(provider.api_key_env or "LLM_API_KEY") or os.getenv("LLM_API_KEY")):
        pytest.fail("Configured model credentials are absent. Set the configured provider key, LLM_API_KEY, or API_KEY in the process environment.", pytrace=False)
    repeats = int(os.getenv("DATASET_QA_LIVE_REPEATS", "1"))
    require(1 <= repeats <= 20, "DATASET_QA_LIVE_REPEATS must be between 1 and 20")
    reports, active = [], {}
    original_call, original_correct = ToolSession.call, Execution.correct

    async def capture_call(tools, alias, arguments, **kwargs):
        active["calls"].append((tools.loaded[alias].name, deepcopy(arguments)))
        return await original_call(tools, alias, arguments, **kwargs)

    def capture_correction(execution, error, limit, **kwargs):
        active["corrections"].append(error.code)
        active["correction_details"].append(safe_correction(error))
        return original_correct(execution, error, limit, **kwargs)

    monkeypatch.setattr(ToolSession, "call", capture_call)
    monkeypatch.setattr(Execution, "correct", capture_correction)

    async def run():
        for repeat in range(repeats):
            async with http_mcp("/api/piflow/v1/mcp") as base:
                dialogue = ObservedDialogue()
                service = DatasetQA(engine, dialogue, MCPGateway({"piflow-corpus": Server(base + "/")}))
                sid = session(service, request=f"{scenario}-{repeat}")
                previous_source = None
                try:
                    for label, utterance in SCENARIOS[scenario]:
                        active.update(calls=[], corrections=[], correction_details=[])
                        started, first_round = time.perf_counter(), len(dialogue.rounds)
                        upstream_start = len(simulated_upstream.calls)
                        report = {"scenario": scenario, "repeat": repeat + 1, "turn": label, "model": "real configured Dialogue",
                            "upstream": "SIMULATED corpus retrieval and PubChem HTTP responses", "correct": False}
                        reports.append(report)
                        try:
                            events = await collect(service, sid, utterance, rid=label)
                            report["final_answer"] = final_answer(events)
                            saved = payload(service, sid, events)
                            report["status"] = events[-1].get("status")
                            report["error_code"] = saved.get("error", {}).get("error_code")
                            report["operation_states"] = [item.get("state") for item in saved.get("operations", [])]
                            require(events[-1].get("status") == "COMPLETED" and not events[-1].get("outcome") and not saved.get("error"), "Turn did not complete all requested work")
                            cards = result_cards(events)
                            report["result_types"] = [card.get("view_type") for card in cards]
                            names = [name for name, _ in active["calls"]]
                            if label.startswith("compounds_"):
                                threshold, limit = (80, 1000) if label == "compounds_80_1000" else (90, 100)
                                require(names == ["query_pubchem_compounds", "export_dataset"], "Expected exactly one query and one export for this request")
                                require(report["operation_states"] == ["succeeded", "succeeded"], "Expected two successful compound operations")
                                acceptance = saved.get("plan", {}).get("acceptance", {})
                                require(bool(acceptance) and all(item["state"] == "accepted" for item in acceptance.values()), "Compound outcomes were not all accepted")
                                args = active["calls"][0][1]
                                expected = query_arguments(threshold, limit)
                                for key in ("smiles", "similarity_threshold", "limit"):
                                    require(args.get(key) == expected[key] and type(args.get(key)) is type(expected[key]), "Query value/type mismatch: " + key)
                                require(isinstance(args.get("filters"), list), "filters must be an actual JSON array")
                                rules = {item["field"]: item for item in args["filters"]}
                                require(len(args["filters"]) == 2 and rules == {item["field"]: item for item in expected["filters"]}, "Property filters differ from user constraints")
                                require(all(type(item[key]) in (int, float) for item in rules.values() for key in ("minimum", "maximum")), "Filter bounds must have JSON number types")
                                outputs = [item for card in cards for item in card["data"]["items"]
                                    if isinstance(item, dict) and item.get("resource", {}).get("format") == "csv"]
                                require(len(outputs) == 1, "Expected one delivered CSV result")
                                report["artifact"] = await verify_csv(outputs[0], base, threshold, limit)
                                source = active["calls"][1][1]["source_ref"]
                                require(source != previous_source, "Changed constraints reused the earlier query resource")
                                previous_source = source
                                report["constraints"] = {"threshold": threshold, "limit": limit, "filters_are_array": True}
                            else:
                                expected_name = {"search": "search_corpus_datasets", "detail": "get_corpus_dataset_detail",
                                    "directory": "get_corpus_dataset_directory"}[label]
                                if label == "search":
                                    report["search"] = verify_search(active["calls"], saved)
                                else:
                                    require(names == [expected_name], "Unexpected retrieval sequence for " + label)
                                require(bool(cards), "Retrieval did not deliver a result card")
                                require(("observations.jsonl" if label == "directory" else STATION["cstr"]) in json.dumps(cards), "Delivered retrieval card is missing expected fixture evidence")
                                if label != "search":
                                    require(active["calls"][0][1].get("cstr") == STATION["cstr"], "Current dataset reference was not preserved")
                                if label == "directory":
                                    require(active["calls"][0][1].get("file_id") is None, "Root directory used a guessed file identifier")
                            report["correct"] = True
                        except Exception as exc:
                            report["failure_type"] = type(exc).__name__
                            report["exception"] = safe_exception(exc)
                            # Only our fixed assertion text is safe; provider exceptions may contain URLs.
                            if isinstance(exc, AcceptanceFailure):
                                report["failure"] = str(exc)
                            raise
                        finally:
                            report.update(seconds=round(time.perf_counter() - started, 3),
                                model_calls=len(dialogue.rounds) - first_round,
                                model_trace=dialogue.rounds[first_round:], corrections=list(active["corrections"]),
                                correction_details=list(active["correction_details"]),
                                correction_count=len(active["corrections"]), mcp_call_count=len(active["calls"]),
                                simulated_upstream_calls=simulated_upstream.calls[upstream_start:],
                                mcp_calls=[{"name": name, "argument_types": type_tree(args),
                                    "public_arguments": safe_arguments(args)} for name, args in active["calls"]])
                            print("DATASET_QA_LIVE_TURN " + json.dumps({key: report[key] for key in
                                ("scenario", "repeat", "turn", "correct", "seconds", "model_calls", "mcp_call_count", "corrections")}), flush=True)
                finally:
                    await service.close()

    failure = None
    try:
        asyncio.run(run())
    except Exception as exc:
        failure = type(exc).__name__
    finally:
        destination = Path(os.getenv("DATASET_QA_LIVE_REPORT_DIR") or tmp_path)
        destination.mkdir(parents=True, exist_ok=True)
        summary = {"scenario": scenario, "real_model": True, "simulated_upstream": True,
            "repeats": repeats, "correct": failure is None, "failure_type": failure, "turns": reports}
        (destination / (scenario + ".json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print("DATASET_QA_LIVE_REPORT " + json.dumps(summary, ensure_ascii=False))
    if failure is not None:
        pytest.fail("Real-model acceptance failed; see sanitized DATASET_QA_LIVE_REPORT (" + failure + ").", pytrace=False)
