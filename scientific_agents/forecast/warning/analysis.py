"""Optional, evidence-bound narrative; never changes the numerical assessment."""
import asyncio
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
import re
from typing import Literal

from pydantic import Field

from ...contracts import StrictModel

log = logging.getLogger(__name__)
VERSION = "1.2"
TIMEOUT_SECONDS = 20
TITLES = {"overview": "主要结论", "evidence": "预测依据", "impacts": "领域影响分析",
          "recommendations": "后续关注建议", "limitations": "不确定性与限制"}
# Fixed generic research guidance. No operational warning/evacuation instructions.
GUIDANCE = {
    "check_quality": "核查监测数据的完整性、时效性及异常记录，结合后续观测检查预测变化。",
    "check_rules": "核对评估规则的对象、指标单位和适用条件；缺少适用规则时先补充评估依据。",
    "check_context": "结合可获得的同期辅助监测资料进一步分析；尚未接入的资料不能作为本次结论的依据。",
    "review_window": "围绕指标峰值或规则触发窗口核查连续观测，并与适用的同期独立资料交叉核对。",
}


class AnalysisNote(StrictModel):
    text: str = Field(min_length=1, max_length=600)
    fact_ids: list[str] = Field(min_length=1, max_length=12)
    context_ids: list[str] = Field(default_factory=list, max_length=8)
    condition: str = Field(default="", max_length=600)
    knowledge_basis: Literal["forecast", "provided", "general"] = "forecast"


class AnalysisDraft(StrictModel):
    title: str = Field(default="科学预测分析报告", min_length=1, max_length=80)
    section_titles: dict[str, str] = Field(default_factory=dict, max_length=5)
    overview: list[AnalysisNote] = Field(min_length=1, max_length=3)
    evidence: list[AnalysisNote] = Field(min_length=1, max_length=5)
    impacts: list[AnalysisNote] = Field(default_factory=list, max_length=5)
    recommendations: list[AnalysisNote] = Field(default_factory=list, max_length=5)
    guidance_ids: list[str] = Field(default_factory=list, max_length=4)  # Legacy drafts / offline fallback.
    limitations: list[AnalysisNote] = Field(min_length=1, max_length=3)


class AnalysisSection(StrictModel):
    id: Literal["overview", "evidence", "impacts", "recommendations", "limitations"]
    title: str
    items: list[AnalysisNote]


class WarningAnalysis(StrictModel):
    # Keep the existing field/type names so historical clients and stored results load.
    schema_version: str = VERSION
    status: Literal["pending", "completed", "fallback", "unavailable"] = "pending"
    source: Literal["llm", "deterministic"] = "deterministic"
    message: str = "预测已完成，正在结合领域背景生成分析。"
    title: str = "科学预测分析报告"
    reason_code: str | None = None
    generated_at: str | None = None
    model: str | None = None
    evidence_sha256: str | None = None
    sections: list[AnalysisSection] = Field(default_factory=list)
    facts: dict[str, str] = Field(default_factory=dict)
    contexts: dict[str, dict] = Field(default_factory=dict)
    report_included: bool = False
    omitted_items: int = 0


def evidence_packet(result):
    # Held-out observations and retrospective errors must not explain historical risk.
    facts = {k: v for k, v in result.facts.items()
             if not k.endswith((".evaluation", ".coverage"))}
    cases, contexts = [], {}
    saved = result.analysis_context
    registered = {c["case_id"]: c for c in saved.get("cases", [])}
    for i, series in enumerate(result.series):
        prefix = f"series_{i}"
        facts[f"{prefix}.quality"] = "输入质量：" + "；".join(
            f"{name}：历史窗口 {q['expected_points']} 点，缺测 {q['missing_before']} 点，填补 {q['filled_points']} 点"
            for name, q in series.quality.items())
        description = registered.get(series.case_id, {})
        context = description.get("context", {})
        for key in ("domain", "subject", "objective", "background"):
            if context.get(key):
                contexts[f"{prefix}.{key}"] = {"text": context[key], "source": "数据源注册信息",
                    "kind": "registered", "case_id": series.case_id}
        if description.get("target", {}).get("description"):
            contexts[f"{prefix}.definition"] = {"text": description["target"]["description"],
                "source": "变量说明", "kind": "registered", "case_id": series.case_id}
        for j, ref in enumerate(context.get("references", [])):
            contexts[f"{prefix}.reference_{j}"] = {**ref, "text": ref["content"], "kind": "reference", "case_id": series.case_id}
        cases.append({"case_id": series.case_id, "label": series.label, "variable": series.variable,
                      "unit": series.unit, "fact_prefix": prefix,
                      "data_description": description,
                      "assessment": ({k: v for k, v in series.assessment.model_dump(mode="json").items()
                                      if k != "evidence"} if series.assessment else None)})
    for key, value in saved.get("user", {}).items():
        if value:
            contexts[f"user.{key}"] = {"text": value, "source": "用户提供（未独立核实）", "kind": "user"}
    facts["analysis_boundary"] = (
        "领域影响是基于背景的条件性分析，不是已验证的因果结论；用户陈述不等于实测依据。"
        "未触发条件或未完成评估不代表低风险；没有适用模型时不提供事件发生概率或自定预警等级。")
    return {"cases": cases, "facts": facts, "contexts": contexts,
            "recent_user_messages": saved.get("recent_user_messages", []),
            "guidance": GUIDANCE, "version": VERSION}


def fallback_draft(packet):
    facts = packet["facts"]
    assessment = [k for k in facts if k.endswith(".outlook")] or ["scope"]
    peaks = [k for k in facts if k.endswith((".profile", ".focus"))] or ["task"]
    limits = [k for k in facts if k.endswith(".limitations")]
    return AnalysisDraft(
        overview=[AnalysisNote(text=facts[key], fact_ids=[key]) for key in assessment[:3]],
        evidence=[AnalysisNote(text="结合预测变化范围和关键时段，核查后续观测是否偏离预测。", fact_ids=peaks[i:i+10]) for i in range(0, len(peaks), 10)],
        recommendations=[AnalysisNote(text="结合预测对象核查峰值附近的观测与输入质量；领域影响需要对应背景支持。", fact_ids=peaks[:10])],
        limitations=[AnalysisNote(text="解释预测结果时需同时考虑数据和评估能力的限制。", fact_ids=["analysis_boundary", "interval", *limits[:10]])])


def validate_draft(draft, packet):
    draft = AnalysisDraft.model_validate(draft)
    if any(key not in GUIDANCE for key in draft.guidance_ids):
        raise ValueError("Unknown guidance reference")
    if any(key not in TITLES or not title or len(title) > 80 for key, title in draft.section_titles.items()):
        raise ValueError("Invalid section title")
    # Numerical values are rendered from facts, never from generated prose. This is
    # a conservative output gate, not a claim of automatic semantic verification.
    prohibited = re.compile(
        r"[\d%％<>]|[零一二三四五六七八九十百千万两点]+(?:毫米|小时|分钟|天|成|级|%)|"
        r"概率|风险等级|预警等级|[红橙黄蓝]色预警|高风险|低风险|中风险|"
        r"必然|必定|一定发生|不会发生|排除灾害|确保安全|撤离|疏散|封路|停工|发布预警|"
        r"probability|percent|high.risk|low.risk|evacuat|certainly", re.I)
    if any(prohibited.search(text) for text in [draft.title, *draft.section_titles.values()]):
        raise ValueError("Ungrounded report title")
    for note in [*draft.overview, *draft.evidence, *draft.impacts, *draft.recommendations, *draft.limitations]:
        if not note.text.strip() or note.text.rstrip().endswith(("：", ":")):
            raise ValueError("Analysis must contain a complete statement")
        if re.search(r"风险(?:上升|下降|升|降|增加|增大|降低|减小)", note.text) and (not note.condition or note.knowledge_basis == "forecast"):
            raise ValueError("Risk interpretation requires a condition and domain basis")
        if (prohibited.search(note.text + note.condition) or any(key not in packet["facts"] for key in note.fact_ids)
                or any(key not in packet.get("contexts", {}) for key in note.context_ids)):
            raise ValueError("Ungrounded analysis output")
        if note.knowledge_basis == "provided" and not note.context_ids:
            raise ValueError("Provided knowledge requires a context reference")
        if note.knowledge_basis == "general" and not note.condition:
            raise ValueError("General knowledge must state its applicability")
        prefixes = {key.split(".")[0] for key in note.fact_ids if key.startswith("series_")}
        if any(key.startswith("series_") and key.split(".")[0] not in prefixes for key in note.context_ids):
            raise ValueError("Context belongs to an uncited series")
    if any(not note.condition or note.knowledge_basis == "forecast"
           or not any(k.startswith("series_") for k in note.fact_ids) for note in draft.impacts):
        raise ValueError("Impact analysis needs a forecast and an explicit condition")
    cited = {key.split(".")[0] for note in draft.evidence for key in note.fact_ids}
    if any(case["fact_prefix"] not in cited for case in packet["cases"]):
        raise ValueError("Analysis omitted a forecast series")
    return draft


def repair_draft(draft, packet):
    """Retain independently valid notes; repairs never alter a computed result."""
    draft = AnalysisDraft.model_validate(draft)
    try:
        return validate_draft(draft, packet), 0
    except ValueError:
        pass
    base = fallback_draft(packet)
    # Ensure the repair's evidence covers every series even with large selections.
    base.evidence = [AnalysisNote(text="预测变化特征需要结合后续观测验证。", fact_ids=[c["fact_prefix"] + ".profile"])
                     for c in packet["cases"][:5]]
    if len(packet["cases"]) > 5:
        base.evidence = [AnalysisNote(text="各指标分别依据自身历史窗口开展预测。", fact_ids=[c["fact_prefix"] + ".profile" for c in packet["cases"]])]
    repaired, omitted = base.model_copy(deep=True), 0
    for group in ("overview", "evidence", "impacts", "recommendations", "limitations"):
        accepted = []
        for note in getattr(draft, group):
            probe = base.model_copy(deep=True)
            if group == "evidence":
                probe.evidence = [AnalysisNote(text="各指标分别依据自身历史窗口开展预测。", fact_ids=[c["fact_prefix"] + ".profile" for c in packet["cases"]]), note]
            else:
                setattr(probe, group, [note])
            try:
                validate_draft(probe, packet)
                accepted.append(note)
            except ValueError:
                omitted += 1
        if accepted:
            setattr(repaired, group, accepted)
    cited = {k.split('.')[0] for n in repaired.evidence for k in n.fact_ids}
    missing = [c["fact_prefix"] + ".profile" for c in packet["cases"] if c["fact_prefix"] not in cited]
    if missing:
        # At most five evidence paragraphs; fold missing coverage into a computed note.
        repaired.evidence = repaired.evidence[:4] + [AnalysisNote(text="其余指标的预测变化也需结合后续观测验证。", fact_ids=missing)]
    probe = repaired.model_copy(update={"title": draft.title, "section_titles": draft.section_titles})
    try:
        validate_draft(probe, packet)
        repaired = probe
    except ValueError:
        omitted += 1
    omitted += len(draft.guidance_ids)
    return validate_draft(repaired, packet), max(1, omitted)


def assemble(packet, draft, *, source="deterministic", reason=None, model=None):
    # Structured assessment remains authoritative; boundaries render only in the footer.
    boundary = AnalysisNote(text="评估边界：", fact_ids=["scope", "interval", "analysis_boundary"])
    followup = [k for k in packet["facts"] if k.endswith(".followup")]
    groups = {"overview": draft.overview, "evidence": draft.evidence, "impacts": draft.impacts,
              "recommendations": draft.recommendations + [AnalysisNote(text=GUIDANCE[key], fact_ids=["analysis_boundary"])
                                  for key in dict.fromkeys(draft.guidance_ids)] +
                                  ([AnalysisNote(text="用新增观测核查预测偏离，及时更新分析。", fact_ids=followup[:10])] if followup else []),
              "limitations": [boundary, *draft.limitations]}
    return WarningAnalysis(status="completed" if source == "llm" else "fallback", source=source,
        title=draft.title, contexts=packet.get("contexts", {}),
        message="预测分析已生成。" if source == "llm" else "已提供基于计算结果的基础分析。",
        reason_code=reason, model=model, generated_at=datetime.now(timezone.utc).isoformat(),
        evidence_sha256=sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        sections=[AnalysisSection(id=key, title=draft.section_titles.get(key, TITLES[key]), items=items)
                  for key, items in groups.items() if items],
        facts=packet["facts"])


class WarningAnalyzer:
    def __init__(self, interpreter=None):
        self.interpreter = interpreter
        self._runner = None

    @property
    def enabled(self):
        return callable(getattr(self.interpreter, "analyze_warning", None))

    def generate(self, result, reason=None):
        packet = evidence_packet(result)
        if self.enabled and reason is None:
            async def invoke():
                return await asyncio.wait_for(self.interpreter.analyze_warning(packet), TIMEOUT_SECONDS)
            try:
                # Reuse the worker's event loop: HTTP connection pools cannot safely
                # migrate between a fresh asyncio.run loop on every forecast.
                if self._runner is None:
                    self._runner = asyncio.Runner()
                draft, omitted = repair_draft(self._runner.run(invoke()), packet)
                output = assemble(packet, draft, source="llm", reason="analysis_partial" if omitted else None,
                                  model=getattr(self.interpreter, "model_name", None))
                output.omitted_items = omitted
                if omitted:
                    output.message = "分析已生成；未通过依据检查的条目已移除，其余结论保留。"
                return output
            except (TimeoutError, asyncio.TimeoutError):
                reason = "analysis_timeout"
            except Exception as exc:
                reason = "analysis_unavailable"
                log.warning("Warning analysis fallback: %s", type(exc).__name__)
        return assemble(packet, fallback_draft(packet), reason=reason or "dialogue_offline")

    def close(self):
        if self._runner is not None:
            try:
                close = getattr(self.interpreter, "close_warning", None)
                if close:
                    self._runner.run(close())
            finally:
                self._runner.close()
                self._runner = None


def context_label(key, ref):
    labels = {"domain": "领域说明", "subject": "对象说明", "objective": "分析目标",
              "background": "背景说明", "definition": "变量定义"}
    return ref.get("title", labels.get(key.split(".")[-1], key)) + " · " + ref.get("source", "提供的背景材料")


def note_text(note, facts):
    """Restore legacy label-only notes without changing stored forecasts."""
    if not note.text.strip() or note.text.rstrip().endswith(("：", ":")):
        return " ".join(dict.fromkeys(facts[k] for k in note.fact_ids if facts.get(k))) or "本条分析缺少可用依据，请重新生成分析。"
    return note.text


def analysis_lines(analysis):
    if analysis is None:
        return []
    lines = [analysis.title]
    seen = set()
    for section in analysis.sections:
        lines.append(section.title)
        for item in section.items:
            lines.append(note_text(item, analysis.facts))
            if item.condition:
                lines.append("成立条件：" + item.condition)
            if item.knowledge_basis == "general":
                lines.append("分析依据：一般领域知识，需结合具体对象核实。")
            for key in item.context_ids:
                ref = analysis.contexts.get(key, {})
                lines.append("背景依据：" + context_label(key, ref))
            for key in item.fact_ids:
                if key not in seen and (section.id == "limitations" or not key.endswith(("boundary", "limitations", "probability")) and key not in {"scope", "interval"}):
                    lines.append(analysis.facts[key])
                    seen.add(key)
    return lines


def save_analysis(result, directory, analyzer, reason=None):
    """Persist the narrative and refresh reports without risking completed forecasts."""
    from ..reports import render_report
    from ..workflow import write_json
    if result.warning_analysis is None or result.warning_analysis.status == "pending":
        result.warning_analysis = analyzer.generate(result, reason)
    analysis = result.warning_analysis
    original_artifacts = list(result.artifacts)
    try:
        analysis.report_included = True
        render_report(result, directory)
        result.report_status = "completed"
    except Exception as exc:
        analysis.report_included = False
        result.report_status = "failed"
        result.artifacts = original_artifacts
        log.warning("Analysis report refresh unavailable: %s", type(exc).__name__)
    write_json(directory / "warning_analysis.json", analysis.model_dump(mode="json"))
    if "warning_analysis.json" not in result.artifacts:
        result.artifacts.append("warning_analysis.json")
    write_json(directory / "result.json", result.model_dump(mode="json"))
    return analysis
