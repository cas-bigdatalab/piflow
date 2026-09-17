"""Report-only changes preserve numerical evidence, exports and replay validation."""
import copy
import json
import re

import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader

from scientific_agents.forecast import reports
from scientific_agents.forecast.schema import ForecastResult, SeriesResult, TaskParams
from scientific_agents.forecast.warning.analysis import AnalysisNote, AnalysisSection, WarningAnalysis
from scientific_agents.forecast.warning.contracts import Scenario
from scientific_agents.forecast.warning.engine import assess


def sample_result():
    origin = pd.Timestamp("2026-09-18T00:00:00+08:00").tz_convert("UTC")
    times = pd.date_range(origin, periods=73, freq="h")[1:]
    history_times = pd.date_range(end=origin, periods=168, freq="h")
    values = 15 + 5 * np.sin(np.arange(72) * np.pi / 12)
    points = [{"timestamp": t.isoformat(), "prediction": float(v), "q10": float(v - 2), "q90": float(v + 2)}
              for t, v in zip(times, values)]
    history = [{"timestamp": t.isoformat(), "value": float(v)}
               for t, v in zip(history_times, 15 + 6 * np.sin(np.arange(168) * np.pi / 12))]
    scenario = Scenario(case_id="station", version="test", area="共和县光伏观测站", hazard_type="temperature",
                        mode="current", use_standard=False, use_history_screening=True)
    metadata = {"frequency_minutes": 60, "variable_label": "气温", "attention": "both",
                "forecast_window": {"start": origin.isoformat(), "end": times[-1].isoformat()},
                "location": {"name": "共和县光伏观测站", "address": "青海省共和县", "latitude": 36.28,
                             "longitude": 100.62, "coordinate_system": "WGS84"}}
    assessment = assess({"scenario": scenario.model_dump(), "frequency_minutes": 60, "variable": "air_temperature",
                         "unit": "°C", "target": [h["value"] for h in history], "timestamps": [h["timestamp"] for h in history],
                         "future": [p["timestamp"] for p in points], "past_covariates": {}, "metadata": metadata}, points)
    series = SeriesResult(case_id="station", label="共和县光伏观测站 · 气温", variable="air_temperature", unit="°C",
                          history=history, predictions=points, observations=[{"timestamp": p["timestamp"], "value": None} for p in points],
                          quality={"air_temperature": {"expected_points": 168, "missing_before": 0, "filled_points": 0,
                                                        "unit": "°C", "aggregation": "mean"}},
                          summary={"max": float(values.max()), "min": float(values.min()), "mean": float(values.mean()),
                                   "max_time": times[int(values.argmax())].isoformat(), "min_time": times[int(values.argmin())].isoformat(),
                                   "end_minus_origin": float(values[-1] - history[-1]["value"])},
                          evaluation={"available": False, "reason": "没有未来实测"},
                          provenance={"air_temperature": {"citation": "台站观测测试样本"}}, assessment=assessment, metadata=metadata)
    result = ForecastResult(run_id="report-layout-test", model={"id": "test-fixture"},
                            task=TaskParams(case_ids=["station"], origin=origin, horizon_hours=72), series=[series],
                            analysis_context={"user": {"objective": "预测气温的变化和关注时段"}})
    result.facts = reports.build_facts(result)
    return result


@pytest.fixture
def small_images(monkeypatch):
    # Layout checks use fixed image sizes; numerical chart generation is unchanged.
    from PIL import Image
    def figures(result, directory):
        outputs = []
        for i, _ in enumerate(result.series, 1):
            png, svg = f"forecast_{i}.png", f"forecast_{i}.svg"
            Image.new("RGB", (1000, 576), "white").save(directory / png)
            (directory / svg).write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            outputs.append((png, svg))
        return outputs
    def location(raw, path):
        Image.new("RGB", (700, 440), "white").save(path)
    monkeypatch.setattr(reports, "_figures", figures)
    monkeypatch.setattr("scientific_agents.forecast.location_map.render_location", location)


@pytest.mark.parametrize("with_analysis", [False, True])
def test_report_section_order_and_data_unchanged(tmp_path, small_images, with_analysis):
    result = sample_result()
    if with_analysis:
        result.warning_analysis = WarningAnalysis(source="llm", status="completed", facts=result.facts,
            sections=[AnalysisSection(id=key, title="任意模型章节标题", items=[AnalysisNote(text=text, fact_ids=[fact])])
                      for key, text, fact in [
                          ("overview", "气温随时间变化。", "series_0.profile"),
                          ("evidence", "关注峰谷附近的监测。", "series_0.focus"),
                          ("impacts", "需结合具体对象核查潜在影响。", "series_0.mean"),
                          ("recommendations", "新观测到达后核查变化。", "series_0.max")]])
    before = copy.deepcopy(result.model_dump(exclude={"artifacts", "report_status"}))
    reports.export_predictions(result, tmp_path)
    csv = (tmp_path / "predictions.csv").read_bytes()
    reports.render_report(result, tmp_path)
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    expected = ["预测位置与概况", "主要结论", "数据走势与关键时段", "主要依据与关注时段",
                "风险分析与预警判定", "后续关注建议", "数据与方法简述"]
    assert re.findall(r"<h3>(.*?)</h3>", html) == expected
    assert "科学预测智能体 · 分析报告" not in html
    assert "结果验证：" not in html and "任意模型章节标题" not in html
    assert "历史参考边界" in html and "HS-1.0" not in html
    pdf = "\n".join(page.extract_text() for page in PdfReader(tmp_path / "report.pdf").pages)
    assert [pdf.index(title) for title in expected] == sorted(pdf.index(title) for title in expected)
    assert result.model_dump(exclude={"artifacts", "report_status"}) == before
    assert (tmp_path / "predictions.csv").read_bytes() == csv
    assert json.loads((tmp_path / "assessment.json").read_text(encoding="utf-8"))["station"] == result.series[0].assessment.model_dump(mode="json")


def test_replay_validation_is_retained(tmp_path, small_images):
    result = sample_result()
    series = result.series[0]
    series.assessment.mode = "historical_replay"
    series.evaluation = {"available": True, "mae_skill": .1}
    series.observations = [{"timestamp": p.timestamp, "value": p.prediction + .5} for p in series.predictions]
    result.facts["series_0.evaluation"] = "回测误差测试说明。"
    reports.render_report(result, tmp_path)
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert html.index("<h3>风险分析与预警判定") < html.index("<h3>历史回放验证（事后实测）") < html.index("<h3>后续关注建议")
    assert "回测误差测试说明。" in html


@pytest.mark.parametrize("combine,phrase", [("all", "需同时满足"), ("any", "满足以下任一条件")])
def test_compound_risk_keeps_windows_quantile_duration_missing_values_and_status(combine, phrase):
    series = sample_result().series[0]
    series.assessment.method = "registered_rules"
    series.assessment.evidence = [{
        "label": "组合条件", "status": "indeterminate", "basis": "median", "combine": combine,
        "duration_minutes": 120, "intervals": [], "conditions": [
            {"condition": {"variable": "rain", "case_id": "other", "statistic": "sum", "window_steps": 6,
                           "operator": "ge", "threshold": 20}, "computed_unit": "mm", "values": [None, 21]},
            {"condition": {"variable": "wind", "statistic": "rate", "window_steps": 2,
                           "operator": "lt", "threshold": -2}, "computed_unit": "m/s/h", "values": [None, None]}]}]
    before = series.model_dump()
    text = "\n".join(reports._report_rule_lines(series, {("other", "rain"): "降雨量"}))
    assert phrase in text and "滚动 6 个采样步的累计量" in text and "相隔 2 个采样步的每小时变化率" in text
    assert "不低于阈值 20 mm" in text and "低于阈值 -2 m/s/h" in text
    assert "连续满足 120 分钟" in text and "部分时段依据缺失" in text and "缺少有效计算值" in text
    assert "依据不足，无法判定" in text
    assert series.model_dump() == before


def test_triggered_quantile_rule_preserves_trigger_times():
    series = sample_result().series[0]
    evidence = series.assessment.evidence[0]
    evidence.update(basis="q10", status="triggered", intervals=[{
        "start": "2026-09-18T00:00:00Z", "end": "2026-09-18T02:00:00Z", "detected_at": "2026-09-18T01:00:00Z"}])
    text = "\n".join(reports._report_rule_lines(series, {}))
    assert "预测下分位数 q10" in text and "已触发" in text
    assert "2026-09-18 08:00 至 2026-09-18 10:00" in text
    assert "达到持续条件的时刻：2026-09-18 09:00" in text


def test_multi_series_without_location_or_rules_and_additive_totals(tmp_path, small_images):
    result = sample_result()
    second = result.series[0].model_copy(deep=True)
    second.case_id = "second"
    second.label = "另一台站 · 降雨量"
    second.variable, second.unit = "rainfall", "mm"
    second.metadata.pop("location")
    second.assessment = None
    second.quality = {"rainfall": {"expected_points": 168, "missing_before": 0, "filled_points": 0,
                                   "unit": "mm", "aggregation": "sum"}}
    result.series.append(second)
    result.task.case_ids.append("second")
    reports.render_report(result, tmp_path)
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert html.count("<h3>主要结论</h3>") == 2
    assert html.count("<h3>预测位置与概况</h3>") == 1
    assert "逐点中位数合计 (mm)" in html
    assert "尚未配置适用的评估规则，本次仅完成指标预测。" in html
