"""Public errors and presentation state, shared by HTTP, SSE and restored tasks."""
import logging
from zoneinfo import ZoneInfo

import pandas as pd

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

log = logging.getLogger(__name__)
DISPLAY_ZONE = ZoneInfo("Asia/Shanghai")


def local_time(value):
    """User-facing Beijing time; stored/API timestamps retain their timezone."""
    return pd.Timestamp(value).tz_convert(DISPLAY_ZONE).strftime("%Y-%m-%d %H:%M")


ACTIVE = {"queued", "running", "cancelling"}
STAGES = {"data": "数据接入与检查", "predict": "模型预测", "evaluate": "统计与回测", "assess": "预警条件评估", "report": "图表报告"}
ERRORS = {
    "unsupported": ("我目前支持已注册数据的时序预测、结果解释和比较。请描述你希望预测的数据和时间范围。", ["edit_parameters"]),
    "intent_parse_failed": ("这次没能理解你的需求，之前确认的信息仍然保留。请重新描述本轮需求。", ["resend_message"]),
    "invalid_parameters": ("这些参数暂时不能用于预测，请调整后再试。", ["edit_parameters"]),
    "version_conflict": ("会话已更新，请刷新参数后再确认。", ["refresh"]),
    "request_conflict": ("同一请求编号不能对应不同消息，请使用新的请求编号。", ["resend_message"]),
    "data_unavailable": ("暂时无法读取所需数据，请稍后重试；若持续失败，请检查数据源配置。", ["retry_task", "contact_support"]),
    "data_quality": ("所选历史窗口的数据不满足预测要求，请更换预测起点。", ["edit_parameters"]),
    "model_failed": ("预测模型本次未能完成计算，可以重试此任务。", ["retry_task", "contact_support"]),
    "evaluation_failed": ("预测输出未通过统计校验，请检查模型或数据配置后新建预测。", ["contact_support", "edit_parameters"]),
    "assessment_failed": ("预警条件评估未能完成，请检查注册规则和数据单位。", ["contact_support", "edit_parameters"]),
    "report_failed": ("报告生成失败，已完成的计算会保留，可以重试生成报告。", ["retry_task"]),
    "task_timeout": ("任务超过允许时间，已经请求停止。", ["refresh"]),
    "task_stalled": ("任务尚未退出，已暂停接收新的预测。请联系管理员检查或重启服务。", ["refresh", "contact_support"]),
    "task_stopping": ("任务正在停止，退出前不能重新执行。", ["refresh"]),
    "session_deleting": ("会话正在停止任务并清理，请稍后刷新状态。", ["refresh"]),
    "task_cancelled": ("任务已取消。你可以调整参数后发起新的预测。", ["edit_parameters"]),
    "task_interrupted": ("服务重启导致任务中断，可以从已保存阶段重试。", ["retry_task"]),
    "task_not_found": ("当前会话中没有找到对应任务，请重新选择。", ["select_task"]),
    "result_not_ready": ("这个任务尚未完成，请查看任务状态。", ["refresh", "select_task"]),
    "result_unavailable": ("结果文件暂时不可读取，请联系管理员检查文件存储。", ["contact_support"]),
    "retry_not_allowed": ("这个任务当前不适合重试，请查看状态或发起新的预测。", ["refresh"]),
    "internal_error": ("本次操作暂时无法完成，请稍后再试；若持续失败，请联系管理员。", ["refresh", "contact_support"]),
}
LABELS = {"resend_message": "重新描述", "edit_parameters": "调整预测条件", "retry_task": "重试任务",
          "refresh": "刷新状态", "contact_support": "联系管理员", "select_task": "选择历史任务",
          "cancel_task": "取消任务", "view_result": "查看结果", "login": "重新登录", "new_session": "新建会话"}


def completion_message(result):
    """Small completion receipt; detailed answers and report contents remain separate."""
    replay = any(s.assessment and s.assessment.mode == "historical_replay" for s in result.series)
    mode = "预测（含历史回放）" if replay else "预测"
    content = f"已完成 {len(result.series)} 个指标的{mode}，时长 {result.task.horizon_hours} 小时。请查看结果区的图表和风险提示。"
    if result.report_status == "pending":
        return content + "详细报告生成中，完成后可下载。"
    if result.report_status == "failed":
        return content + "详细报告生成失败，可单独重试。"
    return content + "详细分析见报告，也可以继续提问。"


class ForecastError(ValueError):
    def __init__(self, code, message=None, *, stage=None, http_status=422):
        self.code, self.stage, self.http_status = code, stage, http_status
        super().__init__(message or ERRORS[code][0])

    def problem(self):
        recovery = list(ERRORS[self.code][1])
        return {"code": self.code, "message": str(self), "stage": self.stage,
                "retryable": "retry_task" in recovery or "resend_message" in recovery, "recovery": recovery}


def classify(exc, stage=None):
    if isinstance(exc, ForecastError):
        return exc
    code = "invalid_parameters" if isinstance(exc, ValidationError) else {
        "data": "data_unavailable", "predict": "model_failed", "evaluate": "evaluation_failed", "assess": "assessment_failed",
        "report": "report_failed"}.get(stage, "internal_error")
    log.warning("Forecast failure type=%s stage=%s", type(exc).__name__, stage)
    return ForecastError(code, stage=stage)


def task_view(task):
    """Additive contract; never changes the stored task or claims that a live job stopped."""
    if task is None:
        return None
    data = dict(task)
    status = data["status"]
    data["terminal"] = status not in ACTIVE
    data["retryable"] = (status in {"failed", "interrupted"}
                         and (data.get("problem") or {}).get("retryable", True))
    actions = (["refresh", "contact_support"] if data.get("stalled") else
               ["refresh", "contact_support"] if status == "completed" and data.get("result_available") is False else
               ["cancel_task"] if status in {"queued", "running"} else
               ["refresh"] if status == "cancelling" else
               ["view_result"] if status == "completed" else
               (data.get("problem") or {}).get("recovery", ["retry_task"] if data["retryable"] else ["edit_parameters"]))
    data["actions"] = [{"type": a, "label": LABELS[a], "run_id": data["run_id"]} for a in actions]
    data["stage_label"] = STAGES.get(data.get("stage"), "等待执行")
    data.setdefault("analysis_status", "not_generated")
    data["analysis_message"] = {"pending": "预测已完成，正在结合领域背景生成分析。",
        "completed": "预测分析已生成。", "fallback": "已提供基于计算结果的基础分析。",
        "unavailable": "补充分析暂时不可读取，预测结果仍可使用。",
        "not_generated": "尚未生成预测分析。"}.get(data["analysis_status"], "")
    return data


def present(response, task=None):
    """A turn is one reply. Task cards are independently keyed by run_id."""
    result = dict(response)
    result["protocol_version"] = "1.0"
    result.setdefault("error", False)
    result.setdefault("problem", None)
    result.setdefault("params", {})
    result.setdefault("interaction", None)
    task = task_view(task)
    result["task"] = task
    result["status"] = ("error" if result["error"] else "awaiting_input" if result["interaction"] else
                        "stopping" if task and task["status"] == "cancelling" else
                        "processing" if task and task["status"] in ACTIVE else
                        "completed" if task and task["status"] == "completed" else
                        "cancelled" if task and task["status"] == "cancelled" else
                        "error" if task and task["status"] in {"failed", "interrupted"} else "idle")
    if result["status"] == "error":
        result["error"] = True
    if task and task.get("problem") and task["status"] != "completed" and not result["problem"]:
        result["problem"] = task["problem"]
    problem = result["problem"]
    if problem:
        result["error_code"] = problem["code"]
    result["actions"] = ([{"type": a, "label": LABELS[a], **({"run_id": result["run_id"]} if result.get("run_id") else {})} for a in problem["recovery"]]
                         if response.get("error") and problem else task["actions"] if task else [])
    return result


def http_error(exc):
    if isinstance(exc, HTTPException):
        status = exc.status_code
        code, message, action = {
            401: ("unauthorized", "请重新登录后继续。", "login"),
            403: ("forbidden", "无权访问，或文件链接已过期，请刷新后重试。", "refresh"),
            404: ("not_found", "资源不存在或当前不可读取。", "refresh"),
            409: ("conflict", "操作冲突，请刷新状态后再试。", "refresh"),
            410: ("session_deleted", "会话已删除，请新建会话。", "new_session"),
        }.get(status, ("invalid_request", "请求参数不符合要求，请检查后重试。", "resend_message"))
        problem = {"code": code, "message": message, "stage": None, "retryable": False, "recovery": [action]}
        if isinstance(exc.detail, dict) and exc.detail.get("code") in ERRORS:
            problem = exc.detail
    else:
        error = (exc if isinstance(exc, ForecastError) else
                 ForecastError("invalid_parameters") if isinstance(exc, (ValueError, RequestValidationError)) else classify(exc))
        status, problem = error.http_status, error.problem()
        if not isinstance(exc, (ValueError, HTTPException, RequestValidationError)):
            status = 500
    return JSONResponse({**present({"content": problem["message"], "error": True, "problem": problem}),
                         "detail": problem["message"]}, status_code=status,
                        headers=getattr(exc, "headers", None))
