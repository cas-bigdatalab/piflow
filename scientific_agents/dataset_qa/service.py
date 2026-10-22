"""Persistent conversation runtime; every MCP tool follows the same path."""
import asyncio
from contextlib import aclosing, nullcontext
import json
import logging
import time
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, message_chunk_to_message
from pydantic import ValidationError

from .context import encode, project, public_result, slice_result
from .contracts import QAError
from .dialogue import BUILTINS, INPUTS, Dialogue
from .execution import Execution, fingerprint
from .operations import Operations
from .mcp import MCPGateway
from .persistence import Store
from .results import collection_paths, combine_results, evidence, evidence_group
from .references import all_references, apply_update, at_path, display_list, preview
from .runtime import Waiting

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
        context = {key: saved[key] for key in ("memory", "summary", "summary_after", "references", "pending", "tools") if key in saved}
        memory = context.setdefault("memory", {})
        history = await asyncio.to_thread(self.store.memory, user, sid, 0, None, 12, True, tid)
        state = context.setdefault("references", {})
        last = None
        if "references" not in saved:
            last = await asyncio.to_thread(self.store.latest_display, user, sid)
            if last and (reference := display_list(last)):
                state["candidates"] = reference
        source_evidence = []
        if options.result_id:
            pinned = await asyncio.to_thread(self.store.results, user, sid, None, options.result_id)
            if not pinned:
                raise QAError("result_not_found", "当前会话中不存在此结果", 404)
            if options.result_id not in {ref["result_id"] for ref in all_references(state)}:
                source_evidence = [evidence(pinned[0], 1800)]
        selection = options.selected_dataset_id or (memory.get("selected_dataset_id") if "references" not in saved and last else None)
        issue = None
        if selection:
            matches = await asyncio.to_thread(self.store.object_reference, user, sid, selection,
                all_references(state), options.result_id if options.selected_dataset_id else last["result_id"])
            if not matches and options.selected_dataset_id and options.result_id:
                matches = await asyncio.to_thread(self.store.object_reference, user, sid, selection, all_references(state))
                if matches:
                    issue = "Explicit selection conflicts with request_source; clarify the intended source before operating."
            if not matches and options.selected_dataset_id:
                raise QAError("reference_not_found", "选择不属于当前会话的结果", 404)
            if len(matches)==1 and not issue:
                state["current"] = matches[0]
            elif len(matches)>1 and options.selected_dataset_id:
                issue = issue or "Explicit selection matches multiple source records; resolve the intended record before operating."
        if options.selected_dataset_id:
            memory["selected_dataset_id"] = options.selected_dataset_id
        if not state and last and not source_evidence:
            source_evidence = [evidence(last, 1800)]
        model_context = {"memory": {key: value for key, value in memory.items() if key!="selected_dataset_id"},
            "pending": context.get("pending"), "summary": context.get("summary", ""),
            "references": await self._reference_view(user, sid, state), "evidence": source_evidence, "history": history}
        if options.result_id:
            model_context["request_source"] = options.result_id
        if issue:
            model_context["references"].pop("current", None)
            model_context["reference_issue"] = {"message": issue, "identifier": selection, "candidates": matches}
        previous = context.get("pending")
        if previous:
            payload_parent = previous["task_id"]
            waiting = await asyncio.to_thread(self.store.task, user, sid, payload_parent)
            operations = json.loads(waiting["payload"]).get("operations", [])
            if operations:
                model_context["pending"] = {**previous, "operations": Operations(operations).view()}
        else:
            payload_parent = None
        await self._write(user, sid, tid, context=context)
        return context, model_context, payload_parent

    async def _reference_view(self, user, sid, state):
        ids = list(dict.fromkeys(ref["result_id"] for ref in all_references(state)))
        if not ids:
            return {}
        cards = await asyncio.to_thread(self.store.selected_results, user, sid, ids)
        view = preview(state, {card["result_id"]: card for card in cards}, min(4000, self.gateway.limits.context_chars//4))
        if any(state.get(key) and key not in view for key in ("current", "candidates")):
            raise QAError("context_too_large", "对象来源引用超过上下文预算，请缩小请求范围")
        return view

    async def _validate_references(self, user, sid, state, patch, extra=()):
        cards = {card["result_id"]: card for card in extra}
        ids = list(dict.fromkeys(ref["result_id"] for ref in all_references(patch) if ref["result_id"] not in cards))
        if ids:
            cards.update((card["result_id"], card) for card in
                await asyncio.to_thread(self.store.selected_results, user, sid, ids))
        return apply_update(state, patch, cards)

    async def _read_result(self, user, sid, values):
        if values.result_id is None:
            if values.path:
                raise QAError("invalid_parameters", "指定path时须同时提供result_id")
            limit = min(values.limit, 8)
            items, more = await asyncio.to_thread(self.store.result_refs, user, sid, values.offset, limit)
            result = {"items": items}
            if more:
                result["next_offset"] = values.offset+limit
            saved = await asyncio.to_thread(self.store.session, user, sid)
            selected = json.loads(saved["context"]).get("references", {}).get("selected", [])
            if selected:
                result.update(selected=selected[values.offset:values.offset+limit], selected_total=len(selected))
                if values.offset+limit<len(selected):
                    result["selected_next_offset"] = values.offset+limit
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

    async def _reply(self, user, sid, tid, messages, definitions, answer=None, phase=None, waiting=None):
        started, first_chunk = time.monotonic(), None
        full, buffer, flushed, sent = None, "", time.monotonic(), False
        deadline = asyncio.get_running_loop().time()+self.gateway.limits.model_timeout
        try:
            async with (waiting.during("模型仍在处理本轮请求，请稍候。") if waiting else nullcontext()), aclosing(self.dialogue.respond(messages, definitions)) as response:
                while True:
                    try:
                        async with asyncio.timeout_at(deadline):
                            chunk = await anext(response)
                    except StopAsyncIteration:
                        break
                    except TimeoutError as exc:
                        raise QAError("model_timeout", "模型响应超时，请稍后重试", 504) from exc
                    except QAError:
                        raise
                    except (ValidationError, json.JSONDecodeError) as exc:
                        raise QAError("invalid_tool_call", "模型返回的工具参数无法解析", 502) from exc
                    except Exception as exc:
                        raise QAError("service_unavailable", "模型服务暂不可用，请稍后重试", 503,
                            detail={"phase": "model"}) from exc
                    if first_chunk is None:
                        first_chunk = time.monotonic()-started
                    try:
                        full = chunk if full is None else full+chunk
                    except (ValidationError, ValueError, TypeError) as exc:
                        raise QAError("invalid_tool_call", "模型返回的工具参数无法解析", 502) from exc
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
                        text, buffer = buffer, ""
                        await self._write(user, sid, tid, {"type": "message", "text": text})
                        flushed, sent = time.monotonic(), True
        finally:
            log.info("Model request: task=%s tools=%s final=%s first_chunk=%s elapsed=%.3fs",
                tid, len(definitions), answer is not None, first_chunk, time.monotonic()-started)
            if buffer:
                await self._write(user, sid, tid, {"type": "message", "text": buffer})
        try:
            if full is not None:
                self.dialogue.validate_calls(full)
            return message_chunk_to_message(full) if full is not None else AIMessage(content="")
        except (ValidationError, ValueError, TypeError) as exc:
            raise QAError("invalid_tool_call", "模型返回的工具参数无法解析", 502) from exc

    async def _notice(self, user, sid, tid, answer, text):
        text = ("\n\n" if answer["text"] else "")+text
        answer["text"] += text
        await self._write(user, sid, tid, {"type": "message", "text": text})

    async def _failure_reply(self, user, sid, tid, answer, reason, operations, payload):
        text = Execution.notice(reason, bool(payload.get("delivery")))
        summary = operations.notice(payload.get("delivery_sources", []))
        await self._notice(user, sid, tid, answer, text+("\n\n"+summary if summary else ""))

    async def _finish_task(self, user, sid, tid, payload, execution, answer, reason=None):
        reason = reason or execution.operations.error(payload.get("delivery_sources", []))
        error = {"code": reason.status, "error_code": reason.code, "message": Execution.notice(reason)} if reason else None
        await asyncio.to_thread(self.store.finish, user, sid, tid, "FAILED" if reason else "COMPLETED",
            message=answer["text"], error=error)

    async def _deliver(self, user, sid, tid, arguments, payload, execution=None, partial=False):
        values = INPUTS["deliver_results"][0].model_validate(arguments)
        result_ids = list(dict.fromkeys(values.result_ids))
        if execution is not None and "result_ids" not in values.model_fields_set:
            result_ids = list(dict.fromkeys(rid for item in execution.operations.items
                if item["state"]=="succeeded" and item["output"]=="result" for rid in execution.operations.result_ids(item)))
        if execution is not None:
            execution.operations.validate_delivery(result_ids, partial)
        cards = await asyncio.to_thread(self.store.selected_results, user, sid, result_ids)
        patch = values.references.model_dump(exclude_unset=True) if values.references else {}
        paths = values.merge_path
        if paths is None and len(cards)>1:
            if execution is None:
                raise QAError("invalid_delivery", "自动汇总需要本轮操作及执行来源")
            paths = collection_paths(cards, execution.operations)
        if paths is not None:
            if not cards:
                raise QAError("invalid_delivery", "合并结果时必须选择已保存的结果")
            if execution is not None and len({card.get("view_type") for card in cards})>1:
                raise QAError("invalid_delivery", "不同展示类型不能合并为一个结果；请保留必要产物并准确说明尚未完成的交付")
            cards = [combine_results(cards, paths, tid+":delivery", values.title)]
            if (candidate := patch.get("candidates")) and candidate["result_id"] in result_ids and candidate.get("path", "")==(
                    paths[candidate["result_id"]] if isinstance(paths, dict) else paths):
                patch["candidates"] = {**candidate, "result_id": cards[0]["result_id"], "path": ""}
        if cards and "candidates" not in patch and (candidate := display_list(cards[0])):
            patch["candidates"] = candidate
        if patch.get("candidates") and patch["candidates"]["result_id"] not in {card["result_id"] for card in cards}:
            raise QAError("invalid_parameters", "候选列表必须来自本次实际交付的结果")
        if patch:
            saved = await asyncio.to_thread(self.store.session, user, sid)
            await self._validate_references(user, sid, json.loads(saved["context"]).get("references", {}), patch, cards)
        if len(encode({"items": [public_result(card) for card in cards]}).encode("utf-8")) > self.gateway.limits.result_bytes:
            raise QAError("result_too_large", "展示结果超过运行预算，请缩小交付范围")
        if paths is not None:
            await self._write(user, sid, tid, card=cards[0])
        payload["delivery"] = [card["result_id"] for card in cards]
        if execution is not None:
            payload["delivery_sources"] = result_ids
            payload["operations"] = execution.operations.items
        if patch:
            payload["references"] = patch
        await self._write(user, sid, tid, payload=payload)
        return {"result_ids": payload["delivery"]}

    async def _fallback_delivery(self, user, sid, tid, payload, execution, required=False):
        if "delivery" in payload:
            return
        cards = list(dict.fromkeys(rid for item in execution.operations.items if item["state"]=="succeeded"
            and item["output"]=="result" for rid in execution.operations.result_ids(item)))
        if cards:
            try:
                await self._deliver(user, sid, tid, {"result_ids": cards}, payload, execution, partial=not required)
            except QAError as exc:
                if required or exc.code!="invalid_delivery":
                    raise
        elif not cards and execution.operations.items and all(item["output"]=="answer" for item in execution.operations.items):
            await self._deliver(user, sid, tid, {"result_ids": []}, payload, execution, partial=not required)
        elif required:
            raise QAError("invalid_delivery", "未明确选择需要展示的结果；原始工具结果已保存")

    async def _fast_delivery(self, user, sid, tid, payload, execution, context):
        """Skip selection only for an unambiguous, fully satisfied atomic request."""
        if not execution.finalizing or len(execution.operations.items)!=1 or execution.failures or context.get("reference_issue"):
            return False
        item = execution.operations.items[0]
        ids = execution.operations.result_ids(item)
        if not item.get("direct") or item["output"]!="result" or len(ids)!=1:
            return False
        card = next((card for card in execution.cards.values() if card["result_id"]==ids[0]), None)
        if card is None or self._evidence(card).get("truncated"):
            return False
        current = context.get("references", {}).get("current")
        if item.get("target"):
            if item["target"]!=current:
                return False  # Let the model ground an explicit focus switch first.
        else:
            surface = display_list(card)
            rows = at_path(card.get("data"), surface["path"]) if surface else None
            if current or len(execution.cards)!=1 or not isinstance(rows, list) or len(rows)==1 or any(not isinstance(row, dict) for row in rows):
                return False
        await self._deliver(user, sid, tid, {"result_ids": ids}, payload, execution)
        log.info("Direct delivery: task=%s operation=%s", tid, item["id"])
        return True

    async def _prepare_operations(self, user, sid, tid, reply, tools, execution, payload, context):
        """Bind native calls by their order, without changing any MCP schema/arguments."""
        native = [call for call in reply.tool_calls if call["name"] in tools.loaded]
        updates = [INPUTS["remember"][0].model_validate(call["args"]) for call in reply.tool_calls
            if call["name"]=="remember" and any(key in call["args"] for key in ("operations", "calls", "resume"))]
        if len(updates)>1:
            raise QAError("invalid_parameters", "同一回复只需一次操作登记，请合并到一个remember调用")
        values = updates[0] if updates else None
        operations = Operations(execution.operations.items)
        resume = payload.get("resume")
        inherited = False
        if payload.get("parent_task_id") and resume is None:
            if values is None or values.resume is None:
                if native:
                    raise QAError("invalid_parameters", "请明确resume：继续待澄清任务为true，独立的新请求为false；可与MCP调用同时输出")
            else:
                resume = values.resume
                if resume:
                    parent = await asyncio.to_thread(self.store.task, user, sid, payload["parent_task_id"])
                    if parent["status"]!="WAITING_INPUT":
                        raise QAError("task_not_running", "待澄清任务已经结束，不能继续执行；请发起新的请求", 409)
                    operations = Operations(json.loads(parent["payload"]).get("operations", []))
                    if any(item["state"]=="running" for item in operations.items):
                        raise QAError("execution_unknown", "原操作的执行状态尚未确认，未重复执行", 504)
                    inherited = True
        elif payload.get("parent_task_id") and values is not None and values.resume is not None and values.resume!=resume:
            raise QAError("invalid_parameters", "本轮任务的继续关系已经确定，不能切换")
        operations.declare(values.operations if values else None)
        bindings = operations.bind(values.calls if values else None, len(native))
        if values and values.operations:
            targets = [item.target.model_dump() for item in values.operations if item.target]
            if targets:
                await self._validate_references(user, sid, {}, {"selected": targets})
        if values and values.references:
            await self._validate_references(user, sid, context.get("references", {}), values.references.model_dump(exclude_unset=True))
        # Commit only after the whole batch's metadata and sources validate.
        if inherited:
            ids = list(dict.fromkeys(rid for item in operations.items for rid in operations.result_ids(item)))
            cards = await asyncio.to_thread(self.store.selected_results, user, sid, ids) if ids else []
            by_id = {card["result_id"]: card for card in cards}
            for item in operations.items:
                for attempt in item["attempts"]:
                    if attempt.get("result_id") in by_id:
                        execution.cards[(attempt["key"], "inherited")] = by_id[attempt["result_id"]]
                if item["state"] in {"failed", "unknown"}:
                    error = item["attempts"][-1]["error"]
                    execution.failures[item["id"]] = QAError(error["code"], error["message"], error["status"], detail=error.get("detail"))
            execution.recovering = True
        execution.operations = operations
        if resume is not None:
            payload["resume"] = resume
        payload["operations"] = operations.items
        consumed = resume is not None and (context.get("pending") or {}).get("task_id")==payload.get("parent_task_id")
        if consumed:
            context.pop("pending", None)
        if consumed or (values and not native):
            await self._write(user, sid, tid, payload=payload, context=context if consumed else None)
        return dict(zip((call["id"] for call in native), bindings))

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
            state = context.get("references", {})
            patch = values.references.model_dump(exclude_unset=True) if values.references else {}
            identifier = values.values.get("selected_dataset_id")
            if identifier is not None:
                matches = await asyncio.to_thread(self.store.object_reference, user, sid, identifier,
                    all_references(patch)+all_references(state))
                if len(matches)!=1:
                    raise QAError("invalid_parameters", "选择须对应唯一的已保存记录；请提供来源引用或澄清具体对象")
                patch.setdefault("current", matches[0])
            state = await self._validate_references(user, sid, state, patch)
            context["memory"] = {k: v for k, v in memory.items() if v is not None}
            context["references"] = state
            await self._write(user, sid, tid, context=context)
            return {"saved": True}
        pending = {"task_id": tid, "question": values.question}
        if values.options:
            pending["options"] = values.options
        context["pending"] = pending
        await self._write(user, sid, tid, context=context)
        return {"waiting": True}

    async def _final_reply(self, user, sid, tid, messages, answer, phase, reason=None, waiting=None):
        await phase("answer", "正在生成答复")
        saved = await asyncio.to_thread(self.store.task, user, sid, tid)
        payload = json.loads(saved["payload"])
        ids = payload.get("delivery", [])
        cards = await asyncio.to_thread(self.store.selected_results, user, sid, ids)
        operations = Operations(payload.get("operations", []))
        if reason:
            await self._failure_reply(user, sid, tid, answer, reason, operations, payload)
            if reason.code not in {"step_limit", "no_progress"}:
                return
        instructions = (str(messages[0].content)+"\nTool use is over. Write only the final user-facing reply, "
            "without internal planning or another tool call. Use actual evidence, distinguish unfinished work, "
            "Do not repeat a runtime notice already shown to the user. "
            "and only refer to display cards listed in final_delivery. Do not claim unperformed work succeeded. "
            "The runtime operations state is authoritative: distinguish execution from delivery and do not describe auxiliary lookups as completion of the request. "
            "Use answer_evidence for supporting facts; only final_delivery defines displayed artifacts. Retrieval totals may overlap: do not add them or infer coverage or suitability without evidence. "
            "When naming an object from returned data, use that object's own non-empty title field verbatim. "
            "Do not substitute identifiers, source/provider labels, or enclosing card titles for object names. "
            "If its title is absent or empty, state that the name was not provided and distinguish it using "
            "a supplied identifier; do not infer or invent a name.")
        source_ids = [rid for item in operations.items if item["state"]=="succeeded" for rid in operations.result_ids(item)]
        for message in messages[2:]:
            if isinstance(message, ToolMessage) and (rid := json.loads(message.content).get("result_id")):
                source_ids.append(rid)
        displayed = {*ids, *payload.get("delivery_sources", [])}
        answer_ids = [rid for rid in dict.fromkeys(source_ids) if rid not in ids]
        answer_cards = await asyncio.to_thread(self.store.selected_results, user, sid, answer_ids) if answer_ids else []
        limit = self.gateway.limits.result_chars
        delivery, _ = project({"final_delivery": [self._evidence(card) for card in cards],
            "stop_reason": str(reason) if reason else None}, limit*2//3 if answer_cards else limit-24)
        support = evidence_group(answer_cards, operations, max(4, limit-len(encode(delivery))-24))
        delivery["answer_evidence"] = support.get("items", [])
        context = json.loads(messages[1].content)
        if operations.items:
            context["operations"] = operations.view()
        context.pop("evidence", None)
        context.pop("mcp_servers", None)
        history = []
        for message in messages[2:]:
            if isinstance(message, ToolMessage):
                value = json.loads(message.content)
                if message.name and message.name.startswith("mcp_") and value.get("result_id") in {*displayed, *answer_ids}:
                    message = message.model_copy(update={"content": encode({key: value[key] for key in
                        ("result_id", "executed", "guidance", "repeated") if key in value})})
            history.append(message)
        final_messages = [messages[0].model_copy(update={"content": instructions}), HumanMessage(encode(context)),
            *history, HumanMessage(encode(delivery))]
        try:
            reply = await self._reply(user, sid, tid, final_messages, [], answer, phase, waiting)
            if reply.tool_calls or reply.invalid_tool_calls:
                raise QAError("invalid_tool_call", "正式答复阶段返回了工具调用", 502)
            if not answer["text"].strip():
                answer["text"] = "请查看下方结果。" if cards else "请补充需要处理的问题。"
                await self._write(user, sid, tid, {"type": "message", "text": answer["text"]})
        except QAError as exc:
            # Only generation failures may degrade a confirmed delivery.
            # Persistence failures and cancellation retain their original status.
            if (not cards and reason is None) or not (exc.code in {"model_timeout", "invalid_tool_call", "context_too_large"}
                    or (exc.code=="service_unavailable" and exc.detail=={"phase": "model"})):
                raise
            log.warning("Final response degraded: task=%s code=%s", tid, exc.code)
            if reason is None:
                await self._notice(user, sid, tid, answer, "答复生成中断，已取得的结果已保留，请查看下方结果。")

    async def _run(self, user, sid, tid, payload, options):
        started = time.monotonic()
        answer, acquired, results = {"text": ""}, False, 0
        messages, active_phase = None, None
        execution, limits = Execution(), self.gateway.limits

        async def phase(stage, title="", *, payload=None):
            nonlocal active_phase
            waiting.stage = stage or waiting.stage
            if active_phase == (stage, title):
                if payload is not None:
                    await self._write(user, sid, tid, payload=payload)
                return
            active_phase = (stage, title) if stage else None
            if stage:
                await self._write(user, sid, tid, {"type": "stage", "stage": stage,
                    "summary": title}, payload=payload)

        waiting = Waiting(limits.wait_notice, phase)
        turn_deadline = asyncio.get_running_loop().time()+limits.turn_timeout
        # Reserve a small part of the same budget for saving receipts and feedback.
        deadline = asyncio.timeout_at(turn_deadline-min(5, limits.turn_timeout/2))
        try:
            async with deadline:
                await phase("prepare", "正在理解请求")
                if self.slots.locked():
                    await phase("prepare", "正在等待可用处理资源")
                async with waiting.during("仍在等待可用处理资源，本轮请求尚未开始执行。"):
                    await self.slots.acquire()
                    acquired = True
                log.info("Task queue: task=%s elapsed=%.3fs", tid, time.monotonic()-started)
                context, model_context, parent = await self._context(user, sid, tid, options)
                if parent:
                    payload["parent_task_id"] = parent
                    await self._write(user, sid, tid, payload=payload)
                reason, ready, delivery_failure = None, False, None
                async with self.gateway.session() as tools:
                    def action_feedback(error):
                        value = execution.feedback(error, execution.actions(tools.loaded))
                        if "detail" in value:
                            log.info("Action validation: task=%s code=%s detail=%s", tid, error.code, encode(value["detail"]))
                        return value

                    tools.prime(payload["message"], context.get("tools", []))
                    model_context["mcp_servers"] = tools.list_servers(payload["message"])
                    messages = self.dialogue.messages(payload["message"], model_context)
                    evidence_ids = ()
                    evidence_cards = {}
                    for _ in range(limits.max_rounds):
                        if execution.calls>=limits.max_calls and not execution.can_deliver:
                            reason = QAError("step_limit", "工具调用达到本轮预算，请缩小请求范围")
                            break
                        rejection = None
                        actions = execution.actions(tools.loaded)
                        definitions = [definition for definition in [*BUILTINS, *tools.definitions()]
                            if definition["function"]["name"] in actions]
                        advertised = {value["function"]["name"] for value in definitions}
                        reply = None
                        bindings = {}
                        updated = json.loads(messages[1].content)
                        if execution.operations.items:
                            updated["operations"] = execution.operations.view()
                        current_ids = tuple(card["result_id"] for card in execution.cards.values())
                        if current_ids!=evidence_ids:
                            for card in execution.cards.values():
                                if card["result_id"] not in evidence_cards:
                                    evidence_cards[card["result_id"]] = self._evidence(card)
                            updated["evidence"] = evidence_group([evidence_cards[rid] for rid in dict.fromkeys(current_ids)], execution.operations, limits.result_chars)
                            evidence_ids = current_ids
                        if payload.get("resume") is not None:
                            updated.pop("pending", None)
                        messages[1] = HumanMessage(encode(updated))
                        try:
                            reply = await self._reply(user, sid, tid, messages, definitions, waiting=waiting)
                            if reply.tool_calls:
                                bindings = await self._prepare_operations(user, sid, tid, reply, tools, execution, payload, context)
                        except QAError as exc:
                            if exc.code not in {"invalid_tool_call", "invalid_parameters", "invalid_pointer", "result_not_found"}:
                                raise
                            rejection = exc
                        except ValidationError as exc:
                            rejection = execution.validation_error(exc)
                        if not rejection and not reply.tool_calls:
                            try:
                                execution.require_result()
                                await self._fallback_delivery(user, sid, tid, payload, execution, required=True)
                            except QAError as exc:
                                if exc.code not in {"mcp_required", "invalid_delivery"}:
                                    raise
                                rejection = exc
                                delivery_failure = exc
                        if rejection:
                            # Never replay malformed calls, missing/duplicate IDs or
                            # unpaired results to the provider during correction.
                            if reply is not None and not reply.tool_calls and not reply.invalid_tool_calls:
                                messages.append(reply)
                            feedback = action_feedback(rejection)
                            messages.append(HumanMessage(encode({"runtime_feedback": feedback})))
                            reason = execution.correct(rejection, limits.max_corrections)
                            log.info("Action correction: task=%s error=%s corrections=%s stopped=%s",
                                tid, rejection.code, execution.corrections, reason is not None)
                            if reason:
                                break
                            continue
                        if not reply.tool_calls:
                            reason = execution.operations.error(payload.get("delivery_sources", []))
                            await self._final_reply(user, sid, tid, messages, answer, phase, reason, waiting)
                            await self._finish_task(user, sid, tid, payload, execution, answer, reason)
                            return
                        messages.append(reply)
                        round_progress = False
                        for call in reply.tool_calls:
                            name, arguments = call["name"], call["args"]
                            tool = tools.loaded.get(name)
                            operation_id = bindings.get(call["id"])
                            key = fingerprint([operation_id, name, arguments])
                            interaction = None
                            rejected = False
                            log.info("Agent action: task=%s name=%s allowed=%s", tid, name, name in advertised)
                            if ready:
                                value = {"executed": False, "message": "交付范围已确定，未继续执行工具"}
                            elif name=="remember" and any(field in arguments for field in ("operations", "calls", "resume")) and not arguments.get("values") and not arguments.get("references"):
                                # Bookkeeping is co-emitted with native calls; it does not consume a business-call slot.
                                value = {"saved": True}
                            elif reason or (execution.calls>=limits.max_calls and (name!="deliver_results" or name not in advertised)):
                                reason = reason or QAError("step_limit", "工具调用达到本轮预算，请缩小请求范围")
                                value = {"error": reason.code, "message": str(reason), "executed": False}
                            elif name not in advertised:
                                execution.calls += 1
                                rejection = QAError("tool_not_loaded", "当前动作尚未开放，请从当前提供的动作中选择")
                                if name=="deliver_results":
                                    if not execution.cards and not execution.failures:
                                        rejection = QAError("mcp_required", "本轮尚未通过MCP执行任务，不能直接交付结果")
                                value = action_feedback(rejection)
                                rejected = True
                            elif name=="deliver_results" and not reason:
                                try:
                                    execution.require_result()
                                    value = await self._deliver(user, sid, tid, arguments, payload, execution)
                                    ready = True
                                except (QAError, ValidationError) as exc:
                                    if isinstance(exc, ValidationError):
                                        exc = execution.validation_error(exc, "交付参数不符合定义")
                                    delivery_failure = exc
                                    value = {"error": exc.code, "message": str(exc)}
                                    if exc.code in {"mcp_required", "invalid_parameters", "invalid_delivery", "invalid_pointer", "result_not_found"}:
                                        rejection = exc
                                        value = action_feedback(rejection)
                                        rejected = True
                            elif tool and operation_id is not None and execution.operations.get(operation_id)["state"] in {"running", "unknown"}:
                                failure = QAError("execution_unknown", "此操作的执行结果尚未确认，未重复执行；请先核实上游状态", 504)
                                execution.failures[operation_id] = failure
                                value = {"error": failure.code, "message": str(failure), "executed": False}
                            elif tool and (completed := execution.completed(key)) is not None:
                                execution.operations.finish(operation_id, key, result_id=completed["result_id"])
                                execution.failures.pop(operation_id or key, None)
                                await self._write(user, sid, tid, payload=payload)
                                value = {**self._evidence(completed), "executed": False,
                                    "guidance": "This operation already completed in this turn. Use the saved result; no additional execution took place."}
                            else:
                                execution.calls += 1
                                call_started = time.monotonic()
                                try:
                                    if name in INPUTS:
                                        async with waiting.during("仍在等待MCP工具目录返回，尚未执行数据操作。") if name=="load_mcp_tools" else nullcontext():
                                            value = await self._builtin(user, sid, tid, name, arguments, tools, context)
                                        if name=="read_result" and arguments.get("result_id") is None:
                                            value["operations"] = execution.operations.view(arguments.get("offset", 0), min(arguments.get("limit", 20), 8))
                                        if name=="remember":
                                            updated = json.loads(messages[1].content)
                                            updated["references"] = await self._reference_view(user, sid, context.get("references", {}))
                                            updated["memory"] = {key: value for key, value in context.get("memory", {}).items()
                                                if key!="selected_dataset_id"}
                                            messages[1] = HumanMessage(encode(updated))
                                        if name=="request_input":
                                            interaction = context["pending"]
                                    else:
                                        previous = execution.failures.get(key) if operation_id is None else None
                                        if previous and (previous.code=="execution_unknown" or (previous.code!="mcp_unavailable" and not execution.reusable(tool))):
                                            raise previous
                                        execution.operations.start(operation_id, key, {"server": tool.server, "name": tool.name}, execution.reusable(tool))
                                        payload["operations"] = execution.operations.items
                                        await phase("execute", "正在处理："+tool.title, payload=payload)
                                        async with waiting.during("正在等待MCP服务返回，尚未取得本次操作的结果。"):
                                            tool, output = await tools.call(name, arguments)
                                        marker = (key, fingerprint(output.payload()))
                                        card = execution.cards.get(marker)
                                        if card is None:
                                            metadata = tool.meta.get("piflow", {})
                                            view = metadata.get("view_type", "tool_result") if isinstance(metadata, dict) else "tool_result"
                                            card = {"result_id": f"{tid}:{results}", "view_type": view,
                                                "title": f"{tool.server} · {tool.title}", **output.payload()}
                                            results += 1
                                            execution.operations.finish(operation_id, key, result_id=card["result_id"])
                                            await self._write(user, sid, tid, card=card, payload=payload)
                                            execution.cards[marker] = card
                                        else:
                                            execution.operations.finish(operation_id, key, result_id=card["result_id"])
                                            await self._write(user, sid, tid, payload=payload)
                                        value = self._evidence(card)
                                        execution.failures.pop(operation_id or key, None)
                                        reference = {"server": tool.server, "name": tool.name}
                                        context["tools"] = [reference, *[ref for ref in context.get("tools", []) if ref!=reference]][:4]
                                        await self._write(user, sid, tid, context=context)
                                except (QAError, ValidationError) as exc:
                                    if isinstance(exc, ValidationError):
                                        exc = execution.validation_error(exc)
                                    log.info("Tool request rejected: task=%s tool=%s operation=%s code=%s",
                                        tid, name, operation_id, exc.code)
                                    value = {"error": exc.code, "message": str(exc)}
                                    if exc.detail:
                                        value["detail"] = exc.detail
                                    if tool:
                                        execution.operations.finish(operation_id, key, error=exc)
                                        await self._write(user, sid, tid, payload=payload)
                                    if exc.code in {"invalid_parameters", "invalid_pointer", "result_not_found", "memory_too_large", "server_not_found"}:
                                        rejection = exc
                                        value = action_feedback(rejection)
                                        rejected = True
                                    elif tool:
                                        execution.failures[operation_id or key] = exc
                                        if exc.code=="tool_failed" and execution.reusable(tool):
                                            # A declared read-only/idempotent operation may correct a
                                            # rejected upstream request within the existing global budget.
                                            rejection = exc
                                            value = action_feedback(rejection)
                                            value["executed"] = True
                                            rejected = True
                                    if name=="load_mcp_tools" and exc.code=="mcp_unavailable":
                                        value.update(server=arguments.get("server"), executed=False,
                                            guidance="Only this service's discovery failed. Use already loaded tools or discover another configured service. Discovery does not execute a user operation.")
                                    elif not tool and exc.code in {"mcp_unavailable", "tool_failed", "execution_unknown", "result_too_large"}:
                                        reason = exc
                                finally:
                                    log.info("Tool request: task=%s tool=%s mcp=%s operation=%s elapsed=%.3fs",
                                        tid, name, tool is not None, operation_id, time.monotonic()-call_started)
                            if tool and value.get("result_id"):
                                evidence_cards[value["result_id"]] = value
                            if interaction:
                                answer["text"] = (answer["text"]+"\n"+interaction["question"]).strip()
                                await asyncio.to_thread(self.store.finish, user, sid, tid, "WAITING_INPUT",
                                    message=answer["text"], interaction=interaction)
                                return
                            if not rejected:
                                progress = execution.observe(key, value, name, arguments, context)
                                round_progress = round_progress or progress
                                if not progress:
                                    value = {**value, "repeated": True,
                                        "guidance": "This call provided no new evidence. Use the saved result, change the request if needed, or answer the user."}
                            messages.append(ToolMessage(content=encode(value), tool_call_id=call["id"], name=name))
                        if not ready and not reason and not rejection and any(call["id"] in bindings for call in reply.tool_calls):
                            fast_context = {**context, "reference_issue": json.loads(messages[1].content).get("reference_issue")}
                            ready = await self._fast_delivery(user, sid, tid, payload, execution, fast_context)
                        if ready:
                            reason = execution.operations.error(payload.get("delivery_sources", []))
                            await self._final_reply(user, sid, tid, messages, answer, phase, reason, waiting)
                            await self._finish_task(user, sid, tid, payload, execution, answer, reason)
                            return
                        if not reason and not tools.loaded and tools.discovery_errors and all(server in tools.discovery_errors for server in tools.servers):
                            reason = next(reversed(tools.discovery_errors.values()))
                        if not rejection:
                            execution.stalled = 0 if round_progress else execution.stalled+1
                        if not reason and not rejection and execution.stalled>=limits.max_stalled_calls:
                            reason = QAError("no_progress", "连续调用未获得新信息，当前无法继续推进；请补充条件或调整请求")
                        if not rejection and execution.operations.items and all(item["state"] in {"succeeded", "failed", "unknown"} for item in execution.operations.items) and any(
                                item["state"] in {"failed", "unknown"} for item in execution.operations.items):
                            reason = execution.operations.error()
                        if rejection and not reason:
                            reason = execution.correct(rejection, limits.max_corrections)
                            log.info("Action correction: task=%s error=%s corrections=%s stopped=%s",
                                tid, rejection.code, execution.corrections, reason is not None)
                        if reason:
                            break
                    reason = reason or QAError("step_limit", "处理达到本轮预算，请缩小请求范围")
                    if reason.code in {"mcp_required", "step_limit", "no_progress"} and not tools.loaded and tools.discovery_errors:
                        reason = next(reversed(tools.discovery_errors.values()))
                    # Delivery selection never executes MCP; final text has no tools.
                    if execution.cards and "delivery" not in payload:
                        try:
                            await self._fallback_delivery(user, sid, tid, payload, execution)
                        except Exception:
                            log.warning("Partial delivery unavailable: task=%s", tid, exc_info=True)
                    if reason is delivery_failure and "delivery" in payload and execution.operations.error(payload.get("delivery_sources", [])) is None:
                        log.info("Delivery recovered from saved evidence: task=%s", tid)
                        reason = None
                    await self._final_reply(user, sid, tid, messages, answer, phase, reason, waiting)
                    await self._finish_task(user, sid, tid, payload, execution, answer, reason)
        except asyncio.CancelledError:
            try:
                await asyncio.to_thread(self.store.finish, user, sid, tid, "CANCELLED", message=answer["text"])
            except QAError:
                pass
        except Exception as exc:
            expired = deadline.expired()
            if expired:
                unknown = QAError("execution_unknown", "MCP服务未在本轮等待上限内返回，暂时无法确认执行结果；未自动重复执行", 504)
                for item in execution.operations.items:
                    if item["state"]=="running":
                        execution.operations.finish(item["id"], item["attempts"][-1]["key"], error=unknown)
                payload["operations"] = execution.operations.items
                message = ("本次请求超过本轮等待上限，暂时无法完成；已取得的有效信息将保留。" if acquired else
                    "等待可用处理资源超过本轮上限，本次请求尚未开始执行。")
                exc = QAError("task_timeout", message, 504, detail={"phase": "execution" if acquired else "queue"})
            log.exception("Agent task failed: task=%s", tid)
            failure = exc if isinstance(exc, QAError) else QAError("service_unavailable", "服务暂不可用，请稍后重试", 503)
            try:
                async with asyncio.timeout_at(turn_deadline) if expired else nullcontext():
                    if expired:
                        await self._write(user, sid, tid, payload=payload)
                    if execution.cards and "delivery" not in payload:
                        try:
                            await self._fallback_delivery(user, sid, tid, payload, execution)
                        except (QAError, ValidationError):
                            pass
                    if expired and payload.get("delivery") and execution.operations.error(payload.get("delivery_sources", [])) is None:
                        await self._notice(user, sid, tid, answer, "答复生成超过等待上限，已完成的操作及结果已保留，请查看下方结果。")
                        await self._finish_task(user, sid, tid, payload, execution, answer)
                        return
                    await self._failure_reply(user, sid, tid, answer, failure, execution.operations, payload)
                    await self._finish_task(user, sid, tid, payload, execution, answer, failure)
            except (QAError, TimeoutError):
                log.warning("Task finalization interrupted: task=%s", tid)
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
