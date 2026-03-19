# runtime/policy.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Policy:
    deny_tools: List[str] = field(default_factory=list)     # internal names e.g. ["shell.exec"]
    allow_tools: List[str] = field(default_factory=list)    # 可选：空表示不限制
    total_call_budget: int = 100
    per_tool_budget: Dict[str, int] = field(default_factory=dict)  # {"shell.exec": 10}

    def check_allowed(self, internal_tool_name: str) -> None:
        if internal_tool_name in self.deny_tools:
            raise PermissionError(f"Tool denied by policy: {internal_tool_name}")

        if self.allow_tools and internal_tool_name not in self.allow_tools:
            raise PermissionError(f"Tool not in allow list: {internal_tool_name}")