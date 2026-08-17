"""副本挑选。"""

from __future__ import annotations

from .schema import (
    CrossDagError,
    IntentDataset,
    ReplicaCandidate,
    ReplicaDecision,
    ReplicaReject,
    ReplicaScore,
)

LOCALITY = "locality"

DEFAULT_WEIGHTS: dict[str, float] = {
    LOCALITY: 0.40,
    "cpu_cores": 0.30,
    "memory_gb": 0.30,
}

DEFAULT_DIRECTIONS: dict[str, str] = {
    "cpu_cores": "higher",
    "memory_gb": "higher",
}

_LOCALITY_SAME = 1.0
_LOCALITY_CROSS = 0.2

DEFAULT_AVAILABLE_STATUSES = frozenset({"AVAILABLE"})


def select_replica(
    dataset: IntentDataset,
    *,
    preferred_center_id: str,
    node_id: str = "",
    weights: dict[str, float] | None = None,
    directions: dict[str, str] | None = None,
    known_centers: set[str] | None = None,
    available_statuses: frozenset[str] | set[str] | None = None,
    required_center_id: str = "",
) -> ReplicaDecision:
    """从 dataset.replicas 里挑一个。没有可用副本时抛 CrossDagError。"""
    resolved_weights = dict(weights) if weights else dict(DEFAULT_WEIGHTS)
    resolved_directions = {**DEFAULT_DIRECTIONS, **(directions or {})}

    decision = ReplicaDecision(
        dataset_alias=dataset.alias,
        dataset_id=dataset.dataset_id,
        node_id=node_id,
        preferred_center_id=preferred_center_id,
    )

    if not dataset.replicas:
        raise CrossDagError(
            f"数据集 {dataset.dataset_id or dataset.alias} 没有任何副本，"
            "请检查数据源注册是否提供了副本清单"
        )

    survivors = _hard_filter(
        dataset.replicas,
        decision,
        known_centers,
        available_statuses or DEFAULT_AVAILABLE_STATUSES,
        required_center_id,
    )
    if not survivors:
        detail = "；".join(f"{r.replica_id}({r.reason})" for r in decision.rejects)
        where = f"（限定数据源 {required_center_id}）" if required_center_id else ""
        raise CrossDagError(
            f"数据集 {dataset.dataset_id or dataset.alias} 没有可用副本{where}：{detail}"
        )

    _score(survivors, decision, resolved_weights, resolved_directions)

    best = max(decision.scores, key=lambda s: (s.total, -_index_of(survivors, s.replica_id)))
    chosen = next(r for r in survivors if r.replica_id == best.replica_id)
    decision.chosen = chosen
    decision.reason = _explain(chosen, best, decision, len(dataset.replicas))
    return decision


def _hard_filter(
    replicas: list[ReplicaCandidate],
    decision: ReplicaDecision,
    known_centers: set[str] | None,
    available_statuses: frozenset[str] | set[str],
    required_center_id: str = "",
) -> list[ReplicaCandidate]:
    survivors: list[ReplicaCandidate] = []
    allowed = {s.strip().upper() for s in available_statuses}

    for replica in replicas:
        if required_center_id and replica.center_id != required_center_id:
            decision.rejects.append(
                ReplicaReject(
                    replica.replica_id,
                    replica.center_id,
                    f"节点已显式钉在数据源 {required_center_id}，该副本不在此处",
                )
            )
            continue
        status = (replica.status or "").strip().upper()
        if status not in allowed:
            decision.rejects.append(
                ReplicaReject(
                    replica.replica_id,
                    replica.center_id,
                    f"数据源状态 {status or '<空>'} 不在可用状态清单 {sorted(allowed)} 中",
                )
            )
            continue
        if not replica.center_id:
            decision.rejects.append(
                ReplicaReject(replica.replica_id, "", "副本未标注所属数据源")
            )
            continue
        if not replica.locator:
            decision.rejects.append(
                ReplicaReject(replica.replica_id, replica.center_id, "副本缺少访问路径")
            )
            continue
        if known_centers and replica.center_id not in known_centers:
            decision.rejects.append(
                ReplicaReject(
                    replica.replica_id,
                    replica.center_id,
                    f"数据源 {replica.center_id} 未在 config/cross_dc.yaml 注册",
                )
            )
            continue
        survivors.append(replica)

    return survivors


def _score(
    survivors: list[ReplicaCandidate],
    decision: ReplicaDecision,
    weights: dict[str, float],
    directions: dict[str, str],
) -> None:
    """按配置声明的维度打分。locality 之外的维度全部来自 metrics。"""
    metric_names = [name for name in weights if name != LOCALITY]
    collected = {
        name: [replica.metric(name) for replica in survivors] for name in metric_names
    }

    for index, replica in enumerate(survivors):
        parts: dict[str, float] = {}

        if LOCALITY in weights:
            parts[LOCALITY] = (
                _LOCALITY_SAME
                if replica.center_id == decision.preferred_center_id
                else _LOCALITY_CROSS
            )

        for name in metric_names:
            parts[name] = _normalize(
                collected[name][index],
                collected[name],
                directions.get(name, "higher"),
            )

        total = sum(weights.get(key, 0.0) * value for key, value in parts.items())
        decision.scores.append(
            ReplicaScore(
                replica_id=replica.replica_id,
                center_id=replica.center_id,
                total=total,
                parts=parts,
            )
        )


def _normalize(value: float | None, values: list[float | None], direction: str) -> float:
    """把一个指标归一化到 0~1。"""
    known = [v for v in values if v is not None]
    if not known or value is None:
        return 0.0 if known else 1.0

    low, high = min(known), max(known)
    if high == low:
        return 1.0

    ratio = (value - low) / (high - low)
    return ratio if direction == "higher" else 1.0 - ratio


def _index_of(survivors: list[ReplicaCandidate], replica_id: str) -> int:
    for index, replica in enumerate(survivors):
        if replica.replica_id == replica_id:
            return index
    return 0


def _explain(
    chosen: ReplicaCandidate,
    score: ReplicaScore,
    decision: ReplicaDecision,
    total_count: int,
) -> str:
    bits = [
        f"{total_count} 个副本中选中 {chosen.replica_id}（数据源 {chosen.center_id}）",
        f"总分 {score.total:.3f}",
    ]
    if chosen.center_id == decision.preferred_center_id:
        bits.append(f"与偏好数据源 {decision.preferred_center_id} 一致，免跨源传输")
    else:
        bits.append(
            f"需从 {chosen.center_id} 跨源取数（偏好 {decision.preferred_center_id}）"
        )

    top_parts = sorted(score.parts.items(), key=lambda kv: -kv[1])[:2]
    bits.append("优势项：" + "、".join(f"{k}={v:.2f}" for k, v in top_parts))
    if decision.rejects:
        bits.append(f"另有 {len(decision.rejects)} 个副本被硬过滤淘汰")
    return "；".join(bits)
