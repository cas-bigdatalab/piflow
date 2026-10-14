"""Persistent conversation runtime; every MCP tool follows the same path."""
import asyncio
from contextlib import aclosing, asynccontextmanager
import json
import logging
import time
from uuid import uuid4

from langchain_core.messages import AIMessage, ToolMessage, message_chunk_to_message
from pydantic import ValidationError

from .context import contains, encode, project, public_result, slice_result
from .contracts import QAError
from .dialogue import BUILTINS, INPUTS, Dialogue
from .execution import Execution, fingerprint
from .mcp import MCPGateway
from .persistence import Store
from .results import evidence

log = logging.getLogger(__name__)

class DatasetQA:
    def __init__(self, engine, dialogue=None, gateway=None):
        self.store, self.gateway = Store(engine), gateway or MCPGateway()
        self.dialogue = dialogue or Dialogue(limits=self.gateway.limits)
        self.owner, self.jobs = uuid4().hex, {}
        self.stopping, self.changed = asyncio.Event(), asyncio.Condition()
        self.ticker, self.slots = None, asyncio.Semaphore(8)

    async def start(self):
        await asyncio.to_thread(self.store.heartbeat, self.owner, [])

        async def heartbeat():
            while not self.stopping.is_set():
                try:
                    await asyncio.wait_for(self.stopping.wait(), 10)
                except TimeoutError:
                    try:
                        running = await asyncio.to_thread(self.store.heartbeat, self.owner, list(self.jobs))
                        for tid, job in list(self.jobs.items()):
                            if tid not in running:
                                job.cancel()
                    except Exception:
                        log.exception("Agent heartbeat failed")
        self.ticker = asyncio.create_task(heartbeat())

    async def close(self):
        self.stopping.set()
        if self.ticker:
            await self.ticker
        for job in list(self.jobs.values()):
            job.cancel()
        await asyncio.gather(*list(self.jobs.values()), return_exceptions=True)
        if hasattr(self.dialogue, "close"):
            await self.dialogue.close()

    @staticmethod
    def session_view(row):
        return {"session_id": row["id"], "agent_id": "dataset_qa", "title": row["title"],
            "version": row["version"], "create_time": row["created_at"], "update_time": row["updated_at"]}

    @staticmethod
    def task_view(row):
        result = {"task_id": row["id"], "status": row["status"]}
        if row["stage"]:
            result["current_stage"] = row["stage"]
        if row["status"] in {"RUNNING", "WAITING_INPUT"}:
            result["available_actions"] = [{"action": "cancel_task", "label": "停止"}]
        error = json.loads(row["payload"]).get("error")
        if error:
            result["error_message"] = error["message"]
        return result

    async def list_sessions(self, user, page, size, keyword=""):
        rows, total = await asyncio.to_thread(self.store.list_sessions, user, page, size, keyword)
        return {"items": [self.session_view(r) for r in rows],
                "pagination": {"total": total, "pageNum": page, "pageSize": size}}

    async def get_session(self, user, sid, after=0, limit=100, before=None, tail=False):
        def read():
            session, rows, tasks, more = self.store.snapshot(user, sid, after, limit, before, tail)
            context = json.loads(session["context"])
            items = []
            for row in rows:
                if row["kind"]=="INTERACTION":
                    continue  # Old stored buttons are not active interactions.
                payload = json.loads(row["payload"])
                if row["kind"]=="RESULT_CARD":
                    payload = public_result(payload)
                else:
                    payload.pop("mode", None)
                items.append({"item_id": row["id"], "task_id": row["task_id"], "item_type": row["kind"],
                    "create_time": row["created_at"], "payload": payload})
            result = {"session": self.session_view(session), "tasks": [self.task_view(t) for t in tasks],
                "items": items, "has_more": more}
            if tail or before is not None:
                result["before_item_id"] = rows[0]["id"] if rows else before
            else:
                result["next_after_item_id"] = rows[-1]["id"] if rows else after
            if context.get("memory"):
                result["context"] = context["memory"]
            # Current interaction is kept once, independently of history paging.
            result["interaction"] = context.get("pending")
            return result
        return await asyncio.to_thread(read)

    async def _notify(self):
        async with self.changed:
            self.changed.notify_all()

    async def stream(self, user, sid, message, request_id, options, parent_task_id=None):
        if not message.strip() or len(message)>12000:
            raise QAError("invalid_parameters", "问题须为1至12000个字符")
        if parent_task_id:
            await asyncio.to_thread(self.store.task, user, sid, parent_task_id)
        payload = {"message": message, "params": options.model_dump(exclude={"after_event_seq", "expected_version"}),
                   "parent_task_id": parent_task_id}
        task, created = await asyncio.to_thread(self.store.submit, user, sid, request_id, payload,
            options.expected_version, self.owner, options.after_event_seq)
        tid = task["id"]
        if created:
            job = asyncio.create_task(self._run(user, sid, tid, payload, options))
            self.jobs[tid] = job
            job.add_done_callback(lambda _: self.jobs.pop(tid, None))
        cursor, last_activity = options.after_event_seq, time.monotonic()
        while True:
            task = await asyncio.to_thread(self.store.task, user, sid, tid)
            values = await asyncio.to_thread(self.store.replay, user, sid, tid, cursor)
            for value in values:
                cursor = value["event_seq"]
                if value["type"]=="message" and not value.get("text"):
                    continue  # Also suppress empty messages in older stored streams.
                if value["type"]=="result":
                    value = {"type": "result", **public_result(value), "task_id": tid, "event_seq": cursor}
                last_activity = time.monotonic()
                yield value
                if value["type"]=="done":
                    return
            if task["status"]!="RUNNING" and not values:
                session = await asyncio.to_thread(self.store.session, user, sid)
                yield {"type": "done", "task_id": tid, "status": task["status"], "version": session["version"]}
                return
            if values:
                continue  # Drain persisted events without a polling delay.
            remaining = self.gateway.limits.heartbeat_seconds-(time.monotonic()-last_activity)
            if remaining<=0:
                last_activity = time.monotonic()
                yield None
                continue
            try:
                async with self.changed:
                    await asyncio.wait_for(self.changed.wait(), min(1, remaining))
            except TimeoutError:
                pass

    async def _write(self, user, sid, tid, data=None, **values):
        if not await asyncio.to_thread(self.store.write, user, sid, tid, data, **values):
            raise asyncio.CancelledError()
        await self._notify()

    @asynccontextmanager
    async def _stage(self, user, sid, tid, stage, title, resume_stage=None):
        event = {"type": "stage", "stage": stage}
        await self._write(user, sid, tid, {**event, "status": "started", "summary": "正在处理："+title})
        try:
            yield
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            summary = str(exc) if isinstance(exc, QAError) else "参数不符合工具定义" if isinstance(exc, ValidationError) else "当前步骤处理失败"
            await self._write(user, sid, tid, {**event, "status": "failed", "summary": summary}, stage=resume_stage)
            raise
        else:
            await self._write(user, sid, tid, {**event, "status": "finished", "summary": "已完成："+title}, stage=resume_stage)

    async def _context(self, user, sid, tid, options):
        session = await asyncio.to_thread(self.store.session, user, sid)
        saved = json.loads(session["context"])
        context = {key: saved[key] for key in ("memory", "summary", "summary_after", "result_id", "pending") if key in saved}
        memory = context.setdefault("memory", {})
        history = await asyncio.to_thread(self.store.memory, user, sid, 0, None, 12, True)
        older = await asyncio.to_thread(self.store.memory, user, sid, context.get("summary_after", 0), history[0]["id"] if history else None)
        if len(older)>=8:
            try:
                context["summary"] = await self.dialogue.summarize(context.get("summary", ""), older)
                context["summary_after"] = older[-1]["id"]
            except Exception:
                log.warning("Conversation summary deferred", exc_info=True)
        if options.result_id:
            context["result_id"] = options.result_id
        evidence = await asyncio.to_thread(self.store.results, user, sid)
        if context.get("result_id"):
            pinned = await asyncio.to_thread(self.store.results, user, sid, None, context["result_id"])
            if not pinned:
                raise QAError("result_not_found", "当前会话中不存在此结果", 404)
            evidence = [pinned[0], *[c for c in reversed(evidence) if c["result_id"]!=pinned[0]["result_id"]]]
        else:
            evidence = list(reversed(evidence))
        if options.selected_dataset_id:
            if not any(contains(c.get("data"), options.selected_dataset_id) for c in evidence):
                raise QAError("reference_not_found", "选择不属于当前会话的结果", 404)
            memory["selected_dataset_id"] = options.selected_dataset_id
        model_context = {"memory": memory, "pending": context.get("pending"), "summary": context.get("summary", ""),
            "evidence": [self._evidence(c) for c in evidence[:3]], "history": history}
        previous = context.pop("pending", None)
        if previous:
            await asyncio.to_thread(self.store.finish, user, sid, previous["task_id"], "COMPLETED")
            payload_parent = previous["task_id"]
        else:
            payload_parent = None
        await self._write(user, sid, tid, context=context)
        return context, model_context, payload_parent

    async def _read_result(self, user, sid, values):
        if values.result_id is None:
            if values.path:
                raise QAError("invalid_parameters", "指定path时须同时提供result_id")
            limit = min(values.limit, 8)
            items, more = await asyncio.to_thread(self.store.result_refs, user, sid, values.offset, limit)
            result = {"items": items}
            if more:
                result["next_offset"] = values.offset+limit
            return result
        cards = await asyncio.to_thread(self.store.results, user, sid, None, values.result_id)
        if not cards:
            raise QAError("result_not_found", "当前会话中不存在此结果", 404)
        data, more = slice_result(cards[0].get("data"), values.path, values.offset, values.limit)
        data, truncated = project(data, self.gateway.limits.result_chars)
        result = {"result_id": values.result_id, "data": data}
        if more:
            result["next_offset"] = values.offset+values.limit
        if truncated:
            result["truncated"] = True
        if cards[0].get("content"):
            result["content"] = self._evidence(cards[0])["content"]
        return result

    def _evidence(self, card):
        return evidence(card, self.gateway.limits.result_chars)

    async def _reply(self, user, sid, tid, messages, definitions, answer, phase):
        log.debug("Model request: task=%s tools=%s", tid, len(definitions))
        full, buffer, flushed, sent = None, "", time.monotonic(), False
        async with aclosing(self.dialogue.respond(messages, definitions)) as response:
            async for chunk in response:
                full = chunk if full is None else full+chunk
                content = str(chunk.text)[:max(0, 16000-len(answer["text"]))]
                if content:
                    await phase("answer", "生成答复")
                    if not sent and not buffer and answer["text"]:
                        content = "\n\n"+content
                    answer["text"] += content
                    buffer += content
                if buffer and (not sent or len(buffer)>=40 or time.monotonic()-flushed>=0.1):
                    await self._write(user, sid, tid, {"type": "message", "message_id": tid, "text": buffer, "mode": "append"})
                    buffer, flushed, sent = "", time.monotonic(), True
        if buffer:
            await self._write(user, sid, tid, {"type": "message", "message_id": tid, "text": buffer, "mode": "append"})
        reply = message_chunk_to_message(full) if full is not None else AIMessage(content="")
        if reply.invalid_tool_calls:
            raise QAError("invalid_tool_call", "模型返回的工具参数无法解析，请重新表述请求", 502)
        return reply

    async def _builtin(self, user, sid, tid, name, arguments, tools, context):
        values = INPUTS[name][0].model_validate(arguments)
        if name=="list_mcp_servers":
            return tools.list_servers(**values.model_dump())
        if name=="load_mcp_tools":
            return await tools.load(**values.model_dump())
        if name=="read_result":
            return await self._read_result(user, sid, values)
        if name=="remember":
            memory = {**context.get("memory", {}), **values.values}
            if len(encode(memory))>4096:
                raise QAError("memory_too_large", "结构化记忆超过运行预算")
            context["memory"] = {k: v for k, v in memory.items() if v is not None}
            await self._write(user, sid, tid, context=context)
            return {"saved": True}
        pending = {"task_id": tid, "question": values.question}
        if values.options:
            pending["options"] = values.options
        context["pending"] = pending
        await self._write(user, sid, tid, context=context)
        return {"waiting": True}

    async def _final_reply(self, user, sid, tid, messages, answer, phase, reason):
        await phase("answer", "整理已有结果与未完成事项")
        notice = ("\n\n" if answer["text"] else "")+str(reason)+"。本轮已停止继续调用工具，已取得的结果仍可查看。\n\n"
        answer["text"] += notice
        await self._write(user, sid, tid, {"type": "message", "message_id": tid, "text": notice, "mode": "append"})
        instructions = (str(messages[0].content)+"\nTool use has stopped. Reason: "+str(reason)+
            ". Summarize available evidence and identify unfinished work. Do not claim unperformed work succeeded. No more tools are available.")
        final_messages = [messages[0].model_copy(update={"content": instructions}), *messages[1:]]
        try:
            reply = await self._reply(user, sid, tid, final_messages, [], answer, phase)
            if reply.tool_calls:
                log.warning("Model requested tools during finalization: task=%s", tid)
        except Exception:
            # Keep the original stop reason and saved results when the model
            # cannot summarize them. Never resume tool use to recover a summary.
            log.warning("Final response unavailable: task=%s", tid, exc_info=True)

    async def _run(self, user, sid, tid, payload, options):
        answer, acquired, results = {"text": ""}, False, 0
        messages, active_phase = None, None
        execution, limits = Execution(), self.gateway.limits

        async def phase(stage, title=""):
            nonlocal active_phase
            if active_phase and active_phase[0]==stage:
                return
            if active_phase:
                previous, label = active_phase
                await self._write(user, sid, tid, {"type": "stage", "stage": previous,
                    "status": "finished", "summary": "已结束："+label})
            active_phase = (stage, title) if stage else None
            if stage:
                await self._write(user, sid, tid, {"type": "stage", "stage": stage,
                    "status": "started", "summary": title})

        try:
            await self._write(user, sid, tid, {"type": "task", **self.task_view(await asyncio.to_thread(self.store.task, user, sid, tid))})
            if self.slots.locked():
                async with self._stage(user, sid, tid, "queued", "等待可用处理资源"):
                    await self.slots.acquire()
                    acquired = True
            else:
                await self.slots.acquire()
                acquired = True
            await phase("prepare", "理解需求")
            context, model_context, parent = await self._context(user, sid, tid, options)
            messages = self.dialogue.messages(payload["message"], model_context)
            if parent:
                payload["parent_task_id"] = parent
                await self._write(user, sid, tid, payload=payload)
            reason = None
            async with self.gateway.session() as tools:
                for _ in range(limits.max_rounds):
                    definitions = [*BUILTINS, *tools.definitions()]
                    advertised = {value["function"]["name"] for value in definitions}
                    reply = await self._reply(user, sid, tid, messages, definitions, answer, phase)
                    if not reply.tool_calls:
                        if not answer["text"].strip():
                            await phase("answer", "生成答复")
                            answer["text"] = "请查看结果卡片。" if results else "请补充需要处理的问题。"
                            await self._write(user, sid, tid, {"type": "message", "message_id": tid,
                                "text": answer["text"], "mode": "replace"})
                        await phase(None)
                        await asyncio.to_thread(self.store.finish, user, sid, tid, "COMPLETED", message=answer["text"])
                        return
                    if any(not call.get("id") for call in reply.tool_calls):
                        raise QAError("invalid_tool_call", "工具调用缺少关联标识", 503)
                    if len({call["id"] for call in reply.tool_calls}) != len(reply.tool_calls):
                        raise QAError("invalid_tool_call", "工具调用关联标识重复", 503)
                    messages.append(reply)
                    await phase("execute", "获取所需结果")
                    for call in reply.tool_calls:
                        name, arguments = call["name"], call["args"]
                        key = fingerprint([name, arguments])
                        tool = tools.loaded.get(name)
                        interaction = None
                        log.debug("Tool request: task=%s tool=%s cached=%s", tid, name, key in execution.cached)
                        if reason or execution.calls>=limits.max_calls:
                            reason = reason or QAError("step_limit", "工具调用达到本轮预算，请缩小请求范围")
                            value = {"error": reason.code, "message": str(reason), "executed": False}
                        elif key in execution.cached and name in advertised:
                            value = execution.cached[key]
                        else:
                            execution.calls += 1
                            try:
                                if name not in advertised:
                                    raise QAError("tool_not_loaded", "工具未加载，请先发现并加载定义")
                                if name in INPUTS:
                                    value = await self._builtin(user, sid, tid, name, arguments, tools, context)
                                    if name=="request_input":
                                        interaction = context["pending"]
                                else:
                                    async with self._stage(user, sid, tid, name, tool.title, resume_stage="execute"):
                                        tool, output = await tools.call(name, arguments)
                                        marker = (key, fingerprint(output.payload()))
                                        card = execution.cards.get(marker)
                                        if card is None:
                                            metadata = tool.meta.get("piflow", {})
                                            view = metadata.get("view_type", "tool_result") if isinstance(metadata, dict) else "tool_result"
                                            card = {"result_id": f"{tid}:{results}", "view_type": view,
                                                "title": f"{tool.server} · {tool.title}", **output.payload()}
                                            results += 1
                                            await self._write(user, sid, tid, card=card)
                                            execution.cards[marker] = card
                                        value = self._evidence(card)
                                        if execution.reusable(tool):
                                            execution.cached[key] = value
                            except (QAError, ValidationError) as exc:
                                log.info("Tool request rejected: task=%s tool=%s code=%s",
                                    tid, name, exc.code if isinstance(exc, QAError) else "invalid_parameters")
                                value = {"error": exc.code if isinstance(exc, QAError) else "invalid_parameters",
                                    "message": str(exc) if isinstance(exc, QAError) else "参数不符合工具定义"}
                                if isinstance(exc, QAError) and exc.detail:
                                    value["detail"] = exc.detail
                                if isinstance(exc, QAError) and exc.code=="mcp_unavailable":
                                    execution.cached[key] = value  # No repeated connection attempts in this turn.
                                if isinstance(exc, QAError) and (exc.code in {"execution_unknown", "result_too_large"}
                                        or (exc.code=="tool_failed" and not (tool and tool.annotations.get("idempotentHint") is True))):
                                    reason = exc
                        if interaction:
                            answer["text"] = (answer["text"]+"\n"+interaction["question"]).strip()
                            await phase(None)
                            await asyncio.to_thread(self.store.finish, user, sid, tid, "WAITING_INPUT",
                                message=answer["text"], interaction=interaction)
                            return
                        progress = execution.observe(key, value)
                        execution.stalled = 0 if progress else execution.stalled+1
                        if not progress:
                            value = {**value, "repeated": True,
                                "guidance": "This call provided no new evidence. Use the saved result, change the request if needed, or answer the user."}
                        messages.append(ToolMessage(content=encode(value), tool_call_id=call["id"], name=name))
                        if not reason and execution.stalled>=limits.max_stalled_calls:
                            reason = QAError("no_progress", "连续调用没有获得新信息")
                    if reason:
                        break
                reason = reason or QAError("step_limit", "处理达到本轮预算，请缩小请求范围")
                # Every pending call has a paired result, including skipped calls.
                # Finalization has its own model request with no advertised tools.
                await self._final_reply(user, sid, tid, messages, answer, phase, reason)
                await phase(None)
                await asyncio.to_thread(self.store.finish, user, sid, tid, "FAILED", message=answer["text"],
                    error={"code": reason.status, "error_code": reason.code, "message": str(reason)})
        except asyncio.CancelledError:
            try:
                await asyncio.to_thread(self.store.finish, user, sid, tid, "CANCELLED", message=answer["text"])
            except QAError:
                pass
        except Exception as exc:
            log.exception("Agent task failed: task=%s", tid)
            error = {"code": exc.status if isinstance(exc, QAError) else 503,
                "error_code": exc.code if isinstance(exc, QAError) else "service_unavailable",
                "message": str(exc) if isinstance(exc, QAError) else "服务暂不可用；已完成结果仍可查看"}
            try:
                if active_phase:
                    await self._write(user, sid, tid, {"type": "stage", "stage": active_phase[0],
                        "status": "failed", "summary": error["message"]})
                await asyncio.to_thread(self.store.finish, user, sid, tid, "FAILED", message=answer["text"], error=error)
            except QAError:
                pass
        finally:
            if acquired:
                self.slots.release()
            await self._notify()

    async def cancel(self, user, sid, tid):
        await asyncio.to_thread(self.store.task, user, sid, tid)
        await asyncio.to_thread(self.store.finish, user, sid, tid, "CANCELLED")
        if tid in self.jobs:
            self.jobs[tid].cancel()
        await self._notify()
        return self.task_view(await asyncio.to_thread(self.store.task, user, sid, tid))

    async def delete_session(self, user, sid):
        tid = await asyncio.to_thread(self.store.delete, user, sid)
        if tid in self.jobs:
            self.jobs[tid].cancel()
        await self._notify()
        return {"session_id": sid, "deleted": True}
