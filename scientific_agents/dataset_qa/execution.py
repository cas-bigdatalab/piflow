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
        self.prepared = {}
        self.stale_scopes, self.blocked = {}, set()

    @property
    def can_deliver(self):
        return bool(self.cards) or bool(self.failures)

    @property
    def finalizing(self):
        return bool(self.operations.required) and all(item["state"]=="succeeded" for item in self.operations.required)

    def actions(self, loaded):
        names = {"read_result", "remember", "request_input"}
        if not (self.finalizing and all(item.get("direct") and item["output"]=="result" for item in self.operations.required)) or self.recovering:
            names.update(("list_mcp_servers", "load_mcp_tools", *loaded))
        if self.can_deliver:
            names.add("deliver_results")
        for alias, tool in loaded.items():
            scopes = [item for item in self.operations.items if item.get("capability")=={"server": tool.server, "name": tool.name}]
            if scopes and all(item["id"] in self.blocked for item in scopes):
                names.discard(alias)
        return names

    def progress(self, observations, limit):
        """Count no-gain rounds per operation, not per argument variant or batch."""
        newly_blocked = set()
        for scope, fresh in observations.items():
            self.stale_scopes[scope] = 0 if fresh else self.stale_scopes.get(scope, 0)+1
            if self.stale_scopes[scope]>=limit and scope not in self.blocked:
                self.blocked.add(scope)
                newly_blocked.add(scope)
        return newly_blocked

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
            "invalid_tool_call": "这次未能正确组织所需操作，暂时无法提供完整结果，请重试。",
            "invalid_parameters": "这次在准备操作参数时遇到了问题，暂时无法提供完整结果，请重试。",
            "invalid_delivery": "这次还无法将所需信息完整整理为展示结果。",
            "mcp_required": "这次还没有取得新的服务结果，暂时无法提供可靠答复。",
            "mcp_unavailable": "本次需要的服务暂时无法访问，请稍后重试。",
            "tool_failed": "所需服务暂时未能完成本次请求。",
            "execution_unknown": "服务尚未返回可确认的结果，为避免重复处理，暂不继续尝试。",
            "model_timeout": "生成答复的等待时间较长，暂时无法完成，请稍后重试。",
            "service_unavailable": "服务暂不可用，请稍后重试。",
            "invalid_mcp_config": "服务配置暂不可用，需要管理员核对后再试。",
            "invalid_schema": "所需服务的能力定义暂不可用，需要管理员核对后再试。",
            "server_not_found": "暂未找到可用的对应服务，请稍后重试。",
            "tool_not_loaded": "暂时无法使用本次所需的服务能力，请重试。",
            "result_too_large": "返回内容超过本次可展示范围，请缩小范围或分批获取。",
            "context_too_large": "本次需要处理的信息较多，请缩小范围或分步提问。",
            "no_progress": "目前没有取得进一步的信息，本次先停止继续尝试。",
            "step_limit": "这次处理步骤较多，暂时无法完成全部请求，已停止继续尝试。",
            "task_timeout": "本次等待已达到上限，暂时无法提供完整结果。",
        }.get(error.code, "本次处理遇到了问题，暂时无法提供完整结果，请稍后重试。")
        if error.code=="task_timeout" and error.detail=={"phase": "queue"}:
            message = "等待可用处理资源的时间较长，本次尚未开始执行，请稍后重试。"
        if error.code=="tool_failed" and isinstance(error.detail, list):
            detail = next((item.strip() for item in error.detail if isinstance(item, str) and item.strip()), "")
            if detail:
                message += "服务反馈："+detail[:300].rstrip("。")+"。"
        return message+("已取得的结果已保留，请查看下方内容。" if retained else "")

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

    def observe(self, key, value, name=None, arguments=None, context=None, *, scope=None, tool=None):
        if name in {"list_mcp_servers", "load_mcp_tools"}:
            markers = {(name, row["name"]) for row in value.get("items", []) if "name" in row and "error" not in row}
            if name=="load_mcp_tools" and value.get("error"):
                markers.add((name, (arguments or {}).get("server"), value["error"]))
        elif name=="remember":
            state = {"references": (context or {}).get("references")}
            state["operations"] = [{key: item[key] for key in ("id", "description", "target", "output")}
                for item in self.operations.items]
            markers = {(name, fingerprint(state))}
        elif name=="read_result":
            args = arguments or {}
            markers = {(name, args.get("result_id"), args.get("path", ""), args.get("offset", 0),
                fingerprint({k: v for k, v in value.items() if k!="operations"}))}
        elif tool is not None:
            from .capabilities import profile
            from .references import at_path, display_list

            # Full saved payloads, rather than a truncated model preview, prove
            # novelty. Argument changes and new receipt IDs prove no new data.
            card = next((card for card in self.cards.values() if card["result_id"]==value.get("result_id")), None)
            origin = (scope, tool.server, tool.name)
            if card is None:
                markers = {(origin, fingerprint({k: v for k, v in value.items()
                    if k not in {"result_id", "executed", "guidance", "repeated", "objects"}}))}
            else:
                descriptor = profile(tool)
                surface = display_list(card)
                pointer = descriptor.collection if descriptor.collection is not None else surface["path"] if surface else None
                rows = None
                if pointer is not None:
                    try:
                        rows = at_path(card.get("data"), pointer)
                    except QAError:
                        pass
                if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
                    markers = {(origin, "collection"), *((origin, "row", fingerprint(row)) for row in rows)}
                    # Pagination metadata is not new evidence; actual media is.
                    if card.get("content"):
                        markers.add((origin, "content", fingerprint(card["content"])))
                else:
                    markers = {(origin, "payload", fingerprint({k: card[k] for k in ("data", "content") if k in card}))}
            operation = self.operations.get(scope)
            if operation:
                markers.add((origin, "state", operation["state"]))
        else:
            # A new result ID or repeated bookkeeping is not new evidence.
            markers = {(key, fingerprint({k: v for k, v in value.items()
                if k not in {"result_id", "executed", "guidance", "repeated", "objects"}}))}
        fresh = bool(markers-self.seen)
        self.seen.update(markers)
        if not fresh and self.recovering and value.get("result_id") and value.get("executed") is False:
            # Reusing a receipt can resolve a correction once, not restart a loop.
            marker = (key, "correction", self.corrections)
            fresh = marker not in self.seen
            self.seen.add(marker)
        return fresh
