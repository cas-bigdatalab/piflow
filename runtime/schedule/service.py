from __future__ import annotations

from datetime import datetime
from typing import Any

from database.postgres import get_connection
from psycopg2.extras import RealDictCursor
from runtime.dag_manager import get_dag_task
from runtime.schedule.constants import (
    ConcurrencyPolicy,
    MisfirePolicy,
    ScheduleStatus,
    TriggerType,
)
from runtime.schedule.repository import (
    create_job,
    delete_job,
    get_job,
    get_run,
    list_jobs,
    list_runs,
    pause_job,
    start_job,
    stop_job,
    update_job,
)
from schemas.schedule.schedule_schema import (
    TriggerConfigRequest,
    TriggerConfigResponse,
)


def _require_user(user_id: str) -> str:
    if not user_id or not user_id.strip():
        raise ValueError("user_id is required")
    return user_id


def _require_text(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


# cron 数字星期 → 中文
_CRON_DOW_CN = {
    "0": "日", "1": "一", "2": "二", "3": "三",
    "4": "四", "5": "五", "6": "六", "7": "日",
}


def describe_trigger_rule(job) -> str:
    """根据任务的 trigger_type + cron/interval 生成中文触发规则描述。

    用于前端展示，例如：
      - ONCE:    "2026年09月10日 10:00 执行一次"
      - INTERVAL:"每30分钟执行一次" / "每2小时执行一次"
      - CRON:    "每日10时00分执行一次" / "每周一、周三 10:00 执行一次"
                 无法识别的 cron 回退为 "按 cron 表达式 '...' 执行"
    """
    if not job:
        return "未知触发规则"

    if job.trigger_type == TriggerType.ONCE:
        if job.start_time:
            return f"{job.start_time.strftime('%Y年%m月%d日 %H:%M')} 执行一次"
        return "执行一次"

    if job.trigger_type == TriggerType.INTERVAL:
        seconds = job.interval_seconds or 0
        if seconds <= 0:
            return "按间隔执行"
        if seconds >= 86400 and seconds % 86400 == 0:
            return f"每{seconds // 86400}天执行一次"
        if seconds >= 3600 and seconds % 3600 == 0:
            return f"每{seconds // 3600}小时执行一次"
        if seconds >= 60 and seconds % 60 == 0:
            return f"每{seconds // 60}分钟执行一次"
        return f"每{seconds}秒执行一次"

    if job.trigger_type == TriggerType.CRON:
        cron = job.cron_expression
        if not cron:
            return "自定义 cron 表达式"
        # 6 字段: 秒 分 时 日 月 周
        parts = cron.split()
        try:
            if len(parts) == 6:
                _sec, minute, hour, dom, month, dow = parts
                # DAILY: 0 MM HH * * ?
                if dom == "*" and month == "*" and dow == "?":
                    return f"每日{hour}时{minute}分执行一次"
                # WEEKLY: 0 MM HH ? * D1,D2,...
                if dom == "?" and month == "*" and dow not in ("*", "?"):
                    days = [_CRON_DOW_CN.get(d, d) for d in dow.split(",")]
                    return f"每周{'、'.join(days)} {hour}:{minute} 执行一次"
                # MONTHLY: 0 MM HH DD * ?
                if month == "*" and dow == "?" and dom not in ("*", "?"):
                    return f"每月第{dom}日 {hour}时{minute}分执行一次"
        except Exception:
            pass
        return f"按 cron 表达式 '{cron}' 执行"

    return "未知触发规则"


def _resolve_definition_binding(
    *,
    dag_task_id: str,
    definition_id: str | None,
    owner_id: str,
) -> str:
    """校验任务归属并解析最终 definition_id。

    definition_id 为空时，自动取该任务 is_current=1 的当前版本；
    传了则校验其归属（属于该任务且属于该用户）。
    执行时始终取最新 current 版本，此返回值仅作为创建时的版本快照。
    """
    task = get_dag_task(dag_task_id)
    if task is None or task.create_user_id != owner_id:
        raise ValueError(f"dag task not found or not owned by user: {dag_task_id}")

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if definition_id:
                cursor.execute(
                    """
                    SELECT 1
                    FROM dag_definition
                    WHERE definition_id = %s
                      AND dag_task_id = %s
                      AND create_user_id = %s
                    """,
                    (definition_id, dag_task_id, owner_id),
                )
                if cursor.fetchone() is None:
                    raise ValueError(
                        "definition not found, not owned by user, "
                        "or does not belong to dag task"
                    )
                return definition_id

            cursor.execute(
                """
                SELECT definition_id
                FROM dag_definition
                WHERE dag_task_id = %s
                  AND create_user_id = %s
                  AND is_current = 1
                """,
                (dag_task_id, owner_id),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(
                    f"dag task has no current definition: {dag_task_id}"
                )
            return row["definition_id"]


def _normalize_trigger_fields(
    *,
    trigger_type: str,
    cron_expression: str | None,
    interval_seconds: int | None,
) -> tuple[str | None, int | None]:
    """按 trigger_type 归一化触发字段，消化前端表单始终传空值的情况。

    - 空白 cron 字符串 → None；interval_seconds <= 0 → None
    - ONCE：cron / interval 强制为 None
    - CRON：interval 强制为 None，cron 保留（为空由 validate_trigger 报错）
    - INTERVAL：cron 强制为 None，interval 保留（<=0 由 validate_trigger 报错）
    """
    cron = (
        cron_expression.strip()
        if isinstance(cron_expression, str) and cron_expression.strip()
        else None
    )
    interval = interval_seconds if isinstance(interval_seconds, int) and interval_seconds > 0 else None

    if trigger_type == TriggerType.ONCE:
        return None, None
    if trigger_type == TriggerType.CRON:
        return cron, None
    if trigger_type == TriggerType.INTERVAL:
        return None, interval
    return cron, interval


def create_schedule_job(
    *,
    owner_id: str,
    schedule_name: str,
    dag_task_id: str,
    definition_id: str | None = None,
    trigger_type: str,
    timezone: str = "Asia/Shanghai",
    cron_expression: str | None = None,
    interval_seconds: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    misfire_policy: str = MisfirePolicy.FIRE_ONCE,
    max_running_instances: int = 1,
    concurrency_policy: str = ConcurrencyPolicy.SKIP_CURRENT,
    payload_json: dict[str, Any] | None = None,
):
    owner_id = _require_user(owner_id)
    schedule_name = _require_text(schedule_name, "schedule_name")
    dag_task_id = _require_text(dag_task_id, "dag_task_id")

    if trigger_type not in TriggerType.ALL:
        raise ValueError(f"unsupported trigger_type: {trigger_type}")
    if misfire_policy not in MisfirePolicy.ALL:
        raise ValueError(f"unsupported misfire policy: {misfire_policy}")
    if concurrency_policy not in ConcurrencyPolicy.ALL:
        raise ValueError(f"unsupported concurrency policy: {concurrency_policy}")
    if max_running_instances <= 0:
        raise ValueError("max_running_instances must be > 0")

    # 归一化：按 trigger_type 清掉无关字段（前端表单会始终传空串/0）
    cron_expression, interval_seconds = _normalize_trigger_fields(
        trigger_type=trigger_type,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
    )

    # 触发参数完整校验：cron 合法性、interval>0、ONCE 有 start_time、end>start、时区
    from runtime.schedule.expression import validate_trigger
    validate_trigger(
        trigger_type=trigger_type,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
        start_time=start_time,
        end_time=end_time,
        timezone_name=timezone,
    )

    definition_id = _resolve_definition_binding(
        dag_task_id=dag_task_id,
        definition_id=definition_id,
        owner_id=owner_id,
    )

    # Jobs are created inactive. start_job() is the only lifecycle operation
    # that initializes next_fire_time.
    return create_job(
        schedule_name=schedule_name,
        dag_task_id=dag_task_id,
        definition_id=definition_id,
        owner_id=owner_id,
        trigger_type=trigger_type,
        status=ScheduleStatus.DRAFT,
        timezone=timezone,
        cron_expression=cron_expression,
        interval_seconds=interval_seconds,
        start_time=start_time,
        end_time=end_time,
        misfire_policy=misfire_policy,
        max_running_instances=max_running_instances,
        concurrency_policy=concurrency_policy,
        payload_json=payload_json,
    )


def update_schedule_job(
    schedule_job_id: str,
    *,
    owner_id: str,
    schedule_name: str | None = None,
    cron_expression: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    timezone: str | None = None,
    misfire_policy: str | None = None,
    max_running_instances: int | None = None,
    concurrency_policy: str | None = None,
    payload_json: dict[str, Any] | None = None,
):
    owner_id = _require_user(owner_id)
    _require_text(schedule_job_id, "schedule_job_id")
    if schedule_name is not None:
        _require_text(schedule_name, "schedule_name")
    # 空白 cron → None（None 表示"不改"，避免把 cron 更新成空串违反 DB 约束）
    if cron_expression is not None:
        cron_expression = cron_expression.strip() or None
    # 改了 cron 就校验合法性
    if cron_expression is not None:
        from runtime.schedule.expression import _parse_cron_expression
        _parse_cron_expression(cron_expression)
    return update_job(
        schedule_job_id,
        owner_id=owner_id,
        schedule_name=schedule_name,
        cron_expression=cron_expression,
        start_time=start_time,
        end_time=end_time,
        timezone=timezone,
        misfire_policy=misfire_policy,
        max_running_instances=max_running_instances,
        concurrency_policy=concurrency_policy,
        payload_json=payload_json,
    )


def start_schedule_job(*, schedule_job_id: str, owner_id: str):
    return start_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def pause_schedule_job(*, schedule_job_id: str, owner_id: str):
    return pause_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def stop_schedule_job(*, schedule_job_id: str, owner_id: str):
    return stop_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def delete_schedule_job(*, schedule_job_id: str, owner_id: str):
    return delete_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def get_schedule_job(*, schedule_job_id: str, owner_id: str):
    return get_job(
        _require_text(schedule_job_id, "schedule_job_id"),
        owner_id=_require_user(owner_id),
    )


def list_schedule_jobs(
    *,
    owner_id: str,
    status: str | None = None,
    dag_task_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    owner_id = _require_user(owner_id)
    return list_jobs(
        owner_id=owner_id,
        status=status,
        dag_task_id=dag_task_id,
        page=page,
        page_size=page_size,
    )


def list_schedule_runs(
    *,
    schedule_job_id: str,
    owner_id: str,
    page: int = 1,
    page_size: int = 20,
):
    owner_id = _require_user(owner_id)
    return list_runs(
        schedule_job_id=_require_text(schedule_job_id, "schedule_job_id"),
        owner_id=owner_id,
        page=page,
        page_size=page_size,
    )


def get_schedule_run(
    *,
    schedule_run_id: str,
    owner_id: str,
):
    owner_id = _require_user(owner_id)
    run = get_run(
        _require_text(schedule_run_id, "schedule_run_id"),
        owner_id=owner_id,
    )
    if run is None:
        return None

    result = {
        "schedule_run_id": run.schedule_run_id,
        "schedule_job_id": run.schedule_job_id,
        "dag_task_id": run.dag_task_id,
        "definition_id": run.definition_id,
        "planned_fire_time": run.planned_fire_time,
        "actual_fire_time": run.actual_fire_time,
        "process_id": run.process_id,
        "status": run.status,
        "attempt": run.attempt,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }

    # 通过 piflow_flow_run 二次查询拼装真实执行状态（设计 §12 方式一）
    if run.process_id:
        from runtime.piflow_run_query import get_piflow_run_progress
        piflow = get_piflow_run_progress(run.process_id)
        if piflow is not None:
            result["piflow_status"] = piflow.get("status")
            result["piflow_progress"] = piflow.get("progress")
            result["piflow_error_message"] = piflow.get("error_message")
            result["piflow_started_at"] = piflow.get("started_at")
            result["piflow_finished_at"] = piflow.get("finished_at")

    return result


# ===== 触发模式预览（前端 UI 配置 → 底层 trigger_type + cron/interval） =====

_INTERVAL_UNIT_FACTORS = {
    "MINUTES": 60,
    "HOURS": 3600,
    "DAYS": 86400,
}

_INTERVAL_UNIT_CN = {
    "MINUTES": "分钟",
    "HOURS": "小时",
    "DAYS": "天",
}

# ISO 8601 星期 → cron 数字（cron: 0=Sunday, 1=Monday...6=Saturday; 0 和 7 都是 Sunday）
_WEEK_DOW_MAP = {
    1: "1",   # MON
    2: "2",   # TUE
    3: "3",   # WED
    4: "4",   # THU
    5: "5",   # FRI
    6: "6",   # SAT
    7: "0",   # SUN
}

_WEEK_DOW_CN = {
    1: "周一",
    2: "周二",
    3: "周三",
    4: "周四",
    5: "周五",
    6: "周六",
    7: "周日",
}


def _parse_execute_time(execute_time: str | None) -> tuple[int, int]:
    """解析 "HH:MM" → (hour, minute)。"""
    if not execute_time:
        raise ValueError("execute_time is required (format: HH:MM)")
    parts = execute_time.split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid execute_time format: {execute_time} (expected HH:MM)")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23):
        raise ValueError(f"hour out of range: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"minute out of range: {minute}")
    return hour, minute


def _merge_schedule_times(
    *,
    trigger_type: str | None,
    start_date,
    execute_time: str | None,
    end_date,
    timezone_name: str = "Asia/Shanghai",
):
    """前端 start_date + execute_time → 底层 start_time (datetime, 带时区)。

    CRON 模式忽略 execute_time（cron 表达式已含时间），start_time 只取日期。
    ONCE / INTERVAL 模式合并日期 + 时间作为 start_time。
    trigger_type=None（update 场景）：传了 execute_time 就合并，否则用 00:00。
    end_date 统一补 23:59:59 作为 end_time。
    生成的时间按 timezone_name 本地化（naive 会被当作该时区本地时间），
    避免插入 TIMESTAMPTZ 时被 PostgreSQL 按 UTC 解释造成时差。
    字段为 None 时返回 None，表示不改（update 场景）。
    """
    from datetime import time as dtime
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(timezone_name)

    start_time = None
    if start_date is not None:
        use_time = execute_time
        if trigger_type is not None and trigger_type not in ("ONCE", "INTERVAL"):
            use_time = None
        if use_time:
            hour, minute = _parse_execute_time(use_time)
            t = dtime(hour, minute, 0)
        else:
            t = dtime(0, 0, 0)
        start_time = datetime.combine(start_date, t).replace(tzinfo=zone)

    end_time = None
    if end_date is not None:
        end_time = datetime.combine(end_date, dtime(23, 59, 59)).replace(tzinfo=zone)

    return start_time, end_time


def preview_trigger_config(req: TriggerConfigRequest) -> TriggerConfigResponse:
    """把前端 trigger_mode 配置转成底层 trigger_type + cron/interval。

    前端拿返回值填到 CreateScheduleRequest 的对应字段调创建接口。
    """
    mode = req.trigger_mode

    if mode == "ONCE":
        if not req.execute_at:
            raise ValueError("execute_at is required for ONCE mode")
        # 兼容两种输入：日期字符串（YYYY-MM-DD，默认 00:00）或完整 datetime 字符串
        try:
            from datetime import datetime as _dt
            parsed = _dt.fromisoformat(req.execute_at)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo(req.timezone))
        except ValueError as e:
            raise ValueError(f"invalid execute_at: {req.execute_at} (expected ISO datetime): {e}")
        return TriggerConfigResponse(
            trigger_type=TriggerType.ONCE,
            start_time=parsed,
            description=f"执行一次：{parsed.strftime('%Y-%m-%d %H:%M')}",
        )

    if mode == "INTERVAL":
        if not req.interval_value or req.interval_value <= 0:
            raise ValueError("interval_value must be > 0")
        unit = req.interval_unit or "MINUTES"
        if unit not in _INTERVAL_UNIT_FACTORS:
            raise ValueError(f"unsupported interval_unit: {unit} (MINUTES/HOURS/DAYS)")
        seconds = req.interval_value * _INTERVAL_UNIT_FACTORS[unit]
        unit_cn = _INTERVAL_UNIT_CN[unit]
        return TriggerConfigResponse(
            trigger_type=TriggerType.INTERVAL,
            interval_seconds=seconds,
            description=f"每 {req.interval_value} {unit_cn}执行",
        )

    if mode == "CRON":
        if not req.cron_expression:
            raise ValueError("cron_expression is required for CRON mode")
        from runtime.schedule.expression import _parse_cron_expression
        _parse_cron_expression(req.cron_expression)
        return TriggerConfigResponse(
            trigger_type=TriggerType.CRON,
            cron_expression=req.cron_expression,
            description=f"自定义：{req.cron_expression}",
        )

    # DAILY / WEEKLY / MONTHLY → 生成 cron（6 字段：秒 分 时 日 月 周）
    hour, minute = _parse_execute_time(req.execute_time)

    if mode == "DAILY":
        cron = f"0 {minute} {hour} * * ?"
        return TriggerConfigResponse(
            trigger_type=TriggerType.CRON,
            cron_expression=cron,
            description=f"每天 {req.execute_time} 执行",
        )

    if mode == "WEEKLY":
        if not req.week_days:
            raise ValueError("week_days is required for WEEKLY mode")
        for d in req.week_days:
            if d not in _WEEK_DOW_MAP:
                raise ValueError(f"invalid week_day: {d} (must be 1-7, ISO 8601)")
        dows = ",".join(_WEEK_DOW_MAP[d] for d in sorted(req.week_days))
        dows_cn = "、".join(_WEEK_DOW_CN[d] for d in sorted(req.week_days))
        cron = f"0 {minute} {hour} ? * {dows}"
        return TriggerConfigResponse(
            trigger_type=TriggerType.CRON,
            cron_expression=cron,
            description=f"每{dows_cn} {req.execute_time} 执行",
        )

    if mode == "MONTHLY":
        if req.month_day is None or not (1 <= req.month_day <= 31):
            raise ValueError("month_day must be 1-31")
        cron = f"0 {minute} {hour} {req.month_day} * ?"
        return TriggerConfigResponse(
            trigger_type=TriggerType.CRON,
            cron_expression=cron,
            description=f"每月 {req.month_day} 日 {req.execute_time} 执行",
        )

    raise ValueError(f"unsupported trigger_mode: {mode}")
