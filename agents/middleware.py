# agents/middleware.py
from __future__ import annotations

import logging
from typing import Any, Dict

from tools.core.base import ToolResult
from tools.core.registry import ToolRegistry

log = logging.getLogger("flow.agent")


def install_registry_hooks(registry: ToolRegistry) -> None:
    if getattr(registry, "_flow_hooks_installed", False):
        return

    def before(internal_name: str, kwargs: Dict[str, Any]) -> None:
        log.info("tool_called internal=%s args=%s", internal_name, kwargs)

    def after(internal_name: str, kwargs: Dict[str, Any], result: ToolResult, cost_sec: float) -> None:
        preview = ""
        if result.success:
            preview = str(result.output)
        else:
            preview = f"ERR: {result.error}"
        if len(preview) > 300:
            preview = preview[:300] + "..."

        log.info(
            "tool_finished internal=%s success=%s cost=%.3fs trace_id=%s preview=%s",
            internal_name, result.success, cost_sec, result.trace_id, preview
        )

    registry.add_before_hook(before)
    registry.add_after_hook(after)
    setattr(registry, "_flow_hooks_installed", True)
