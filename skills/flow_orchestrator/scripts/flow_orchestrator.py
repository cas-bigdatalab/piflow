"""
Flow orchestrator for assembling operator + datasource JSON into a complete flow JSON.
"""

from __future__ import annotations

import importlib.util
import json
import uuid
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path
from typing import Any

from runtime.workspace_manager import WorkspaceManager


NODE_TYPE_PRIORITY = {
    "source": 0,
    "compute": 1,
    "sink": 2,
}

REQUIRED_SOURCE_STOP_KEYS = {
    "customizedProperties",
    "dataSourceId",
    "dataCenter",
    "registerId",
    "sourceType",
    "webAddress",
    "name",
    "uuid",
    "bundle",
    "properties",
}


def _parse_ports(raw: Any) -> list[str]:
    if not isinstance(raw, str):
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _safe_lower(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.lower().strip()


def _discover_operator_scripts(skills_root: Path) -> list[Path]:
    scripts: list[Path] = []
    for script in skills_root.glob("*/scripts/*.py"):
        if script.name == "__init__.py":
            continue
        if script.parent.parent.name == "flow_orchestrator":
            continue
        scripts.append(script)
    return sorted(scripts, key=lambda p: str(p))


def _load_module(script_path: Path):
    module_name = f"flow_orchestrator_{script_path.stem}_{abs(hash(str(script_path)))}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_operator_fragment(script_path: Path) -> tuple[dict[str, Any] | None, str]:
    module = _load_module(script_path)
    if module is None:
        return None, script_path.parent.parent.name

    emit_operator = getattr(module, "emit_operator", None)
    if not callable(emit_operator):
        return None, script_path.parent.parent.name

    fragment = emit_operator()
    if not isinstance(fragment, dict):
        return None, script_path.parent.parent.name

    if "operator_name" not in fragment or "stop" not in fragment:
        return None, script_path.parent.parent.name

    return fragment, script_path.parent.parent.name


def _load_operator_fragments() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    project_root = Path(__file__).resolve().parents[3]
    skills_root = project_root / "skills"

    fragments: dict[str, dict[str, Any]] = {}
    skill_name_by_operator: dict[str, str] = {}

    for script in _discover_operator_scripts(skills_root):
        fragment, skill_name = _load_operator_fragment(script)
        if fragment is None:
            continue

        operator_name = str(fragment["operator_name"]).strip()
        if not operator_name:
            continue
        if operator_name in fragments:
            continue

        fragments[operator_name] = fragment
        skill_name_by_operator[operator_name] = skill_name

    return fragments, skill_name_by_operator


def _build_alias_map(
    fragments: dict[str, dict[str, Any]],
    skill_name_by_operator: dict[str, str],
) -> dict[str, str]:
    aliases: dict[str, str] = {}

    for operator_name, fragment in fragments.items():
        stop_name = ""
        if isinstance(fragment.get("stop"), dict):
            stop_name = str(fragment["stop"].get("name", "")).strip()

        skill_name = skill_name_by_operator.get(operator_name, "")
        keys = {
            operator_name,
            _safe_lower(operator_name),
            stop_name,
            _safe_lower(stop_name),
            skill_name,
            _safe_lower(skill_name),
        }

        if skill_name.endswith("_operator"):
            base = skill_name[: -len("_operator")]
            keys.add(base)
            keys.add(_safe_lower(base))

        for key in keys:
            if key:
                aliases[key] = operator_name

    return aliases


def _normalize_selected(
    selected_operators: list[str] | str | None,
    aliases: dict[str, str],
) -> tuple[set[str], list[str]]:
    if selected_operators is None:
        return set(), []

    if isinstance(selected_operators, str):
        candidates = [x.strip() for x in selected_operators.split(",")]
    else:
        candidates = [str(x).strip() for x in selected_operators]

    selected: set[str] = set()
    original: list[str] = []

    for item in candidates:
        if not item:
            continue
        original.append(item)
        resolved = aliases.get(item) or aliases.get(_safe_lower(item))
        if resolved:
            selected.add(resolved)

    return selected, original


def _expand_dependencies(selected: set[str], fragments: dict[str, dict[str, Any]]) -> set[str]:
    expanded = set(selected)
    stack = list(selected)
    while stack:
        current = stack.pop()
        fragment = fragments.get(current)
        if not fragment:
            continue
        for dep in fragment.get("requires", []):
            dep_name = str(dep).strip()
            if dep_name in fragments and dep_name not in expanded:
                expanded.add(dep_name)
                stack.append(dep_name)
    return expanded


def _add_reachable_sinks(selected: set[str], fragments: dict[str, dict[str, Any]]) -> set[str]:
    expanded = set(selected)
    changed = True
    while changed:
        changed = False
        for name, fragment in fragments.items():
            node_type = str(fragment.get("node_type", "")).strip().lower()
            if node_type != "sink" or name in expanded:
                continue
            requires = [str(x).strip() for x in fragment.get("requires", []) if str(x).strip()]
            if requires and all(dep in expanded for dep in requires):
                expanded.add(name)
                changed = True
    return expanded


def _node_sort_key(name: str, fragments: dict[str, dict[str, Any]]) -> tuple[int, str]:
    node_type = str(fragments.get(name, {}).get("node_type", "")).strip().lower()
    return NODE_TYPE_PRIORITY.get(node_type, 99), name


def _topological_order(selected: set[str], fragments: dict[str, dict[str, Any]]) -> list[str]:
    indegree = {name: 0 for name in selected}
    graph: dict[str, list[str]] = defaultdict(list)

    for name in selected:
        requires = [str(x).strip() for x in fragments[name].get("requires", []) if str(x).strip()]
        for dep in requires:
            if dep in selected:
                graph[dep].append(name)
                indegree[name] += 1

    queue = deque(sorted([n for n, d in indegree.items() if d == 0], key=lambda x: _node_sort_key(x, fragments)))
    ordered: list[str] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for nxt in sorted(graph[node], key=lambda x: _node_sort_key(x, fragments)):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) < len(selected):
        remaining = [n for n in selected if n not in set(ordered)]
        ordered.extend(sorted(remaining, key=lambda x: _node_sort_key(x, fragments)))

    return ordered


def _extract_inports(fragment: dict[str, Any]) -> list[str]:
    stop = fragment.get("stop", {})
    if not isinstance(stop, dict):
        return []
    props = stop.get("properties", {})
    if not isinstance(props, dict):
        return []
    return _parse_ports(props.get("inports"))


def _extract_outports(fragment: dict[str, Any]) -> list[str]:
    stop = fragment.get("stop", {})
    if not isinstance(stop, dict):
        return []
    props = stop.get("properties", {})
    if not isinstance(props, dict):
        return []
    return _parse_ports(props.get("outports"))


def _infer_outport(source_fragment: dict[str, Any], dep_index: int) -> str:
    source_type = str(source_fragment.get("node_type", "")).strip().lower()
    if source_type == "source":
        return ""
    outports = _extract_outports(source_fragment)
    if not outports:
        return ""
    if len(outports) == 1:
        return outports[0]
    if dep_index < len(outports):
        return outports[dep_index]
    return outports[0]


def _collect_explicit_edges(selected: set[str], fragments: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for name in selected:
        fragment = fragments[name]
        for key in ("paths", "edges"):
            raw = fragment.get(key, [])
            if not isinstance(raw, list):
                continue
            for edge in raw:
                if not isinstance(edge, dict):
                    continue
                source = str(edge.get("from", "")).strip()
                target = str(edge.get("to", "")).strip()
                if not source or not target:
                    continue
                if source not in selected or target not in selected:
                    continue
                edges.append(
                    {
                        "inport": str(edge.get("inport", "")).strip(),
                        "from": source,
                        "to": target,
                        "outport": str(edge.get("outport", "")).strip(),
                    }
                )
    return edges


def _build_operator_edges(
    selected_order: list[str],
    selected_set: set[str],
    fragments: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for target_name in selected_order:
        target_fragment = fragments[target_name]
        requires = [str(x).strip() for x in target_fragment.get("requires", []) if str(x).strip()]
        inports = _extract_inports(target_fragment)
        for idx, dep in enumerate(requires):
            if dep not in selected_set:
                continue
            source_fragment = fragments[dep]
            edges.append(
                {
                    "inport": inports[idx] if idx < len(inports) else "",
                    "from": dep,
                    "to": target_name,
                    "outport": _infer_outport(source_fragment, idx),
                }
            )
    return edges


def _dedupe_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    deduped: list[dict[str, str]] = []
    for edge in edges:
        key = (edge["from"], edge["to"], edge["inport"], edge["outport"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def _normalize_node_types(selected_node_types: list[str] | str | None) -> set[str]:
    if selected_node_types is None:
        return set()
    if isinstance(selected_node_types, str):
        values = [x.strip().lower() for x in selected_node_types.split(",")]
    else:
        values = [str(x).strip().lower() for x in selected_node_types]
    return {x for x in values if x}


def _normalize_dataset_stops(selected_dataset_stops: list[dict[str, Any]] | str | None) -> list[dict[str, Any]]:
    if selected_dataset_stops is None:
        return []

    if isinstance(selected_dataset_stops, str):
        raw = selected_dataset_stops.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
    else:
        parsed = selected_dataset_stops

    if isinstance(parsed, dict):
        parsed = [parsed]
    elif isinstance(parsed, str):
        return []
    elif not isinstance(parsed, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in parsed:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def _normalize_source_bindings(source_bindings: dict[str, str] | str | None) -> dict[str, str]:
    if source_bindings is None:
        return {}
    if isinstance(source_bindings, str):
        raw = source_bindings.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
    else:
        parsed = source_bindings

    if not isinstance(parsed, dict):
        return {}

    return {str(k).strip(): str(v).strip() for k, v in parsed.items() if str(k).strip() and str(v).strip()}


def _collect_required_source_names(
    selected_order: list[str],
    fragments: dict[str, dict[str, Any]],
    selected_set: set[str],
) -> list[str]:
    required: list[str] = []
    seen = set()
    for name in selected_order:
        requires = [str(x).strip() for x in fragments[name].get("requires", []) if str(x).strip()]
        for dep in requires:
            if dep in selected_set or dep in seen:
                continue
            seen.add(dep)
            required.append(dep)
    return required


def _dedupe_dataset_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for stop in stops:
        if not isinstance(stop, dict):
            continue
        key = (str(stop.get("dataSourceId", "")).strip(), str(stop.get("name", "")).strip())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(deepcopy(stop))
    return deduped


def _validate_complete_dataset_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for idx, stop in enumerate(stops):
        missing_keys = sorted([key for key in REQUIRED_SOURCE_STOP_KEYS if key not in stop])
        if missing_keys:
            invalid.append(
                {
                    "index": idx,
                    "name": str(stop.get("name", "")).strip(),
                    "missing_keys": missing_keys,
                }
            )
            continue

        for required_text_key in ("dataSourceId", "name", "bundle"):
            if not str(stop.get(required_text_key, "")).strip():
                invalid.append(
                    {
                        "index": idx,
                        "name": str(stop.get("name", "")).strip(),
                        "missing_keys": [required_text_key],
                    }
                )
                break

    return invalid


def _resolve_required_source_map(
    required_sources: list[str],
    selected_dataset_stops: list[dict[str, Any]],
    source_bindings: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    by_name: dict[str, dict[str, Any]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for stop in selected_dataset_stops:
        name = str(stop.get("name", "")).strip()
        ds_id = str(stop.get("dataSourceId", "")).strip()
        if name:
            by_name[name] = stop
        if ds_id:
            by_id[ds_id] = stop

    required_to_stop_name: dict[str, str] = {}
    missing: list[str] = []

    for required_name in required_sources:
        binding_token = source_bindings.get(required_name, "")
        matched_name = ""
        if binding_token:
            if binding_token in by_name:
                matched_name = binding_token
            elif binding_token in by_id:
                matched_name = str(by_id[binding_token].get("name", "")).strip()

        if not matched_name and required_name in by_name:
            matched_name = required_name

        if not matched_name:
            missing.append(required_name)
            continue

        required_to_stop_name[required_name] = matched_name

    return required_to_stop_name, missing


def _build_external_source_edges(
    selected_order: list[str],
    selected_set: set[str],
    fragments: dict[str, dict[str, Any]],
    required_to_stop_name: dict[str, str],
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for target_name in selected_order:
        target_fragment = fragments[target_name]
        requires = [str(x).strip() for x in target_fragment.get("requires", []) if str(x).strip()]
        inports = _extract_inports(target_fragment)
        for idx, dep in enumerate(requires):
            if dep in selected_set:
                continue
            source_stop_name = required_to_stop_name.get(dep, "")
            if not source_stop_name:
                continue
            edges.append(
                {
                    "inport": inports[idx] if idx < len(inports) else "",
                    "from": source_stop_name,
                    "to": target_name,
                    "outport": "",
                }
            )
    return edges


def _cache_flow(flow: dict[str, Any]) -> dict[str, Any]:
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    session_id = uuid.uuid4().hex
    file_name = f"dam_flow_{session_id}.json"
    abs_path = workspace.temp / file_name
    flow_payload = {"flow": flow}
    flow_json_text = json.dumps(flow_payload, ensure_ascii=False, indent=2)

    storage_mode = "temp_file"
    inline_flow_json_text = ""
    try:
        abs_path.write_text(flow_json_text, encoding="utf-8")
    except Exception:
        storage_mode = "inline"
        inline_flow_json_text = flow_json_text

    run_payload: dict[str, Any] = {"flow_session_id": session_id}
    if storage_mode != "temp_file":
        run_payload["flow_json_text"] = inline_flow_json_text

    return {
        "flow_session_id": session_id,
        "storage_mode": storage_mode,
        "run_payload": run_payload,
        "flow_payload": flow_payload,
        "flow_payload_json_text": flow_json_text,
        "flow_json_text": inline_flow_json_text if storage_mode == "inline" else "",
    }


def _build_dag_preview(flow: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []

    for stop in flow.get("stops", []):
        if not isinstance(stop, dict):
            continue
        bundle = str(stop.get("bundle", ""))
        if "CsvSave" in bundle:
            node_type = "sink"
        elif "HdfsPathToDf" in bundle or "CsvParser" in bundle:
            node_type = "source"
        else:
            node_type = "compute"
        nodes.append({"id": str(stop.get("name", "")), "type": node_type})

    for path in flow.get("paths", []):
        if not isinstance(path, dict):
            continue
        edges.append(
            {
                "from": str(path.get("from", "")),
                "to": str(path.get("to", "")),
                "inport": str(path.get("inport", "")),
                "outport": str(path.get("outport", "")),
            }
        )

    return {"nodes": nodes, "edges": edges}


def build_flow(
    selected_operators: list[str] | str | None = None,
    user_request: str = "",
    selected_dataset_stops: list[dict[str, object]] | str | None = None,
    source_bindings: dict[str, str] | str | None = None,
    selected_node_types: list[str] | str | None = None,
    flow_name: str = "协同智能编排",
    include_dependencies: bool = True,
    include_reachable_sinks: bool = True,
    executor_number: str = "1",
    driver_memory: str = "1g",
    executor_memory: str = "1g",
    executor_cores: str = "1",
) -> dict[str, Any]:
    """
    Assemble a full flow JSON from selected algorithm operators and selected datasource stops.
    """
    fragments, skill_name_by_operator = _load_operator_fragments()
    aliases = _build_alias_map(fragments, skill_name_by_operator)

    selected_from_inputs, original_inputs = _normalize_selected(selected_operators, aliases)
    selected = set(selected_from_inputs)
    available = set(fragments.keys())
    request_text = str(user_request or "").strip()

    fallback_to_all = False
    if not selected and selected_operators is None and not request_text:
        selected = set(available)
        fallback_to_all = True

    node_types = _normalize_node_types(selected_node_types)
    if node_types:
        selected = {
            name
            for name in selected
            if str(fragments[name].get("node_type", "")).strip().lower() in node_types
        }

    if include_dependencies:
        selected = _expand_dependencies(selected, fragments)
    if include_reachable_sinks:
        selected = _add_reachable_sinks(selected, fragments)

    selected_order = _topological_order(selected, fragments)
    selected_set = set(selected_order)

    required_sources = _collect_required_source_names(selected_order, fragments, selected_set)
    normalized_dataset_stops = _dedupe_dataset_stops(_normalize_dataset_stops(selected_dataset_stops))
    normalized_source_bindings = _normalize_source_bindings(source_bindings)
    required_to_stop_name, missing_required_sources = _resolve_required_source_map(
        required_sources=required_sources,
        selected_dataset_stops=normalized_dataset_stops,
        source_bindings=normalized_source_bindings,
    )

    algorithm_stops = [deepcopy(fragments[name]["stop"]) for name in selected_order]
    stops = normalized_dataset_stops + algorithm_stops

    explicit_edges = _collect_explicit_edges(set(selected_order), fragments)
    inferred_operator_edges = _build_operator_edges(selected_order, selected_set, fragments)
    external_source_edges = _build_external_source_edges(
        selected_order=selected_order,
        selected_set=selected_set,
        fragments=fragments,
        required_to_stop_name=required_to_stop_name,
    )
    paths = _dedupe_edges(explicit_edges + inferred_operator_edges + external_source_edges)

    invalid_inputs = sorted(
        x
        for x in original_inputs
        if (aliases.get(x) or aliases.get(_safe_lower(x))) not in fragments
    )

    if fallback_to_all:
        selection_mode = "all"
    elif not selected_order:
        selection_mode = "none"
    else:
        selection_mode = "explicit"

    return {
        "flow": {
            "executorNumber": str(executor_number),
            "driverMemory": str(driver_memory),
            "executorMemory": str(executor_memory),
            "executorCores": str(executor_cores),
            "name": flow_name,
            "uuid": uuid.uuid4().hex,
            "stops": stops,
            "paths": paths,
        },
        "meta": {
            "selected_operators": selected_order,
            "invalid_operators": invalid_inputs,
            "available_operators": sorted(available),
            "required_sources": required_sources,
            "bound_sources": required_to_stop_name,
            "missing_required_sources": missing_required_sources,
            "selected_dataset_names": [str(x.get("name", "")).strip() for x in normalized_dataset_stops],
            "selection_mode": selection_mode,
            "user_request": request_text,
        },
    }


def plan_analysis(
    user_request: str = "",
    selected_operators: list[str] | str | None = None,
    include_dependencies: bool = True,
    include_reachable_sinks: bool = True,
) -> dict[str, Any]:
    """
    Stage-1: return selected operators and required datasource names.
    """
    assembled = build_flow(
        selected_operators=selected_operators,
        user_request=user_request,
        selected_dataset_stops=[],
        source_bindings={},
        include_dependencies=include_dependencies,
        include_reachable_sinks=include_reachable_sinks,
    )

    meta = assembled.get("meta", {})
    selected = [str(x) for x in meta.get("selected_operators", [])]
    analysis_name = user_request.strip() or " / ".join(selected) or "未识别分析"

    operator_stops: list[dict[str, Any]] = []
    for stop in assembled.get("flow", {}).get("stops", []):
        if not isinstance(stop, dict):
            continue
        if "dataSourceId" in stop:
            continue
        operator_stops.append(deepcopy(stop))

    return {
        "analysis_name": analysis_name,
        "selected_operators": selected,
        "required_sources": [str(x) for x in meta.get("required_sources", [])],
        "operator_stops": operator_stops,
        "selection_mode": str(meta.get("selection_mode", "")),
        "invalid_operators": [str(x) for x in meta.get("invalid_operators", [])],
    }


def build_flow_with_selected_sources(
    selected_operators: list[str] | str,
    selected_dataset_stops: list[dict[str, object]] | str,
    source_bindings: dict[str, str] | str | None = None,
    flow_name: str = "协同智能编排",
    include_dependencies: bool = True,
    include_reachable_sinks: bool = True,
    executor_number: str = "1",
    driver_memory: str = "1g",
    executor_memory: str = "1g",
    executor_cores: str = "1",
) -> dict[str, Any]:
    """
    Stage-2: assemble full flow JSON using selected datasource JSON + selected operators.
    Also caches the flow JSON for stage-3 execution.
    """
    normalized_selected_dataset_stops = _dedupe_dataset_stops(_normalize_dataset_stops(selected_dataset_stops))
    if not normalized_selected_dataset_stops:
        raise ValueError(
            "selected_dataset_stops must be a non-empty list of full datasource stop JSON objects."
        )

    invalid_dataset_stops = _validate_complete_dataset_stops(normalized_selected_dataset_stops)
    if invalid_dataset_stops:
        raise ValueError(
            "selected_dataset_stops must be full datasource stop JSON objects. "
            f"invalid_items={json.dumps(invalid_dataset_stops, ensure_ascii=False)}"
        )

    assembled = build_flow(
        selected_operators=selected_operators,
        selected_dataset_stops=normalized_selected_dataset_stops,
        source_bindings=source_bindings,
        flow_name=flow_name,
        include_dependencies=include_dependencies,
        include_reachable_sinks=include_reachable_sinks,
        executor_number=executor_number,
        driver_memory=driver_memory,
        executor_memory=executor_memory,
        executor_cores=executor_cores,
    )
    cached = _cache_flow(assembled["flow"])
    assembled.update(cached)
    assembled["dag_preview"] = _build_dag_preview(assembled["flow"])
    assembled["dag_preview_json_text"] = json.dumps(assembled["dag_preview"], ensure_ascii=False, indent=2)
    return assembled


def build_flow_json(
    selected_operators: list[str] | str | None = None,
    user_request: str = "",
    selected_dataset_stops: list[dict[str, object]] | str | None = None,
    source_bindings: dict[str, str] | str | None = None,
    selected_node_types: list[str] | str | None = None,
    flow_name: str = "协同智能编排",
    include_dependencies: bool = True,
    include_reachable_sinks: bool = True,
    executor_number: str = "1",
    driver_memory: str = "1g",
    executor_memory: str = "1g",
    executor_cores: str = "1",
) -> str:
    """
    Return assembled result JSON text.
    """
    result = build_flow(
        selected_operators=selected_operators,
        user_request=user_request,
        selected_dataset_stops=selected_dataset_stops,
        source_bindings=source_bindings,
        selected_node_types=selected_node_types,
        flow_name=flow_name,
        include_dependencies=include_dependencies,
        include_reachable_sinks=include_reachable_sinks,
        executor_number=executor_number,
        driver_memory=driver_memory,
        executor_memory=executor_memory,
        executor_cores=executor_cores,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


def prepare_dam_analysis_session(
    selected_operators: list[str] | str | None = None,
    user_request: str = "",
    selected_dataset_stops: list[dict[str, object]] | str | None = None,
    source_bindings: dict[str, str] | str | None = None,
    flow_name: str = "协同智能编排",
    include_dependencies: bool = True,
    include_reachable_sinks: bool = True,
    executor_number: str = "1",
    driver_memory: str = "1g",
    executor_memory: str = "1g",
    executor_cores: str = "1",
) -> dict[str, Any]:
    """
    Compatibility wrapper. Prefer build_flow_with_selected_sources in new flow.
    """
    return build_flow_with_selected_sources(
        selected_operators=selected_operators or [],
        selected_dataset_stops=selected_dataset_stops or [],
        source_bindings=source_bindings,
        flow_name=flow_name,
        include_dependencies=include_dependencies,
        include_reachable_sinks=include_reachable_sinks,
        executor_number=executor_number,
        driver_memory=driver_memory,
        executor_memory=executor_memory,
        executor_cores=executor_cores,
    )


def _resolve_temp_json_file(flow_session_id: str | None, temp_json_file: str | None) -> Path:
    workspace = WorkspaceManager()
    workspace.ensure_workspace()

    if flow_session_id:
        sid = flow_session_id.strip()
        if sid:
            return workspace.temp / f"dam_flow_{sid}.json"

    if temp_json_file:
        raw = temp_json_file.strip()
        if raw.startswith("/temp/"):
            return workspace.temp / raw.split("/temp/", 1)[1]
        p = Path(raw)
        if p.is_absolute():
            return p
        return workspace.temp / raw

    candidates = sorted(
        workspace.temp.glob("dam_flow_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise ValueError("No temporary flow JSON found in /temp.")
    return candidates[0]


def execute_flow_from_temp(
    flow_session_id: str | None = None,
    temp_json_file: str | None = None,
    run_label: str = "",
) -> dict[str, Any]:
    """
    Stage-3: read cached flow JSON and return execution placeholder.
    """
    file_path = _resolve_temp_json_file(flow_session_id, temp_json_file)
    if not file_path.exists():
        raise ValueError(f"Temporary flow JSON not found: {file_path}")

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("flow"), dict):
        payload = payload["flow"]

    if not isinstance(payload, dict) or "stops" not in payload or "paths" not in payload:
        raise ValueError("Invalid flow JSON file content.")

    execution_id = uuid.uuid4().hex
    inferred_session_id = file_path.stem.replace("dam_flow_", "", 1)

    return {
        "status": "submitted_placeholder",
        "execution_id": execution_id,
        "flow_session_id": flow_session_id or inferred_session_id,
        "run_label": run_label,
        "flow_name": str(payload.get("name", "")),
        "stop_count": len(payload.get("stops", [])),
        "path_count": len(payload.get("paths", [])),
        "message": "Execution placeholder accepted. Replace this logic with real backend submission.",
    }
