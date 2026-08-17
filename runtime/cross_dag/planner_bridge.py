"""规划态 JSON -> 逻辑 DAG。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable

from .schema import (
    Binding,
    CrossDagError,
    InputParam,
    LogicalDag,
    LogicalNode,
    OutParam,
)

log = logging.getLogger("flow.cross_dag.planner_bridge")

SkillResolver = Callable[[str], str]


def identity_skill_resolver(skill_name: str) -> str:
    """默认解析器：skill_name 原样作为 skill_id。"""
    return skill_name


def database_skill_resolver() -> SkillResolver:
    """从 dag_skills 表建立 skill_name -> skill_id 映射。"""
    mapping: dict[str, str] = {}
    try:
        from runtime.dag_manager import list_dag_skills

        response = list_dag_skills(page=1, page_size=1000) or {}
        for skill in response.get("data") or []:
            name = getattr(skill, "skill_name", None) or getattr(skill, "name", None)
            skill_id = getattr(skill, "skill_id", None)
            if name and skill_id:
                mapping[str(name)] = str(skill_id)
    except Exception:
        log.warning("dag_skills 不可用，skill_name 将原样作为 skill_id", exc_info=True)

    def _resolve(skill_name: str) -> str:
        return mapping.get(skill_name, skill_name)

    return _resolve


@dataclass(frozen=True)
class SkillParamSpec:
    """一个算子的参数契约。"""

    all_params: frozenset[str]
    upstream_params: frozenset[str] | None = None


def _spec_from_params(raw: Any) -> SkillParamSpec | None:
    """从 {"params":[{name, role, ...}]} 或 [{...}] 构造契约。"""
    if isinstance(raw, dict):
        raw = raw.get("params")
    if not isinstance(raw, list):
        return None

    all_names: set[str] = set()
    upstream: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        param_name = item.get("name") or item.get("param_name")
        if not param_name:
            continue
        all_names.add(str(param_name))
        if str(item.get("role", "")) == "input_data":
            upstream.add(str(param_name))

    if not all_names:
        return None

    return SkillParamSpec(
        all_params=frozenset(all_names),
        upstream_params=frozenset(upstream) if upstream else None,
    )


def database_param_resolver() -> Callable[[str], SkillParamSpec | None]:
    """skill_name -> 参数契约。查不到返回 None（跳过校验）。"""
    mapping: dict[str, SkillParamSpec] = {}
    try:
        from infra.config_loader import resolve_workspace_root
        from runtime.dag_manager import list_dag_skills

        workspace_root = resolve_workspace_root()
        response = list_dag_skills(page=1, page_size=1000) or {}
        for skill in response.get("data") or []:
            name = getattr(skill, "skill_name", None) or getattr(skill, "name", None)
            if not name:
                continue

            spec = None
            skill_path = getattr(skill, "skill_path", None)
            if skill_path:
                spec = _spec_from_skill_json(workspace_root / skill_path / "skill.json")
            if spec is None:
                spec = _spec_from_params(getattr(skill, "input_params", None))
            if spec is not None:
                mapping[str(name)] = spec
    except Exception:
        log.warning("dag_skills 不可用，跳过参数校验", exc_info=True)

    def _resolve(skill_name: str) -> SkillParamSpec | None:
        return mapping.get(skill_name)

    return _resolve


def _spec_from_skill_json(path: Any) -> SkillParamSpec | None:
    import json as _json
    from pathlib import Path as _Path

    try:
        target = _Path(path)
        if not target.is_file():
            return None
        return _spec_from_params(_json.loads(target.read_text(encoding="utf-8")).get("input_params"))
    except Exception:
        return None


def expand_planning_json(
    planning_json: dict[str, Any],
    *,
    skill_resolver: SkillResolver | None = None,
    param_resolver: Callable[[str], SkillParamSpec | None] | None = None,
    task_id: str = "",
) -> LogicalDag:
    resolver = skill_resolver or identity_skill_resolver

    raw_nodes = planning_json.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise CrossDagError("规划 JSON 缺少 nodes，或 nodes 为空")

    task = planning_json.get("task") or {}
    task_name = str(task.get("name") or task.get("dag_task_name") or "跨域任务")

    node_ids = _assign_node_ids(raw_nodes)
    nodes: list[LogicalNode] = []
    bindings: list[Binding] = []
    produced_params: dict[str, set[str]] = {}

    for index, raw_node in enumerate(raw_nodes):
        node_name = str(raw_node.get("node_name") or "").strip()
        if not node_name:
            raise CrossDagError(f"第 {index + 1} 个节点缺少 node_name")

        skill_name = str(raw_node.get("skill_name") or "").strip()
        if not skill_name:
            raise CrossDagError(f"节点 {node_name} 缺少 skill_name")

        node_id = node_ids[node_name]
        input_params: list[InputParam] = []

        spec = param_resolver(skill_name) if param_resolver else None
        if spec:
            used = set((raw_node.get("params") or {}).keys())
            unknown = sorted(used - spec.all_params)
            if unknown:
                raise CrossDagError(
                    f"节点 {node_name}（算子 {skill_name}）使用了该算子未声明的参数 {unknown}；"
                    f"可用参数为 {sorted(spec.all_params)}"
                )

        for param_name, param_value in (raw_node.get("params") or {}).items():
            _reject_multi_reference(node_name, str(param_name), param_value)
            reference = _as_reference(param_value)

            if (
                reference is not None
                and spec
                and spec.upstream_params is not None
                and str(param_name) not in spec.upstream_params
            ):
                raise CrossDagError(
                    f"节点 {node_name}（算子 {skill_name}）把参数 {param_name} 绑成了上游引用，"
                    f"但它不是输入端口，运行时取不到上游产物。"
                    f"该算子可接上游的参数只有 {sorted(spec.upstream_params) or '（无）'}；"
                    f"{param_name} 必须给字面值"
                )

            if reference is None:
                input_params.append(
                    InputParam(
                        param_name=str(param_name),
                        value_mode="manual",
                        param_value=param_value,
                    )
                )
                continue

            source_node_name, source_param = reference
            source_node_id = node_ids.get(source_node_name)
            if source_node_id is None:
                raise CrossDagError(
                    f"节点 {node_name} 的参数 {param_name} 引用了不存在的节点 {source_node_name}"
                )

            binding = Binding(
                from_node_id=source_node_id,
                from_param_name=source_param,
                to_node_id=node_id,
                to_param_name=str(param_name),
            )
            bindings.append(binding)
            produced_params.setdefault(source_node_id, set()).add(source_param)
            input_params.append(
                InputParam(
                    param_name=str(param_name),
                    value_mode="reference",
                    param_value="",
                    binding_id=binding.binding_id,
                )
            )

        nodes.append(
            LogicalNode(
                node_id=node_id,
                node_name=node_name,
                skill_id=resolver(skill_name),
                node_type=str(raw_node.get("node_type") or "default"),
                data_center=str(raw_node.get("dataCenter") or "").strip(),
                input_params=input_params,
                out_params=[],
                position={"x": float(index * 260), "y": 80.0},
            )
        )

    for node in nodes:
        for param_name in sorted(produced_params.get(node.node_id, set())):
            node.out_params.append(OutParam(param_name=param_name, param_type="file"))

    dag = LogicalDag(
        task_name=task_name,
        task_id=task_id,
        nodes=nodes,
        bindings=bindings,
    )
    _assert_no_duplicate_bindings(dag)
    return dag


def _as_reference(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict):
        return None
    source_node = value.get("source_node")
    source_param = value.get("source_param")
    if not source_node or not source_param:
        return None
    return str(source_node), str(source_param)


def _reject_multi_reference(node_name: str, param_name: str, value: Any) -> None:
    """一个入参只能接一个上游 —— 引擎的硬约束。"""
    if not isinstance(value, list):
        return
    refs = [item for item in value if _as_reference(item) is not None]
    if not refs:
        return
    raise CrossDagError(
        f"节点 {node_name} 的参数 {param_name} 引用了 {len(refs)} 个上游输出。"
        "一个参数只能引用一个上游 —— PiFlow 的输入端口是一个端口一个产物，"
        "绑多条边后一条会覆盖另一条。请改为单个引用，"
        "或先用单输入算子把多路数据合并成一路再传入。"
    )


def _assign_node_ids(raw_nodes: list[dict[str, Any]]) -> dict[str, str]:
    """node_name -> node_id。名称在 DAG 内唯一是 §8.2 的硬要求。"""
    mapping: dict[str, str] = {}
    used: set[str] = set()

    for index, raw_node in enumerate(raw_nodes):
        node_name = str(raw_node.get("node_name") or "").strip()
        if not node_name:
            continue
        if node_name in mapping:
            raise CrossDagError(f"节点名称重复: {node_name}（规划 JSON 要求 DAG 内唯一）")

        slug = _slugify(node_name) or f"node-{index + 1}"
        candidate = slug
        suffix = 2
        while candidate in used:
            candidate = f"{slug}-{suffix}"
            suffix += 1

        used.add(candidate)
        mapping[node_name] = candidate

    return mapping


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z一-鿿]+", "-", text).strip("-")
    return normalized[:48].lower()


def _assert_no_duplicate_bindings(dag: LogicalDag) -> None:
    """同一个入参被接两次，说明规划有误，运行时会取到不确定的值。"""
    seen: set[tuple[str, str]] = set()
    for binding in dag.bindings:
        key = (binding.to_node_id, binding.to_param_name)
        if key in seen:
            raise CrossDagError(
                f"节点 {binding.to_node_id} 的入参 {binding.to_param_name} 被多次绑定"
            )
        seen.add(key)
