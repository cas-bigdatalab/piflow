"""Deterministic defaults; data sufficiency is checked in the supervised data stage."""
import math
import pandas as pd

from .feedback import ForecastError, local_time


class OriginChoice(Exception):
    def __init__(self, prompt, field="origin_mode", options=None):
        self.interaction = {"field": field, "prompt": prompt, "options": options or []}


def resolve_origin(params, registry):
    """Pure catalogue/clock lookup. Never substitutes old observations for 'now'."""
    result = dict(params)
    mode = result.get("origin_mode") or ("explicit" if result.get("origin") else "now")
    scenarios = [registry.warnings.get(registry.cases[key]) for key in result["case_ids"]]
    if mode == "explicit":
        if not result.get("origin"):
            raise OriginChoice("请指定这次历史回放的起点并包含时区。", "origin")
    elif mode == "now":
        if any(s.mode != "current" for s in scenarios):
            choices = ([{"id": "replay", "label": "使用历史数据回放"}]
                       if all(s.mode == "historical_replay" for s in scenarios) else [])
            raise OriginChoice("所选数据包含历史回放资料，不能用于预测当前未来时段。"
                               + ("可以选择历史回放，我会自动使用配置的回放时点。" if choices else "请改选同一模式的监测案例。"), options=choices)
        frequency = math.lcm(*(registry.warnings.timing(key)[0] for key in result["case_ids"]))
        result["origin"] = pd.Timestamp.now(tz="UTC").floor(f"{frequency}min").isoformat()
    else:
        if any(s.mode != "historical_replay" for s in scenarios):
            raise ForecastError("invalid_parameters", "所选场景包含当前监测案例，请改选历史回放案例。")
        dates = {s.default_replay_origin for s in scenarios}
        if None in dates or len(dates) != 1:
            raise OriginChoice("所选案例未配置共同的默认回放时点。请指定一个共同的历史起点（含时区），或更换案例。", "origin")
        result["origin"] = pd.Timestamp(next(iter(dates))).tz_convert("UTC").isoformat()
    result["origin_mode"] = mode
    return result


def history_steps(params, registry, case_id):
    frequency, minimum, _ = registry.warnings.timing(case_id)
    if params.history_hours is not None:
        if params.history_hours * 60 % frequency:
            raise ForecastError("invalid_parameters", "指定历史长度必须对齐数据采样频率。")
        requested = params.history_hours * 60 // frequency
        if requested < minimum:
            raise ForecastError("invalid_parameters", f"{case_id}至少需要 {minimum * frequency / 60:g} 小时历史数据；不会自动改变你指定的长度。")
    else:
        horizon_steps = params.horizon_hours * 60 // frequency
        requested = max(minimum, horizon_steps * registry.settings.history_multiplier)
    if requested > 15360:
        raise ForecastError("invalid_parameters", "历史窗口超出固定模型支持的最大长度，请缩短历史长度。")
    return requested, minimum


def plan_message(params, registry):
    windows = [history_steps(params, registry, key)[0] * registry.warnings.timing(key)[0] / 60
               for key in params.case_ids]
    history = (f"参考过去 {windows[0]:g} 小时的历史记录" if len(set(windows)) == 1
               else "按各案例配置确定历史窗口")
    mode = "历史回放" if all(registry.warnings.get(registry.cases[k]).mode == "historical_replay" for k in params.case_ids) else "当前预测"
    return (f"已匹配数据，将进行{mode}，从 {local_time(params.origin)}（北京时间）起预测 {params.horizon_hours} 小时，{history}。"
            "正在检查数据时效和完整性；满足要求后会自动预测，否则会说明原因。")
