"""Shared, forecast-only findings for the page, narrative and downloadable report.

Reference ranges describe the actual input window, never a climatology or a risk
threshold. Coincident changes are observations on forecast paths, not causation.
"""
import numpy as np
import pandas as pd


def intervals(timestamps, flags):
    """Contiguous samples; duration is elapsed time, not a guessed sample interval."""
    result = []
    for timestamp, flag in zip(timestamps, flags, strict=True):
        if flag:
            if result and result[-1].pop("open", False):
                result[-1].update(end=timestamp, points=result[-1]["points"] + 1, open=True)
            else:
                result.append({"start": timestamp, "end": timestamp, "points": 1, "open": True})
        elif result:
            result[-1]["open"] = False
    for item in result:
        item.pop("open", None)
        item["duration_minutes"] = (pd.Timestamp(item["end"]) - pd.Timestamp(item["start"])).total_seconds() / 60
    return result


def build_research(result):
    from .warning.insights import retrospective, risk_status
    features, findings, groups = [], [], {}
    for i, series in enumerate(result.series):
        prefix = f"series_{i}"
        p = np.array([v.prediction for v in series.predictions])
        times = [v.timestamp for v in series.predictions]
        history = np.array([v["value"] for v in series.history], dtype=float)
        attention = series.metadata.get("attention", "both")
        lower, upper = float(history.min()), float(history.max())
        change = np.diff(np.r_[history[-1], p])
        elapsed = np.diff(pd.to_datetime([series.history[-1]["timestamp"], *times], utc=True).asi8) / 3.6e12
        rates = change / elapsed
        extreme = int(np.abs(rates).argmax())
        high, low = p > upper, p < lower
        flags = high if attention == "high" else low if attention == "low" else high | low
        feature = {"case_id": series.case_id, "attention": attention,
            "reference": {"start": series.history[0]["timestamp"], "end": series.history[-1]["timestamp"],
                          "min": lower, "max": upper, "label": "本次历史输入窗口范围"},
            "high_windows": intervals(times, high), "low_windows": intervals(times, low),
            "largest_rate": {"value": float(rates[extreme]), "unit": series.unit + "/h", "timestamp": times[extreme]},
            "evaluation": {}}
        observed = np.array([v.get("value") for v in series.observations], dtype=float)
        # Full-window extreme validation is meaningful only with complete truth.
        if len(observed) == len(p) and np.isfinite(observed).all():
            for kind, op in (("max", np.argmax), ("min", np.argmin)):
                pi, oi = int(op(p)), int(op(observed))
                feature["evaluation"][kind] = {"prediction": float(p[pi]), "observation": float(observed[oi]),
                    "error": float(p[pi] - observed[oi]),
                    "timing_error_minutes": (pd.Timestamp(times[pi]) - pd.Timestamp(times[oi])).total_seconds() / 60}
        features.append(feature)

        def finding(suffix, title, text, windows, kind="computed"):
            findings.append({"id": f"{prefix}.{suffix}", "case_ids": [series.case_id],
                "title": title, "text": text, "kind": kind, "windows": windows,
                "fact_ids": [f"{prefix}.{suffix}"]})

        if attention == "change":
            finding("feature_change", "变化最快时段", f"{series.label}：预测相邻采样点间最大绝对变化速率为 {rates[extreme]:.6g} {series.unit}/h，出现在 {times[extreme]}；不代表全过程趋势。",
                    [{"start": times[max(0, extreme - 1)], "end": times[extreme]}])
        else:
            for kind in (["min"] if attention == "low" else ["max"] if attention == "high" else ["min", "max"]):
                t = series.summary[kind + "_time"]
                finding("feature_" + kind, "低值关注" if kind == "min" else "高值关注",
                    f"{series.label}：预测{'最低' if kind == 'min' else '最高'}值 {series.summary[kind]:.6g} {series.unit}，首次出现在 {t}。",
                    [{"start": t, "end": t}])
        for direction, windows in (("high", feature["high_windows"]), ("low", feature["low_windows"])):
            if windows and attention in {"both", "change", direction}:
                finding("feature_" + direction, "超出历史窗口范围",
                    f"{series.label}：预测有 {sum(w['points'] for w in windows)} 个采样点{'高于' if direction == 'high' else '低于'}本次历史输入范围 {lower:.6g}–{upper:.6g} {series.unit}。这不是季节异常或风险阈值判定。", windows)
        if series.assessment:
            for rule in series.assessment.evidence:
                dependencies = list(dict.fromkeys([series.case_id, *[c["condition"].get("case_id") for c in rule["conditions"] if c["condition"].get("case_id")]]))
                if rule["status"] == "triggered":
                    identifier = f"{prefix}.feature_rule_{len(findings)}"
                    findings.append({"id": identifier, "case_ids": dependencies, "title": rule["label"],
                        "text": f"{series.label}：预测满足登记条件“{rule['label']}”。判据来源：{rule['source']}；版本：{rule['rule_version']}。",
                        "kind": "rule", "windows": rule["intervals"], "fact_ids": [identifier]})
        station = series.metadata.get("station_id")
        source = series.metadata.get("source_id")
        if station and source:
            # Different cadences are not interpolated merely to create overlap.
            groups.setdefault((source, station, tuple(times)), []).append((i, series, flags))

    for (_, station, times), members in groups.items():
        # Compare distinct variables, not duplicate runs of the same indicator.
        unique = {s.variable: (i, s, mask) for i, s, mask in members}
        members = list(unique.values())
        if len(members) < 2:
            continue
        matrix = np.stack([mask for _, _, mask in members])
        windows = intervals(list(times), matrix.sum(axis=0) >= 2)
        if not windows:
            continue
        participating = [(i, s) for row, (i, s, _) in enumerate(members) if np.any(matrix[row] & (matrix.sum(axis=0) >= 2))]
        identifier = f"series_{participating[0][0]}.feature_overlap"
        findings.append({"id": identifier, "case_ids": [s.case_id for _, s in participating],
            "title": "多指标同时偏离各自历史范围", "kind": "coincidence", "windows": windows,
            "text": f"{station}：所列时段至少两个指标的预测同时超出各自本次历史输入范围；仅表示时间重合，未验证因果关系或复合风险。",
            "fact_ids": [identifier, *[f"series_{i}.profile" for i, _ in participating]]})
    return {"version": "1.1", "time_zone": "UTC", "features": features, "findings": findings,
            "validation": [{"case_id": s.case_id, "text": retrospective(s)} for s in result.series if retrospective(s)],
            "risk_status": [{"case_id": s.case_id, "text": risk_status(s)} for s in result.series],
            "alignment": "按预测时间戳精确对齐；不同单位保持独立纵轴。",
            "reference_note": "历史范围来自本次输入窗口，不是气候常态、统计显著性检验或风险等级。"}
