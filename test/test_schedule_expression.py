from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from runtime.schedule.constants import TriggerType
from runtime.schedule.expression import (
    compute_first_fire_time,
    compute_next_fire_time,
    validate_trigger,
)


def test_cron_first_fire_time():
    start_time = datetime(2026, 9, 2, 9, 59, 50, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = compute_first_fire_time(
        trigger_type=TriggerType.CRON,
        cron_expression="0 0 10 * * ?",
        start_time=start_time,
        end_time=None,
        timezone_name="Asia/Shanghai",
    )
    assert result == datetime(2026, 9, 2, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_cron_next_fire_time():
    after = datetime(2026, 9, 2, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = compute_next_fire_time(
        trigger_type=TriggerType.CRON,
        cron_expression="0 0 10 * * ?",
        start_time=None,
        end_time=None,
        timezone_name="Asia/Shanghai",
        after=after,
    )
    assert result == datetime(2026, 9, 3, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_end_time_returns_none():
    after = datetime(2026, 9, 2, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    end_time = datetime(2026, 9, 2, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = compute_next_fire_time(
        trigger_type=TriggerType.CRON,
        cron_expression="0 0 10 * * ?",
        start_time=None,
        end_time=end_time,
        timezone_name="Asia/Shanghai",
        after=after,
    )
    assert result is None


def test_invalid_cron_raises():
    with pytest.raises(ValueError):
        validate_trigger(
            trigger_type=TriggerType.CRON,
            cron_expression="bad cron",
            start_time=None,
            end_time=None,
            timezone_name="Asia/Shanghai",
        )


def test_once_first_fire_time():
    start_time = datetime(2026, 9, 2, 11, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = compute_first_fire_time(
        trigger_type=TriggerType.ONCE,
        cron_expression=None,
        start_time=start_time,
        end_time=None,
        timezone_name="Asia/Shanghai",
    )
    assert result == start_time
