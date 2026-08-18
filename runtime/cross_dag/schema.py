"""跨域规划的数据结构与 DSL 常量。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DSL_VERSION = "1.0"

BUNDLE_REMOTE_SUBDAG = (
    "piflow_engine.cn.piflow.engine.local.remote_subdag_source_stop.RemoteSubDagSourceStop"
)
BUNDLE_FILE_SAVE = "piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop"
BUNDLE_SOURCE_FILE = "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop"

REMOTE_OUTPUT_PORT = "output"
FILE_SAVE_INPUT_PORT = "output"

EXPORT_NODE_PREFIX = "__export__"
REMOTE_NODE_PREFIX = "__remote__"

DATASET_URI_PREFIX = "dataset://"

MODE_DIRECT = "direct"
MODE_COMPOSITION = "composition"
MODE_UNAVAILABLE = "unavailable"

# 需求维度的两种性质。注册方新增维度只需在 config 里声明性质，不用改代码。
#   cover_all  可由多个数据集各覆盖一部分，合起来满足 —— 只有这类维度会驱动组装
#   match_all  每个数据集必须自身满足，组装帮不上忙（如空间范围、时间范围）
FACET_COVER_ALL = "cover_all"
FACET_MATCH_ALL = "match_all"


@dataclass
class ReplicaCandidate:
    """一个物理副本 —— 某个数据集在某个数据源上的那一份。"""

    replica_id: str
    source_id: str
    center_id: str
    locator: str
    status: str = "AVAILABLE"
    metrics: dict[str, float] = field(default_factory=dict)

    def metric(self, name: str) -> float | None:
        """取指标值。缺失返回 None，打分时按最差处理。"""
        value = self.metrics.get(name)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def to_json(self) -> dict[str, Any]:
        return {
            "replica_id": self.replica_id,
            "source_id": self.source_id,
            "center_id": self.center_id,
            "locator": self.locator,
            "status": self.status,
            "metrics": dict(self.metrics),
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "ReplicaCandidate":
        source_ip = str(
            raw.get("source_ip") or raw.get("center_id") or raw.get("source_id") or ""
        )
        return cls(
            replica_id=str(raw.get("replica_id", "") or ""),
            source_id=str(raw.get("source_id") or source_ip),
            center_id=source_ip,
            locator=str(raw.get("locator", "") or ""),
            status=str(raw.get("status", "AVAILABLE") or "AVAILABLE"),
            metrics={
                str(k): float(v)
                for k, v in (raw.get("metrics") or {}).items()
                if _is_number(v)
            },
        )


def _is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


@dataclass
class ReplicaScore:
    replica_id: str
    center_id: str
    total: float
    parts: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "replica_id": self.replica_id,
            "center_id": self.center_id,
            "total": round(self.total, 4),
            "parts": {k: round(v, 4) for k, v in self.parts.items()},
        }


@dataclass
class ReplicaReject:
    replica_id: str
    center_id: str
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "replica_id": self.replica_id,
            "center_id": self.center_id,
            "reason": self.reason,
        }


@dataclass
class ReplicaDecision:
    """挑选结果。落选理由要一路传到最终计划里，否则"智能"就是黑箱。"""

    dataset_alias: str
    dataset_id: str
    node_id: str = ""
    preferred_center_id: str = ""
    chosen: ReplicaCandidate | None = None
    scores: list[ReplicaScore] = field(default_factory=list)
    rejects: list[ReplicaReject] = field(default_factory=list)
    reason: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "dataset_alias": self.dataset_alias,
            "dataset_id": self.dataset_id,
            "node_id": self.node_id,
            "preferred_center_id": self.preferred_center_id,
            "chosen": self.chosen.to_json() if self.chosen else None,
            "reason": self.reason,
            "scores": [s.to_json() for s in self.scores],
            "rejects": [r.to_json() for r in self.rejects],
        }


@dataclass
class RequirementFacet:
    """用户需求在某个维度上的要求。

    key 与数据集元数据里的维度键一一对应。平台不预设维度是什么：地学可能是
    variables / region / time_range，化学可能是 discipline / language，
    天文可能是 band / sky_area —— 由注册方的元数据和 config 共同定义。
    """

    key: str
    values: list[str] = field(default_factory=list)
    label: str = ""
    mode: str = FACET_COVER_ALL

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label or self.key,
            "mode": self.mode,
            "values": list(self.values),
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "RequirementFacet":
        return cls(
            key=str(raw.get("key", "") or ""),
            values=[str(v).strip() for v in raw.get("values") or [] if str(v).strip()],
            label=str(raw.get("label", "") or ""),
            mode=str(raw.get("mode", "") or FACET_COVER_ALL),
        )


@dataclass
class FacetCoverage:
    """某个数据集在某个需求维度上的覆盖情况。"""

    key: str
    label: str
    mode: str
    required: list[str] = field(default_factory=list)
    covered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    declared: bool = True

    @property
    def satisfied(self) -> bool:
        # 数据集没声明这个维度时不算满足 —— 核实不了的事不能替它认下，
        # 宁可退化成组装，也不要让用户以为需求被满足了。
        return self.declared and not self.missing

    def to_json(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "mode": self.mode,
            "declared": self.declared,
            "satisfied": self.satisfied,
            "required": list(self.required),
            "covered": list(self.covered),
            "missing": list(self.missing),
        }


@dataclass
class DatasetCoverage:
    """一个候选数据集对整体需求的覆盖情况，即覆盖矩阵的一行。"""

    dataset_id: str
    alias: str = ""
    name: str = ""
    facets: list[FacetCoverage] = field(default_factory=list)
    # 意图识别是否挑中了它。false 表示模型没选，是后端扫目录时补出来的。
    selected: bool = True

    @property
    def undeclared_facets(self) -> list[str]:
        return [f.label or f.key for f in self.facets if not f.declared]

    @property
    def covered_count(self) -> int:
        """在可分摊维度上覆盖到的取值个数，用来衡量单集最大覆盖。"""
        return sum(len(f.covered) for f in self.facets if f.mode == FACET_COVER_ALL)

    @property
    def required_count(self) -> int:
        return sum(len(f.required) for f in self.facets if f.mode == FACET_COVER_ALL)

    @property
    def full_match(self) -> bool:
        return bool(self.facets) and all(f.satisfied for f in self.facets)

    def to_json(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "alias": self.alias,
            "name": self.name,
            "selected": self.selected,
            "full_match": self.full_match,
            "covered_count": self.covered_count,
            "required_count": self.required_count,
            "undeclared_facets": self.undeclared_facets,
            "facets": [f.to_json() for f in self.facets],
        }


@dataclass
class SatisfactionReport:
    """需求满足分析的结论：有没有单个数据集能独立满足需求，决定直接获取还是组装。"""

    facets: list[RequirementFacet] = field(default_factory=list)
    coverages: list[DatasetCoverage] = field(default_factory=list)
    mode: str = MODE_COMPOSITION
    reason: str = ""
    notes: list[str] = field(default_factory=list)
    scanned_count: int = 0

    @property
    def missing_values(self) -> list[str]:
        """所有候选数据集加起来也覆盖不到的取值 —— 平台确实没有这部分数据。"""
        covered: set[str] = set()
        for cover in self.coverages:
            for facet in cover.facets:
                covered.update(facet.covered)
        missing: list[str] = []
        for facet in self.facets:
            for value in facet.values:
                if value not in covered and value not in missing:
                    missing.append(value)
        return missing

    @property
    def full_matches(self) -> list[DatasetCoverage]:
        return [c for c in self.coverages if c.full_match]

    @property
    def required_count(self) -> int:
        return sum(len(f.values) for f in self.facets if f.mode == FACET_COVER_ALL)

    @property
    def max_coverage(self) -> int:
        return max((c.covered_count for c in self.coverages), default=0)

    def to_json(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reason": self.reason,
            "notes": list(self.notes),
            "required_count": self.required_count,
            "max_coverage": self.max_coverage,
            "scanned_count": self.scanned_count,
            "missing_values": self.missing_values,
            "full_match_count": len(self.full_matches),
            "full_match_dataset_ids": [c.dataset_id for c in self.full_matches],
            "facets": [f.to_json() for f in self.facets],
            "coverages": [c.to_json() for c in self.coverages],
        }


@dataclass
class DirectAccess:
    """直接获取的产物：目标数据集 + 选中的副本 + 其余同样完整匹配的候选。"""

    dataset_id: str
    name: str = ""
    alias: str = ""
    replica_decision: "ReplicaDecision | None" = None
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "alias": self.alias,
            "replica_decision": (
                self.replica_decision.to_json() if self.replica_decision else None
            ),
            "alternatives": list(self.alternatives),
        }


@dataclass
class IntentDataset:
    """意图里引用的一个逻辑数据集。"""

    alias: str
    dataset_id: str = ""
    source_id: str = ""
    center_id: str = ""
    locator: str = ""
    name: str = ""
    replicas: list[ReplicaCandidate] = field(default_factory=list)
    facets: dict[str, list[str]] = field(default_factory=dict)

    def replica_by_id(self, replica_id: str) -> ReplicaCandidate | None:
        for item in self.replicas:
            if item.replica_id == replica_id:
                return item
        return None

    def to_json(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "dataset_id": self.dataset_id,
            "source_id": self.source_id,
            "center_id": self.center_id,
            "locator": self.locator,
            "name": self.name,
            "replicas": [r.to_json() for r in self.replicas],
            "facets": {k: list(v) for k, v in self.facets.items()},
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "IntentDataset":
        return cls(
            alias=str(raw.get("alias", "") or ""),
            dataset_id=str(raw.get("dataset_id", "") or ""),
            source_id=str(raw.get("source_id", "") or ""),
            center_id=str(raw.get("center_id", "") or ""),
            locator=str(raw.get("locator", "") or ""),
            name=str(raw.get("name", "") or ""),
            replicas=[ReplicaCandidate.from_json(r) for r in raw.get("replicas") or []],
            facets={
                str(k): [str(x) for x in (v or [])]
                for k, v in (raw.get("facets") or {}).items()
            },
        )


@dataclass
class LocationHint:
    """用户明确指定的执行位置要求。"""

    center_id: str
    applies_to: str = ""
    raw: str = ""

    def to_json(self) -> dict[str, Any]:
        return {"center_id": self.center_id, "applies_to": self.applies_to, "raw": self.raw}

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "LocationHint":
        return cls(
            center_id=str(raw.get("center_id", "") or ""),
            applies_to=str(raw.get("applies_to", "") or ""),
            raw=str(raw.get("raw", "") or ""),
        )


@dataclass
class IntentSpec:
    goal: str = ""
    datasets: list[IntentDataset] = field(default_factory=list)
    operations: list[dict[str, Any]] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    location_hints: list[LocationHint] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    user_request: str = ""
    requirements: list[RequirementFacet] = field(default_factory=list)

    def facet(self, key: str) -> RequirementFacet | None:
        for item in self.requirements:
            if item.key == key:
                return item
        return None

    def dataset_by_alias(self, alias: str) -> IntentDataset | None:
        for item in self.datasets:
            if item.alias == alias:
                return item
        return None

    def to_json(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "user_request": self.user_request,
            "datasets": [item.to_json() for item in self.datasets],
            "operations": list(self.operations),
            "location_hints": [h.to_json() for h in self.location_hints],
            "output": dict(self.output),
            "assumptions": list(self.assumptions),
            "unresolved": list(self.unresolved),
            "requirements": [r.to_json() for r in self.requirements],
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "IntentSpec":
        return cls(
            goal=str(raw.get("goal", "") or ""),
            user_request=str(raw.get("user_request", "") or ""),
            datasets=[IntentDataset.from_json(d) for d in raw.get("datasets") or []],
            operations=list(raw.get("operations") or []),
            location_hints=[
                LocationHint.from_json(h) for h in raw.get("location_hints") or []
            ],
            output=dict(raw.get("output") or {}),
            assumptions=[str(x) for x in raw.get("assumptions") or []],
            unresolved=[str(x) for x in raw.get("unresolved") or []],
            requirements=[
                RequirementFacet.from_json(r) for r in raw.get("requirements") or []
            ],
        )


@dataclass
class InputParam:
    param_name: str
    value_mode: str = "manual"
    param_value: Any = ""
    param_type: str = "string"
    binding_id: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "param_name": self.param_name,
            "param_type": self.param_type,
            "value_mode": self.value_mode,
            "param_value": self.param_value,
            "binding_id": self.binding_id,
        }


@dataclass
class OutParam:
    param_name: str
    param_type: str = "file"

    def to_json(self) -> dict[str, Any]:
        return {"param_name": self.param_name, "param_type": self.param_type}


@dataclass
class LogicalNode:
    node_id: str
    node_name: str
    skill_id: str
    # 解析前的算子名。skill_id 可能是注册表分配的 UUID，认不出是哪个算子；
    # 保留原名才能做占位算子/产出算子这类按名字的判定，前端也才有得展示。
    skill_name: str = ""
    node_type: str = "default"
    data_center: str = ""
    input_params: list[InputParam] = field(default_factory=list)
    out_params: list[OutParam] = field(default_factory=list)
    position: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})

    def input_param(self, name: str) -> InputParam | None:
        for param in self.input_params:
            if param.param_name == name:
                return param
        return None

    def to_dsl(self) -> dict[str, Any]:
        node: dict[str, Any] = {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "skill": {
                "skill_id": self.skill_id,
                "skill_name": self.skill_name or self.skill_id,
                "version": "1.0.0",
            },
            "position": dict(self.position),
            "input_params": [p.to_json() for p in self.input_params],
            "out_params": [p.to_json() for p in self.out_params],
        }
        if self.data_center:
            node["dataCenter"] = self.data_center
        return node


@dataclass
class Binding:
    from_node_id: str
    from_param_name: str
    to_node_id: str
    to_param_name: str

    @property
    def binding_id(self) -> str:
        return f"{self.from_node_id}:{self.from_param_name}->{self.to_node_id}:{self.to_param_name}"

    def to_dsl(self) -> dict[str, str]:
        return {
            "binding_id": self.binding_id,
            "from_node_id": self.from_node_id,
            "from_param_name": self.from_param_name,
            "to_node_id": self.to_node_id,
            "to_param_name": self.to_param_name,
        }


@dataclass
class LogicalDag:
    task_name: str = ""
    task_id: str = ""
    description: str = ""
    nodes: list[LogicalNode] = field(default_factory=list)
    bindings: list[Binding] = field(default_factory=list)

    def node_map(self) -> dict[str, LogicalNode]:
        return {node.node_id: node for node in self.nodes}

    def predecessors(self, node_id: str) -> list[str]:
        return [b.from_node_id for b in self.bindings if b.to_node_id == node_id]

    def successors(self, node_id: str) -> list[str]:
        return [b.to_node_id for b in self.bindings if b.from_node_id == node_id]

    def source_node_ids(self) -> list[str]:
        consumed = {b.to_node_id for b in self.bindings}
        return [n.node_id for n in self.nodes if n.node_id not in consumed]

    def sink_node_ids(self) -> list[str]:
        produced = {b.from_node_id for b in self.bindings}
        return [n.node_id for n in self.nodes if n.node_id not in produced]

    def to_json(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "description": self.description,
            "nodes": [node.to_dsl() for node in self.nodes],
            "bindings": [b.to_dsl() for b in self.bindings],
            "source_node_ids": self.source_node_ids(),
            "sink_node_ids": self.sink_node_ids(),
        }


@dataclass
class BindResult:
    center_of: dict[str, str] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)
    replica_decisions: list[ReplicaDecision] = field(default_factory=list)


@dataclass
class Segment:
    segment_id: str
    center_id: str
    level: int
    node_ids: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "center_id": self.center_id,
            "level": self.level,
            "node_ids": list(self.node_ids),
        }


@dataclass
class SegmentGraph:
    segments: dict[str, Segment] = field(default_factory=dict)
    segment_of: dict[str, str] = field(default_factory=dict)
    levels: dict[str, int] = field(default_factory=dict)
    cross_edges: list[Binding] = field(default_factory=list)

    def upstream_segments(self, segment_id: str) -> set[str]:
        return {
            self.segment_of[b.from_node_id]
            for b in self.cross_edges
            if self.segment_of[b.to_node_id] == segment_id
        }

    def downstream_segments(self, segment_id: str) -> set[str]:
        return {
            self.segment_of[b.to_node_id]
            for b in self.cross_edges
            if self.segment_of[b.from_node_id] == segment_id
        }

    def root_segments(self) -> list[str]:
        """出度为 0 的段，即最下游段。嵌套构造从这里开始。"""
        return sorted(
            seg_id for seg_id in self.segments if not self.downstream_segments(seg_id)
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "segments": [s.to_json() for s in self.segments.values()],
            "cross_edges": [b.to_dsl() for b in self.cross_edges],
        }


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)

    def to_json(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings)}


@dataclass
class CrossDagPlan:
    """规划的完整产物，可直接落库或提交执行。"""

    plan_id: str
    intent: IntentSpec
    logical_dag: LogicalDag
    bind_result: BindResult
    segment_graph: SegmentGraph
    nested_dsl: dict[str, Any]
    validation: ValidationReport
    mode: str = MODE_COMPOSITION
    satisfaction: SatisfactionReport | None = None
    direct_access: DirectAccess | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "mode": self.mode,
            "satisfaction": self.satisfaction.to_json() if self.satisfaction else None,
            "direct_access": self.direct_access.to_json() if self.direct_access else None,
            "intent": self.intent.to_json(),
            "binding": {
                "center_of": dict(self.bind_result.center_of),
                "reasons": dict(self.bind_result.reasons),
                "replica_decisions": [
                    d.to_json() for d in self.bind_result.replica_decisions
                ],
            },
            "segments": self.segment_graph.to_json(),
            "nested_dsl": self.nested_dsl,
            "validation": self.validation.to_json(),
        }


class CrossDagError(RuntimeError):
    """规划阶段的可预期失败，接口层转成 4xx。"""


def build_dsl(
    *,
    task_id: str,
    task_name: str,
    nodes: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> dict[str, Any]:
    """组装一份画板 DSL。"""
    seen: set[tuple[str, str]] = set()
    edges: list[dict[str, str]] = []
    for binding in bindings:
        pair = (binding["from_node_id"], binding["to_node_id"])
        if pair in seen:
            continue
        seen.add(pair)
        edges.append(
            {
                "edge_id": f"edge-{pair[0]}-{pair[1]}",
                "from_node_id": pair[0],
                "to_node_id": pair[1],
            }
        )

    return {
        "dsl_version": DSL_VERSION,
        "task": {"dag_task_id": task_id, "dag_task_name": task_name},
        "nodes": nodes,
        "edges": edges,
        "bindings": bindings,
    }
