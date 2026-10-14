"""Per-turn execution budgets and evidence-based convergence checks."""
from hashlib import sha256
import json


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class Execution:
    def __init__(self):
        self.calls, self.stalled = 0, 0
        self.seen, self.cached, self.cards = set(), {}, {}

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
