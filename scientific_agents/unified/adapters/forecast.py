"""Forecast projections only; dialogue, workers, memory and report logic remain native."""
import asyncio
import base64
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from fastapi import HTTPException
from fastapi.responses import HTMLResponse

from ..schemas import PREFIX, available, event, file_view, item, options, result_view, segment, session_view, status, task_view

BASE = "/api/piflow/v1/forecast"


def task_status(value):
    return {"queued": "PROCESSING", "running": "EXECUTING", "interrupted": "FAILED"}.get(value, str(value).upper())


class ForecastAdapter:
    agent_id, label = "forecast", "科学预测"
    session_path = BASE + "/sessions"
    capabilities = ("delete_session", "tasks", "actions", "results", "files")

    def __init__(self, native):
        self.n = native

    def owns_session(self, sid):
        return self.n.extension.sessions.lookup(self.n.user, sid) is not None

    def task_session(self, tid):
        from sqlalchemy import select
        ext = self.n.extension
        sessions, tasks = ext.sessions.sessions, ext.store.tasks
        with ext.store.engine.connect() as conn:
            return conn.execute(select(sessions.c.thread_id).join(tasks, tasks.c.session == sessions.c.session).where(
                tasks.c.run_id == tid, sessions.c.user_id == self.n.user)).scalar_one_or_none()

    async def create_session(self, body):
        data = await self.n.json("POST", self.session_path, {"title": body.title, "request_id": body.request_id})
        return session_view(data, self.agent_id)

    async def list_sessions(self, page, size):
        data = await self.n.json("GET", self.session_path, query={"pageNum": page, "pageSize": size})
        # One batch read for this page; no per-session history loading or model calls.
        def summaries():
            from sqlalchemy import select
            from ...forecast.persistence import session_key
            table = self.n.extension.store.tasks
            keys = {session_key(self.n.user, s["session_id"]): s["session_id"] for s in data["sessions"]}
            values = {sid: {"task_count": 0, "latest_task_id": None,
                           "latest_task_status": None, "latest_task_stage": None} for sid in keys.values()}
            with self.n.extension.store.engine.connect() as conn:
                rows = conn.execute(select(table).where(table.c.session.in_(keys)).order_by(table.c.updated_at.desc())).mappings()
                for row in rows:
                    value = values[keys[row["session"]]]
                    if not value["task_count"]:
                        task = json.loads(row["payload"])
                        value.update(latest_task_id=row["run_id"], latest_task_status=task_status(row["status"]),
                                     latest_task_stage=task.get("stage"))
                    value["task_count"] += 1
            return values
        stats = await asyncio.to_thread(summaries)
        return {"items": [{**session_view(s, self.agent_id), **stats[s["session_id"]]} for s in data["sessions"]],
                "total": data["total"], "pageNum": page, "pageSize": size}

    def task(self, value):
        from ...forecast.feedback import task_view as native_task_view
        value = native_task_view(value)
        actions = [available(a["type"], a["label"]) for a in value["actions"] if a["type"] in {"cancel_task", "retry_task"}]
        state = value["status"]
        if state == "completed" and value.get("report_status") != "pending" and value.get("result_available") is not False:
            actions.append(available("regenerate_report", "重新生成报告"))
        result = task_view(value["run_id"], state, stage=value.get("stage"), data=value, actions=actions,
            outputs=[{"type": "forecast", "status": "ready" if state == "completed" else status(state)},
                     {"type": "analysis", "status": "completed" if value.get("analysis_status") == "fallback" else value.get("analysis_status", "not_generated")},
                     {"type": "report", "status": value.get("report_status", "not_generated")}])
        return {**result, "status": task_status(state), "native_status": state,
                "create_time": value.get("created_at"), "update_time": value.get("updated_at"),
                "error_message": value.get("error") or (value.get("problem") or {}).get("message", "")}

    async def get_session(self, sid, after, limit):
        # Native forecast pages are capped at 200. Aggregate only the requested
        # window so the public contract can keep Cross DAG's 1000/2000 limits.
        messages, cursor = [], after
        while len(messages) < limit:
            data = await self.n.json("GET", BASE + f"/session/{sid}",
                                     query={"after": cursor, "limit": min(200, limit - len(messages))})
            messages.extend(data["messages"])
            if not data["has_more"] or data["next_after"] <= cursor:
                break
            cursor = data["next_after"]
        tasks = [{**self.task(t), "session_id": sid} for t in data["tasks"]]
        items = []
        for m in messages:
            tid = m.get("run_id")
            payload = {"message_id": m.get("reply_id", str(m["id"])), "text": m["content"], "mode": "replace"}
            kind = "USER_MESSAGE" if m["role"] == "user" else "ASSISTANT_MESSAGE"
            if tid:
                kind = "RESULT_CARD"
                payload = result_view(tid, "forecast", "预测结果", {"summary": m["content"]})
            items.append(item(m["id"], kind, payload, tid, role=m["role"], created=m.get("create_time")))
        metadata = {key: data[key] for key in ("session_id", "title", "created_at", "updated_at", "status") if key in data}
        return {"session": session_view(metadata, self.agent_id), "tasks": tasks, "items": items,
                "interaction": data["view"].get("interaction"), "next_after_item_id": data["next_after"], "has_more": data["has_more"]}

    async def delete_session(self, sid):
        await self.n.json("DELETE", BASE + f"/session/{sid}")
        return {"session_id": sid, "deleted": True}

    async def get_task(self, sid, tid):
        from ...forecast.persistence import session_key
        # Validate the live host session before reading native task state.
        await asyncio.to_thread(self.n.extension.sessions.require, self.n.user, sid)
        value = await asyncio.to_thread(self.n.extension.store.task, tid, session_key(self.n.user, sid))
        if value is None:
            raise HTTPException(404, "当前会话中不存在此任务")
        return {**self.task(value), "session_id": sid}

    async def native_result(self, sid, tid):
        return await self.n.json("GET", BASE + f"/result/{tid}", query={"session_id": sid})

    async def detail(self, sid, tid):
        return {"task": await self.get_task(sid, tid), "items": [], "snapshots": {}}

    async def execution_status(self, sid, tid, query):
        if query:
            raise HTTPException(422, "预测任务不支持取数结果节点参数")
        task = await self.get_task(sid, tid)
        state = task["native_status"]
        return {**task, "status": {"queued": "SUBMITTED", "running": "RUNNING", "cancelling": "RUNNING",
                                  "completed": "SUCCESS", "interrupted": "FAILED"}.get(state, state.upper()),
                "downloadable": task.get("result_available") is True}

    async def get_results(self, sid, tid):
        value = await self.native_result(sid, tid)
        task = await self.get_task(sid, tid)
        files = [file_view(f["name"], f["name"], self.n.file_url(sid, tid, f["name"])) for f in value["downloads"]]
        return {"items": [result_view(tid, "forecast", "预测与潜在影响分析", value["result"],
                artifacts=files, actions=task["available_actions"])], "task": task}

    async def download_file(self, sid, tid, fid):
        value = await self.native_result(sid, tid)  # Native ownership + report availability filtering.
        file = next((f for f in value["downloads"] if f["name"] == fid), None)
        if file is None:
            raise HTTPException(404, "文件尚不可用")
        query = {k: v[0] for k, v in parse_qs(urlsplit(file["url"]).query).items()}
        response = await self.n.response("GET", BASE + f"/files/{tid}/{fid}", query=query)
        if fid == "report.html":
            # Make authenticated HTML usable as a fetched blob: its images must not
            # need another Bearer header from the iframe or inherit an invalid blob base.
            html = response.body.decode("utf-8")
            for f in value["downloads"]:
                if f["name"].endswith(".png"):
                    image = await self.n.response("GET", BASE + f"/files/{tid}/{segment(f['name'])}", query=query)
                    raw = await asyncio.to_thread(Path(image.path).read_bytes)
                    url = "data:image/png;base64," + base64.b64encode(raw).decode()
                    html = re.sub(r"src=(['\"])" + re.escape(f["name"]) + r"(?:\?[^'\"]*)?\1", lambda m: f'src="{url}"', html)
            return HTMLResponse(html, headers={"Content-Security-Policy": "default-src 'none'; img-src data:; style-src 'unsafe-inline'",
                                               "Referrer-Policy": "no-referrer"})
        return response

    async def stream_turn(self, sid, body):
        extra = options(body, {"detail", "expected_version", "message_id"})
        extra.pop("detail", None)  # Shared diagnostic flag; native forecast has no detail option.
        message = body.user_request
        if body.parent_task_id:
            await self.get_task(sid, segment(body.parent_task_id))
            message = f"针对任务 {body.parent_task_id}：{message}"
        source = self.n.events(BASE + "/chat/stream", {"session_id": sid, "request_id": body.request_id,
            "message": message, "attachments": body.attachments, **extra})
        async for value in self.convert(source, sid):
            yield value

    async def convert(self, source, sid=None):
        failed = False
        result = {"view_type": "forecast"}
        try:
            async for value in source:
                if value is None:
                    yield None
                    continue
                kind, tid = value["type"], value.get("run_id")
                native_task = value.get("task")
                if native_task:
                    tid = native_task["run_id"]
                    yield event("task", self.task(native_task), tid)
                elif tid and tid != result.get("task_id") and sid:
                    # Announce a real running task before completion, so the shared
                    # frontend can save its ID and offer status/cancel controls.
                    yield event("task", await self.get_task(sid, tid), tid)
                if tid:
                    result["task_id"] = tid
                    if sid:
                        result["results_url"] = str(self.n.request.base_url).rstrip("/") + PREFIX + f"/tasks/{segment(tid)}/results"
                if kind in {"message", "message_delta"}:
                    result["content"] = value.get("content", result.get("content", ""))
                    yield event("message", {"message_id": value.get("reply_id"),
                        "text": value.get("delta", value.get("content", "")),
                        "mode": "append" if kind == "message_delta" else "replace"}, tid)
                elif kind == "interaction.required":
                    result["interaction"] = value["payload"]
                    yield event("interaction", value["payload"], tid)
                elif kind in {"result.ready", "analysis.ready", "analysis.unavailable"}:
                    yield event("result", result_view(tid, "forecast", "预测结果", {
                        "summary": value.get("content"), "warning_analysis": value.get("warning_analysis")}), tid)
                elif kind in {"error", "task.failed"}:
                    failed = True
                    yield event("error", {"code": 500 if kind == "task.failed" else 422,
                        "error_code": (value.get("problem") or {}).get("code", "task_failed"),
                        "message": (value.get("problem") or {}).get("message") or value.get("content", "操作失败")}, tid)
                elif kind == "done":
                    if "content" in value:
                        result["content"] = value["content"]
                    if value.get("error") and not failed:
                        problem = value.get("problem") or {}
                        yield event("error", {"code": 422, "error_code": problem.get("code"),
                            "message": problem.get("message") or value.get("content", "操作未完成")}, tid)
                    yield event("done", {"result": result, "error": failed or bool(value.get("error"))}, result.get("task_id"))
                else:
                    state = status(value.get("status"))
                    yield event("stage", {**value, "stage": value.get("stage") or kind.split(".")[0],
                        "status": {"completed": "finished", "failed": "failed"}.get(state, "started"),
                        "summary": value.get("summary", value.get("message", value.get("content", "")))}, tid)
        finally:
            await source.aclose()

    async def stream_action(self, sid, tid, body):
        await self.get_task(sid, tid)
        if body.action == "regenerate_report":
            options(body, set())
            await self.n.json("POST", BASE + f"/result/{tid}/report", query={"session_id": sid})
            yield event("task", await self.get_task(sid, tid), tid)
        elif body.action in {"cancel_task", "retry_task"}:
            extra = options(body, {"expected_version"})
            command = "取消任务" if body.action == "cancel_task" else "重试任务"
            source = self.n.events(BASE + "/chat/stream", {"session_id": sid, "request_id": body.request_id,
                                   "message": f"{command} {tid}", **extra})
            async for value in self.convert(source, sid):
                yield value
        else:
            raise HTTPException(422, "不支持的预测操作")
