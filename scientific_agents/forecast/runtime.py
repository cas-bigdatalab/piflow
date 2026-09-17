"""Persistent conversational loop plus a single CPU worker, independent of SSE lifetime."""
from hashlib import sha256
from typing import TypedDict
import logging
import threading
import uuid
import pandas as pd

from langgraph.graph import StateGraph, START, END

from .dialogue import Interpreter
from .persistence import Store, session_key
from .reports import compare_results, render_reply
from .schema import ForecastResult, Intent, TaskParams, TurnInput
from .workflow import ForecastWorkflow
from .execution import TaskRunner
from .feedback import ACTIVE, ForecastError, classify, present, task_view
from .history import TaskHistory, TaskChoice
from .planning import OriginChoice, resolve_origin, plan_message
from .matching import candidates as match_candidates, matches_target, area_suggestions, area_selection, AreaChoice, normalized

log = logging.getLogger(__name__)


class Conversation(TypedDict, total=False):
    params: dict
    history: list
    runs: list[str]
    version: int
    message: str
    turn_id: str
    last_turn_id: str
    session: str
    intent: dict
    response: dict
    parse_error: bool
    pending_task: dict | None
    pending_match: dict | None
    case_selection: bool
    selection_reply: bool
    scope: dict
    analysis_context: dict
    analysis_messages: list


def request_turn_id(request: TurnInput) -> str:
    session = session_key(request.user_id, request.thread_id, "forecast")
    identity = request.request_id or (f"message:{request.message_id}" if request.message_id is not None else uuid.uuid4().hex)
    return sha256(f"{session}:{identity}".encode()).hexdigest()


class ForecastAgent:
    agent_id = "forecast"

    def __init__(self, workflow: ForecastWorkflow, store: Store, checkpointer, interpreter: Interpreter):
        self.workflow, self.store, self.interpreter = workflow, store, interpreter
        self._lock = threading.RLock()  # Serialize short graph/checkpoint transactions, not prediction jobs.
        self.runner = TaskRunner(workflow, store, interpreter)
        self._jobs = self.runner.jobs
        self.task_history = TaskHistory(store)
        self.session_manager = None
        self.checkpointer = checkpointer
        graph = StateGraph(Conversation)
        graph.add_node("understand", self._understand)
        graph.add_node("advance", self._advance)
        graph.add_edge(START, "understand")
        graph.add_edge("understand", "advance")
        graph.add_edge("advance", END)
        self.graph = graph.compile(checkpointer=checkpointer)

    def state(self, user: str, thread: str):
        key = session_key(user, thread, self.agent_id)
        with self._lock:
            return dict(self.graph.get_state({"configurable": {"thread_id": key}}).values or {})

    def turn(self, request: TurnInput) -> dict:
        session = session_key(request.user_id, request.thread_id, self.agent_id)
        turn_id = request_turn_id(request)
        config = {"configurable": {"thread_id": session}}
        with self._lock:
            if self.session_manager:
                self.session_manager.require(request.user_id, request.thread_id)
            previous = self.store.turn(turn_id)
            if previous:
                if previous["input"] != request.message:
                    raise ForecastError("request_conflict")
                return previous["response"]
            current = dict(self.graph.get_state(config).values or {})
            if request.expected_version is not None and request.expected_version != current.get("version", 0):
                raise ForecastError("version_conflict")
            if request.attachments:
                raise ForecastError("invalid_parameters", "本智能体只使用已注册数据源，不接受临时附件替换输入")
            if current.get("last_turn_id") == turn_id:
                response = current["response"]
            else:
                output = self.graph.invoke({"message": request.message, "turn_id": turn_id, "session": session}, config)
                response = output["response"]
            self.store.save_turn(turn_id, session, {"input": request.message, "response": response,
                                                  "message_id": request.message_id})
            self.store.emit(session, {"type": "turn.completed", **response})
            if self.session_manager:
                self.session_manager.sync_safely(session)
            return response

    def _understand(self, state):
        try:
            selected = self.task_history.answer(state["message"], state.get("pending_task"))
            tasks = self.task_history.list(state["session"])
            context = {**state, "task_catalog": [self.task_history.summary(t) for t in tasks[-20:]], "task_count": len(tasks)}
            mode_reply = None
            match = state.get("pending_match")
            case_id = area_selection(state["message"], match["options"]) if match else None
            case_reply = (Intent.model_validate_json(state["message"]) if state["message"].lstrip().startswith("{")
                          else Intent(case_ids=[case_id])) if case_id else None
            if case_reply:
                supplied_context = case_reply.analysis_context.model_dump(exclude_unset=True) if case_reply.analysis_context else {}
                case_reply = Intent.model_validate({**case_reply.model_dump(),
                    "analysis_context": {**match["analysis_context"], **supplied_context}})
            interaction = state.get("response", {}).get("interaction") or {}
            if interaction.get("field") == "origin_mode" and any(o.get("id") == "replay" for o in interaction.get("options", [])):
                if state["message"].strip().rstrip("。") in {"replay", "历史回放", "使用历史数据回放", "选择历史回放", "可以", "好的", "1"}:
                    mode_reply = Intent(origin_mode="replay")
            intent = case_reply or selected or mode_reply or self.interpreter.parse(state["message"], context, self.workflow.registry.list_cases())
            intent = Intent.model_validate(intent)
            if intent.auxiliary_case_ids and not state["message"].lstrip().startswith("{"):
                raise ForecastError("invalid_parameters", "组合预测请在数据选择器中手动选择目标和辅助变量")
            pending = state.get("pending_task")
            if (not selected and pending and intent.action == pending["intent"]["action"]
                    and len(intent.run_ids) == 1 and intent.run_ids[0] in pending["candidate_ids"]):
                selected = self.task_history.answer(intent.run_ids[0], pending)
                intent = selected
            return {"intent": intent.model_dump(), "parse_error": False, "selection_reply": selected is not None,
                    "case_selection": case_reply is not None}
        except Exception as exc:
            # Do not log provider response bodies, credentials or users' messages.
            log.warning("Forecast intent failed: %s status=%s session=%s turn=%s",
                        type(exc).__name__, getattr(exc, "status_code", None),
                        state.get("session"), state.get("turn_id"))
            return {"intent": {"action": "help"}, "parse_error": True, "selection_reply": False, "case_selection": False}

    def _advance(self, state):
        intent = Intent.model_validate(state["intent"])
        if (intent.action == "predict" and intent.wants_probability and not any([
                intent.case_ids, intent.origin, intent.horizon_hours, intent.origin_mode, intent.history_hours,
                intent.requested_area, intent.requested_variable, intent.requested_hazard])):
            intent.action = "explain" if state.get("runs") else "help"
        params = dict(state.get("params", {}))
        scope = dict(state.get("scope", {}))
        report_context = dict(state.get("analysis_context", {}))
        report_messages = list(state.get("analysis_messages", []))
        runs = list(state.get("runs", []))
        version = state.get("version", 0) + 1
        response = {"content": "", "state_version": version, "run_id": None, "interaction": None}
        session = state["session"]
        pending = state.get("pending_task")
        pending_match = state.get("pending_match")
        try:
            if state.get("parse_error"):
                raise ForecastError("intent_parse_failed")
            elif intent.action == "help":
                response["content"] = self.help_text()
            elif intent.action == "unsupported":
                raise ForecastError("unsupported",
                    f"当前已注册的数据与预测能力暂不能支持这项请求：“{state['message'][:300]}”。"
                    "目前仅匹配已注册数据，不会自动搜索或接入外部数据源。"
                    "如果是预测需求，需要先接入对应地区和变量的数据；也可以询问目前有哪些可用数据。")
            elif intent.action == "clarify":
                response.update(content="你希望查看已有结果，还是按之前的条件重新预测？",
                    interaction={"field": "action", "prompt": "请选择接下来要做什么。",
                                 "options": ["查看已有结果", "重新预测"], "state_version": version})
            elif intent.action in {"status", "cancel", "retry"}:
                task = self._task_for(state, intent)
                pending = None
                response["run_id"] = task["run_id"]
                if intent.action == "status":
                    view = task_view(task)
                    response["content"] = {"queued": "任务已排队，轮到后会自动开始。",
                        "running": f"正在进行{view['stage_label']}，完成后会提供结果。",
                        "completed": "这次预测已经完成，可以查看图表和报告。",
                        "cancelled": "这次任务已取消，你可以调整条件后重新预测。",
                        "cancelling": "已请求停止任务，正在等待当前计算退出。"}.get(task["status"],
                        (task.get("problem") or {}).get("message", "任务尚未完成，请查看恢复建议。"))
                    if task.get("stalled"):
                        response["content"] = task["problem"]["message"]
                elif intent.action == "cancel":
                    if task["status"] in {"queued", "running"}:
                        self.runner.stop(task["run_id"], session)
                        response["content"] = "已请求取消，将在当前计算步骤结束后停止。"
                    else:
                        response["content"] = "该任务当前不在运行。"
                elif task_view(task)["retryable"]:
                    self.submit(task["run_id"], session, TaskParams.model_validate(task["params"]))
                    response["content"] = "已从已保存阶段重新提交任务。"
                else:
                    raise ForecastError("task_stopping" if task["status"] in ACTIVE else "retry_not_allowed")
            elif intent.action in {"explain", "report", "compare"}:
                selected = [t["run_id"] for t in self._tasks_for(state, intent)]
                pending = None
                results = [self.result(run_id, session) for run_id in selected]
                response["run_id"] = selected[-1]
                if intent.action == "compare":
                    response["content"] = compare_results(*results)
                else:
                    result = results[-1]
                    try:
                        fact_ids = self.interpreter.select_facts(state["message"], result.facts)
                        response["content"] = render_reply(result, fact_ids)
                    except Exception:
                        response["content"] = render_reply(result)
                    response["artifacts"] = result.artifacts
                    response["warning_analysis"] = (result.warning_analysis.model_dump(mode="json")
                                                    if result.warning_analysis else None)
            else:
                if pending_match and state.get("case_selection"):
                    params = dict(pending_match["params"])
                    scope = dict(pending_match["scope"])
                    scope.pop("requested_area", None)  # Only the explicitly confirmed name may change.
                    report_messages = list(pending_match["analysis_messages"])
                    intent.requested_area = next(c["area"] for c in pending_match["options"] if c["id"] == intent.case_ids[0])
                elif pending_match and intent.action == "predict" and not any(
                        value and normalized(value) in normalized(state["message"])
                        for value in [intent.requested_area, intent.requested_variable, intent.requested_hazard]):
                    raise ForecastError("invalid_parameters", "请明确选择候选数据的名称、编号或列表序号；也可以重新描述需要预测的对象。")
                if intent.action == "reuse":
                    source = self._task_for(state, intent)
                    report_context = dict(source.get("analysis_context", {}).get("user", {}))
                    report_messages = []
                    params = dict(source["params"])
                    params["origin_mode"] = "explicit"  # Reuse the saved instant, not a new wall clock.
                    response["source_run_id"] = source["run_id"]
                updates = {k: getattr(intent, k) for k in ["case_ids", "auxiliary_case_ids", "origin", "horizon_hours", "history_hours", "origin_mode"] if getattr(intent, k) is not None}
                if intent.origin_mode == "tomorrow" and intent.horizon_hours is None:
                    updates["horizon_hours"] = 24
                proposed = {**params, **updates}
                if intent.case_ids and intent.case_ids != params.get("case_ids") and intent.auxiliary_case_ids is None:
                    proposed.pop("auxiliary_case_ids", None)
                if intent.history_mode == "auto":
                    proposed.pop("history_hours", None)
                if intent.origin:
                    proposed["origin_mode"] = "explicit"
                    proposed.pop("history_cutoff", None)
                elif intent.origin_mode in {"now", "replay", "tomorrow"}:
                    proposed.pop("origin", None)
                    proposed.pop("history_cutoff", None)
                cfg = self.workflow.settings
                catalogue = self.workflow.registry.list_cases()
                candidates = catalogue
                if intent.action == "reuse" or (intent.case_ids and params.get("case_ids") and not state.get("case_selection")):
                    scope = {}
                target, hazard = intent.requested_variable, intent.requested_hazard
                if not target and hazard and any(matches_target(c, hazard) for c in catalogue):
                    target, hazard = hazard, None  # Normalize legacy variable requests before merging conversation scope.
                if target:
                    if any(matches_target(c, scope.get("requested_hazard")) for c in catalogue):
                        scope.pop("requested_hazard", None)
                    scope["requested_variable"] = target
                scope.update({k: v for k, v in {"requested_area": intent.requested_area,
                                              "requested_hazard": hazard}.items() if v})
                if scope:
                    candidates = self._candidates(scope)
                    if not candidates:
                        suggestions = area_suggestions(catalogue, scope)
                        if suggestions:
                            raise AreaChoice(suggestions)
                        requested = "、".join(str(v) for v in scope.values() if v)
                        horizon = proposed.get("horizon_hours")
                        duration = f"未来 {horizon} 小时" if horizon else ""
                        raise ForecastError("unsupported",
                            f"当前已注册数据目录没有匹配“{requested}”的数据，暂时无法执行{duration}预测。"
                            "不会使用其他地区替代，也尚未接入外部数据搜索。"
                            "请核对目录中的名称和变量；确认未注册后再接入对应数据。预测当前未来时段还需满足数据时效要求。")
                    candidate_ids = {c["id"] for c in candidates}
                    if intent.case_ids and not set(intent.case_ids) <= candidate_ids:
                        raise ForecastError("invalid_parameters", "所选案例与请求的区域、预测变量或风险类型不匹配。")
                    if not intent.case_ids and (not proposed.get("case_ids") or not set(proposed["case_ids"]) <= candidate_ids):
                        proposed["case_ids"] = [candidates[0]["id"]] if len(candidates) == 1 else []
                previous_cases = state.get("params", {}).get("case_ids") if state.get("case_selection") else params.get("case_ids")
                if previous_cases and set(proposed.get("case_ids", [])) != set(previous_cases):
                    report_context, report_messages = {}, []
                    if state.get("case_selection"):
                        report_messages = list(pending_match["analysis_messages"])
                    if intent.auxiliary_case_ids is None:
                        proposed.pop("auxiliary_case_ids", None)
                if intent.analysis_context:
                    report_context.update({k: v for k, v in intent.analysis_context.model_dump().items() if v})
                report_messages = [*report_messages, {"role": "user", "content": state["message"][:2000]}][-6:]
                if "case_ids" in proposed:
                    ids = proposed["case_ids"]
                    if (not ids and not scope) or len(ids) > cfg.max_cases or len(set(ids)) != len(ids) or any(i not in self.workflow.registry.cases for i in ids):
                        raise ForecastError("invalid_parameters", "请选择目录中的案例，且不超过允许数量")
                if proposed.get("horizon_hours") is not None:
                    self.workflow.registry.warnings.validate_hours(proposed["horizon_hours"], proposed.get("case_ids", []))
                if proposed.get("origin"):
                    # Validate timezone now, even if other fields are still missing.
                    TaskParams(case_ids=["validation"], origin=proposed["origin"], horizon_hours=1)
                interaction = self._interaction(proposed, state["turn_id"], version)
                if interaction:
                    if interaction["field"] == "case_ids" and scope:
                        interaction["options"] = candidates
                    params = proposed
                    response.update(content=interaction["prompt"], interaction=interaction)
                else:
                    proposed = resolve_origin(proposed, self.workflow.registry)
                    validated = TaskParams.model_validate(proposed)
                    if intent.action != "reuse" and validated.auxiliary_case_ids is None:
                        validated.auxiliary_case_ids = []
                    selected_registry = self.workflow.registry.bind(validated)
                    self.workflow.validate(validated)
                    params = proposed
                    active = next((t for t in self.store.list_tasks(session) if t["status"] in ACTIVE), None)
                    if active:
                        response["content"] = "新参数已保存。当前任务保持原参数运行；完成后发送“开始预测”执行新参数，或先取消当前任务。"
                        response["run_id"] = active["run_id"]
                    else:
                        run_id = "fc-" + state["turn_id"][:24]
                        from .analysis_context import snapshot
                        self.submit(run_id, session, validated,
                                    snapshot(selected_registry, validated.case_ids, report_context, report_messages))
                        if run_id not in runs:
                            runs.append(run_id)
                        response.update(run_id=run_id, content=plan_message(validated, self.workflow.registry))
                pending = None
                pending_match = None
        except AreaChoice as choice:
            requested = scope["requested_area"]
            prompt = f"未精确匹配“{requested}”，找到名称相近且符合指标条件的数据，请确认具体对象。确认前不会开始预测。"
            pending_match = {"options": choice.options, "params": proposed, "scope": scope,
                             "analysis_context": intent.analysis_context.model_dump(exclude_none=True) if intent.analysis_context else {},
                             "analysis_messages": [*report_messages, {"role": "user", "content": state["message"][:2000]}][-6:]}
            # Pending corrections are checkpointed separately from confirmed parameters.
            params, scope = dict(state.get("params", {})), dict(state.get("scope", {}))
            report_context = dict(state.get("analysis_context", {}))
            report_messages = list(state.get("analysis_messages", []))
            pending = None
            response.update(content=prompt, interaction={"field": "case_ids", "prompt": prompt,
                            "options": choice.options, "reason": "similar_name"})
        except TaskChoice as choice:
            pending_match = None
            pending = {"intent": choice.pending, "chosen": choice.chosen, "remaining": choice.remaining,
                       "options": choice.options[:20], "candidate_ids": [t["run_id"] for t in choice.options]}
            response.update(content="找到多个符合描述的历史任务，请确认你指的是哪一次。",
                interaction={"field": "run_ids", "options": pending["options"], "total_options": len(choice.options),
                             "prompt": "回复任务编号或当前列表中的序号即可继续。", "state_version": version})
        except Exception as exc:
            error = classify(exc)
            # Never commit an invalid proposal or a failed historical reuse.
            params = dict(state.get("params", {}))
            scope = dict(state.get("scope", {}))
            report_context = dict(state.get("analysis_context", {}))
            report_messages = list(state.get("analysis_messages", []))
            # A rejected scope is not a request to choose from unrelated cases.
            # Retain confirmed parameters, but never suggest them as a substitute.
            rejected_scope = error.code == "unsupported" or (
                error.code == "invalid_parameters" and (intent.requested_area or intent.requested_hazard))
            interaction = (state.get("response", {}).get("interaction") if pending_match else None if rejected_scope else
                           state.get("response", {}).get("interaction") if pending else
                           self._interaction(params, state["turn_id"], version, scope))
            response.update(content=str(error), error=True, problem=error.problem(), interaction=interaction)
        if intent.wants_probability:
            response["content"] += "\n当前提供指标预测及已注册规则评估，尚未接入事件概率模型，不会把分位数换算成事件发生概率。"
            response["probability_available"] = False
        response["params"] = dict(params)
        response["reply_id"] = "reply-" + state["turn_id"]
        if response["interaction"]:
            response["interaction"] = {**response["interaction"], "interaction_id": state["turn_id"], "state_version": version}
        task = self.store.task(response["run_id"], session) if response["run_id"] else None
        response = present(response, task)
        history = [*state.get("history", []), {"role": "user", "content": state["message"]},
                   {"role": "assistant", "content": response["content"]}][-12:]
        return {"params": params, "runs": runs[-30:], "history": history, "version": version,
                "analysis_context": report_context, "analysis_messages": report_messages,
                "response": response, "last_turn_id": state["turn_id"], "pending_task": pending,
                "pending_match": pending_match, "scope": scope}

    def _candidates(self, scope):
        return match_candidates(self.workflow.registry.list_cases(), scope)

    def _interaction(self, params, turn_id, version, scope=None):
        field = next((key for key in ["case_ids", "horizon_hours"] if not params.get(key)), None)
        if field is None:
            try:
                resolve_origin(params, self.workflow.registry)
                return None
            except OriginChoice as choice:
                return {**choice.interaction, "interaction_id": turn_id, "state_version": version}
        warnings = self.workflow.registry.warnings
        case_ids = params.get("case_ids", [])
        allowed = warnings.allowed_hours(case_ids)
        # These are shortcuts, not an admission white list; arbitrary integer hours remain valid.
        choices = sorted({h for h in (1, 3, 6, 12, 24, 48, 72, 120, 168, allowed[-1]) if h in allowed})
        questions = {"case_ids": "我还需要确认使用哪份数据，请选择一个预测案例。",
                     "origin": "请提供预测起点（含时区）。历史资料仅用于历史回放，不代表当前监测。",
                     "horizon_hours": "你希望评估未来多长时间？" + warnings.hours_description(case_ids) + "，可直接输入时长或选择常用时长。"}
        options = self._candidates(scope or {}) if field == "case_ids" else choices if field == "horizon_hours" else []
        if field == "case_ids" and not options:
            return None
        return {"field": field, "options": options, "prompt": questions[field],
                "interaction_id": turn_id, "state_version": version}

    def help_text(self):
        cases = "\n".join(f"- {c['label']}" for c in self.workflow.registry.list_cases())
        return f"告诉我希望预测的对象或数据、指标和未来多长时间，我会检查数据并自动确定起点与历史窗口。历史资料会先确认回放模式，不会当作当前监测；也可指定历史长度或回放时间。\n{cases}\n支持时长以所选场景为准；尚不提供事件发生概率。也可询问进度、取消、重试、解释结果、比较历史结果或下载报告。"

    def _task_for(self, state, intent):
        return self._tasks_for(state, intent)[0]

    def _tasks_for(self, state, intent):
        pending = state.get("pending_task") if state.get("selection_reply") else None
        return self.task_history.resolve(state["session"], intent, pending=pending)

    def result(self, run_id, session) -> ForecastResult:
        task = self.store.task(run_id, session)
        if not task or task["status"] != "completed":
            raise ForecastError("result_not_ready", http_status=404)
        path = self.workflow.settings.root / "runs" / run_id / "result.json"
        try:
            result = ForecastResult.model_validate_json(path.read_text(encoding="utf-8"))
            from .result_view import build
            result.presentation = build(result)
            if task.get("report_status"):
                result.report_status = task["report_status"]
            if task.get("analysis_status") == "unavailable":
                from .warning.analysis import WarningAnalysis
                result.warning_analysis = WarningAnalysis(status="unavailable", reason_code="analysis_storage_failed",
                    message="补充分析暂时不可读取，已完成的预测结果仍可使用。")
            return result
        except (OSError, ValueError) as exc:
            raise ForecastError("result_unavailable", http_status=503) from exc

    def submit(self, run_id, session, params, analysis_context=None):
        self.runner.submit(run_id, session, params, analysis_context)

    def close(self):
        self.runner.close()
