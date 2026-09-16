"""Dimension-preserving historical anomaly screening, never a disaster threshold."""
import numpy as np

from .contracts import Condition, Rule


def historical_rules(source):
    values = np.asarray(source["target"], dtype=float)
    values = values[np.isfinite(values)]
    metadata = source.get("metadata", {})
    # Older saved inputs recorded the transform in provenance, before it was
    # included in variable metadata. Preserve their assessment without names.
    derivation = source.get("provenance", {}).get(source["variable"], {}).get("derivation", "")
    if (metadata.get("transform") == "unwrap_degrees" or metadata.get("semantics") == "circular_degrees"
            or derivation.startswith("causal_unwrap_degrees;")):
        return [], "环形变量不能按标量历史分布判定异常；请结合适用的相关指标评估。"
    if len(values) < 24:
        return [], "历史有效样本不足24点，无法建立异常筛查基准。"
    if np.ptp(values) <= max(1e-12, abs(float(np.median(values))) * 1e-9):
        return [], "历史序列恒定，无法估计异常范围；请核查观测通道，不能据此判断安全。"
    q01, q25, q75, q99 = np.quantile(values, [.01, .25, .75, .99])
    iqr = q75 - q25
    low, high = min(q01, q25 - 1.5 * iqr), max(q99, q75 + 1.5 * iqr)
    attention = metadata.get("attention", "both")
    rules = []
    for direction, threshold, operator in [("low", low, "lt"), ("high", high, "gt")]:
        if attention in {"low", "high"} and attention != direction:
            continue
        bounds = source.get("bounds", {})
        if direction == "low" and bounds.get("minimum") is not None and threshold <= bounds["minimum"]:
            continue
        if direction == "high" and bounds.get("maximum") is not None and threshold >= bounds["maximum"]:
            continue
        rules.append(Rule(id=f"history.{direction}", version="HS-1.0", approved=True,
            label="预测值低于历史参考范围" if direction == "low" else "预测值高于历史参考范围",
            source=f"项目历史异常筛查 HS-1.0；仅使用本次历史窗口 {len(values)} 个有效样本；"
                   "参考边界取P1/P99与1.5倍四分位距外侧值；不是领域判定阈值或事件发生概率。",
            severity=1, level="R1 异常关注", conditions=[Condition(variable=source["variable"],
                unit=source["unit"], statistic="value", operator=operator, threshold=float(threshold))]))
    return rules, "历史异常筛查仅描述相对本次历史样本的偏离，不替代适用领域的评估标准。"
