"""Per-turn execution budgets and evidence-based convergence checks."""
from hashlib import sha256
import json

from .context import project
from .contracts import QAError
from .operations import Operations
from .responses import notice


def fingerprint(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


class Execution:
    def __init__(self):
        self.calls, self.stalled = 0, 0
        self.seen, self.cards = set(), {}
        self.failures = {}
        self.corrections = 0
        self.previous_correction = None
        self.recovering = False
        self.operations = Operations()
        self.prepared = {}
        self.stale_scopes, self.blocked = {}, set()
        self.reviewed_failures = set()
        self.discovery_recovered = False
        self.repeated_lookups = set()

    @property
    def can_deliver(self):
        return bool(self.cards) or bool(self.failures)

    @property
    def unfinished_searches(self):
        return [item for item in self.operations.items
            if item.get("search") and not item["search"]["done"]]

    @property
    def finalizing(self):
        return self.settled and all(self.operations.assessment(item) == "accepted"
            for item in self.operations.required)

    @property
    def settled(self):
        """Successful receipts can settle work without supplying all requested content."""
        goals = self.operations.required
        return bool(goals) and not self.unfinished_searches and all(item["state"] == "succeeded"
            and self.operations.result_ids(item)
            and self.operations.assessment(item) in {"accepted", "unavailable", "incomplete"}
            for item in goals)

    def actions(self, loaded, *, planning=False, plan=None, closing=False, continuations=()):
        """Derive the legal decision surface from receipts and execution mode.

        Search continuation is work owned by an existing goal. It does not
        block independent goals or authorize arbitrary direct calls in a plan.
        The caller narrows continuation arguments to the existing search queue.
        """
        from .capabilities import profile

        names = {"read_result", "remember", "request_input", "resolve_resource", "find_artifacts"}
        if not self.operations.items and not self.cards and not self.failures:
            names.add("respond_from_context")
        if not (self.finalizing and all(item.get("direct") and item["output"]=="result" for item in self.operations.required)):
            names.update(("list_mcp_servers", "load_mcp_tools", *loaded))
        if self.can_deliver and not self.unfinished_searches:
            names.add("deliver_results")
        if not planning and not plan and len(self.operations.required) == 1:
            goal = self.operations.required[0]
            if goal.get("direct") and goal.get("search") and not goal["search"]["done"]:
                # A confirmed single-outcome search already has its capability.
                # Scope can still be revised explicitly through remember; it
                # must not drift into unrelated lookups while awaiting keywords.
                names -= {alias for alias, tool in loaded.items()
                    if goal.get("capability") != {"server": tool.server, "name": tool.name}}
        blocked = set()
        for alias, tool in loaded.items():
            if profile(tool).plan_required:
                names.discard(alias)
            scopes = [item for item in self.operations.items if item.get("capability")=={"server": tool.server, "name": tool.name}]
            if scopes and all(item["id"] in self.blocked for item in scopes):
                blocked.add(alias)
                names.discard(alias)
        if planning or plan:
            names -= set(loaded)
        review_pending = plan and plan.get("reviewed") != plan["revision"]
        if plan:
            names.add("remember")
            if review_pending:
                names &= {"remember", "read_result", "load_mcp_tools", "request_input", "find_artifacts"}
                names.add("review_plan")
            else:
                searching = [item for item in self.unfinished_searches
                    if item["state"] not in {"failed", "unknown", "unavailable"} and item["id"] not in self.blocked]
                names.update(alias for alias in set(continuations) & set(loaded) - blocked
                    if any(item.get("capability") == {"server": loaded[alias].server, "name": loaded[alias].name}
                        for item in searching))
        if closing and not self.unfinished_searches and not review_pending and (
                not self.operations.required or self.finalizing):
            names &= {"deliver_results", "remember", "request_input", "respond_from_context"}
        if self.discovery_recovered:
            names -= self.repeated_lookups
        return names

    def recover_discovery(self, status, *, available=False):
        """Offer one ordinary decision to use or inspect relevant capabilities.

        No new model/call budget is allocated and no user operation is inferred.
        Completed or blocked business work keeps its existing recovery policy.
        """
        if (self.discovery_recovered or not (status.get("pending") or available)
                or self.operations.items or self.cards or self.failures):
            return False
        self.discovery_recovered = True
        self.stalled = 0
        return True

    def failure_decision(self, *, planned=False, consume=False):
        """Allow one scope decision for unplanned blocked work, not a replanning loop."""
        blocked = self.operations.blocking()
        if not blocked:
            return None
        goals = self.operations.required
        if goals and all(self.operations.assessment(item) == "unavailable" for item in self.unfinished_searches) and all(
                self.operations.assessment(item) in {"accepted", "unavailable", "incomplete"} for item in goals):
            # A different, safely correctable prerequisite still deserves its
            # existing correction budget, even if another branch is blocked.
            if not any(item["state"] == "failed" and item["attempts"]
                    and self.operations.retryable(item["attempts"][-1]) for item in self.operations.items):
                return self.operations.error()
        known_scope = {key for item in blocked for key in item["attempts"][-1].get("scope", [])}
        if planned or any(self.operations.assessment(item) == "pending" and item["id"] in known_scope for item in goals):
            return None
        markers = {(item["id"], item["attempts"][-1]["key"]) for item in blocked}
        if markers <= self.reviewed_failures:
            return next((error for item in blocked if (error := self.operations.failure(item))), None)
        if consume:
            self.reviewed_failures.update(markers)
        return None

    def progress(self, observations, limit):
        """Count no-gain rounds per operation, not per argument variant or batch."""
        newly_blocked = set()
        for scope, fresh in observations.items():
            self.stale_scopes[scope] = 0 if fresh else self.stale_scopes.get(scope, 0)+1
            if self.stale_scopes[scope]>=limit and scope not in self.blocked:
                self.blocked.add(scope)
                newly_blocked.add(scope)
        return newly_blocked

    def correct(self, error, limit, *, decision=None):
        """Bound corrections; an unchanged rejected decision gets one repair chance.

        Callers supply the semantic proposal and current decision surface,
        without volatile call IDs or rejected-attempt timestamps. Changed
        arguments or newly available evidence retain the ordinary budget.
        """
        self.recovering = True
        marker = None
        if decision is not None:
            try:
                marker = fingerprint([error.code, str(error), error.detail, decision])
            except (TypeError, ValueError):
                pass  # Malformed model values must not break error handling.
        repeated = marker is not None and marker == self.previous_correction
        self.previous_correction = marker
        if repeated or self.corrections>=limit:
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
        detail = {"errors": [
            {"path": list(item["loc"]), "constraint": item["type"], "message": item["msg"][:300]}
            for item in errors[:3]]}
        if any("plan" in item["loc"] for item in errors):
            detail["guidance"] = ("Use remember.plan={steps:[{key,tool,arguments,object?}]}. "
                "Use object=source_step_key for a file source. Runtime derives output kinds, producers and dependencies. "
                "Do not submit outcomes/kind/produces or direct-call metadata. Preserve keys, constraints and requested format.")
        return QAError("invalid_parameters", message, detail=detail)

    notice = staticmethod(notice)

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

    def observe(self, key, value, name=None, arguments=None, context=None, *, scope=None, tool=None, runtime=None):
        if name in {"list_mcp_servers", "load_mcp_tools"}:
            markers = {(name, row["name"]) for row in value.get("items", []) if "name" in row and "error" not in row}
            if name=="load_mcp_tools" and value.get("error"):
                markers.add((name, (arguments or {}).get("server"), value["error"]))
        elif name=="remember":
            state = {"references": (context or {}).get("references")}
            state["operations"] = [{key: item[key] for key in ("id", "description", "target", "output")}
                for item in self.operations.items]
            if runtime is not None:
                # Stable goal IDs do not imply a stable execution plan. Count
                # accepted transitions, never echoed model args or timestamps.
                plan = runtime.get("plan") or {}
                state["planning"] = bool(runtime.get("planning"))
                state["plan"] = {key: plan[key] for key in ("revision", "spec", "operations", "reviewed") if key in plan}
            markers = {(name, fingerprint(state))}
        elif name=="find_artifacts":
            markers = {(name, fingerprint(value.get("data", value)))}
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
        if name == "find_artifacts" and not fresh:
            self.repeated_lookups.add(name)
        self.seen.update(markers)
        if not fresh and self.recovering and value.get("result_id") and value.get("executed") is False:
            # Reusing a receipt can resolve a correction once, not restart a loop.
            marker = (key, "correction", self.corrections)
            fresh = marker not in self.seen
            self.seen.add(marker)
        return fresh
