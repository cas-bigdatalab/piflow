"""Persistent conversation runtime; every MCP tool follows the same path."""
import asyncio
from contextlib import aclosing
import json
import logging
import time
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, message_chunk_to_message
from pydantic import ValidationError

from .context import contains, encode, project, public_result, slice_result
from .contracts import QAError
from .dialogue import BUILTINS, INPUTS, Dialogue
from .execution import Execution, fingerprint
from .mcp import MCPGateway
from .persistence import Store
from .results import combine_results, evidence

log = logging.getLogger("flow.dataset_qa")

class DatasetQA:
    def __init__(self, engine, dialogue=None, gateway=None):
        self.store, self.gateway = Store(engine), gateway or MCPGateway()
        self.dialogue = dialogue or Dialogue(limits=self.gateway.limits)
        self.owner, self.jobs = uuid4().hex, {}
        self.summaries = {}
        self.summary_slot = asyncio.Semaphore(1)
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
        for job in list(self.summaries.values()):
            job.cancel()
        await asyncio.gather(*list(self.summaries.values()), return_exceptions=True)
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
        legacy_result_sent, previous_stage = False, None
        while True:
            task = await asyncio.to_thread(self.store.task, user, sid, tid)
            values = await asyncio.to_thread(self.store.replay, user, sid, tid, cursor)
            for value in values:
                cursor = value["event_seq"]
                if value["type"] not in {"stage", "message", "result", "interaction", "done"}:
                    continue
                if value["type"]=="message":
                    if not value.get("text"):
                        continue
                    value = {k: value[k] for k in ("type", "text", "task_id", "event_seq")}
                if value["type"]=="stage":
                    if value.get("status") in {"finished", "failed", "cancelled"}:
                        continue
                    stage = value["stage"]
                    if stage not in {"prepare", "execute", "answer"}:
                        if not stage.startswith("mcp_") and stage != "queued":
                            continue
                        stage = "prepare" if stage == "queued" else "execute"
                    signature = (stage, value.get("summary", ""))
                    if signature == previous_stage:
                        continue
                    previous_stage = signature
                    value = {"type": "stage", "stage": stage, "summary": signature[1],
                        "task_id": tid, "event_seq": cursor}
                if value["type"]=="result":
                    if "items" in value:
                        cards = value["items"]
                    else:
                        if legacy_result_sent:
                            continue
                        cards = await asyncio.to_thread(self.store.display_results, user, sid, tid)
                        legacy_result_sent = True
                    value = {"type": "result", "items": [public_result(card) for card in cards],
                        "task_id": tid, "event_seq": cursor}
                if value["type"]=="done" and value.get("status")=="FAILED" and "code" not in value:
                    saved = await asyncio.to_thread(self.store.task, user, sid, tid)
                    error = json.loads(saved["payload"]).get("error")
                    if error:
                        value.update(code=error.get("error_code", error.get("code")), message=error["message"])
                last_activity = time.monotonic()
                yield value
                if value["type"]=="done":
                    return
            if task["status"]!="RUNNING" and not values:
                session = await asyncio.to_thread(self.store.session, user, sid)
                value = {"type": "done", "task_id": tid, "status": task["status"],
                    "version": session["version"], "event_seq": cursor}
                error = json.loads(task["payload"]).get("error")
                if error:
                    value.update(code=error.get("error_code", error.get("code")), message=error["message"])
                yield value
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

    def _schedule_summary(self, user, sid):
        if self.stopping.is_set() or sid in self.summaries:
            return
        job = asyncio.create_task(self._summarize(user, sid))
        self.summaries[sid] = job
        job.add_done_callback(lambda _: self.summaries.pop(sid, None))

    async def _summarize(self, user, sid):
        started = time.monotonic()
        try:
            session = await asyncio.to_thread(self.store.session, user, sid)
            context = json.loads(session["context"])
            recent = await asyncio.to_thread(self.store.memory, user, sid, 0, None, 12, True)
            previous = context.get("summary_after", 0)
            older = await asyncio.to_thread(self.store.memory, user, sid, previous, recent[0]["id"] if recent else None, 24)
            if len(older)<8 or session["active_task_id"] or self.summary_slot.locked():
                return
            async with self.summary_slot, asyncio.timeout(self.gateway.limits.summary_timeout):
                summary = await self.dialogue.summarize(context.get("summary", ""), older)
            await asyncio.to_thread(self.store.save_summary, user, sid, previous, summary, older[-1]["id"])
            log.info("Conversation summary: session=%s elapsed=%.3fs", sid, time.monotonic()-started)
        except QAError:
            pass  # The session may have been deleted while the summary ran.
        except Exception:
            log.warning("Conversation summary deferred: session=%s", sid, exc_info=True)

    async def _context(self, user, sid, tid, options):
        session = await asyncio.to_thread(self.store.session, user, sid)
        saved = json.loads(session["context"])
        context = {key: saved[key] for key in ("memory", "summary", "summary_after", "result_id", "pending", "tools") if key in saved}
        memory = context.setdefault("memory", {})
        history = await asyncio.to_thread(self.store.memory, user, sid, 0, None, 12, True)
        older = await asyncio.to_thread(self.store.memory, user, sid, context.get("summary_after", 0), history[0]["id"] if history else None, 24)
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
        if older:
            model_context["unsummarized_history"] = older
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

    async def _reply(self, user, sid, tid, messages, definitions, answer=None, phase=None):
        started, first_chunk = time.monotonic(), None
        full, buffer, flushed, sent = None, "", time.monotonic(), False
        try:
            async with asyncio.timeout(self.gateway.limits.model_timeout), aclosing(self.dialogue.respond(messages, definitions)) as response:
                async for chunk in response:
                    if first_chunk is None:
                        first_chunk = time.monotonic()-started
                    full = chunk if full is None else full+chunk
                    if answer is None:
                        continue  # Planning text and tool-call fragments stay internal.
                    content = str(chunk.text)[:max(0, 16000-len(answer["text"]))]
                    if content:
                        await phase("answer", "正在生成答复")
                        if not sent and not buffer and answer["text"]:
                            content = "\n\n"+content
                        answer["text"] += content
                        buffer += content
                    if buffer and (not sent or len(buffer)>=40 or time.monotonic()-flushed>=0.1):
                        await self._write(user, sid, tid, {"type": "message", "text": buffer})
                        buffer, flushed, sent = "", time.monotonic(), True
        except TimeoutError as exc:
            raise QAError("model_timeout", "模型响应超时，请稍后重试", 504) from exc
        finally:
            log.info("Model request: task=%s tools=%s final=%s first_chunk=%s elapsed=%.3fs",
                tid, len(definitions), answer is not None, first_chunk, time.monotonic()-started)
        if buffer:
            await self._write(user, sid, tid, {"type": "message", "text": buffer})
        reply = message_chunk_to_message(full) if full is not None else AIMessage(content="")
        if reply.invalid_tool_calls:
            raise QAError("invalid_tool_call", "模型返回的工具参数无法解析，请重新表述请求", 502)
        return reply

    async def _deliver(self, user, sid, tid, arguments, payload):
        values = INPUTS["deliver_results"][0].model_validate(arguments)
        result_ids = list(dict.fromkeys(values.result_ids))
        cards = await asyncio.to_thread(self.store.selected_results, user, sid, result_ids)
        if values.merge_path is not None:
            if not cards:
                raise QAError("invalid_delivery", "合并结果时必须选择已保存的结果")
            cards = [combine_results(cards, values.merge_path, tid+":delivery", values.title)]
        if len(encode({"items": [public_result(card) for card in cards]}).encode("utf-8")) > self.gateway.limits.result_bytes:
            raise QAError("result_too_large", "展示结果超过运行预算，请缩小交付范围")
        if values.merge_path is not None:
            await self._write(user, sid, tid, card=cards[0])
        payload["delivery"] = [card["result_id"] for card in cards]
        await self._write(user, sid, tid, payload=payload)
        return {"result_ids": payload["delivery"]}

    async def _fallback_delivery(self, user, sid, tid, payload, execution, required=False):
        if "delivery" in payload:
            return
        cards = {card["result_id"]: card for card in execution.cards.values()}
        if len(cards)==1:
            await self._deliver(user, sid, tid, {"result_ids": list(cards)}, payload)
        elif required:
            raise QAError("invalid_delivery", "未明确选择需要展示的结果；原始工具结果已保存")

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

    async def _final_reply(self, user, sid, tid, messages, answer, phase, reason=None):
        await phase("answer", "正在生成答复")
        saved = await asyncio.to_thread(self.store.task, user, sid, tid)
        ids = json.loads(saved["payload"]).get("delivery", [])
        cards = await asyncio.to_thread(self.store.selected_results, user, sid, ids)
        if reason:
            notice = str(reason)+"。本轮已停止继续调用工具。\n\n"
            answer["text"] += notice
            await self._write(user, sid, tid, {"type": "message", "text": notice})
        instructions = (str(messages[0].content)+"\nTool use is over. Write only the final user-facing reply, "
            "without internal planning or another tool call. Use actual evidence, distinguish unfinished work, "
            "and only refer to display cards listed in final_delivery. Do not claim unperformed work succeeded. "
            "When naming an object from returned data, use that object's own non-empty title field verbatim. "
            "Do not substitute identifiers, source/provider labels, or enclosing card titles for object names. "
            "If its title is absent or empty, state that the name was not provided and distinguish it using "
            "a supplied identifier; do not infer or invent a name.")
        delivery, _ = project({"final_delivery": [self._evidence(card) for card in cards],
            "stop_reason": str(reason) if reason else None}, self.gateway.limits.result_chars)
        context = json.loads(messages[1].content)
        context.pop("evidence", None)
        context.pop("mcp_servers", None)
        history = []
        for message in messages[3:]:
            if isinstance(message, ToolMessage):
                value = json.loads(message.content)
                if value.get("result_id") in ids:
                    message = message.model_copy(update={"content": encode({"result_id": value["result_id"]})})
            history.append(message)
        final_messages = [messages[0].model_copy(update={"content": instructions}), HumanMessage(encode(context)),
            messages[2], *history, HumanMessage(encode(delivery))]
        try:
            reply = await self._reply(user, sid, tid, final_messages, [], answer, phase)
            if reply.tool_calls:
                raise QAError("invalid_tool_call", "正式答复阶段返回了工具调用", 502)
            if not answer["text"].strip():
                answer["text"] = "请查看下方结果。" if cards else "请补充需要处理的问题。"
                await self._write(user, sid, tid, {"type": "message", "text": answer["text"]})
        except Exception:
            # Keep the original stop reason and saved results when the model
            # cannot summarize them. Never resume tool use to recover a summary.
            if reason is None:
                raise
            log.warning("Final response unavailable: task=%s", tid, exc_info=True)

    async def _run(self, user, sid, tid, payload, options):
        started = time.monotonic()
        answer, acquired, results = {"text": ""}, False, 0
        messages, active_phase = None, None
        execution, limits = Execution(), self.gateway.limits

        async def phase(stage, title=""):
            nonlocal active_phase
            if active_phase == (stage, title):
                return
            active_phase = (stage, title) if stage else None
            if stage:
                await self._write(user, sid, tid, {"type": "stage", "stage": stage,
                    "summary": title})

        try:
            await phase("prepare", "正在理解请求")
            if self.slots.locked():
                await phase("prepare", "正在等待可用处理资源")
            await self.slots.acquire()
            log.info("Task queue: task=%s elapsed=%.3fs", tid, time.monotonic()-started)
            acquired = True
            context, model_context, parent = await self._context(user, sid, tid, options)
            if parent:
                payload["parent_task_id"] = parent
                await self._write(user, sid, tid, payload=payload)
            reason, ready, recovering = None, False, False
            async with self.gateway.session() as tools:
                def action_feedback(error):
                    actions = {definition["function"]["name"] for definition in BUILTINS
                        if definition["function"]["name"]!="deliver_results" or execution.can_deliver}
                    return execution.feedback(error, actions | set(tools.loaded))

                tools.prime(payload["message"], context.get("tools", []))
                model_context["mcp_servers"] = tools.list_servers(payload["message"])
                messages = self.dialogue.messages(payload["message"], model_context)
                for _ in range(limits.max_rounds):
                    if execution.calls>=limits.max_calls and not execution.can_deliver:
                        reason = QAError("step_limit", "工具调用达到本轮预算，请缩小请求范围")
                        break
                    rejection = None
                    definitions = [definition for definition in BUILTINS
                        if definition["function"]["name"]!="deliver_results" or execution.can_deliver]
                    definitions.extend(tools.definitions())
                    advertised = {value["function"]["name"] for value in definitions}
                    reply = await self._reply(user, sid, tid, messages, definitions)
                    if reply.tool_calls:
                        if any(not call.get("id") for call in reply.tool_calls):
                            raise QAError("invalid_tool_call", "工具调用缺少关联标识", 503)
                        if len({call["id"] for call in reply.tool_calls}) != len(reply.tool_calls):
                            raise QAError("invalid_tool_call", "工具调用关联标识重复", 503)
                        try:
                            reply = self.dialogue.decode_actions(reply)
                        except QAError as exc:
                            rejection = exc
                    else:
                        try:
                            execution.require_result()
                            await self._fallback_delivery(user, sid, tid, payload, execution, required=True)
                        except QAError as exc:
                            if exc.code not in {"mcp_required", "invalid_delivery"}:
                                raise
                            rejection = exc
                    if rejection:
                        messages.append(reply)
                        feedback = action_feedback(rejection)
                        if reply.tool_calls:
                            messages.extend(ToolMessage(content=encode(feedback), tool_call_id=call["id"], name=call["name"])
                                for call in reply.tool_calls)
                        else:
                            messages.append(HumanMessage(encode({"runtime_feedback": feedback})))
                        reason = execution.correct(rejection, limits.max_corrections)
                        log.info("Action correction: task=%s error=%s corrections=%s stopped=%s",
                            tid, rejection.code, execution.corrections, reason is not None)
                        if reason:
                            break
                        recovering = True
                        continue
                    if not reply.tool_calls:
                        await self._final_reply(user, sid, tid, messages, answer, phase)
                        await asyncio.to_thread(self.store.finish, user, sid, tid, "COMPLETED", message=answer["text"])
                        return
                    messages.append(reply)
                    for call in reply.tool_calls:
                        name, arguments = call["name"], call["args"]
                        key = fingerprint([name, arguments])
                        tool = tools.loaded.get(name)
                        interaction = None
                        rejected = False
                        log.info("Agent action: task=%s name=%s allowed=%s", tid, name, name in advertised)
                        if ready:
                            value = {"executed": False, "message": "交付范围已确定，未继续执行工具"}
                        elif reason or (execution.calls>=limits.max_calls and (name!="deliver_results" or name not in advertised)):
                            reason = reason or QAError("step_limit", "工具调用达到本轮预算，请缩小请求范围")
                            value = {"error": reason.code, "message": str(reason), "executed": False}
                        elif name not in advertised:
                            execution.calls += 1
                            rejection = QAError("tool_not_loaded", "当前动作尚未开放，请从当前提供的动作中选择")
                            if name=="deliver_results":
                                if execution.failures:
                                    reason = next(iter(execution.failures.values()))
                                elif not execution.cards:
                                    rejection = QAError("mcp_required", "本轮尚未通过MCP执行任务，不能直接交付结果")
                            value = action_feedback(rejection)
                            rejected = True
                        elif name=="deliver_results" and not reason:
                            try:
                                execution.require_result()
                                value = await self._deliver(user, sid, tid, arguments, payload)
                                ready = True
                            except (QAError, ValidationError) as exc:
                                value = {"error": exc.code if isinstance(exc, QAError) else "invalid_parameters",
                                    "message": str(exc) if isinstance(exc, QAError) else "交付参数不符合定义"}
                                if isinstance(exc, QAError) and (exc.code=="mcp_required" or execution.failures):
                                    reason = exc
                                elif isinstance(exc, ValidationError) or exc.code in {"invalid_delivery", "invalid_pointer", "result_not_found"}:
                                    rejection = exc if isinstance(exc, QAError) else QAError("invalid_parameters", "交付参数不符合定义")
                                    value = action_feedback(rejection)
                                    rejected = True
                        elif (recovering or rejection is not None) and tool and (completed := execution.completed(key)) is not None:
                            value = {**self._evidence(completed), "executed": False,
                                "guidance": "This operation already completed in this turn. Use the saved result; no additional execution took place."}
                        elif key in execution.cached and name in advertised:
                            value = execution.cached[key]
                        else:
                            execution.calls += 1
                            call_started = time.monotonic()
                            try:
                                if name in INPUTS:
                                    value = await self._builtin(user, sid, tid, name, arguments, tools, context)
                                    if name=="request_input":
                                        interaction = context["pending"]
                                else:
                                    await phase("execute", "正在处理："+tool.title)
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
                                    execution.failures.pop(name, None)
                                    recovering = False
                                    reference = {"server": tool.server, "name": tool.name}
                                    context["tools"] = [reference, *[ref for ref in context.get("tools", []) if ref!=reference]][:4]
                                    await self._write(user, sid, tid, context=context)
                                    if execution.reusable(tool):
                                        execution.cached[key] = value
                            except (QAError, ValidationError) as exc:
                                log.info("Tool request rejected: task=%s tool=%s code=%s",
                                    tid, name, exc.code if isinstance(exc, QAError) else "invalid_parameters")
                                value = {"error": exc.code if isinstance(exc, QAError) else "invalid_parameters",
                                    "message": str(exc) if isinstance(exc, QAError) else "参数不符合工具定义"}
                                if isinstance(exc, QAError) and exc.detail:
                                    value["detail"] = exc.detail
                                if isinstance(exc, ValidationError) or exc.code in {"invalid_parameters", "invalid_pointer", "result_not_found", "memory_too_large"}:
                                    rejection = exc if isinstance(exc, QAError) else QAError("invalid_parameters", "参数不符合工具定义")
                                    value = action_feedback(rejection)
                                    rejected = True
                                elif tool and isinstance(exc, QAError):
                                    execution.failures[name] = exc
                                if isinstance(exc, QAError) and exc.code=="mcp_unavailable":
                                    execution.cached[key] = value  # No repeated connection attempts in this turn.
                                if isinstance(exc, QAError) and (exc.code in {"execution_unknown", "result_too_large"}
                                        or (exc.code=="tool_failed" and not (tool and tool.annotations.get("idempotentHint") is True))):
                                    reason = exc
                            finally:
                                log.info("Tool request: task=%s tool=%s mcp=%s elapsed=%.3fs",
                                    tid, name, tool is not None, time.monotonic()-call_started)
                        if interaction:
                            answer["text"] = (answer["text"]+"\n"+interaction["question"]).strip()
                            await asyncio.to_thread(self.store.finish, user, sid, tid, "WAITING_INPUT",
                                message=answer["text"], interaction=interaction)
                            return
                        if not rejected:
                            progress = execution.observe(key, value)
                            execution.stalled = 0 if progress else execution.stalled+1
                            if not progress:
                                value = {**value, "repeated": True,
                                    "guidance": "This call provided no new evidence. Use the saved result, change the request if needed, or answer the user."}
                        messages.append(ToolMessage(content=encode(value), tool_call_id=call["id"], name=name))
                        if not rejected and not ready and not reason and execution.stalled>=limits.max_stalled_calls:
                            reason = QAError("no_progress", "连续调用没有获得新信息")
                    if ready:
                        await self._final_reply(user, sid, tid, messages, answer, phase)
                        await asyncio.to_thread(self.store.finish, user, sid, tid, "COMPLETED", message=answer["text"])
                        return
                    if rejection and not reason:
                        reason = execution.correct(rejection, limits.max_corrections)
                        log.info("Action correction: task=%s error=%s corrections=%s stopped=%s",
                            tid, rejection.code, execution.corrections, reason is not None)
                    recovering = recovering or (rejection is not None and reason is None)
                    if reason:
                        break
                reason = reason or QAError("step_limit", "处理达到本轮预算，请缩小请求范围")
                # Delivery selection never executes MCP; final text has no tools.
                if results and "delivery" not in payload:
                    try:
                        await self._fallback_delivery(user, sid, tid, payload, execution)
                    except Exception:
                        log.warning("Partial delivery unavailable: task=%s", tid, exc_info=True)
                await self._final_reply(user, sid, tid, messages, answer, phase, reason)
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
                "message": str(exc) if isinstance(exc, QAError) else "服务暂不可用，请稍后重试"}
            try:
                await asyncio.to_thread(self.store.finish, user, sid, tid, "FAILED", message=answer["text"], error=error)
            except QAError:
                pass
        finally:
            if acquired:
                self.slots.release()
                if not asyncio.current_task().cancelling():
                    self._schedule_summary(user, sid)
            log.info("Agent task finished: task=%s elapsed=%.3fs", tid, time.monotonic()-started)
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
        if sid in self.summaries:
            self.summaries[sid].cancel()
        if tid in self.jobs:
            self.jobs[tid].cancel()
        await self._notify()
        return {"session_id": sid, "deleted": True}
