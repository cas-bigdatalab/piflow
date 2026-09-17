"""Compact station-format template; expands to the existing Case/Scenario contracts."""
from copy import deepcopy


def normalize_units(source, scenarios):
    """Canonical labels for equivalent Campbell units; no value or threshold conversion."""
    aliases = {"degc": "°C", "°c": "°C", "℃": "°C", "degree": "°", "degrees": "°"}

    def label(unit):
        if not unit:
            return unit
        base, separator, denominator = unit.partition("/")
        return aliases.get(base.strip().casefold(), base) + separator + denominator

    case_ids = {case["id"] for case in source.get("cases", [])}
    for case in source.get("cases", []):
        for variable in [case["target"], *case.get("covariates", [])]:
            variable["unit"] = label(variable["unit"])
    # Keep explicitly registered rule units consistent, including linked station targets.
    for scenario in scenarios:
        for rule in scenario.get("rules", []):
            for condition in rule.get("conditions", []):
                if (condition.get("case_id") or scenario["case_id"]) in case_ids:
                    condition["unit"] = label(condition["unit"])
                    if condition.get("output_unit"):
                        condition["output_unit"] = label(condition["output_unit"])


def expand(source, scenarios):
    """Add one target per known Campbell channel, preserving explicitly registered cases."""
    options = source.get("options", {})
    if not options.get("register_all_variables"):
        return
    if not source.get("cases"):
        raise ValueError("Campbell 全变量模板需要一个基础案例及场景")
    base = source["cases"][0]
    station_name = source.get("display_name") or base["station_id"]
    if source.get("display_name"):
        old_name = base["label"].split(" · ")[0]
        for case in source["cases"]:
            if case["label"].startswith(old_name + " · "):
                case["label"] = station_name + case["label"][len(old_name):]
    scenario = next((s for s in scenarios if s["case_id"] == base["id"]), None)
    if scenario is None:
        raise ValueError("Campbell 基础案例缺少场景配置")
    if source.get("display_name"):
        scenario["aliases"] = list(dict.fromkeys([*scenario.get("aliases", []), scenario["area"]]))
        scenario["area"] = station_name
    prefix = options.get("case_prefix", base["id"])
    variables, labels, companions = {}, {}, {}

    def add(name, column, label, unit, aliases=(), minimum=None, maximum=None, auxiliary=()):
        variables[name] = dict(name=name, value_column=column, unit=unit, timezone=base["target"].get("timezone", "Asia/Shanghai"),
            aggregation="mean", aliases=list(dict.fromkeys([column, label, *aliases])),
            description=f"{column}；台站原始观测，字段含义和单位待数据方确认。")
        if minimum is not None:
            variables[name]["minimum"] = minimum
        if maximum is not None:
            variables[name]["maximum"] = maximum
        labels[name], companions[name] = label, list(auxiliary)

    weather = ["air_temperature", "relative_humidity", "air_pressure", "wind_speed", "wind_direction"]
    add("air_temperature", "TA_Avg", "气温", "°C", ["温度", "空气温度", "temperature"], auxiliary=weather[1:])
    add("relative_humidity", "RH_Avg", "相对湿度", "%", ["湿度", "humidity"], 0, 100, ["air_temperature", "wind_speed", "air_pressure"])
    add("air_pressure", "BP_Avg", "气压", "hPa", ["大气压", "pressure"], 0, auxiliary=["air_temperature", "relative_humidity", "wind_speed"])
    add("wind_speed", "WS_Avg", "风速", "m/s", ["风", "windspeed"], 0, auxiliary=["air_temperature", "relative_humidity", "air_pressure", "wind_direction"])
    add("radiation", "RA_Avg", "辐射观测", "原始单位", ["辐射", "太阳辐射"], 0, auxiliary=["air_temperature", "relative_humidity", "wind_speed"])
    add("rainfall_amount", "rain_Tot", "降雨量", "mm", ["rainfall", "precipitation", "降雨", "降水", "雨量", "降水量"], 0, auxiliary=weather)
    variables["rainfall_amount"]["aggregation"] = "sum"
    add("wind_direction_unwrapped", "WD_Unwrapped", "风向（连续角度）", "°", ["风向", "风向角", "wind_direction", "WD_Avg"],
        auxiliary=["wind_speed", "air_temperature", "relative_humidity", "air_pressure"])
    variables["wind_direction_unwrapped"]["description"] = (
        "WD_Avg 因果展开为连续角度，避免0°/360°跳变；可超出0～360°，对360取模得到方向。"
        "区间是连续角度表示上的模型分位数，不是环形置信区域。")
    add("battery_voltage", "batt_Min", "电池最低电压", "V", ["电池", "电压", "电源电压"], 0,
        auxiliary=["air_temperature", "radiation"])
    variables["battery_voltage"]["aggregation"] = "last"
    for probe in (1, 2, 3):
        moisture, ec, temperature = (f"soil_{kind}_probe{probe}" for kind in ("moisture", "conductivity", "temperature"))
        add(moisture, f"MS{probe}_Avg", f"第{probe}组水分观测", "原始单位", ["土壤水分", "水分", "soil_moisture"], 0,
            auxiliary=[temperature, "rainfall_amount", "air_temperature", "relative_humidity"])
        add(ec, f"EC{probe}_Avg", f"第{probe}组电导率观测", "原始单位", ["电导率", "soil_conductivity"], 0,
            auxiliary=[moisture, temperature, "rainfall_amount"])
        add(temperature, f"TS{probe}_Avg", f"第{probe}组温度观测", "°C", ["土壤温度", "地温", "soil_temperature"],
            auxiliary=[moisture, "air_temperature", "radiation"])
    for probe in (1, 2):
        for depth in (5, 10, 20, 30, 40, 50):
            suffix = f"{depth}cm" + ("_2" if probe == 2 else "")
            temperature = f"soil_temperature_{suffix}"
            for key, name, label, unit in [("VWC", "soil_water_content", "体积含水量", "原始单位"),
                                           ("Ka", "soil_dielectric", "介电常数", "原始单位"),
                                           ("T", "soil_temperature", "土壤温度", "°C"),
                                           ("BulkEC", "soil_bulk_conductivity", "土壤体电导率", "原始单位")]:
                auxiliary = ["air_temperature", "rainfall_amount", "relative_humidity"]
                auxiliary.insert(0, "radiation" if key == "T" else temperature)
                add(f"{name}_{suffix}", f"{key}_{suffix}_Avg", f"第{probe}组{depth}cm{label}", unit,
                    [label, name, f"{depth}cm{label}", *( ["土壤水分", "soil_moisture"] if key == "VWC" else [])],
                    minimum=None if key == "T" else 0, auxiliary=auxiliary)

    # Reuse the original rain case's exact variable definitions across roles.
    for v in [base["target"], *base.get("covariates", [])]:
        configured = deepcopy(v)
        configured["aliases"] = list(dict.fromkeys([*variables.get(v["name"], {}).get("aliases", []), *v.get("aliases", [])]))
        variables[v["name"]] = configured
    existing = {c["target"]["name"] for c in source["cases"]}
    for name, label in labels.items():
        if name in existing:
            continue
        case = dict(id=f"{prefix}_{name}", label=f"{station_name} · {label}",
                    station_id=base["station_id"], target=deepcopy(variables[name]),
                    covariates=[deepcopy(variables[v]) for v in companions[name] if v != name],
                    analysis_context=dict(domain="台站观测", subject=label,
                        objective=f"预测{label}的变化和关注时段。",
                        background="台站地址见数据源位置元信息；传感器含义和单位待核实，原始单位不做猜测换算。恒定或全零输入需核查，不能据此判断环境安全。"
                        + (variables[name]["description"] if name == "wind_direction_unwrapped" else "")))
        source["cases"].append(case)
        item = deepcopy(scenario)
        item.update(case_id=case["id"], hazard_type="unspecified", hazard_aliases=[], rules=[], use_standard=False)
        scenarios.append(item)
