"""One CPU worker with supervised deadlines and cooperative, race-safe stopping."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import threading
import time

from .feedback import ACTIVE, ForecastError, classify, completion_message
from .workflow import Cancelled
from .warning.analysis import WarningAnalysis, WarningAnalyzer, save_analysis

log = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class TaskRunner:
    def __init__(self, workflow, store, interpreter=None):
        self.workflow, self.store = workflow, store
        self.analyzer = WarningAnalyzer(interpreter)
        self.jobs, self.clocks = {}, {}
        self.lock = threading.RLock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="forecast-cpu")
        self.stopping = threading.Event()
        for task in store.list_tasks():
            if task["status"] in ACTIVE:
                error = ForecastError("task_interrupted")
                self.store.put_task(task["run_id"], task["session"], "interrupted",
                                    error=str(error), problem=error.problem(), stalled=False)
            elif task["status"] == "completed" and task.get("analysis_status") == "pending":
                self._recover_analysis(task)
        self.watcher = threading.Thread(target=self._watch, name="forecast-supervisor", daemon=True)
        self.watcher.start()

    def submit(self, run_id, session, params, analysis_context=None):
        with self.lock:
            if self.stopping.is_set():
                raise ForecastError("task_stopping")
            if any(self.store.task(r).get("stalled") for r in self.clocks):
                raise ForecastError("task_stalled")
            previous = self.store.task(run_id, session)
            if analysis_context is None:
                from .analysis_context import snapshot
                analysis_context = ((previous or {}).get("analysis_context") or
                                    snapshot(self.workflow.registry.bind(params), params.case_ids))
            job = self.jobs.get(run_id)
            if job and not job.done():
                raise ForecastError("task_stopping")
            if previous and previous["status"] == "completed":
                return
            self.clocks[run_id] = {"queued": time.monotonic(), "started": None,
                                   "progress": time.monotonic(), "stop": None, "reason": None}
            self.store.put_task(run_id, session, "queued", params=params.model_dump(mode="json"),
                analysis_context=analysis_context,
                error="", problem=None, artifacts=[], stalled=False, stage=None, stage_status=None,
                started_at=None, stage_started_at=None, last_progress_at=utcnow(), stop_requested_at=None,
                finished_at=None, data_plan=None, attempt=(previous or {}).get("attempt", 0) + 1)
            self.jobs[run_id] = self.pool.submit(self._execute, run_id, session, params)

    def stop(self, run_id, session, reason="task_cancelled"):
        with self.lock:
            task = self.store.task(run_id, session)
            if not task or task["status"] not in ACTIVE:
                return
            clock = self.clocks.get(run_id)
            if not clock or clock["stop"] is not None:
                return
            clock.update(stop=time.monotonic(), reason=reason)
            error = ForecastError(reason, stage=task.get("stage"))
            self.store.put_task(run_id, session, "cancelling", error=str(error), problem=error.problem(),
                                stage_status="stopping", stop_requested_at=utcnow())
            # A queued future can be cancelled immediately. A running call must exit first.
            job = self.jobs.get(run_id)
            if job and job.cancel():
                self._finish_stop(run_id, session, clock)

    def _finish_stop(self, run_id, session, clock):
        task = self.store.task(run_id)
        code = clock["reason"] or "task_cancelled"
        error = ForecastError(code, stage=task.get("stage"))
        problem = error.problem()
        if code == "task_timeout":
            problem.update(message="任务超时后已停止。可以重试，或调整预测条件。",
                           retryable=True, recovery=["retry_task", "edit_parameters"])
        status = "cancelled" if code == "task_cancelled" else "failed"
        self.store.put_task(run_id, session, status, error=problem["message"], problem=problem,
                            finished_at=utcnow(), stalled=False, artifacts=[], stage_status=status)
        self.store.emit(session, {"type": "task.failed", "run_id": run_id, "status": status,
                                 "message": problem["message"], "problem": problem, "attempt": task.get("attempt", 1)})
        self.clocks.pop(run_id, None)

    def _execute(self, run_id, session, params):
        def cancelled():
            with self.lock:
                clock = self.clocks.get(run_id)
                return clock is None or clock["stop"] is not None

        def emit(stage, status):
            with self.lock:
                self.monitor()
                if cancelled():
                    raise Cancelled("任务已请求停止")
                if stage == "process":
                    self.store.put_task(run_id, session, "running", process_id=status)
                    return
                if stage == "plan":
                    self.store.put_task(run_id, session, "running", data_plan=status)
                    adjusted = any(w.get("adjusted") for w in status["history_windows"].values())
                    self.store.emit(session, {"type": "data.ready", "run_id": run_id,
                        "status": "completed", "data_plan": status, "message": "数据检查通过，已确定实际历史窗口。"
                        + ("部分案例的默认窗口数据不足，已缩短至通过检查的最低历史窗口。" if adjusted else "")})
                    return
                now = utcnow()
                self.clocks[run_id]["progress"] = time.monotonic()
                fields = {"stage": stage, "stage_status": status, "last_progress_at": now}
                if status == "running":
                    fields["stage_started_at"] = now
                self.store.put_task(run_id, session, "running", **fields)
                task = self.store.task(run_id)
                self.store.emit(session, {"type": "task.progress", "run_id": run_id,
                    "stage": stage, "status": status, "attempt": task["attempt"], "at": now})

        try:
            with self.lock:
                if cancelled():
                    raise Cancelled("任务已取消")
                self.clocks[run_id]["started"] = time.monotonic()
                self.store.put_task(run_id, session, "running", started_at=utcnow())
            result = self.workflow.run(run_id, params, emit, cancelled, defer_report=True)
            result.analysis_context = self.store.task(run_id, session).get("analysis_context", {})
            from .workflow import write_json
            directory = self.workflow.settings.root / "runs" / run_id
            result.warning_analysis = WarningAnalysis()
            write_json(directory / "result.json", result.model_dump(mode="json"))
            with self.lock:
                self.monitor()
                if cancelled():
                    raise Cancelled("任务已请求停止")
                self.store.put_task(run_id, session, "completed", artifacts=result.artifacts,
                                    error="", problem=None, finished_at=utcnow(), stalled=False,
                                    analysis_status=result.warning_analysis.status, report_status="pending")
                self.store.emit(session, {"type": "result.ready", "run_id": run_id,
                    "content": completion_message(result), "artifacts": result.artifacts,
                    "warning_analysis": result.warning_analysis.model_dump(mode="json"),
                    "attempt": self.store.task(run_id)["attempt"]})
                self.clocks.pop(run_id, None)
        except Exception as exc:
            with self.lock:
                clock = self.clocks.get(run_id)
                if clock and (clock["stop"] is not None or isinstance(exc, Cancelled)):
                    self._finish_stop(run_id, session, clock)
                else:
                    task = self.store.task(run_id)
                    error = classify(exc, task.get("stage"))
                    self.store.put_task(run_id, session, "failed", error=str(error), problem=error.problem(),
                                        finished_at=utcnow(), stalled=False, artifacts=[], stage_status="failed")
                    self.store.emit(session, {"type": "task.failed", "run_id": run_id, "status": "failed",
                        "message": str(error), "problem": error.problem(), "attempt": task.get("attempt", 1)})
                    self.clocks.pop(run_id, None)
            return
        # Prediction is already completed and readable. Optional analysis has its own
        # timeout and cannot retroactively fail/cancel that prediction. The same job
        # owns writes so session deletion continues to wait for the actual worker.
        if result.warning_analysis.status == "pending":
            self._complete_analysis(result, session)

    def _complete_analysis(self, result, session, reason=None):
        run_id = result.run_id
        try:
            self.store.emit(session, {"type": "analysis.progress", "run_id": run_id,
                                     "status": "pending", "message": "正在结合领域背景生成预测分析。"})
            analysis = save_analysis(result, self.workflow.settings.root / "runs" / run_id, self.analyzer, reason)
            self.store.put_task(run_id, session, "completed", analysis_status=analysis.status,
                                artifacts=result.artifacts, report_status=result.report_status)
            self.store.emit(session, {"type": "analysis.ready", "run_id": run_id,
                "status": analysis.status, "warning_analysis": analysis.model_dump(mode="json"),
                "content": completion_message(result), "artifacts": result.artifacts})
        except Exception as exc:
            # Storage problems must not turn a usable forecast into a failed task.
            log.error("Analysis persistence unavailable: %s", type(exc).__name__)
            self.store.put_task(run_id, session, "completed", analysis_status="unavailable", report_status="failed")
            self.store.emit(session, {"type": "analysis.unavailable", "run_id": run_id,
                "status": "unavailable", "message": "补充分析暂时不可读取，已完成的预测结果仍可使用。"})

    def retry_report(self, run_id, session):
        """Regenerate explanation/report only; never rerun the numerical model."""
        from .schema import ForecastResult
        from .workflow import write_json
        with self.lock:
            task = self.store.task(run_id, session)
            if not task or task["status"] != "completed":
                raise ForecastError("result_not_ready", http_status=409)
            if self.stopping.is_set():
                raise ForecastError("task_stopping")
            if run_id in self.jobs and not self.jobs[run_id].done():
                return
            path = self.workflow.settings.root / "runs" / run_id / "result.json"
            result = ForecastResult.model_validate_json(path.read_text(encoding="utf-8"))
            result.warning_analysis, result.report_status = WarningAnalysis(), "pending"
            write_json(path, result.model_dump(mode="json"))
            self.store.put_task(run_id, session, "completed", analysis_status="pending", report_status="pending")
            self.jobs[run_id] = self.pool.submit(self._complete_analysis, result, session)

    def _recover_analysis(self, task):
        from .schema import ForecastResult
        path = self.workflow.settings.root / "runs" / task["run_id"] / "result.json"
        try:
            result = ForecastResult.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.store.put_task(task["run_id"], task["session"], "completed", analysis_status="unavailable")
            return
        self._complete_analysis(result, task["session"], "analysis_interrupted")

    def monitor(self, now=None):
        now = time.monotonic() if now is None else now
        limits = self.workflow.settings.execution
        with self.lock:
            for run_id, clock in list(self.clocks.items()):
                task = self.store.task(run_id)
                if not task:
                    continue
                if clock["stop"] is not None:
                    if now - clock["stop"] >= limits.cancel_grace_seconds and not task.get("stalled"):
                        error = ForecastError("task_stalled", stage=task.get("stage"))
                        self.store.put_task(run_id, task["session"], "cancelling", stalled=True,
                                            error=str(error), problem=error.problem())
                        self.store.emit(task["session"], {"type": "task.stalled", "run_id": run_id,
                            "status": "cancelling", "problem": error.problem(), "attempt": task["attempt"]})
                    continue
                elapsed = now - (clock["started"] or clock["queued"])
                limit = limits.task_seconds if clock["started"] is not None else limits.queue_seconds
                if elapsed >= limit or (clock["started"] is not None and now - clock["progress"] >= limits.stage_seconds):
                    self.stop(run_id, task["session"], "task_timeout")

    def _watch(self):
        while not self.stopping.wait(.5):
            try:
                self.monitor()
            except Exception as exc:
                log.error("Forecast supervision unavailable: %s", type(exc).__name__)

    def close(self):
        with self.lock:
            for run_id in list(self.clocks):
                self.stop(run_id, self.store.task(run_id)["session"])
        self.pool.shutdown(wait=True)
        try:
            self.analyzer.close()
        except Exception as exc:
            log.warning("Analysis client cleanup unavailable: %s", type(exc).__name__)
        self.stopping.set()
        self.watcher.join()
