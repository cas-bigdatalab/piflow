"""One set of factual labels for restored replies, HTML and PDF."""
from html import escape

STATUS = {"triggered": "已触发配置条件", "not_triggered": "未触发配置条件",
          "indeterminate": "依据不足，无法判定", "not_assessed": "仅完成指标预测"}
BASIS = {"median": "预测中位数", "q10": "预测下分位数q10", "q90": "预测上分位数q90"}


def facts(series):
    a = series.assessment
    if a is None:
        return {}
    result = {"assessment": f"{a.area} / {'历史异常筛查' if a.method == 'historical_screening' else a.hazard_type}：{STATUS[a.status]}。"
              + (f"研究分级：{a.level}。" if a.level else "未提供研究分级。")
              + f"评估窗口：{a.window_start} 至 {a.window_end}；"
              + ("历史回放。" if a.mode == "historical_replay" else "当前数据评估。"),
              "probability": "未接入适用的事件概率模型，不提供发生概率。",
              "limitations": " ".join(a.limitations)}
    for index, e in enumerate(a.evidence):
        windows = "；".join(f"{w['start']} 至 {w['end']}，满足持续条件的时刻 {w['detected_at']}" for w in e["intervals"])
        conditions = "；".join(f"{c['condition']['variable']} {c['condition']['statistic']} "
            f"{c['condition']['operator']} {c['condition']['threshold']} {c['computed_unit']}"
            for c in e["conditions"])
        result[f"rule_{index}"] = (f"{e['label']}：{STATUS[e['status']]}；依据{BASIS[e['basis']]}。"
            f"条件：{conditions}。" + (f"触发窗口：{windows}。" if windows else "")
            + f"规则 {e['rule_id']}@{e['rule_version']}；来源：{e['source']}。")
    return result


def card(series):
    a = series.assessment
    if a is None:
        return ""
    label = "历史回放" if a.mode == "historical_replay" else "当前评估"
    return (f"<section class='assessment {a.status}' aria-label='规则评估'>"
            f"<div class='muted'>{escape(label)} · {escape(a.hazard_type)}</div>"
            f"<h2>{escape(a.area)}</h2><strong>{escape(STATUS[a.status])}</strong>"
            f"<p>{escape(a.window_start)} — {escape(a.window_end)}</p>"
            f"<p>研究分级：{escape(a.level or '未提供')} · 事件概率：未提供</p>"
            f"<p>{escape(' '.join(a.limitations))}</p></section>")


def annotate(ax, timeline, series):
    """Static evidence timeline; no spatial interpolation or probability colouring."""
    import numpy as np
    import pandas as pd
    a = series.assessment
    if a is None or not a.evidence:
        timeline.text(.5, .5, "No registered warning policy", ha="center", va="center", transform=timeline.transAxes)
        timeline.set_yticks([])
        return
    for row, e in enumerate(a.evidence):
        x = pd.to_datetime(e["timestamps"], utc=True)
        for condition in e["conditions"]:
            c = condition["condition"]
            if c["variable"] == series.variable and c["statistic"] == "value":
                ax.axhline(c["threshold"], color="#AD573B", linestyle="--", alpha=.6,
                           label=f"{e['rule_id']} ({e['basis']})")
        timeline.plot(x, np.full(len(x), row), color="#AEB9C4", linewidth=5)
        for window in e["intervals"]:
            start, end = pd.Timestamp(window["start"]), pd.Timestamp(window["end"])
            timeline.plot([start, end], [row, row], color="#B35B32", linewidth=7, marker="|")
        if e["status"] == "indeterminate":
            timeline.scatter(x, np.full(len(x), row), marker="x", s=8, color="#64748B")
    timeline.set_yticks(range(len(a.evidence)), [e["rule_id"] for e in a.evidence], fontsize=7)
    timeline.set_ylabel("Rule windows")
    timeline.set_ylim(-.6, len(a.evidence) - .4)
    ax.legend(loc="best", fontsize=7)
