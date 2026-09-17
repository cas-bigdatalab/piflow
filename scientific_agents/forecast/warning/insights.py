"""Forecast-only evidence and generic follow-up; no disaster-specific heuristics."""
import numpy as np
import pandas as pd


def number(value):
    return format(float(value), ".5g")


def time_label(value):
    return pd.Timestamp(value).tz_convert("UTC").strftime("%m-%d %H:%M")


def risk_status(series):
    a = series.assessment
    status = a.status if a else "not_assessed"
    if a and a.method == "historical_screening":
        return {"triggered": "预测出现超出历史参考范围的异常时段，建议核查；这是异常关注，不代表实际影响已发生。",
                "not_triggered": "历史异常筛查未发现明显偏离；未触发不代表不存在潜在风险。",
                "indeterminate": a.limitations[-1] if a.limitations else "历史基准不足，需核查输入数据。",
                "not_assessed": "历史异常筛查尚未完成。"}[status]
    return {
        "triggered": "预测满足已登记的评估条件，需重点核查对应时段；规则触发不代表实际影响已发生。",
        "not_triggered": "预测未触发已登记的评估条件；这不代表不存在潜在风险。",
        "indeterminate": "规则评估依据不完整，当前无法判断是否触发；需补齐条件输入。",
        "not_assessed": "尚未配置适用的评估规则，本次仅完成指标预测。",
    }[status]


def periods(series):
    """Group actual interval-end samples by requested 24-hour windows, never by point counts."""
    points = series.predictions
    window = series.metadata.get("forecast_window", {})
    start = pd.Timestamp(window.get("start") or (series.assessment.window_start if series.assessment else None)
                         or series.metadata.get("data_alignment", {}).get("requested_origin") or series.history[-1]["timestamp"])
    end = pd.Timestamp(window.get("end") or (series.assessment.window_end if series.assessment else None) or points[-1].timestamp)
    times = pd.to_datetime([p.timestamp for p in points], utc=True)
    rows = []
    additive = series.quality.get(series.variable, {}).get("aggregation") == "sum"
    while start < end:
        stop = min(start + pd.Timedelta(days=1), end)
        chunk = [points[i] for i in np.flatnonzero((times > start) & (times <= stop))]
        if not chunk:
            start = stop
            continue
        values = np.array([p.prediction for p in chunk])
        peak = chunk[int(values.argmax())]
        rows.append({"start": start.isoformat(), "end": stop.isoformat(), "max": float(values.max()), "max_time": peak.timestamp,
                     "mean": float(values.mean()), "total": float(values.sum()) if additive else None})
        start = stop
    return rows


def facts(series):
    p = np.array([v.prediction for v in series.predictions])
    history = np.array([v["value"] for v in series.history], dtype=float)
    zero_fraction = float(np.mean(history == 0))
    amplitude, past_amplitude = float(np.ptp(p)), float(np.ptp(history))
    profile = (f"历史窗口零值占比 {zero_fraction * 100:.2f}%；" if zero_fraction >= .5 else "")
    profile += f"预测变化范围 {number(p.min())}–{number(p.max())} {series.unit}。"
    if past_amplitude > 0 and amplitude < past_amplitude * .05:
        profile += "预测曲线相较历史波动明显平缓，应重点核查新观测是否出现模型未捕捉的突变。"
    else:
        profile += "关注预测峰值前后的变化及其与后续监测的吻合程度。"
    a = series.assessment
    conclusion = {"triggered": "已满足登记的评估条件，重点核查触发窗口内的观测变化及条件持续性。",
                  "not_triggered": "当前预测未满足登记条件，后续重点跟踪指标变化与触发条件的距离。",
                  "indeterminate": "部分评估条件的输入依据不完整，应优先补齐缺失指标后重新评估。",
                  "not_assessed": "本次围绕监测指标变化开展分析，重点关注变化时段和后续观测验证。"}
    outlook = conclusion[a.status] if a else conclusion["not_assessed"]
    if a and a.method == "historical_screening":
        outlook = risk_status(series)
    if a is None or a.status == "not_assessed":
        outlook = ("关注重点：预测变化明显弱于历史波动，优先核查后续突发变化是否被遗漏。"
                   if past_amplitude > 0 and amplitude < past_amplitude * .05 else
                   "关注重点：跟踪指标峰值前后的连续变化，并用新增监测核查变化是否持续。")
    focus = (f"指标预测峰值为 {number(series.summary['max'])} {series.unit}，"
             f"首次出现在 {time_label(series.summary['max_time'])} UTC。")
    if np.ptp(p) == 0:
        focus = f"全预测窗口中位数均为 {number(p[0])} {series.unit}，没有可区分的峰值时段，应持续跟踪整个窗口。"
    elif series.metadata.get("attention") == "low":
        focus = f"指标预测最低值为 {number(series.summary['min'])} {series.unit}，首次出现在 {time_label(series.summary['min_time'])} UTC。"
    elif series.metadata.get("attention", "both") == "both":
        focus += f" 最低值为 {number(series.summary['min'])} {series.unit}，首次出现在 {time_label(series.summary['min_time'])} UTC。"
    followup = "新观测到达后更新预测，优先核查与预测范围偏离的时段，并结合可获得的辅助记录交叉验证。"
    if a and a.status == "triggered":
        followup = "优先复核已触发条件对应的原始监测记录，跟踪持续时间及后续是否解除触发。"
    elif a and a.status == "indeterminate":
        followup = "先补齐无法判定条件所需的监测数据，再重新计算触发窗口。"
        if a.method == "historical_screening":
            followup = "核查观测通道及历史样本覆盖，明确指标含义后配置适用阈值，再更新分析。"
    return {"outlook": outlook, "profile": profile, "focus": focus, "followup": followup}


def retrospective(series):
    """Explicitly separate held-out validation from forecast-time hazard evidence."""
    if not series.evaluation.get("available"):
        return None
    values = np.array([v.get("value") for v in series.observations], dtype=float)
    valid = np.isfinite(values)
    if not valid.any():
        return None
    index = int(np.nanargmax(values))
    pred = series.predictions[index]
    text = (f"回放检验：已观测时段最高值 {number(values[index])} {series.unit}（{time_label(pred.timestamp)} UTC），"
            f"同一时刻预测中位数 {number(pred.prediction)} {series.unit}。")
    if values[index] > pred.q90:
        text += "实际峰值超出预测上分位数，本次预测未覆盖该峰值，应优先排查突变捕捉能力。"
    if series.evaluation.get("mae_skill") is not None and series.evaluation["mae_skill"] <= 0:
        text += "整体误差未优于保持最后观测值的基线。"
    return text
