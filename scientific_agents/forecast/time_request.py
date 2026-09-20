"""Deterministic forecast dates. Date words never silently fall back to tomorrow."""
import re

import pandas as pd

from .feedback import ForecastError

NUMBER = r"(?:\d+|[零〇一二两三四五六七八九十]+)"
DATE = re.compile(rf"(?:(?P<year>\d{{4}})年)?(?P<month>{NUMBER})月(?P<day>{NUMBER})[日号]"
                  r"|(?P<iso>\d{4}-\d{1,2}-\d{1,2})")
DURATION = re.compile(rf"({NUMBER})\s*(?:个)?\s*(小时|天|日|周)")
RANGE = re.compile(r"\s*(?:[-—–~～]+|至|到)\s*")


def integer(text):
    if text.isdecimal():
        return int(text)
    digits = {v: i for i, v in enumerate("零一二三四五六七八九")}
    text = text.replace("两", "二").replace("〇", "零")
    if "十" in text:
        left, right = text.split("十", 1)
        return (digits[left] if left else 1) * 10 + (digits[right] if right else 0)
    return int("".join(str(digits[v]) for v in text))


def read_date(message, match, year):
    start = (pd.Timestamp(match["iso"]) if match["iso"] else
             pd.Timestamp(year=int(match["year"] or year), month=integer(match["month"]), day=integer(match["day"])))
    rest = message[match.end():]
    clock = re.match(r"[T\s]*(\d{1,2})(?::(\d{2})(?::(\d{2}))?|[点时](?:(\d{1,2})分?)?)", rest)
    consumed = match.end()
    if clock:
        hour, minute, second = int(clock[1]), int(clock[2] or clock[4] or 0), int(clock[3] or 0)
        if not (0 <= hour <= 24 and 0 <= minute < 60 and 0 <= second < 60) or (hour == 24 and (minute or second)):
            raise ValueError("invalid clock")
        start += pd.Timedelta(hours=hour, minutes=minute, seconds=second)
        consumed += clock.end()
        rest = rest[clock.end():]
    zone = re.match(r"\s*(UTC|GMT|Z|[+-]\d{2}:\d{2}|北京时间)", rest)
    tz = zone[1] if zone else "Asia/Shanghai"
    tz = "UTC" if tz in {"UTC", "GMT", "Z"} else "Asia/Shanghai" if tz == "北京时间" else tz
    if zone:
        consumed += zone.end()
    return start.tz_localize(tz), bool(clock), consumed


def range_dates(message, left, right, year):
    start, _, left_end = read_date(message, left, year)
    if not RANGE.fullmatch(message[left_end:right.start()]):
        raise ValueError("unclear range separator")
    end, clock, right_end = read_date(message, right, start.year)
    if not right["iso"] and not right["year"] and end.month < start.month:
        end = end.replace(year=start.year + 1)
    if not clock:
        end += pd.Timedelta(days=1)  # A named end day is included in full.
    if end <= start:
        raise ValueError("reversed or empty range")
    return start, end, right_end


def parse_time_request(message, now=None, *, default_year=None):
    """Return only explicit time changes; unspecified years/timezones use Beijing time."""
    if message.lstrip().startswith("{"):
        return {}
    now = pd.Timestamp.now(tz="Asia/Shanghai") if now is None else pd.Timestamp(now).tz_convert("Asia/Shanghai")
    year = now.year if default_year is None else default_year
    # Relative calendar days have the same priority and duration rules as named dates.
    offsets = {"前天": -2, "昨天": -1, "今日": 0, "今天": 0, "明天": 1, "明日": 1, "后天": 2}
    message = re.sub("|".join(offsets), lambda m: (now.normalize() + pd.Timedelta(days=offsets[m[0]])).strftime("%Y年%m月%d日"), message)
    history_duration = re.search(rf"(?:(?:基于|使用|参考|根据|利用|用)\s*(?:过去|最近)?|历史(?:窗口|长度)?(?:为|是)?)\s*({NUMBER})\s*(?:个)?\s*(小时|天|日|周)", message)
    if history_duration:
        hours = integer(history_duration[1]) * {"小时": 1, "天": 24, "日": 24, "周": 168}[history_duration[2]]
        if hours < 1:
            raise ForecastError("invalid_time", "历史输入时长必须大于零。")
        result = parse_time_request(message[:history_duration.start()] + message[history_duration.end():], now, default_year=year)
        if result.get("history_hours") not in {None, hours} or result.get("history_start"):
            raise ForecastError("invalid_time", "请只指定一组历史输入区间或历史时长。")
        return {**result, "history_hours": hours, "history_mode": "explicit"}
    # Expand a shared month in a range before distinguishing history from forecast dates.
    message = re.sub(rf"({NUMBER})月({NUMBER})([日号])(\s*(?:[-—–~～]+|至|到)\s*)({NUMBER})([日号])",
                     r"\1月\2\3\4\1月\5\6", message)
    matches = list(DATE.finditer(message))
    if len(matches) > 1:
        try:
            for left, right in zip(matches, matches[1:]):
                markers = re.findall(r"基于|使用|参考|根据|利用|用|历史|预测|预报", message[:left.start()])
                if not markers or markers[-1] in {"预测", "预报"}:
                    continue
                start, end, consumed = range_dates(message, left, right, year)
                remaining = message[:left.start()] + message[consumed:]
                result = parse_time_request(remaining, now, default_year=end.year)
                if result.get("history_start"):
                    raise ValueError("multiple history windows")
                if result.get("origin") and end > pd.Timestamp(result["origin"]):
                    raise ValueError("historical input extends into forecast")
                hours = (end - start).total_seconds() / 3600
                result.update(history_start=start.isoformat(), history_cutoff=end.isoformat(),
                              history_hours=int(hours) if hours.is_integer() else None, history_mode=None)
                return result
            if len(matches) == 2:
                start, end, _ = range_dates(message, *matches, year)
                hours = (end - start).total_seconds() / 3600
                if not hours.is_integer():
                    raise ValueError("forecast duration must be whole hours")
                return dict(origin=start.isoformat(), origin_mode="explicit", horizon_hours=int(hours))
            raise ValueError("unclear multiple dates")
        except (ValueError, KeyError, OverflowError) as exc:
            if isinstance(exc, ForecastError):
                raise
            raise ForecastError("invalid_time", "无法确定时间区间，请分别说明历史输入的起止日期和预测日期；历史输入不能晚于预测起点。") from exc
    if not matches:
        if re.search(rf"{NUMBER}月|{NUMBER}号|\d{{4}}[-/]\d{{1,2}}[-/]", message):
            raise ForecastError("invalid_time", "未能确定完整预测日期，请明确月、日和预测时长；不会改用明天。")
        relative = re.search(rf"(?:未来|接下来|从现在(?:起|开始)?)\s*({NUMBER})\s*(?:个)?\s*(小时|天|日|周)", message)
        if relative:
            hours = integer(relative[1]) * {"小时": 1, "天": 24, "日": 24, "周": 168}[relative[2]]
            return {"origin": None, "origin_mode": "now" if relative[2] == "小时" or "从现在" in message else "tomorrow",
                    "horizon_hours": hours}
        return {}
    match = matches[0]
    try:
        start, clock, consumed = read_date(message, match, year)
        rest = message[consumed:]
        if not clock and re.match(r"\s*(?:之|以)?后", rest):
            start += pd.Timedelta(days=1)
        duration_text = message[:match.start()] + rest
        duration_text = re.sub(rf"(?:参考\s*(?:过去|最近)?|过去|最近|历史(?:窗口|长度)?(?:为|是)?)\s*{NUMBER}\s*(?:个)?\s*(?:小时|天|日|周)", "", duration_text)
        duration = DURATION.search(duration_text)
        hours = integer(duration[1]) * {"小时": 1, "天": 24, "日": 24, "周": 168}[duration[2]] if duration else None
        if hours is not None and hours < 1:
            raise ValueError("invalid duration")
        if re.search(r"(?:至|到)\s*\d+[日号]", rest):
            raise ValueError("ambiguous end date")
    except (ValueError, KeyError, OverflowError) as exc:
        raise ForecastError("invalid_time", "日期或时间范围无效，请明确有效的起点和持续时长；不会改用明天。") from exc
    result = {"origin": start.isoformat(), "origin_mode": "explicit"}
    # A date without a clock denotes its full calendar day; a clock alone keeps the chosen duration.
    if hours is not None or not clock:
        result["horizon_hours"] = hours if hours is not None else 24
    return result
