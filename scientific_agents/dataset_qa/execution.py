"""Per-turn execution budgets and evidence-based convergence checks."""
from hashlib import sha256
import json

from .context import project
from .contracts import QAError
from .operations import Operations


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class Execution:
    def __init__(self):
        self.calls, self.stalled = 0, 0
        self.seen, self.cards = set(), {}
        self.failures = {}
        self.corrections = 0
        self.recovering = False
        self.operations = Operations()

    @property
    def can_deliver(self):
        return bool(self.cards) or bool(self.failures)

    @property
    def finalizing(self):
        return bool(self.operations.items) and all(item["state"]=="succeeded" for item in self.operations.items)

    def actions(self, loaded):
        names = {"read_result", "remember", "request_input"}
        if not (self.finalizing and all(item.get("direct") and item["output"]=="result" for item in self.operations.items)) or self.recovering:
            names.update(("list_mcp_servers", "load_mcp_tools", *loaded))
        if self.can_deliver:
            names.add("deliver_results")
        return names

    def correct(self, error, limit):
        self.recovering = True
        if self.corrections>=limit:
            return error
        self.corrections += 1

    @staticmethod
    def feedback(error, actions):
        value = {"error": error.code, "message": str(error), "executed": False,
            "available_actions": sorted(actions),
            "guidance": "Choose only an available action with valid arguments. Execute requested operations through MCP before delivery; use saved results for already completed calls. Ask request_input if information is missing."}
        if error.detail:
            value["detail"], _ = project(error.detail, 1200)
        return value

    @staticmethod
    def validation_error(error, message="参数不符合工具定义"):
        errors = error.errors(include_url=False, include_context=False, include_input=False)
        return QAError("invalid_parameters", message, detail={"errors": [
            {"path": list(item["loc"]), "constraint": item["type"], "message": item["msg"][:300]}
            for item in errors[:3]]})

    @staticmethod
    def notice(error, retained=False):
        message = {
            "invalid_tool_call": "未能生成有效的工具调用，本轮操作未完成。请重试或补充请求。",
            "invalid_parameters": "本轮未能生成有效的操作参数，操作尚未完成。",
        }.get(error.code, str(error).rstrip("。")+"。")
        if error.code=="tool_failed" and isinstance(error.detail, list):
            detail = next((item.strip() for item in error.detail if isinstance(item, str) and item.strip()), "")
            if detail:
                message += "上游反馈："+detail[:300].rstrip("。")+"。"
        if error.code in {"step_limit", "no_progress"}:
            message += "本轮已停止继续调用工具。"
        return message+("本轮已取得的结果已保留。" if retained else "")

    def completed(self, key):
        return next((card for (call, _), card in reversed(self.cards.items()) if call==key), None)

    def require_result(self):
        if not self.cards and not self.failures:
            raise QAError("mcp_required", "本轮尚未通过MCP执行任务，不能直接交付结果")

    @staticmethod
    def reusable(tool):
        # Read-only does not imply deterministic: random sampling is read-only.
        return (tool is not None and tool.annotations.get("readOnlyHint") is True
            and tool.annotations.get("idempotentHint") is True)

    def observe(self, key, value, name=None, arguments=None, context=None):
        if name in {"list_mcp_servers", "load_mcp_tools"}:
            markers = {(name, row["name"]) for row in value.get("items", []) if "name" in row and "error" not in row}
        elif name=="remember":
            state = {"references": (context or {}).get("references")}
            state["operations"] = [{key: item[key] for key in ("id", "description", "target", "output")}
                for item in self.operations.items]
            markers = {(name, fingerprint(state))}
        elif name=="read_result":
            args = arguments or {}
            markers = {(name, args.get("result_id"), args.get("path", ""), args.get("offset", 0),
                fingerprint({k: v for k, v in value.items() if k!="operations"}))}
        else:
            # A new result ID or repeated bookkeeping is not new evidence.
            markers = {(key, fingerprint({k: v for k, v in value.items()
                if k not in {"result_id", "executed", "guidance", "repeated"}}))}
        fresh = bool(markers-self.seen)
        self.seen.update(markers)
        if not fresh and self.recovering and value.get("result_id") and value.get("executed") is False:
            # Reusing a receipt can resolve a correction once, not restart a loop.
            marker = (key, "correction", self.corrections)
            fresh = marker not in self.seen
            self.seen.add(marker)
        return fresh
