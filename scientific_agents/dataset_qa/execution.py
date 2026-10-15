"""Per-turn execution budgets and evidence-based convergence checks."""
from hashlib import sha256
import json

from .contracts import QAError


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class Execution:
    def __init__(self):
        self.calls, self.stalled = 0, 0
        self.seen, self.cached, self.cards = set(), {}, {}
        self.failures = {}
        self.corrections = 0

    @property
    def can_deliver(self):
        return bool(self.cards) and not self.failures

    def correct(self, error, limit):
        if self.corrections>=limit:
            return error
        self.corrections += 1

    @staticmethod
    def feedback(error, actions):
        value = {"error": error.code, "message": str(error), "executed": False,
            "available_actions": sorted(actions),
            "guidance": "Choose only an available action with valid arguments. Execute requested operations through MCP before delivery; use saved results for already completed calls. Ask request_input if information is missing."}
        if error.detail:
            value["detail"] = error.detail
        return value

    def completed(self, key):
        return next((card for (call, _), card in reversed(self.cards.items()) if call==key), None)

    def require_result(self):
        if self.failures:
            raise next(iter(self.failures.values()))
        if not self.cards:
            raise QAError("mcp_required", "本轮尚未通过MCP执行任务，不能直接交付结果")

    @staticmethod
    def reusable(tool):
        # Read-only does not imply deterministic: random sampling is read-only.
        return (tool is not None and tool.annotations.get("readOnlyHint") is True
            and tool.annotations.get("idempotentHint") is True)

    def observe(self, key, value):
        marker = (key, fingerprint(value))
        fresh = marker not in self.seen
        self.seen.add(marker)
        return fresh
