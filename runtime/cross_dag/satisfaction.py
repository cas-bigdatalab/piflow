"""需求满足分析：判断单个数据集能否独立满足需求，据此选择直接获取还是智能组装。

这一层刻意做成确定性的，不调用 LLM。覆盖矩阵是要摆给用户看的证据，必须可复现、
可单测；让模型去判断「这个数据集覆盖了哪几个变量」，矩阵就成了模型的说法而不是事实。

维度（facet）由注册方的元数据和 config/cross_dc.yaml 共同定义，平台侧不认识
任何具体含义，只做取值集合的比对 —— 地学是变量/区域/时间，化学可以是学科/语种，
天文可以是波段/天区，换学科不用改这里的代码。
"""

from __future__ import annotations

from typing import Any

from .config import CrossDcConfig, get_cross_dc_config
from .registry_stub import DatasourceRegistry
from .schema import (
    FACET_COVER_ALL,
    MODE_COMPOSITION,
    MODE_DIRECT,
    MODE_UNAVAILABLE,
    DatasetCoverage,
    FacetCoverage,
    IntentSpec,
    RequirementFacet,
    SatisfactionReport,
)


def analyze_satisfaction(
    intent: IntentSpec,
    *,
    config: CrossDcConfig | None = None,
    registry: DatasourceRegistry | None = None,
) -> SatisfactionReport:
    """产出覆盖矩阵与分支结论。纯函数，无副作用。

    覆盖判定对整个数据集目录做，而不只看意图识别挑出来的那几个：模型负责理解
    需求，能不能满足是确定性比对的事。这样模型漏选也能被补上，用户也才看得到
    「平台里还有哪些数据集同样满足需求」。
    """
    resolved = config or get_cross_dc_config()
    facets = resolve_facets(intent, resolved)
    report = SatisfactionReport(facets=facets)

    candidates = _collect_candidates(intent, registry)
    report.scanned_count = len(candidates)

    if not facets:
        if not intent.datasets:
            report.mode = MODE_UNAVAILABLE
            report.reason = "没有识别出可比对的需求维度，也没有匹配到任何数据集"
            report.notes.extend(intent.unresolved)
            return report
        report.mode = MODE_COMPOSITION
        report.reason = "意图里没有可比对的需求维度，无法判断单个数据集是否已经满足需求"
        report.notes.append(
            "意图识别没有产出结构化需求维度（requirements），需求满足分析被跳过，"
            "按组装处理。这是保守退化，不影响正确性，但用户看不到覆盖矩阵"
        )
        return report

    selected_ids = {d.dataset_id for d in intent.datasets}
    coverages = [
        _cover(item, facets, selected=item["dataset_id"] in selected_ids)
        for item in candidates
    ]
    # 覆盖矩阵只保留「模型选中的」和「至少覆盖到一项需求的」，
    # 完全不相关的数据集不进矩阵，免得目录一大就淹没有效信息。
    report.coverages = [
        cover
        for cover in coverages
        if cover.selected or any(facet.covered for facet in cover.facets)
    ]
    _collect_notes(report, facets, candidates)

    if not any(_contributes(cover, facets) for cover in coverages):
        report.mode = MODE_UNAVAILABLE
        report.reason = (
            f"检索了 {report.scanned_count} 个数据集，没有一个能提供需求里的内容，"
            "平台当前没有这部分数据"
        )
        report.notes.extend(intent.unresolved)
        return report

    full_matches = report.full_matches
    if not full_matches and not intent.datasets:
        # 判定要组装，可意图识别一个数据集都没选中 —— 组装无从谈起。
        # 这一步不兜住的话，后面规划阶段会抛"没有可用数据集"，
        # 用户看到的是一个异常而不是"平台没有这份数据"的结论。
        report.mode = MODE_UNAVAILABLE
        report.reason = (
            f"检索了 {report.scanned_count} 个数据集，没有一个能满足需求，"
            "也没有可供组装的数据源，平台当前没有这部分数据"
        )
        report.notes.extend(intent.unresolved)
        return report

    if not full_matches:
        report.mode = MODE_COMPOSITION
        report.reason = (
            f"没有任何单个数据集能完整满足需求（需求 {report.required_count} 项，"
            f"单集最大覆盖 {report.max_coverage} 项），需要多源组装"
        )
        return report

    if intent.operations:
        names = "、".join(
            str(op.get("op") or "").strip()
            for op in intent.operations
            if isinstance(op, dict) and str(op.get("op") or "").strip()
        )
        report.mode = MODE_COMPOSITION
        report.reason = (
            f"有 {len(full_matches)} 个数据集完整覆盖了需求维度，"
            f"但意图里还有需要计算的加工步骤（{names or '未命名操作'}），"
            "不能直接交付原始数据集"
        )
        return report

    report.mode = MODE_DIRECT
    report.reason = (
        f"{len(full_matches)} 个数据集完整满足需求，且无需进一步加工，可直接获取"
    )
    return report


def _contributes(cover: DatasetCoverage, facets: list[RequirementFacet]) -> bool:
    """这个数据集能不能为需求提供内容。

    只看可分摊维度（cover_all）—— 那是"要哪些数据"的维度，多个数据集各覆盖一部分
    才谈得上组装。只匹配上 match_all 维度不算数：用户要"长江流域的地下水位"，
    平台里所有长江流域的数据集都匹配得上区域，但一个都提供不了地下水位。
    按"命中任意维度"来判，就会得出"有相关数据"的错误结论。

    需求里没有可分摊维度时退回原判断，否则会把一切都判成没有。
    """
    splittable = [f.key for f in facets if f.mode == FACET_COVER_ALL]
    if not splittable:
        return any(f.covered for f in cover.facets)
    return any(f.covered for f in cover.facets if f.key in splittable)


def resolve_facets(
    intent: IntentSpec,
    config: CrossDcConfig | None = None,
) -> list[RequirementFacet]:
    """把意图里的需求维度补全成带 label / mode 的完整声明。"""
    resolved = config or get_cross_dc_config()
    facets: list[RequirementFacet] = []
    for item in intent.requirements:
        key = (item.key or "").strip()
        values = [str(v).strip() for v in item.values if str(v).strip()]
        if not key or not values:
            continue
        facets.append(
            RequirementFacet(
                key=key,
                values=_dedupe(values),
                label=item.label or resolved.facet_label(key),
                mode=item.mode if item.mode else resolved.facet_mode(key),
            )
        )
    return facets


def _collect_candidates(
    intent: IntentSpec,
    registry: DatasourceRegistry | None,
) -> list[dict[str, Any]]:
    """待比对的数据集：意图挑中的 + 目录里的其余，按 dataset_id 去重。"""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    for dataset in intent.datasets:
        if dataset.dataset_id in seen:
            continue
        seen.add(dataset.dataset_id)
        candidates.append(
            {
                "dataset_id": dataset.dataset_id,
                "alias": dataset.alias,
                "name": dataset.name,
                "facets": dict(dataset.facets),
            }
        )

    if registry is not None:
        for record in registry.list_datasets():
            if record.dataset_id in seen:
                continue
            seen.add(record.dataset_id)
            candidates.append(
                {
                    "dataset_id": record.dataset_id,
                    "alias": "",
                    "name": record.name,
                    "facets": {
                        str(k): list(v) for k, v in (record.facets or {}).items()
                    },
                }
            )
    return candidates


def _cover(
    dataset: dict[str, Any],
    facets: list[RequirementFacet],
    *,
    selected: bool = True,
) -> DatasetCoverage:
    coverages: list[FacetCoverage] = []
    for facet in facets:
        provided = dataset["facets"].get(facet.key)
        declared = provided is not None
        available = {_norm(v) for v in (provided or [])}
        covered = [v for v in facet.values if _norm(v) in available]
        missing = [v for v in facet.values if _norm(v) not in available]
        coverages.append(
            FacetCoverage(
                key=facet.key,
                label=facet.label,
                mode=facet.mode,
                required=list(facet.values),
                covered=covered,
                missing=missing,
                declared=declared,
            )
        )
    return DatasetCoverage(
        dataset_id=dataset["dataset_id"],
        alias=dataset["alias"],
        name=dataset["name"],
        facets=coverages,
        selected=selected,
    )


def _collect_notes(
    report: SatisfactionReport,
    facets: list[RequirementFacet],
    datasets: list[dict[str, Any]],
) -> None:
    """两类信号值得单独说：候选里根本没有的取值，以及注册方没声明的维度。"""
    for facet in facets:
        union: set[str] = set()
        declared_by_any = False
        for dataset in datasets:
            provided = dataset["facets"].get(facet.key)
            if provided is None:
                continue
            declared_by_any = True
            union |= {_norm(v) for v in provided}
        if not declared_by_any:
            # 整个维度没人声明，那是元数据缺失，不是"平台没有这份数据"，
            # 由下面的未声明提示统一说，这里不重复也不误导。
            continue
        unreachable = [v for v in facet.values if _norm(v) not in union]
        if unreachable:
            report.notes.append(
                f"{facet.label}：{unreachable} 在所有候选数据集里都找不到，"
                "即使组装也覆盖不了，请确认需求描述或数据源是否缺失"
            )

    _note_undeclared(report)


def _note_undeclared(report: SatisfactionReport) -> None:
    """只报「补上就能满足」的未声明维度。

    此前是把所有候选数据集的未声明维度并起来报一条，结果被完全不相关的数据集
    触发：用户查降水，站点元信息表没声明时间范围，于是干净的直接获取结果上挂了
    一条「这会让本可以直接获取的需求退化成组装」—— 而这次明明就是直接获取成功的。
    告警说了一件没发生的事，比不说更糟。

    真正值得提醒的只有一种情况：某个数据集除了「这个维度没声明」之外，其余维度
    全都满足。补齐元数据它就能用，这才是可执行的建议。
    """
    blocked: dict[str, set[str]] = {}
    for cover in report.coverages:
        undeclared = [f for f in cover.facets if not f.declared]
        if not undeclared:
            continue
        others_ok = all(f.satisfied for f in cover.facets if f.declared)
        if not others_ok:
            # 还差别的维度，未声明不是它用不上的原因，补了也白补
            continue
        for facet in undeclared:
            blocked.setdefault(facet.label or facet.key, set()).add(cover.name or cover.dataset_id)

    for label in sorted(blocked):
        names = sorted(blocked[label])
        report.notes.append(
            f"{label}：在数据源注册里补齐 {names} 的这项元数据后，它们就能完整满足"
            "本次需求；目前因为无法核实而不计入满足"
        )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = _norm(value)
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()
