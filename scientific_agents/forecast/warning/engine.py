"""Deterministic conditions on forecast paths; missing evidence never means safe."""
import math
import operator

import numpy as np
import pandas as pd

from .contracts import Assessment, Scenario

OPS = {"gt": operator.gt, "ge": operator.ge, "lt": operator.lt, "le": operator.le}


def _values(condition, history, future, minutes):
    x = pd.Series([*history, *future], dtype=float)
    width = condition.window_steps
    if condition.statistic in {"sum", "mean", "max", "min"}:
        x = getattr(x.rolling(width, min_periods=width), condition.statistic)()
        if condition.statistic == "sum" and condition.input_kind == "rate_per_hour":
            x *= minutes / 60
    elif condition.statistic == "rate":
        x = x.diff(width) / (width * minutes / 60)
    return x.iloc[len(history):].to_numpy()


def assess(source, points, related=None):
    scenario = Scenario.model_validate(source["scenario"])
    minutes = source["frequency_minutes"]
    window = source.get("metadata", {}).get("forecast_window", {})
    assessment = Assessment(mode=scenario.mode, capability="indicator_forecast", status="not_assessed",
        area=scenario.area, hazard_type=scenario.hazard_type, scenario_version=scenario.version,
        window_start=window.get("start", source.get("metadata", {}).get("data_alignment", {}).get("requested_origin", source["timestamps"][-1])),
        window_end=window.get("end", source["future"][-1]),
        location=({"latitude": scenario.latitude, "longitude": scenario.longitude} if scenario.latitude is not None else None))
    assessment.limitations.append("预测区间及规则触发不等于事件发生概率；未触发不代表没有潜在风险。")
    if source.get("quality", {}).get(source["variable"], {}).get("constant_input"):
        assessment.limitations.append("目标在本次历史窗口内为恒定值，缺少变化信息；全零通道需核查传感器，预测不能作为环境安全或设备正常的依据。")
    gap = source.get("gap_steps", 0)
    if gap and source.get("metadata", {}).get("data_alignment", {}).get("method") != "calendar_forecast":
        assessment.limitations.append(f"最新共同观测落后请求起点 {gap * minutes / 60:g} 小时，模型跨越该间隔预测；间隔无真实观测，涉及该间隔的累计或变化规则按证据不足处理。")
    rules = [r for r in scenario.rules if r.approved]
    if rules:
        assessment.method = "registered_rules"
    elif scenario.use_history_screening and not scenario.rules:
        from .screening import historical_rules
        rules, reason = historical_rules(source)
        assessment.method = "historical_screening"
        assessment.limitations.append(reason)
        if not rules:
            assessment.status = "indeterminate"
            return assessment
    if not rules:
        assessment.limitations.append("当前场景未登记经审核且适用的评估规则，仅提供指标预测。")
        return assessment
    assessment.capability = "rule_assessment"
    levels = []
    history = {key: [*values, *([None] * gap)] for key, values in
               {source["variable"]: source["target"], **source["past_covariates"]}.items()}
    # Explicit linked targets are aligned exactly; held-out observations are never used.
    related = related or {}
    for rule in rules:
        checks, samples = [], []
        for c in rule.conditions:
            key = {"median": "prediction", "q10": "q10", "q90": "q90"}[rule.basis]
            history_values = history.get(c.variable, [None] * len(source["target"]))
            origin = "target_prediction" if c.variable == source["variable"] else "provided_future"
            forecast = ([p[key] for p in points]
                        if c.variable == source["variable"] else
                        source.get("future_covariates", {}).get(c.variable, [None] * len(points)))
            if c.case_id:
                linked = related.get(c.case_id)
                origin = "selected_prediction" if linked else "missing_selected_prediction"
                forecast, history_values = [None] * len(points), [None] * len(source["target"])
                if linked:
                    raw, predicted = linked
                    if (raw["variable"] == c.variable and raw["unit"] == c.unit
                            and raw["frequency_minutes"] == minutes
                            and pd.Timestamp(raw["future"][0]) == pd.Timestamp(source["future"][0])):
                        aligned = {pd.Timestamp(t): p[key] for t, p in zip(raw["future"], predicted)}
                        forecast = [aligned.get(pd.Timestamp(t)) for t in source["future"]]
                        past = {pd.Timestamp(t): v for t, v in zip(raw["timestamps"], raw["target"])}
                        history_grid = pd.date_range(end=pd.Timestamp(source["future"][0]) - pd.Timedelta(minutes=minutes),
                            periods=len(source["timestamps"]) + gap, freq=f"{minutes}min")
                        history_values = [past.get(t) for t in history_grid]
                    else:
                        origin = "incompatible_selected_prediction"
            values = _values(c, history_values, forecast, minutes)
            checks.append([None if not np.isfinite(v) else bool(OPS[c.operator](v, c.threshold)) for v in values])
            samples.append({"condition": c.model_dump(), "input_source": origin, "computed_unit": (c.output_unit or
                (c.unit + "/h" if c.statistic == "rate" else c.unit)),
                "values": [float(v) if np.isfinite(v) else None for v in values]})
        combined = []
        for row in zip(*checks):
            if rule.combine == "all":
                combined.append(False if False in row else None if None in row else True)
            else:
                combined.append(True if True in row else None if None in row else False)
        # Duration is elapsed time between forecast samples, not the sample count.
        required = 1 + math.ceil(rule.duration_minutes / minutes)
        if rule.duration_minutes % minutes or required > len(points):
            # Reject a duration that cannot be represented exactly on this grid.
            combined = [None] * len(points)
        intervals, streak = [], 0
        for index, value in enumerate(combined):
            streak = streak + 1 if value is True else 0
            if streak == required:
                intervals.append({"start": source["future"][index - required + 1], "end": source["future"][index],
                                  "detected_at": source["future"][index], "points": required})
            elif streak > required:
                intervals[-1].update(end=source["future"][index], points=streak)
        status = "triggered" if intervals else "indeterminate" if None in combined else "not_triggered"
        if status == "triggered" and rule.level is not None:
            levels.append((rule.severity, rule.level))
        assessment.evidence.append({"rule_id": rule.id, "rule_version": rule.version, "label": rule.label,
            "source": rule.source, "basis": rule.basis, "combine": rule.combine, "status": status,
            "level": rule.level, "duration_minutes": rule.duration_minutes, "intervals": intervals,
            "timestamps": source["future"], "conditions": samples})
    statuses = [e["status"] for e in assessment.evidence]
    assessment.status = "triggered" if "triggered" in statuses else "indeterminate" if "indeterminate" in statuses else "not_triggered"
    assessment.level = max(levels)[1] if levels else None
    if "indeterminate" in statuses:
        assessment.limitations.append("部分条件缺少未来变量或完整窗口，相关规则无法判定；已有触发仍保留。")
    return assessment
