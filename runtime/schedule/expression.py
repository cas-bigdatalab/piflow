from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from runtime.schedule.constants import TriggerType

_CRON_SEARCH_WINDOW_DAYS = 366


def _get_zone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except Exception as exc:
        raise ValueError(f"invalid timezone: {timezone_name}") from exc


def _ensure_aware(dt: datetime, zone: ZoneInfo) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=zone)
    return dt.astimezone(zone)


def _normalize_boundary(dt: datetime | None, zone: ZoneInfo) -> datetime | None:
    if dt is None:
        return None
    return _ensure_aware(dt, zone)


def _parse_cron_field(
    field: str,
    *,
    minimum: int,
    maximum: int,
    allow_question: bool = False,
) -> set[int] | None:
    field = field.strip()
    if not field:
        raise ValueError("cron field must not be empty")
    if field == "*" or (allow_question and field == "?"):
        return None

    values: set[int] = set()
    parts = field.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            raise ValueError("cron field contains empty segment")

        step = 1
        if "/" in part:
            base, step_text = part.split("/", 1)
            if not step_text.isdigit():
                raise ValueError(f"invalid cron step: {part}")
            step = int(step_text)
            if step <= 0:
                raise ValueError(f"invalid cron step: {part}")
        else:
            base = part

        if base in ("*", "?") and not allow_question:
            if base == "?":
                raise ValueError("question mark is not allowed in this cron field")
            start = minimum
            end = maximum
        elif base in ("*", "?"):
            start = minimum
            end = maximum
        elif "-" in base:
            start_text, end_text = base.split("-", 1)
            if not (start_text.isdigit() and end_text.isdigit()):
                raise ValueError(f"invalid cron range: {part}")
            start = int(start_text)
            end = int(end_text)
        else:
            if not base.isdigit():
                raise ValueError(f"invalid cron value: {part}")
            start = end = int(base)

        if start > end:
            raise ValueError(f"invalid cron range: {part}")
        if start < minimum or end > maximum:
            raise ValueError(f"cron value out of range: {part}")

        for value in range(start, end + 1, step):
            values.add(value)

    return values


def _parse_cron_expression(
    cron_expression: str,
) -> dict[str, set[int] | None]:
    parts = [part for part in cron_expression.split() if part]
    if len(parts) not in (5, 6, 7):
        raise ValueError("cron_expression must contain 5, 6, or 7 fields")

    if len(parts) == 5:
        second_part = "0"
        minute_part, hour_part, dom_part, month_part, dow_part = parts
        year_part = "*"
    elif len(parts) == 6:
        second_part, minute_part, hour_part, dom_part, month_part, dow_part = parts
        year_part = "*"
    else:
        second_part, minute_part, hour_part, dom_part, month_part, dow_part, year_part = parts

    return {
        "second": _parse_cron_field(second_part, minimum=0, maximum=59),
        "minute": _parse_cron_field(minute_part, minimum=0, maximum=59),
        "hour": _parse_cron_field(hour_part, minimum=0, maximum=23),
        "dom": _parse_cron_field(dom_part, minimum=1, maximum=31, allow_question=True),
        "month": _parse_cron_field(month_part, minimum=1, maximum=12),
        "dow": _parse_cron_field(dow_part, minimum=0, maximum=7, allow_question=True),
        "year": _parse_cron_field(year_part, minimum=1970, maximum=2099),
    }


def _cron_weekday(dt: datetime) -> int:
    return (dt.weekday() + 1) % 7


def _matches_cron(dt: datetime, spec: dict[str, set[int] | None]) -> bool:
    if spec["year"] is not None and dt.year not in spec["year"]:
        return False
    if spec["month"] is not None and dt.month not in spec["month"]:
        return False
    if spec["hour"] is not None and dt.hour not in spec["hour"]:
        return False
    if spec["minute"] is not None and dt.minute not in spec["minute"]:
        return False
    if spec["second"] is not None and dt.second not in spec["second"]:
        return False

    dom = spec["dom"]
    dow = spec["dow"]
    dom_wildcard = dom is None
    dow_wildcard = dow is None

    if dom_wildcard and dow_wildcard:
        return True
    if dom_wildcard:
        return _cron_weekday(dt) in (dow or set())
    if dow_wildcard:
        return dt.day in (dom or set())
    return dt.day in (dom or set()) or _cron_weekday(dt) in (dow or set())


def validate_trigger(
    *,
    trigger_type: str,
    cron_expression: str | None,
    interval_seconds: int | None = None,
    start_time: datetime | None,
    end_time: datetime | None,
    timezone_name: str,
) -> None:
    zone = _get_zone(timezone_name)

    if start_time is not None:
        _ensure_aware(start_time, zone)
    if end_time is not None:
        _ensure_aware(end_time, zone)

    if start_time is not None and end_time is not None:
        if _ensure_aware(end_time, zone) <= _ensure_aware(start_time, zone):
            raise ValueError("end_time must be greater than start_time")

    if trigger_type == TriggerType.ONCE:
        if cron_expression is not None:
            raise ValueError("cron_expression must be empty for ONCE trigger")
        if start_time is None:
            raise ValueError("start_time is required for ONCE trigger")
        return

    if trigger_type == TriggerType.CRON:
        if not cron_expression:
            raise ValueError("cron_expression is required for CRON trigger")
        _parse_cron_expression(cron_expression)
        return

    if trigger_type == TriggerType.INTERVAL:
        if interval_seconds is None or interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0 for INTERVAL trigger")
        if cron_expression is not None:
            raise ValueError("cron_expression must be empty for INTERVAL trigger")
        return

    raise ValueError(f"unsupported trigger_type: {trigger_type}")


def compute_first_fire_time(
    *,
    trigger_type: str,
    cron_expression: str | None,
    interval_seconds: int | None = None,
    start_time: datetime | None,
    end_time: datetime | None,
    timezone_name: str,
) -> datetime | None:
    zone = _get_zone(timezone_name)
    validate_trigger(
        trigger_type=trigger_type,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
        start_time=start_time,
        end_time=end_time,
        timezone_name=timezone_name,
    )

    normalized_start = _normalize_boundary(start_time, zone)
    normalized_end = _normalize_boundary(end_time, zone)

    if trigger_type == TriggerType.ONCE:
        if normalized_end is not None and normalized_start is not None and normalized_start > normalized_end:
            return None
        return normalized_start

    if trigger_type == TriggerType.CRON:
        now = datetime.now(zone)
        anchor = normalized_start if normalized_start and normalized_start > now else now
        return compute_next_fire_time(
            trigger_type=trigger_type,
            cron_expression=cron_expression,
            start_time=normalized_start,
            end_time=normalized_end,
            timezone_name=timezone_name,
            after=anchor - timedelta(seconds=1),
        )

    if trigger_type == TriggerType.INTERVAL:
        now = datetime.now(zone)
        if normalized_start is not None and normalized_start > now:
            if normalized_end is not None and normalized_start > normalized_end:
                return None
            return normalized_start
        if normalized_start is not None:
            elapsed = (now - normalized_start).total_seconds()
            n = int(elapsed // interval_seconds) + 1
            candidate = normalized_start + timedelta(seconds=n * interval_seconds)
        else:
            candidate = now
        if normalized_end is not None and candidate > normalized_end:
            return None
        return candidate

    raise ValueError(f"unsupported trigger_type: {trigger_type}")


def compute_next_fire_time(
    *,
    trigger_type: str,
    cron_expression: str | None,
    interval_seconds: int | None = None,
    start_time: datetime | None,
    end_time: datetime | None,
    timezone_name: str,
    after: datetime,
) -> datetime | None:
    zone = _get_zone(timezone_name)
    validate_trigger(
        trigger_type=trigger_type,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
        start_time=start_time,
        end_time=end_time,
        timezone_name=timezone_name,
    )

    normalized_after = _ensure_aware(after, zone)
    normalized_start = _normalize_boundary(start_time, zone)
    normalized_end = _normalize_boundary(end_time, zone)

    if normalized_end is not None and normalized_after >= normalized_end:
        return None

    if trigger_type == TriggerType.ONCE:
        candidate = normalized_start
        if candidate is None:
            return None
        if candidate <= normalized_after:
            return None
        if normalized_end is not None and candidate > normalized_end:
            return None
        return candidate

    if trigger_type == TriggerType.CRON:
        cron_spec = _parse_cron_expression(cron_expression or "")
        candidate = normalized_after + timedelta(seconds=1)
        if normalized_start is not None and candidate < normalized_start:
            candidate = normalized_start

        deadline = normalized_end
        if deadline is None:
            deadline = candidate + timedelta(days=_CRON_SEARCH_WINDOW_DAYS)

        while candidate <= deadline:
            if _matches_cron(candidate, cron_spec):
                return candidate
            candidate += timedelta(seconds=1)

        return None

    if trigger_type == TriggerType.INTERVAL:
        candidate = normalized_after + timedelta(seconds=interval_seconds)
        if normalized_start is not None and candidate < normalized_start:
            candidate = normalized_start
        if normalized_end is not None and candidate > normalized_end:
            return None
        return candidate

    raise ValueError(f"unsupported trigger_type: {trigger_type}")


@dataclass(slots=True)
class ScheduleExpression:
    trigger_type: str
    timezone: str = "Asia/Shanghai"
    cron_expression: str | None = None
    interval_seconds: int | None = None

    def validate(self) -> None:
        zone = _get_zone(self.timezone)

        if self.trigger_type == TriggerType.ONCE:
            if self.cron_expression is not None:
                raise ValueError("cron_expression must be empty for ONCE trigger")
            if self.interval_seconds is not None:
                raise ValueError("interval_seconds must be empty for ONCE trigger")
            return

        if self.trigger_type == TriggerType.CRON:
            if not self.cron_expression:
                raise ValueError("cron_expression is required for CRON trigger")
            _parse_cron_expression(self.cron_expression)
            if self.interval_seconds is not None:
                raise ValueError("interval_seconds must be empty for CRON trigger")
            _ = zone
            return

        if self.trigger_type == TriggerType.INTERVAL:
            if self.interval_seconds is None or self.interval_seconds <= 0:
                raise ValueError("interval_seconds must be > 0 for INTERVAL trigger")
            if self.cron_expression is not None:
                raise ValueError("cron_expression must be empty for INTERVAL trigger")
            _ = zone
            return

        raise ValueError(f"unsupported trigger_type: {self.trigger_type}")

    def first_fire_time(
        self,
        *,
        start_time: datetime | None,
        now: datetime,
    ) -> datetime | None:
        return compute_first_fire_time(
            trigger_type=self.trigger_type,
            cron_expression=self.cron_expression,
            start_time=start_time or now,
            end_time=None,
            timezone_name=self.timezone,
        )
