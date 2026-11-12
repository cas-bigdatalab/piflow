"""Versioned outcome contracts and dependency scheduling, without model execution.

Plans contain only intent, parameters and source pointers. Receipts remain in the
existing operations ledger; neither a planner nor a review can invent success.
"""
from copy import deepcopy
from typing import Annotated, Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .context import encode, pointer_tokens
from .contracts import QAError
from .references import at_path


Key = Annotated[str, Field(min_length=1, max_length=48, pattern=r"^[A-Za-z0-9_-]+$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Check(Contract):
    path: str = Field(max_length=1000)
    test: Literal["exists", "equals", "at_least", "at_most"] = "exists"
    value: str | int | float | bool | None = None
    optional: bool = False

    @model_validator(mode="after")
    def valid(self):
        pointer_tokens(self.path)
        if self.test in {"at_least", "at_most"} and (isinstance(self.value, bool) or not isinstance(self.value, (int, float))):
            raise ValueError("A numeric check requires a finite number.")
        return self

    def matches(self, data):
        try:
            actual = at_path(data, self.path)
        except QAError:
            return self.optional
        if self.test == "exists":
            return actual is not None
        if self.test == "equals":
            return Draft202012Validator({"const": self.value}).is_valid(actual)
        actual = len(actual) if isinstance(actual, (list, dict)) else actual
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return False
        return actual >= self.value if self.test == "at_least" else actual <= self.value


class ResultContract(Contract):
    """Adapter-owned result semantics; no matching of user wording."""
    kind: str = Field(min_length=1, max_length=100)
    requires: list[Check] = Field(default_factory=list, max_length=16)
    unavailable_when: list[Check] = Field(default_factory=list, max_length=8)
    target_paths: list[str] = Field(default_factory=list, max_length=8,
        description="Adapter-declared quantities whose shortfall is reported without blocking usable results.")
    argument_paths: dict[str, str] = Field(default_factory=dict, max_length=8,
        description="Result fields that must equal actual tool input values, e.g. an output format.")

    def assess(self, data):
        if self.unavailable_when and all(check.matches(data) for check in self.unavailable_when):
            return "unavailable"
        return "accepted" if all(check.matches(data) for check in self.requires) else "incomplete"

    def validate_arguments(self, data, arguments):
        """One output contract for direct, planned and dependency-bound calls."""
        if not self.argument_paths or self.assess(data) == "unavailable":
            return
        mismatches = []
        for argument, path in self.argument_paths.items():
            if argument not in arguments:
                continue  # An omitted optional input is not an explicit constraint.
            try:
                actual = at_path(data, path)
            except QAError:
                mismatches.append(path)
                continue
            if not Draft202012Validator({"const": arguments[argument]}).is_valid(actual):
                mismatches.append(path)
        if mismatches:
            raise QAError("invalid_result", "工具结果与请求参数不一致，未确认为已完成", 502,
                detail={"paths": mismatches, "dispatched": True})


class Outcome(Contract):
    key: Key
    description: str = Field(min_length=1, max_length=240)
    kind: str = Field(min_length=1, max_length=100, description="Advertised output kind; schema is not records, job submission is not an artifact.")
    constraints: list[Annotated[str, Field(min_length=1, max_length=300)]] = Field(default_factory=list, max_length=12, description="Preserve user scope, counts and rules.")
    checks: list[Check] = Field(default_factory=list, max_length=16, description="Checks on full results. Empty search results are valid.")
    targets: list[Check] = Field(default_factory=list, max_length=16, description="Desired quantities; report shortfalls without blocking usable artifacts.")


class FromStep(Contract):
    step: Key
    path: str = Field(default="", max_length=1000, description="JSON Pointer into the saved result data, never a model-generated value.")

    @model_validator(mode="after")
    def valid(self):
        pointer_tokens(self.path)
        return self


class Step(Contract):
    key: Key
    tool: str = Field(min_length=1, max_length=200)
    arguments: dict = Field(default_factory=dict)
    fresh: bool = Field(default=False, description="True only for an explicitly independent fresh execution. Random/non-idempotent tools are never coalesced.")
    object: str | FromStep | None = Field(default=None, description="Supplied handle or dependency object pointer; resolve ambiguity first.")
    inputs: dict[str, FromStep] = Field(default_factory=dict, max_length=16)
    depends_on: list[Key] = Field(default_factory=list, max_length=16)
    produces: list[Key] = Field(default_factory=list, max_length=16, description="User outcomes completed by this step; empty means an auxiliary prerequisite.")

    def dependencies(self):
        refs = [*self.inputs.values(), *([self.object] if isinstance(self.object, FromStep) else [])]
        return set(self.depends_on) | {ref.step for ref in refs}


class Plan(Contract):
    outcomes: list[Outcome] = Field(min_length=1, max_length=16)
    steps: list[Step] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def valid(self):
        keys, outcomes = {step.key for step in self.steps}, {outcome.key for outcome in self.outcomes}
        if len(keys) != len(self.steps) or len(outcomes) != len(self.outcomes):
            raise ValueError("Step and outcome keys must be unique in their respective lists.")
        produced = [key for step in self.steps for key in step.produces]
        if set(produced) != outcomes or len(produced) != len(outcomes):
            raise ValueError("Each outcome needs exactly one terminal producer; auxiliary steps produce no outcome.")
        pending = {step.key: step.dependencies() for step in self.steps}
        if any(not deps <= keys for deps in pending.values()):
            raise ValueError("Dependencies must name steps in this plan.")
        while pending:
            ready = {key for key, deps in pending.items() if not deps & pending.keys()}
            if not ready:
                raise ValueError("Dependencies must form an acyclic graph.")
            pending = {key: deps for key, deps in pending.items() if key not in ready}
        needed = {step.key for step in self.steps if step.produces}
        by_key = {step.key: step for step in self.steps}
        while (expanded := needed | set().union(*(by_key[key].dependencies() for key in needed))) != needed:
            needed = expanded
        if needed != keys:
            raise ValueError("Every auxiliary step must support a requested outcome.")
        if len(encode(self.model_dump())) > 12000:
            raise ValueError("Plan exceeds the bounded intent contract.")
        return self


class Review(Contract):
    revision: int = Field(ge=1)
    covered: list[Key] = Field(min_length=1, max_length=16, description="All outcome keys, after comparing the original request, selections and constraints with this plan. If any requirement is missing, revise remember.plan instead of confirming.")


def validate_revision(previous, plan):
    """Rewording cannot drop requirements or replay completed work."""
    if not previous:
        return
    old = Plan.model_validate(previous["spec"])
    current = {outcome.key: outcome for outcome in plan.outcomes}
    for outcome in old.outcomes:
        value = current.get(outcome.key)
        if (value is None or value.kind != outcome.kind
                or not set(outcome.constraints) <= set(value.constraints)
                or not all(check in value.checks for check in outcome.checks)
                or not all(check in value.targets for check in outcome.targets)):
            raise QAError("invalid_parameters", "计划修订须保留尚需交付的成果及原有要求")


def plan_view(saved, operations):
    if not saved:
        return None
    plan = Plan.model_validate(saved["spec"])
    return {"revision": saved["revision"], "reviewed": saved.get("reviewed") == saved["revision"],
        "outcomes": [outcome.model_dump() for outcome in plan.outcomes],
        "steps": [{**step.model_dump(exclude_defaults=True),
            "state": (operations.get(saved["operations"][step.key]) or {}).get("state", "pending")}
            for step in plan.steps], "acceptance": deepcopy(saved.get("acceptance", {}))}


def outcome_status(saved, operations, cards):
    """Use complete persisted data, never a truncated model preview."""
    plan = Plan.model_validate(saved["spec"])
    by_id = {card["result_id"]: card for card in cards}
    outcomes = {outcome.key: outcome for outcome in plan.outcomes}
    status = {}
    for step in plan.steps:
        operation = operations.get(saved["operations"][step.key])
        ids = operations.result_ids(operation) if operation else []
        contract = ResultContract.model_validate(saved["contracts"][step.key])
        for key in step.produces:
            state = "pending"
            if (operation and operation["state"] == "succeeded" and ids and all(rid in by_id for rid in ids)
                    and (not operation.get("search") or operation["search"]["done"])):
                assessments = [contract.assess(by_id[rid].get("data")) for rid in ids]
                if all(item == "unavailable" for item in assessments):
                    state = "unavailable"
                elif all(item == "accepted" for item in assessments):
                    state = "accepted" if all(all(check.matches(by_id[rid].get("data"))
                        for check in outcomes[key].checks) for rid in ids) else "incomplete"
                else:
                    state = "incomplete"
            elif operation and operation["state"] in {"failed", "unknown", "unavailable"}:
                state = "unavailable"
            status[key] = {"state": state, "result_ids": ids}
            if outcomes[key].targets:
                status[key]["targets_met"] = bool(ids) and all(rid in by_id and all(
                    check.matches(by_id[rid].get("data")) for check in outcomes[key].targets) for rid in ids)
    return status


def require_delivery(saved, operations, cards):
    if not saved:
        return
    status = outcome_status(saved, operations, cards)
    saved["acceptance"] = status
    if saved.get("reviewed") != saved["revision"] or any(value["state"] not in {"accepted", "unavailable"} for value in status.values()):
        raise QAError("invalid_delivery", "请求的成果尚未全部核实，请继续必要操作或依据已有内容说明可提供的部分", detail={
            "outcomes": status, "review_required": saved.get("reviewed") != saved["revision"]})
