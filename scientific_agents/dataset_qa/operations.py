"""Private task goals and execution receipts, independent of MCP names and views."""
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .context import encode, project
from .contracts import QAError
from .references import Reference
from .search import SearchRun


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=48, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = Field(min_length=1, max_length=240, description="One necessary user outcome. Query variants and pages may support the same outcome; independently requested operations remain separate.")
    target: Reference | None = None
    output: Literal["result", "answer"] = Field(default="result", description="Whether this operation requires a displayed artifact or a factual text answer.")
    direct: bool = Field(default=False, description="True only when successful execution itself yields the final requested artifact; no further inspection, pagination, interpretation or selection is needed.")


class Operations:
    """The model declares intent; only runtime receipts establish execution state."""

    def __init__(self, saved=None):
        self.items = deepcopy(saved or [])

    @property
    def required(self):
        return [item for item in self.items if item.get("required", True)]

    def register(self, description, capability, target=None, output="result", planned=False, required=True):
        """Runtime identities follow capability and grounded target, not model IDs."""
        matches = [item for item in self.items if item.get("capability")==capability
            and item.get("target")==target and (item["output"]==output or (planned and not item.get("planned")))
            and (required or not item.get("required", True))]
        if planned:
            # A new semantic declaration cannot adopt every receipt of an old
            # auxiliary capability. Reuse requires a matching invocation or an
            # explicit, source-checked confirmation of the existing evidence.
            matches = [item for item in matches if item.get("planned") and item["description"]==description]
        if matches:
            item = matches[0]
            if required:
                item["required"] = True
            if planned:
                item.update(description=description, planned=True, required=True, output=output)
            return item["id"]
        if len(self.items)>=16:
            raise QAError("invalid_parameters", "本轮目标较多，请分批处理")
        key = "op"+str(len(self.items)+1)
        while self.get(key):
            key += "_"
        self.items.append({"id": key, "description": description[:240], "capability": capability,
            "target": deepcopy(target), "output": output, "direct": False, "planned": planned,
            "required": required, "state": "pending", "attempts": []})
        return key

    def receipt(self, invocation, operation_id):
        """A semantic bookkeeping correction must not re-execute a receipt.

        Distinct outcomes declared before execution may intentionally repeat a
        call (for example two independent samples). New bookkeeping alone may not.
        """
        operation = self.get(operation_id)
        claimed_elsewhere = {rid for item in self.required if item["id"]!=operation_id
            for rid in self.result_ids(item)} if operation and operation.get("required", True) else set()
        for owner in self.items:
            for attempt in owner["attempts"]:
                if attempt.get("invocation")!=invocation or attempt["state"]!="succeeded":
                    continue
                if owner.get("search") and owner["id"]!=operation_id and not (operation or {}).get("search"):
                    continue  # A page receipt cannot bypass a bounded discovery's completion policy.
                # Reusing an auxiliary receipt must not bypass its subsequent
                # ownership by another independently requested outcome. The
                # original dispatch may predate both goals and have no scope.
                if attempt.get("result_id") in claimed_elsewhere:
                    continue
                explicit_repeat = (owner["id"]!=operation_id and operation_id in attempt.get("scope", [])
                    and owner.get("required", True) and operation is not None and operation.get("required", True))
                if not explicit_repeat:
                    return attempt

    def reuse(self, operation_id, key, receipt):
        item = self.get(operation_id)
        if item and not any(attempt["key"]==key and attempt["state"]=="succeeded" for attempt in item["attempts"]):
            first_evidence = item["state"]=="pending" and all(attempt["state"]=="rejected" for attempt in item["attempts"])
            item["attempts"].append({**deepcopy(receipt), "key": key, "dispatched": False, "reused": True})
            if first_evidence:
                item["state"] = "succeeded"

    def _confirmation_sources(self, available_ids):
        """Original receipts that no independently required outcome owns yet."""
        available = set(available_ids)
        claimed = {rid for item in self.required for rid in self.result_ids(item)}
        return [(owner, attempt) for owner in self.items
            if not owner.get("required", True) and owner["state"]=="succeeded" and owner.get("capability")
            and (not owner.get("search") or owner["search"]["done"])
            for attempt in owner["attempts"]
            if attempt["state"]=="succeeded" and attempt.get("key") and attempt.get("invocation")
            and attempt.get("result_id") in available-claimed
            and not attempt.get("reused") and attempt.get("dispatched", True) is not False
            and (not attempt.get("tool") or attempt["tool"]==owner["capability"])]

    def confirmable(self, available_ids):
        """Offer evidence choices; never infer that matching tools imply completion.

        Only a goal declared after an original successful execution may adopt its
        receipt. Existing attempts and independently requested repeats retain
        their original execution requirements.
        """
        sources = self._confirmation_sources(available_ids)
        result = {}
        for goal in self.required:
            if not goal.get("planned") or goal["state"]!="pending" or goal["attempts"]:
                continue
            ids = list(dict.fromkeys(attempt["result_id"] for owner, attempt in sources
                if owner["capability"]==goal.get("capability") and owner.get("target")==goal.get("target")
                and goal["id"] not in attempt.get("scope", [])))
            if ids:
                result[goal["id"]] = ids
        return result

    def confirm(self, confirmations, available_ids):
        """Atomically associate explicitly selected evidence with late goals.

        This is a semantic confirmation of saved execution, not a new dispatch.
        A repeated confirmation is idempotent only while its original confirmed
        attempts remain the goal's complete, successful execution history.
        """
        available = set(available_ids)
        proposed = Operations(self.items)

        def reject(reason, goal=None):
            raise QAError("invalid_delivery", "请明确已有结果满足的目标，或继续完成尚缺的操作", detail={
                "decision": "confirm_outcome", "reason": reason, "goal": goal,
                "eligible": self.confirmable(available),
                "guidance": "Choose supplied goal/result_ids only when that saved evidence satisfies the outcome. "
                    "Otherwise execute the missing operation. Do not reuse one result for independent outcomes, "
                    "or confirm an old success over a later unfinished attempt."})

        if not isinstance(confirmations, list):
            reject("invalid_confirmations")
        seen = set()
        for confirmation in confirmations:
            if not isinstance(confirmation, dict):
                reject("invalid_confirmation")
            goal_id, ids = confirmation.get("goal"), confirmation.get("result_ids")
            if (not isinstance(goal_id, str) or not goal_id or not isinstance(ids, list) or not ids
                    or any(not isinstance(rid, str) or not rid for rid in ids) or len(set(ids))!=len(ids)):
                reject("invalid_confirmation")
            if goal_id in seen:
                reject("duplicate_goal", goal_id)
            seen.add(goal_id)
            goal = proposed.get(goal_id)
            if goal is None or not goal.get("required", True) or not goal.get("planned"):
                reject("unknown_goal", goal_id)
            if not set(ids)<=available:
                reject("unavailable_result", goal_id)
            claimed_elsewhere = {rid for other in proposed.required if other["id"]!=goal_id
                for rid in proposed.result_ids(other)}
            if set(ids).intersection(claimed_elsewhere):
                reject("result_already_owned", goal_id)
            if (goal["state"]=="succeeded" and goal["attempts"]
                    and all(attempt["state"]=="succeeded" and attempt.get("confirmation") is True
                        for attempt in goal["attempts"])
                    and set(ids)==set(proposed.result_ids(goal))):
                continue
            eligible = proposed.confirmable(available).get(goal_id, [])
            if not set(ids)<=set(eligible):
                reject("ineligible_evidence", goal_id)
            sources = {attempt["result_id"]: attempt for owner, attempt in proposed._confirmation_sources(available)
                if owner["capability"]==goal.get("capability") and owner.get("target")==goal.get("target")
                and goal_id not in attempt.get("scope", [])}
            searches = [owner["search"] for owner in proposed.items if owner.get("search")
                and set(ids).intersection(proposed.result_ids(owner))]
            if searches:
                if len(searches)!=1 or set(ids)!=set(searches[0]["result_ids"]):
                    reject("confirm_complete_search_evidence", goal_id)
                goal["search"] = deepcopy(searches[0])
            for rid in ids:
                receipt = sources[rid]
                proposed.reuse(goal_id, receipt["key"], {**receipt, "confirmation": True})
            if set(ids)!=set(proposed.result_ids(goal)):
                reject("conflicting_receipts", goal_id)
        self.items = proposed.items

    def declare(self, values):
        if values is None:
            return
        if len({value.id for value in values})!=len(values):
            raise QAError("invalid_parameters", "操作标识不能重复")
        proposed = {value.id: value.model_dump(mode="json") for value in values}
        existing = {item["id"]: item for item in self.items}
        if not existing.keys()<=proposed.keys():
            raise QAError("invalid_parameters", "不能删除本轮尚需完成的操作；请保留完整操作列表")
        for key, item in existing.items():
            value = proposed[key]
            if any(value[field]!=item[field] for field in ("description", "output")) or (
                    (item.get("target") is not None or any(attempt["state"]!="rejected" for attempt in item["attempts"])) and value["target"]!=item.get("target")):
                raise QAError("invalid_parameters", "已登记操作及目标不能替换；新的必要操作请使用新的标识")
        self.items = [{**value, "state": "pending", "attempts": [], **existing.get(key, {}),
            "target": value["target"], "direct": value["direct"]} for key, value in proposed.items()]

    def get(self, operation_id):
        return next((item for item in self.items if item["id"]==operation_id), None)

    def bind(self, bindings, count):
        if not count:
            if bindings:
                raise QAError("invalid_parameters", "calls只能关联同一条模型回复中的MCP调用")
            return []
        if not self.items or bindings is None or len(bindings)!=count:
            raise QAError("invalid_parameters", "请通过remember登记完整必要操作，并用calls按同一回复中MCP调用的顺序关联操作标识；辅助查询使用null，可与MCP调用一起输出")
        if any(key is not None and self.get(key) is None for key in bindings):
            raise QAError("invalid_parameters", "calls引用了尚未登记的操作")
        return bindings

    def start(self, operation_id, key, tool=None, retry_safe=False, invocation=None, presentation=None):
        item = self.get(operation_id)
        if item is None:
            return
        if invocation:
            for owner in self.items:
                if owner is item:
                    continue
                for attempt in owner["attempts"]:
                    if attempt.get("invocation")==invocation and (attempt["state"] in {"running", "unknown"}
                            or (attempt["state"]=="failed" and not attempt.get("retry_safe") and attempt.get("error", {}).get("code")!="mcp_unavailable")):
                        failure = attempt.get("error") or {"code": "execution_unknown", "message": "相同调用的执行结果尚未确认，未重复执行", "status": 504}
                        item.update(state="unknown" if failure["code"]=="execution_unknown" else "failed")
                        item["attempts"].append({"key": key, "state": item["state"], "invocation": invocation,
                            "tool": tool, "retry_safe": retry_safe, "dispatched": False, "error": deepcopy(failure)})
                        raise QAError(failure["code"], failure["message"], failure["status"], detail=failure.get("detail"))
        if item["state"] in {"running", "unknown"}:
            raise QAError("execution_unknown", "此操作的执行结果尚未确认，未重复执行；请先核实上游状态", 504)
        if item["state"]=="failed":
            previous = item["attempts"][-1]
            error = previous.get("error", {})
            if error.get("code")!="mcp_unavailable" and not previous.get("retry_safe"):
                raise QAError(error.get("code", "tool_failed"), "此操作已经失败，未重复执行可能产生副作用的操作", 502, detail=error.get("detail"))
        item["state"] = "running"
        item["attempts"].append({"key": key, "state": "running", "tool": tool, "retry_safe": retry_safe,
            "invocation": invocation, "scope": [goal["id"] for goal in self.required]})
        if presentation is not None:
            item["attempts"][-1]["presentation"] = deepcopy(presentation)

    def finish(self, operation_id, key, *, result_id=None, error=None):
        item = self.get(operation_id)
        if item is None:
            return
        attempt = next((value for value in reversed(item["attempts"]) if value["key"]==key and value["state"]=="running"), None)
        if attempt is None:
            if error:
                return  # A blocked dispatch must not rewrite an earlier execution receipt.
            if not any(value["key"]==key and value["state"]=="succeeded" and value.get("result_id")==result_id for value in item["attempts"]):
                raise QAError("invalid_delivery", "缺少此操作对应的成功执行证据")
            # A replay proves only the old result. It cannot resolve a later
            # failed, unknown or rejected attempt of the same outcome.
            return
        rejected = error and error.code in {"invalid_parameters", "invalid_pointer", "result_not_found"}
        state = "rejected" if rejected else "unknown" if error and error.code=="execution_unknown" else "failed" if error else "succeeded"
        attempt.update(state=state)
        if result_id:
            attempt["result_id"] = result_id
        if error:
            attempt["error"] = {"code": error.code, "message": str(error)[:400], "status": error.status}
            if error.detail:
                attempt["error"]["detail"], _ = project(error.detail, 1200)
        item["state"] = "pending" if rejected else state

    def result_ids(self, item):
        return list(dict.fromkeys(value["result_id"] for value in item["attempts"]
            if value["state"]=="succeeded" and value.get("result_id")))

    def delivery_ids(self, output="result"):
        """Successful artifacts survive a later attempt's failure or rejection.

        Eligibility is separate from goal completion: ``error`` still reports
        unfinished work, and supporting receipts never become deliverables.
        """
        return list(dict.fromkeys(rid for item in self.required if item["output"]==output
            for rid in self.result_ids(item)))

    def validate_delivery(self, ids, partial=False):
        if not self.required:
            raise QAError("invalid_delivery", "尚未明确本轮必要操作，不能确定最终交付")
        unfinished_searches = {item["id"]: SearchRun(item["search"]).view() for item in self.items
            if item.get("search") and not item["search"]["done"]}
        if unfinished_searches and not partial:
            raise QAError("invalid_delivery", "检索尚未达到六条去重结果，也尚未完成四个不同关键词", detail={"searches": unfinished_searches})
        owners = {rid for item in self.required for rid in self.result_ids(item)}
        if not set(ids)<=owners:
            raise QAError("invalid_delivery", "交付结果必须来自本轮必要操作的成功证据，不能选择辅助查询或无关历史结果",
                detail={"unrelated": sorted(set(ids)-owners), "pending": [item["id"] for item in self.required if item["state"]!="succeeded"]})
        pending = [item for item in self.required if item["state"] in {"pending", "running"}]
        uncovered = [item for item in self.required if item["state"]=="succeeded" and item["output"]=="result"
            and not set(ids).intersection(self.result_ids(item))]
        if not partial and (pending or uncovered):
            raise QAError("invalid_delivery", "必要操作或交付尚未完成，请继续处理；成功的操作不需要重复执行",
                detail={"pending": [item["id"] for item in pending], "undelivered": [item["id"] for item in uncovered]})

    def error(self, ids=()):
        for item in self.required:
            if item["state"] in {"failed", "unknown", "running"}:
                failure = next((value.get("error") for value in reversed(item["attempts"]) if value.get("error")), None)
                if failure:
                    return QAError(failure["code"], failure["message"], failure["status"], detail=failure.get("detail"))
                return QAError("execution_unknown", "部分操作的执行结果尚未确认", 504)
        if any(item.get("search") and not item["search"]["done"] for item in self.items):
            # A completed prerequisite may be auxiliary in the artifact view;
            # changing its delivery role cannot erase an unfinished policy.
            return QAError("invalid_delivery", "检索范围尚未按约定完成")
        if any(item["state"]!="succeeded" or (item.get("search") and not item["search"]["done"])
                or (item["output"]=="result" and not set(ids).intersection(self.result_ids(item))) for item in self.required):
            return QAError("invalid_delivery", "本轮必要操作或结果交付尚未全部完成")

    def view(self, offset=0, limit=16, budget=3600):
        rows = []
        owned = {rid for item in self.required for rid in self.result_ids(item)}
        for item in self.items[offset:offset+limit]:
            row = {key: item[key] for key in ("id", "description", "target", "output", "state")}
            ids = self.result_ids(item)
            if item.get("capability"):
                row["capability"] = item["capability"]
            if item.get("search"):
                row["search"] = SearchRun(item["search"]).view()
            if not item.get("required", True):
                # A native action without an explicit goal still needs a
                # delivery decision. It was not declared an auxiliary lookup.
                # Explicitly adopted receipts now support their required goal;
                # partial adoption leaves the other saved outcomes undecided.
                pending = item.get("inferred") and (not ids or not set(ids)<=owned)
                row["delivery_pending" if pending else "supporting"] = True
            if item.get("direct"):
                row["direct"] = True
            row["result_ids"] = ids[:2]
            if len(ids)>2:
                row["result_count"] = len(ids)
            if item["attempts"] and item["attempts"][-1].get("error"):
                error = item["attempts"][-1]["error"]
                row["error"] = {"code": error["code"], "message": error["message"][:200]}
            if len(encode(rows+[row]))>budget:
                break
            rows.append(row)
        result = {"items": rows, "total": len(self.items)}
        if offset+len(rows)<len(self.items):
            result["next_offset"] = offset+len(rows)
        return result

    def notice(self, ids):
        done, partial, unfinished = [], [], []
        for item in self.required:
            if not item["description"].strip():
                continue  # A private/unknown label is not a user-facing outcome.
            delivered = item["output"]=="answer" or bool(set(ids).intersection(self.result_ids(item)))
            if item["state"]=="succeeded" and delivered:
                done.append(item["description"])
            elif self.result_ids(item) and delivered:
                partial.append(item["description"]+"（尚有内容未完成）")
            else:
                suffix = ("（信息已取得，暂未整理为展示结果）" if item["state"]=="succeeded" else
                    "（已取得部分信息，暂未整理为展示结果）" if self.result_ids(item) else
                    "（结果尚未确认）" if item["state"] in {"running", "unknown"} else "")
                unfinished.append(item["description"]+suffix)
        if not unfinished and not partial:
            return ""
        return "\n".join(label+"；".join(values)+"。" for label, values in (
            ("已为您完成：", done), ("已取得部分信息：", partial), ("暂时还无法提供：", unfinished)) if values)
