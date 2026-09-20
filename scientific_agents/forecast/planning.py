"""Deterministic defaults; data sufficiency is checked in the supervised data stage."""
import pandas as pd

from .feedback import ForecastError, local_time


def sampling_floor(value, frequency):
    """Use the same UTC epoch grid as analytics.resample; never restart it at a window boundary."""
    return pd.Timestamp(value).tz_convert("UTC").floor(f"{frequency}min")


def forecast_grid(origin, hours, frequency):
    """Interval-end labels in (requested start, requested end], without partial extra steps."""
    start = pd.Timestamp(origin).tz_convert("UTC")
    first_boundary = sampling_floor(start, frequency)
    last = sampling_floor(start + pd.Timedelta(hours=hours), frequency)
    step = pd.Timedelta(minutes=frequency)
    count = int((last - first_boundary) / step)
    if count < 1:
        raise ForecastError("invalid_parameters", "请求时间窗口内没有采样点，请扩大预测时间范围。")
    if count > 1024:
        raise ForecastError("invalid_parameters", "请求超出固定模型支持的预测长度限制。")
    return pd.date_range(start=first_boundary + step, periods=count, freq=step)


class OriginChoice(Exception):
    def __init__(self, prompt, field="origin_mode", options=None):
        self.interaction = {"field": field, "prompt": prompt, "options": options or []}


def resolve_origin(params, registry, now=None):
    """Pure catalogue/clock lookup. Never substitutes old observations for 'now'."""
    result = dict(params)
    now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now).tz_convert("UTC")
    mode = result.get("origin_mode") or ("explicit" if result.get("origin") else "now")
    ids = [*result["case_ids"], *(result.get("auxiliary_case_ids") or [])]
    if any(key not in registry.cases for key in ids):
        raise ForecastError("invalid_parameters", "所选目标或辅助变量已不在当前数据目录中，请重新选择。")
    scenarios = [registry.warnings.get(registry.cases[key]) for key in ids]
    if mode == "explicit":
        if not result.get("origin"):
            raise OriginChoice("请指定这次历史回放的起点并包含时区。", "origin")
        origin = pd.Timestamp(result["origin"])
        if origin.tzinfo is None:
            raise ForecastError("invalid_time", "预测起点必须包含时区。")
        result.setdefault("forecast_mode", "historical_replay" if origin < now else "current")
        if result["forecast_mode"] == "current" and any(s.mode != "current" for s in scenarios):
            raise OriginChoice("所选资料仅用于历史回放，请指定历史日期或选择当前监测数据。", "origin")
        if origin > now:
            result.setdefault("history_cutoff", now.isoformat())
    elif mode in {"now", "tomorrow"}:
        if any(s.mode != "current" for s in scenarios):
            choices = [{"id": "replay", "label": "使用历史数据回放"}]
            raise OriginChoice("所选数据包含历史回放资料，不能用于预测当前未来时段。"
                               "可以选择历史回放，我会根据配置或可用数据确定共同回放窗口。", options=choices)
        result["forecast_mode"] = "current"
        # Each series aligns its model input independently; the user's time window is shared.
        result["origin"] = now.isoformat()
        if not result.get("history_start"):
            result.pop("history_cutoff", None)
        if mode == "tomorrow":
            if not result.get("history_start"):
                result["history_cutoff"] = now.isoformat()
            result["origin"] = (now.tz_convert("Asia/Shanghai").normalize() + pd.Timedelta(days=1)).isoformat()
            result.setdefault("horizon_hours", 24)
    else:
        if not result.get("history_start"):
            result.pop("history_cutoff", None)
        result["forecast_mode"] = "historical_replay"
        dates = {s.default_replay_origin for s in scenarios}
        if result.get("history_start") and result.get("history_cutoff"):
            result["origin"] = result["history_cutoff"]
        elif None not in dates and len(dates) == 1:
            result["origin"] = pd.Timestamp(next(iter(dates))).tz_convert("UTC").isoformat()
        else:
            latest = [getattr(registry, "series_info", {}).get(key, {}).get("latest_observation") for key in ids]
            if not all(latest) or not result.get("horizon_hours"):
                raise OriginChoice("请指定历史回放日期和时长；当前没有足够的目录信息确定共同回放窗口。", "origin")
            end = min([now, *(pd.Timestamp(t).tz_convert("UTC") for t in latest)])
            if result["horizon_hours"] % 24 == 0:
                end = end.tz_convert("Asia/Shanghai").normalize()
            result["origin"] = (end - pd.Timedelta(hours=result["horizon_hours"])).isoformat()
    result["origin_mode"] = mode
    if result.get("history_start"):
        start = pd.Timestamp(result["history_start"])
        cutoff = pd.Timestamp(result.get("history_cutoff") or result["origin"])
        if start.tzinfo is None or cutoff.tzinfo is None or not start < cutoff <= pd.Timestamp(result["origin"]):
            raise ForecastError("invalid_time", "历史输入区间必须有明确时区，起点早于终点，且终点不能晚于预测起点。")
    return result


def history_steps(params, registry, case_id):
    frequency, minimum, _ = registry.warnings.timing(case_id)
    if params.history_start is not None:
        cutoff = pd.Timestamp(params.history_cutoff or params.origin)
        start = pd.Timestamp(params.history_start)
        if not start < cutoff <= pd.Timestamp(params.origin):
            raise ForecastError("invalid_time", "历史输入区间无效或延伸到了预测区间。")
        requested = int((sampling_floor(cutoff, frequency) - sampling_floor(start, frequency)) / pd.Timedelta(minutes=frequency))
        if params.history_hours is not None and pd.Timedelta(hours=params.history_hours) != cutoff - start:
            raise ForecastError("invalid_parameters", "历史起止时间与指定历史小时数不一致，请调整历史条件。")
        if requested < minimum:
            raise ForecastError("invalid_parameters", f"指定历史区间包含 {requested} 个采样点，少于所需 {minimum} 点；不会向区间外补取数据。")
    elif params.history_hours is not None:
        requested = params.history_hours * 60 // frequency
        if requested < minimum:
            raise ForecastError("invalid_parameters", f"{case_id}至少需要 {minimum * frequency / 60:g} 小时历史数据；不会自动改变你指定的长度。")
    else:
        horizon_steps = len(forecast_grid(params.origin, params.horizon_hours, frequency))
        requested = max(minimum, min(15360, horizon_steps * registry.settings.history_multiplier))
    if requested > 15360:
        raise ForecastError("invalid_parameters", "历史窗口超出固定模型支持的最大长度，请缩短历史长度。")
    return requested, minimum


def plan_message(params, registry):
    windows = [history_steps(params, registry, key)[0] * registry.warnings.timing(key)[0] / 60
               for key in params.case_ids]
    history = (f"参考过去 {windows[0]:g} 小时的历史记录" if len(set(windows)) == 1
               else "按各案例配置确定历史窗口")
    mode = "历史回放" if (params.forecast_mode == "historical_replay" or
        params.forecast_mode is None and all(registry.warnings.get(registry.cases[k]).mode == "historical_replay" for k in params.case_ids)) else "当前预测"
    if params.history_start is not None:
        end = pd.Timestamp(params.origin) + pd.Timedelta(hours=params.horizon_hours)
        return (f"已匹配数据，将进行{mode}。历史输入区间：{local_time(params.history_start)} 至 "
                f"{local_time(params.history_cutoff or params.origin)}（北京时间）；预测区间：{local_time(params.origin)} 至 "
                f"{local_time(end)}（北京时间），共 {params.horizon_hours} 小时。"
                "正在检查指定历史区间，不会自动缩短窗口或使用区间外观测。")
    if params.history_cutoff is not None:
        end = pd.Timestamp(params.origin) + pd.Timedelta(hours=params.horizon_hours)
        return (f"已匹配数据，将进行{mode}，使用截至 {local_time(params.history_cutoff)}（北京时间）的历史输入，"
                f"预测 {local_time(params.origin)} 至 {local_time(end)}（北京时间）的完整时段，{history}。"
                "正在检查数据时效和完整性；满足要求后会自动预测，否则会说明原因。")
    end = pd.Timestamp(params.origin) + pd.Timedelta(hours=params.horizon_hours)
    return (f"已匹配数据，将进行{mode}，预测窗口为 {local_time(params.origin)} 至 {local_time(end)}（北京时间），共 {params.horizon_hours} 小时，{history}。"
            + ("仅使用回放起点及之前可用的数据，正在检查历史输入完整性。" if mode == "历史回放" else
               "正在检查数据时效和完整性；满足要求后会自动预测，否则会说明原因。"))
