"""Chemical DAG scheduler that wraps software-bound nodes for remote execution."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from infra.config_loader import resolve_workspace_root

from .config import ChemicalConfig, ChemicalNode
from .remote_pipeline_stop import ChemicalRemotePipelineStop


CHEMICAL_REMOTE_PIPELINE_BUNDLE = "chemical.remote_pipeline_stop.ChemicalRemotePipelineStop"


@dataclass(frozen=True)
class ChemicalScheduleDecision:
    node_id: str
    node_name: str
    required_software: tuple[str, ...]
    execution_target: str
    execution_node_name: str
    transformed: bool
    reason: str


@dataclass(frozen=True)
class ChemicalSchedulePlan:
    dag_definition: dict[str, Any]
    decisions: tuple[ChemicalScheduleDecision, ...]


SkillJsonResolver = Callable[
    [str],
    dict[str, Any] | tuple[dict[str, Any], str] | None,
]


def schedule_chemical_dag(
    dag_definition: Mapping[str, Any],
    *,
    config: ChemicalConfig,
    skill_json_resolver: SkillJsonResolver | None = None,
) -> ChemicalSchedulePlan:
    """Schedule a frontend DAG by converting software-bound nodes to remote stops."""

    if not isinstance(dag_definition, Mapping):
        raise TypeError("dag_definition must be a mapping")

    scheduled = copy.deepcopy(dict(dag_definition))
    nodes = scheduled.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("dag_definition field 'nodes' must be a list")

    local_server = f"{config.main_node.ip}:{config.main_node.port}"
    local_software = _main_node_software(config)
    decisions: list[ChemicalScheduleDecision] = []

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue

        skill_id = _node_skill_id(node)
        skill_json, _ = _resolve_for_schedule(
            skill_id,
            resolver=skill_json_resolver,
        )
        required_software = _required_software(skill_json)
        if not required_software:
            decisions.append(
                _decision(
                    node,
                    required_software=(),
                    target=local_server,
                    node_name="main_node",
                    transformed=False,
                    reason="skill has no required_software; keep local execution",
                )
            )
            continue

        if _software_set_contains(local_software, required_software):
            decisions.append(
                _decision(
                    node,
                    required_software=required_software,
                    target=local_server,
                    node_name="main_node",
                    transformed=False,
                    reason="required software is available on main node; keep local execution",
                )
            )
            continue

        execution_node = _select_execution_node(
            config=config,
            required_software=required_software,
        )
        target_server = f"{execution_node.ip}:{execution_node.port}"
        nodes[index] = _remote_pipeline_node(
            original_node=node,
            target_server=target_server,
            local_server=local_server,
        )
        decisions.append(
            _decision(
                node,
                required_software=required_software,
                target=target_server,
                node_name=execution_node.name,
                transformed=True,
                reason="required software is available on remote chemical node",
            )
        )

    return ChemicalSchedulePlan(
        dag_definition=scheduled,
        decisions=tuple(decisions),
    )


def schedule_chemical_dag_file(
    dag_path: str | Path,
    *,
    config: ChemicalConfig,
    skill_json_resolver: SkillJsonResolver | None = None,
) -> ChemicalSchedulePlan:
    """Load a frontend DAG JSON file and schedule it."""

    path = Path(dag_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"chemical DAG file not found: {path}")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"chemical DAG JSON must decode to an object: {path}")
    return schedule_chemical_dag(
        loaded,
        config=config,
        skill_json_resolver=skill_json_resolver,
    )


def resolve_skill_json_by_skill_id(skill_id: str) -> dict[str, Any] | None:
    """Resolve a frontend skill id or absolute skill.json path to skill metadata."""

    resolved = resolve_skill_definition_by_skill_id(skill_id)
    return resolved[0] if resolved is not None else None


def resolve_skill_definition_by_skill_id(
    skill_id: str,
) -> tuple[dict[str, Any], str] | None:
    """Resolve skill metadata and its absolute skill.json path."""

    raw_skill_id = str(skill_id or "").strip()
    if not raw_skill_id:
        return None

    direct_path = Path(raw_skill_id).expanduser()
    if direct_path.is_file():
        resolved_path = str(direct_path.resolve())
        return _read_skill_json(direct_path), resolved_path

    try:
        from runtime.dag_manager import get_dag_skill
    except Exception:
        return None

    dag_skill = get_dag_skill(raw_skill_id)
    if not dag_skill or not dag_skill.skill_path:
        return None

    skill_json_path = (resolve_workspace_root() / dag_skill.skill_path / "skill.json").resolve()
    if not skill_json_path.is_file():
        return None
    return _read_skill_json(skill_json_path), str(skill_json_path)


def _read_skill_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"skill.json must decode to an object: {path}")
    return loaded


def _remote_pipeline_node(
    *,
    original_node: dict[str, Any],
    target_server: str,
    local_server: str,
) -> dict[str, Any]:
    node_definition = copy.deepcopy(original_node)
    remote_node = copy.deepcopy(original_node)
    remote_node["skill"] = {
        **dict(original_node.get("skill") or {}),
        "skill_id": CHEMICAL_REMOTE_PIPELINE_BUNDLE,
        "skill_name": "chemical_remote_pipeline_stop",
    }
    remote_node["input_params"] = [
        {
            "binding_id": "",
            "param_name": "node_definition_json",
            "value_mode": "manual",
            "param_value": node_definition,
        },
        {
            "binding_id": "",
            "param_name": "target_server",
            "value_mode": "manual",
            "param_value": target_server,
        },
        {
            "binding_id": "",
            "param_name": "local_server",
            "value_mode": "manual",
            "param_value": local_server,
        },
    ]
    remote_node["out_params"] = copy.deepcopy(original_node.get("out_params", []))
    return remote_node


def _resolve_for_schedule(
    skill_id: str,
    *,
    resolver: SkillJsonResolver | None,
) -> tuple[dict[str, Any] | None, str]:
    if not skill_id:
        return None, ""

    if resolver is None:
        resolved = resolve_skill_definition_by_skill_id(skill_id)
        return resolved if resolved is not None else (None, "")

    resolved = resolver(skill_id)
    if resolved is None:
        return None, ""
    if isinstance(resolved, tuple):
        metadata, path = resolved
        if not isinstance(metadata, dict):
            raise TypeError("skill resolver metadata must be a mapping")
        return metadata, str(path or "")
    if not isinstance(resolved, dict):
        raise TypeError("skill resolver result must be a mapping or (mapping, path)")

    direct_path = Path(skill_id).expanduser()
    if direct_path.is_file():
        return resolved, str(direct_path.resolve())
    return resolved, ""


def _select_execution_node(
    *,
    config: ChemicalConfig,
    required_software: tuple[str, ...],
) -> ChemicalNode:
    candidates = [
        node for node in config.nodes
        if _node_has_all_software(node, required_software)
        and node.ip.strip().lower() != config.main_node.ip.strip().lower()
    ]
    if not candidates:
        required_text = ", ".join(required_software)
        raise ValueError(f"no chemical node provides required software: {required_text}")

    return candidates[0]


def _node_has_all_software(node: ChemicalNode, required_software: tuple[str, ...]) -> bool:
    available = {item.strip().lower() for item in node.software}
    return all(item.strip().lower() in available for item in required_software)


def _main_node_software(config: ChemicalConfig) -> set[str]:
    """Merge software from every configured node sharing the main node IP."""

    main_ip = config.main_node.ip.strip().lower()
    software: set[str] = set()
    for node in config.nodes:
        if node.ip.strip().lower() == main_ip:
            software.update(item.strip().lower() for item in node.software)
    return software


def _software_set_contains(
    available: set[str],
    required_software: tuple[str, ...],
) -> bool:
    return all(item.strip().lower() in available for item in required_software)


def _required_software(skill_json: dict[str, Any] | None) -> tuple[str, ...]:
    if not skill_json:
        return ()

    value = skill_json.get("required_software")
    if value in (None, ""):
        return ()
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        raise ValueError("skill.json field 'required_software' must be a string or string list")

    result = tuple(str(item).strip() for item in items if str(item).strip())
    if len(result) != len(items):
        raise ValueError("skill.json field 'required_software' must contain non-empty strings")
    return result


def _node_skill_id(node: dict[str, Any]) -> str:
    skill = node.get("skill") or {}
    if not isinstance(skill, dict):
        return ""
    return str(skill.get("skill_id", "") or "").strip()


def _decision(
    node: dict[str, Any],
    *,
    required_software: tuple[str, ...],
    target: str,
    node_name: str,
    transformed: bool,
    reason: str,
) -> ChemicalScheduleDecision:
    return ChemicalScheduleDecision(
        node_id=str(node.get("node_id", "")),
        node_name=str(node.get("node_name", "")),
        required_software=required_software,
        execution_target=target,
        execution_node_name=node_name,
        transformed=transformed,
        reason=reason,
    )


__all__ = [
    "CHEMICAL_REMOTE_PIPELINE_BUNDLE",
    "ChemicalScheduleDecision",
    "ChemicalSchedulePlan",
    "schedule_chemical_dag",
    "schedule_chemical_dag_file",
    "resolve_skill_definition_by_skill_id",
    "resolve_skill_json_by_skill_id",
]
