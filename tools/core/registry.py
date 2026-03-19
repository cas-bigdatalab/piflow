from __future__ import annotations

import time
import uuid
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from tools.core.base import ToolSpec, ToolResult
from tools.core.naming import to_external_name, to_internal_name
from runtime.policy import Policy
from runtime.events import event_bus

log = logging.getLogger("flow.tools")


MaybeAwaitable = Union[Any, Awaitable[Any]]
ToolFunc = Callable[..., MaybeAwaitable]

HookBefore = Callable[[str, Dict[str, Any]], None]
HookAfter = Callable[[str, Dict[str, Any], ToolResult, float], None]


@dataclass
class ToolRecord:
    spec: ToolSpec
    func: ToolFunc
    external_name: str


class ToolRegistry:
    """
    Tool registry.

    Stores canonical internal tool names (with namespace).
    Generates external tool names for LangChain / deepagents usage.
    Maintains internal <-> external mapping.
    """

    def __init__(self, policy: Optional[Policy] = None):

        self._by_internal: Dict[str, ToolRecord] = {}
        self._internal_by_external: Dict[str, str] = {}

        self._policy = policy or Policy()

        self._before_hooks: List[HookBefore] = []
        self._after_hooks: List[HookAfter] = []

        # metrics
        self.total_calls = 0
        self.calls_by_tool: Dict[str, int] = {}

    # ----------------------------
    # Hooks
    # ----------------------------

    def add_before_hook(self, hook: HookBefore) -> None:
        self._before_hooks.append(hook)

    def add_after_hook(self, hook: HookAfter) -> None:
        self._after_hooks.append(hook)

    # ----------------------------
    # Tool registration
    # ----------------------------

    def register(self, spec: ToolSpec, func: ToolFunc) -> None:

        internal = spec.name

        if internal in self._by_internal:
            raise ValueError(f"Tool already registered: {internal}")

        external = to_external_name(internal)

        if external in self._internal_by_external:
            raise ValueError(
                f"External tool name collision: {external} from {internal}"
            )

        self._by_internal[internal] = ToolRecord(
            spec=spec,
            func=func,
            external_name=external,
        )

        self._internal_by_external[external] = internal

    # ----------------------------
    # Query helpers
    # ----------------------------

    def has(self, internal_name: str) -> bool:
        return internal_name in self._by_internal

    def has_external(self, external_name: str) -> bool:
        return external_name in self._internal_by_external

    def internal_name_from_external(self, external_name: str) -> str:

        return self._internal_by_external.get(external_name) or to_internal_name(
            external_name
        )

    def get_record_by_internal(self, internal_name: str) -> ToolRecord:

        if internal_name not in self._by_internal:
            raise KeyError(f"Tool not found: {internal_name}")

        return self._by_internal[internal_name]

    def list_records(self) -> List[ToolRecord]:
        return list(self._by_internal.values())

    def list_tools(self) -> List[str]:
        return list(self._by_internal.keys())

    # ----------------------------
    # Metrics / budget
    # ----------------------------

    def _bump_budget(self, internal_name: str) -> None:

        self.total_calls += 1

        self.calls_by_tool[internal_name] = (
            self.calls_by_tool.get(internal_name, 0) + 1
        )

        if self.total_calls > self._policy.total_call_budget:
            raise RuntimeError(
                f"Total tool call budget exceeded: "
                f"{self.total_calls} > {self._policy.total_call_budget}"
            )

        limit = self._policy.per_tool_budget.get(internal_name)

        if limit is not None and self.calls_by_tool[internal_name] > limit:
            raise RuntimeError(
                f"Tool budget exceeded for {internal_name}: "
                f"{self.calls_by_tool[internal_name]} > {limit}"
            )

    # ----------------------------
    # Tool execution
    # ----------------------------

    async def call_internal(
        self,
        internal_name: str,
        kwargs: Dict[str, Any],
    ) -> ToolResult:

        trace_id = uuid.uuid4().hex

        # emit tool_called
        event_bus.emit(
            "tool_called",
            {
                "tool": internal_name,
                "args": kwargs,
            },
            trace_id=trace_id,
        )

        log.info("tool call internal=%s args=%s", internal_name, kwargs)

        self._policy.check_allowed(internal_name)

        self._bump_budget(internal_name)

        for h in self._before_hooks:
            h(internal_name, kwargs)

        rec = self.get_record_by_internal(internal_name)

        t0 = time.time()

        try:

            out = rec.func(**kwargs)

            if hasattr(out, "__await__"):
                out = await out  # type: ignore

            if isinstance(out, ToolResult):

                result = out

                if result.trace_id is None:
                    result.trace_id = trace_id

            else:

                result = ToolResult(
                    success=True,
                    output=out,
                    trace_id=trace_id,
                )

        except Exception as e:

            # emit tool_error
            event_bus.emit(
                "tool_error",
                {
                    "tool": internal_name,
                    "error": str(e),
                },
                trace_id=trace_id,
            )

            result = ToolResult(
                success=False,
                output=None,
                error=str(e),
                trace_id=trace_id,
            )

        cost = time.time() - t0

        # emit tool_finished
        event_bus.emit(
            "tool_finished",
            {
                "tool": internal_name,
                "success": result.success,
                "duration": cost,
                "output": result.output,
            },
            trace_id=result.trace_id,
        )

        if result.success:
            log.info(
                "tool result internal=%s success=%s trace_id=%s cost=%.3fs output=%s",
                internal_name,
                result.success,
                result.trace_id,
                cost,
                result.output,
            )
        else:
            log.error(
                "tool result internal=%s success=%s trace_id=%s cost=%.3fs error=%s",
                internal_name,
                result.success,
                result.trace_id,
                cost,
                result.error,
            )

        for h in self._after_hooks:
            h(internal_name, kwargs, result, cost)

        return result

    # ----------------------------
    # Reset / clear
    # ----------------------------

    def clear(self) -> None:

        self._by_internal.clear()
        self._internal_by_external.clear()

        self.total_calls = 0
        self.calls_by_tool.clear()

        self._before_hooks.clear()
        self._after_hooks.clear()


# --------------------------------
# Global singleton
# --------------------------------

registry = ToolRegistry()
