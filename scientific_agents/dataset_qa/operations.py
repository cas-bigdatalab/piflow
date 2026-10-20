"""Private task goals and execution receipts, independent of MCP names and views."""
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .context import encode, project
from .contracts import QAError
from .references import Reference


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=48, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = Field(min_length=1, max_length=240, description="One necessary user-requested operation, not an auxiliary lookup.")
    target: Reference | None = None
    output: Literal["result", "answer"] = Field(default="result", description="Whether this operation requires a displayed artifact or a factual text answer.")


class Operations:
    """The model declares intent; only runtime receipts establish execution state."""

    def __init__(self, saved=None):
        self.items = deepcopy(saved or [])

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
            "target": value["target"]} for key, value in proposed.items()]

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

    def start(self, operation_id, key, tool=None, retry_safe=False):
        item = self.get(operation_id)
        if item is None:
            return
        if item["state"] in {"running", "unknown"}:
            raise QAError("execution_unknown", "此操作的执行结果尚未确认，未重复执行；请先核实上游状态", 504)
        if item["state"]=="failed":
            previous = item["attempts"][-1]
            error = previous.get("error", {})
            if error.get("code")!="mcp_unavailable" and not previous.get("retry_safe"):
                raise QAError(error.get("code", "tool_failed"), "此操作已经失败，未重复执行可能产生副作用的操作", 502, detail=error.get("detail"))
        item["state"] = "running"
        item["attempts"].append({"key": key, "state": "running", "tool": tool, "retry_safe": retry_safe})

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
            item["state"] = "succeeded"
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

    def validate_delivery(self, ids, partial=False):
        if not self.items:
            raise QAError("invalid_delivery", "尚未明确本轮必要操作，不能确定最终交付")
        owners = {rid for item in self.items if item["state"]=="succeeded" for rid in self.result_ids(item)}
        if not set(ids)<=owners:
            raise QAError("invalid_delivery", "交付结果必须来自本轮必要操作的成功证据，不能选择辅助查询或无关历史结果",
                detail={"unrelated": sorted(set(ids)-owners), "pending": [item["id"] for item in self.items if item["state"]!="succeeded"]})
        pending = [item for item in self.items if item["state"] in {"pending", "running"}]
        uncovered = [item for item in self.items if item["state"]=="succeeded" and item["output"]=="result"
            and not set(ids).intersection(self.result_ids(item))]
        if not partial and (pending or uncovered):
            raise QAError("invalid_delivery", "必要操作或交付尚未完成，请继续处理；成功的操作不需要重复执行",
                detail={"pending": [item["id"] for item in pending], "undelivered": [item["id"] for item in uncovered]})

    def error(self, ids=()):
        for item in self.items:
            if item["state"] in {"failed", "unknown", "running"}:
                failure = next((value.get("error") for value in reversed(item["attempts"]) if value.get("error")), None)
                if failure:
                    return QAError(failure["code"], failure["message"], failure["status"], detail=failure.get("detail"))
                return QAError("execution_unknown", "部分操作的执行结果尚未确认", 504)
        if any(item["state"]!="succeeded" or (item["output"]=="result" and not set(ids).intersection(self.result_ids(item))) for item in self.items):
            return QAError("invalid_delivery", "本轮必要操作或结果交付尚未全部完成")

    def view(self, offset=0, limit=16, budget=3600):
        rows = []
        for item in self.items[offset:offset+limit]:
            row = {key: item[key] for key in ("id", "description", "target", "output", "state")}
            ids = self.result_ids(item)
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
        done, unfinished = [], []
        for item in self.items:
            delivered = item["output"]=="answer" or bool(set(ids).intersection(self.result_ids(item)))
            if item["state"]=="succeeded" and delivered:
                done.append(item["description"])
            else:
                suffix = "（已执行，尚未交付）" if item["state"]=="succeeded" else "（执行结果尚未确认）" if item["state"] in {"running", "unknown"} else ""
                if item["state"]=="failed":
                    error = item["attempts"][-1].get("error", {})
                    detail = error.get("detail")
                    message = next((value for value in detail if isinstance(value, str) and value.strip()), "") if isinstance(detail, list) else ""
                    suffix = "（"+(message or error.get("message", "操作失败"))[:180]+"）"
                unfinished.append(item["description"]+suffix)
        return "\n".join(label+"；".join(values)+"。" for label, values in (("已完成：", done), ("未完成：", unfinished)) if values)
