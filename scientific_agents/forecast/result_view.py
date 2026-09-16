"""Small, deterministic page projection shared with report naming."""
import re

from .warning.insights import risk_status

NAMES = {"rainfall_amount": "降雨量", "precipitation_amount": "降水量", "air_temperature": "气温",
         "discharge": "流量", "water_level": "水位",
         "relative_humidity": "相对湿度", "wind_speed": "风速", "wind_direction_unwrapped": "风向",
         "air_pressure": "气压", "visibility": "能见度", "sea_water_temperature": "海水温度",
         "sea_water_salinity": "海水盐度", "battery_voltage": "电池电压"}


def names(series):
    label = re.sub(r"\s*[·|]\s*(?:\d{4}.*?回放|实时.*?预测|历史回放)\s*$", "", series.label)
    area = series.metadata.get("area") or (series.assessment.area if series.assessment else None)
    area = re.sub(r"[（(]位置待确认[）)]", "", area or series.metadata.get("station_id") or label.split("·")[0]).strip()
    variable = series.metadata.get("variable_label") or NAMES.get(series.variable) or label.split("·")[-1].strip()
    if area == series.label or area == label:
        area = label.rsplit("·", 1)[0].strip() if "·" in label else series.metadata.get("station_id", "观测站")
    return area, variable


def title(result, report=False):
    pairs = [names(s) for s in result.series]
    areas = list(dict.fromkeys(a for a, _ in pairs))
    variables = list(dict.fromkeys(v for _, v in pairs))
    area = areas[0] if len(areas) == 1 else "、".join(areas)
    variable = "、".join(variables)
    return f"{area} {variable}预测{'报告' if report else '结果'}".strip()


def build(result):
    cards = []
    for series in result.series:
        values = [p.prediction for p in series.predictions]
        if not values:
            continue
        area, variable = names(series)
        a = series.assessment
        explanation = risk_status(series)
        metrics = [{"label": "预测最低值", "value": min(values), "unit": series.unit},
                   {"label": "预测最高值", "value": max(values), "unit": series.unit}]
        additive = series.quality.get(series.variable, {}).get("aggregation") == "sum"
        metrics.append({"label": "逐点中位数合计" if additive else "预测末值",
                        "value": sum(values) if additive else values[-1], "unit": series.unit})
        warnings = []
        if series.quality.get(series.variable, {}).get("constant_input"):
            warnings.append("历史输入恒定，缺少变化信息；全零通道需核查传感器。")
        if series.evaluation.get("available") and any(o.get("value") is not None and o["value"] > p.q90
                                                     for o, p in zip(series.observations, series.predictions)):
            warnings.append("回放实测部分超出预测范围，精度分析见报告。")
        cards.append(dict(case_id=series.case_id, label=f"{area} · {variable}", metrics=metrics,
            summary=f"预测值约为 {min(values):.4g}–{max(values):.4g} {series.unit}。{explanation}",
            risk_status=a.status if a else "not_assessed", risk_method=a.method if a else "none",
            risk_level=a.level if a else None, warnings=warnings))
    return {"title": title(result), "report_title": title(result, True), "series": cards}
