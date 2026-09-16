"""Cross DAG's session/task semantics retained, with a shared presentation envelope."""
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException

from ..schemas import PREFIX, available, file_view, options, result_view, segment, session_view, task_view

BASE = "/api/piflow/v1/xdc"


class CrossDagAdapter:
    agent_id, label = "cross_dag", "智能取数"
    session_path = BASE + "/sessions"
    capabilities = ("delete_session", "tasks", "actions", "results", "files")

    def __init__(self, native):
        self.n = native

    def owns_session(self, sid):
        from repositories.xdc_session_repository import get_session
        return get_session(session_id=sid, user_id=self.n.user) is not None

    def task_session(self, tid):
        from repositories.xdc_session_repository import get_task
        task = get_task(task_id=tid, user_id=self.n.user)
        return task["session_id"] if task else None

    async def execution_status(self, sid, tid, query):
        await self.detail(sid, tid)
        return self.links(await self.call("GET", f"/tasks/{tid}/execution/status", query=query))

    async def call(self, method, path, body=None, query=None):
        return (await self.n.json(method, BASE + path, body, query))["result"]

    async def create_session(self, body):
        return session_view(await self.call("POST", "/sessions", {"title": body.title}), self.agent_id)

    async def list_sessions(self, page, size):
        data = await self.call("GET", "/sessions", query={"pageNum": page, "pageSize": size})
        pagination = data["pagination"]
        return {"items": [session_view(s, self.agent_id) for s in data["items"]],
                "total": pagination["total"], "pageNum": pagination["pageNum"], "pageSize": pagination["pageSize"]}

    def task(self, data):
        actions = [available("execute", "确认执行")] if data.get("status") == "PLANNED" else []
        return task_view(data["task_id"], data.get("status"), stage=data.get("current_stage"), actions=actions, data=data)

    async def get_session(self, sid, after, limit):
        data = await self.call("GET", f"/sessions/{sid}", query={"after_item_id": after, "item_limit": limit})
        return {**data, "session": session_view(data["session"], self.agent_id),
                "tasks": [self.task(t) for t in data["tasks"]],
                "items": [self.links(row) for row in data["items"]],
                "interaction": None, "has_more": len(data["items"]) == limit}

    async def delete_session(self, sid):
        await self.call("DELETE", f"/sessions/{sid}")
        return {"session_id": sid, "deleted": True}

    async def detail(self, sid, tid):
        data = await self.call("GET", f"/tasks/{tid}")
        if data["task"]["session_id"] != sid:
            raise HTTPException(404, "当前会话中不存在此任务")
        return self.links(data)

    async def get_task(self, sid, tid):
        data = await self.detail(sid, tid)
        if data["task"].get("process_id"):
            # Use the Task endpoint that synchronizes native history, not a separate monitor.
            execution = self.links(await self.call("GET", f"/tasks/{tid}/execution/status"))
            data = await self.detail(sid, tid)
            data["task"]["execution"] = execution
        return self.task(data["task"])

    async def get_results(self, sid, tid):
        data = await self.detail(sid, tid)
        task, artifacts = self.task(data["task"]), []
        execution = data["snapshots"].get("execution", {})
        if execution.get("downloadable"):
            name = (execution.get("result_file") or {}).get("file_name", "result")
            artifacts.append(file_view("result", name, self.n.file_url(sid, tid, "result")))
        content = {"plan": data["snapshots"].get("bound_view", data["snapshots"].get("pre_bind_view", {})), "execution": execution}
        return {"items": [result_view(tid, "cross_dag", "取数方案与结果", content,
                artifacts=artifacts, actions=task["available_actions"])], "task": task}

    async def download_file(self, sid, tid, fid):
        data = await self.detail(sid, tid)
        process = data["task"].get("process_id")
        if fid != "result" or not process:
            raise HTTPException(404, "当前任务没有此结果文件")
        execution = data["snapshots"].get("execution", {})
        query = {key: execution[key] for key in ("result_node_id", "result_output_name") if execution.get(key)}
        query.update({key: self.n.request.query_params[key] for key in ("result_node_id", "result_output_name")
                      if key in self.n.request.query_params})
        return await self.n.response("GET", BASE + f"/execution/{segment(process)}/download", query=query)

    async def stream_turn(self, sid, body):
        if body.attachments:
            raise HTTPException(422, "当前取数接口不支持附件")
        extra = options(body, {"detail"})
        if body.parent_task_id:
            await self.detail(sid, segment(body.parent_task_id))
        source = self.n.events(BASE + f"/sessions/{sid}/tasks/plan/pre-bind/stream",
            {"user_request": body.user_request, "parent_task_id": body.parent_task_id, **extra})
        async for value in self.convert(source):
            yield value

    async def stream_action(self, sid, tid, body):
        await self.detail(sid, tid)
        if body.action != "execute":
            raise HTTPException(422, "不支持的取数操作")
        extra = options(body, {"detail", "selected_dataset_id"})
        source = self.n.events(BASE + f"/tasks/{tid}/bind-and-execute/stream", extra)
        async for value in self.convert(source):
            yield value

    async def process_response(self, pid, operation):
        query = dict(self.n.request.query_params)
        path = BASE + f"/execution/{pid}/{operation}"
        if operation == "download":
            return await self.n.response("GET", path, query=query)
        # The original handler retains process ownership, selectors and errors.
        return self.links(await self.n.json("GET", path, query=query))

    def links(self, value):
        """Only replace the API prefix; keep native URL paths and selectors."""
        if isinstance(value, list):
            return [self.links(v) for v in value]
        if not isinstance(value, dict):
            return value
        result = {k: self.links(v) for k, v in value.items()}
        for key in ("status_url", "process_status_url", "download_url"):
            if isinstance(result.get(key), str):
                url = urlsplit(result[key])
                if url.path.startswith(BASE + "/"):
                    path = PREFIX + url.path[len(BASE):]
                    result[key] = str(self.n.request.base_url).rstrip("/") + urlunsplit(("", "", path, url.query, url.fragment))
        return result

    async def convert(self, source):
        try:
            async for value in source:
                yield self.links(value)
        finally:
            await source.aclose()
