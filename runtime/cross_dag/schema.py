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
class IntentDataset:
    """意图里引用的一个逻辑数据集。"""

    alias: str
    dataset_id: str = ""
    source_id: str = ""
    center_id: str = ""
    locator: str = ""
    name: str = ""
    replicas: list[ReplicaCandidate] = field(default_factory=list)

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
            "skill": {"skill_id": self.skill_id, "version": "1.0.0"},
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

    def to_json(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
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
