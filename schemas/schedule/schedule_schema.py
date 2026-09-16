from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class CreateScheduleRequest(BaseModel):
    schedule_name: str
    dag_task_id: str
    # 不传自动取该任务 is_current=1 的当前版本定义
    definition_id: Optional[str] = None
    trigger_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    # 前端始终传这三个字段，后端按 trigger_type 决定怎么用
    start_date: Optional[date] = None
    execute_time: Optional[str] = None  # "HH:MM"，CRON 模式下忽略
    end_date: Optional[date] = None
    timezone: str = "Asia/Shanghai"
    misfire_policy: str = "SKIP"
    max_running_instances: int = 1
    concurrency_policy: str = "SKIP_CURRENT"
    payload_json: Optional[dict] = None


class UpdateScheduleRequest(BaseModel):
    schedule_name: Optional[str] = None
    cron_expression: Optional[str] = None
    start_date: Optional[date] = None
    execute_time: Optional[str] = None
    end_date: Optional[date] = None
    timezone: Optional[str] = None
    misfire_policy: Optional[str] = None
    max_running_instances: Optional[int] = None
    concurrency_policy: Optional[str] = None
    payload_json: Optional[dict] = None


class TriggerConfigRequest(BaseModel):
    """前端触发模式配置，后端转换成底层 trigger_type + cron/interval。"""
    trigger_mode: Literal["ONCE", "INTERVAL", "DAILY", "WEEKLY", "MONTHLY", "CRON"]
    # ONCE 模式（传 ISO 字符串，后端解析；空串视为未传）
    execute_at: Optional[str] = None
    # INTERVAL 模式
    interval_value: Optional[int] = None
    interval_unit: Optional[str] = None  # MINUTES / HOURS / DAYS
    # DAILY / WEEKLY / MONTHLY 模式
    execute_time: Optional[str] = None  # "HH:MM"
    # WEEKLY 模式
    week_days: Optional[list[int]] = None  # ISO 8601: 1=周一 ... 7=周日
    # MONTHLY 模式
    month_day: Optional[int] = None  # 1-31
    # CRON 模式
    cron_expression: Optional[str] = None
    timezone: str = "Asia/Shanghai"


class TriggerConfigResponse(BaseModel):
    """预览结果，前端拿着调创建接口。"""
    trigger_type: str  # ONCE / CRON / INTERVAL
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None  # ONCE 模式返回 execute_at
    description: Optional[str] = None
