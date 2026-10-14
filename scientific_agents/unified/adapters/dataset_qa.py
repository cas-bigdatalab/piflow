"""Dataset QA projection into the existing unified routes."""
import asyncio

from fastapi import HTTPException
from pydantic import ValidationError

from ..schemas import options
from ...dataset_qa.contracts import Options, QAError


class DatasetQAAdapter:
    agent_id, label, session_path = "dataset_qa", "智能取数", None
    capabilities = ("delete_session", "tasks", "actions", "results", "session_search", "history_paging")

    def __init__(self, native):
        self.n = native

    @property
    def service(self):
        service = self.n.extension.session_services.get(self.agent_id)
        if service is None:
            raise HTTPException(503, "智能取数服务尚未就绪")
        return service

    async def call(self, function, *args, **kwargs):
        try:
            return await function(self.n.user, *args, **kwargs)
        except QAError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    def owns_session(self, sid):
        try:
            self.service.store.session(self.n.user, sid)
            return True
        except QAError:
            return False

    def task_session(self, tid):
        return self.service.store.task_session(self.n.user, tid)

    async def create_session(self, body):
        try:
            row = await asyncio.to_thread(self.service.store.create, self.n.user, body.title, body.request_id)
            return self.service.session_view(row)
        except QAError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    async def list_sessions(self, page, size):
        return await self.call(self.service.list_sessions, page, size)

    async def search_sessions(self, page, size, keyword):
        return await self.call(self.service.list_sessions, page, size, keyword)

    async def get_session(self, sid, after, limit):
        return await self.call(self.service.get_session, sid, after, limit)

    async def page_session(self, sid, after, limit, before, tail):
        return await self.call(self.service.get_session, sid, after, limit, before, tail)

    async def delete_session(self, sid):
        return await self.call(self.service.delete_session, sid)

    async def get_task(self, sid, tid):
        try:
            row = await asyncio.to_thread(self.service.store.task, self.n.user, sid, tid)
            return self.service.task_view(row)
        except QAError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    async def detail(self, sid, tid):
        return {"task": await self.get_task(sid, tid), "items": (await self.get_results(sid, tid))["items"]}

    async def execution_status(self, sid, tid, query):
        if query:
            raise HTTPException(422, "智能取数问答不支持执行节点参数")
        return await self.get_task(sid, tid)

    async def get_results(self, sid, tid):
        from ...dataset_qa.context import public_result
        await self.get_task(sid, tid)
        cards = await asyncio.to_thread(self.service.store.results, self.n.user, sid, tid)
        return {"items": [public_result(c) for c in cards]}

    async def stream_turn(self, sid, body):
        try:
            if body.attachments:
                raise QAError("unsupported_attachment", "当前问答暂不支持上传文件")
            values = options(body, {*Options.model_fields, "detail"})
            values.pop("detail", None)
            opts = Options.model_validate(values)
            async for value in self.service.stream(self.n.user, sid, body.user_request, body.request_id, opts, body.parent_task_id):
                yield value
        except (QAError, ValidationError, HTTPException) as exc:
            yield {"type": "error", "code": exc.status if isinstance(exc, QAError) else getattr(exc, "status_code", 422),
                "error_code": exc.code if isinstance(exc, QAError) else "invalid_parameters",
                "message": str(exc) if isinstance(exc, QAError) else str(exc.detail) if isinstance(exc, HTTPException) else "请求参数不符合接口约定"}
            yield {"type": "done", "status": "FAILED"}

    async def stream_action(self, sid, tid, body):
        if body.action != "cancel_task":
            raise HTTPException(422, "请通过聊天接口提交提问或选择；操作接口当前仅支持cancel_task")
        values = options(body, {"expected_version"})
        try:
            opts = Options.model_validate(values)
        except ValidationError as exc:
            raise HTTPException(422, "请求参数不符合接口约定") from exc
        task = await self.get_task(sid, tid)
        if opts.expected_version is not None and task["status"] != "CANCELLED":
            session = await asyncio.to_thread(self.service.store.session, self.n.user, sid)
            if opts.expected_version != session["version"]:
                raise HTTPException(409, "会话已更新，请刷新后重试")
        task = await self.call(self.service.cancel, sid, tid)
        session = await asyncio.to_thread(self.service.store.session, self.n.user, sid)
        yield {"type": "task", **task}
        yield {"type": "done", "task_id": tid, "status": task["status"], "version": session["version"]}
