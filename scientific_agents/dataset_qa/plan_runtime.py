"""Bridge declarative plans to the existing validated MCP execution pipeline."""
from copy import deepcopy
import logging

from jsonschema import Draft202012Validator
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from .capabilities import OBJECT, SUPPORTING, GOAL, TASK, inputs, profile, request_identifiers, resolve_tool, validate_intent
from .contracts import QAError
from .context import encode, same_identity
from .operations import Operations
from .execution import Execution, fingerprint
from .planning import Check, FromStep, Outcome, Plan, ResultContract, Step, Workflow, outcome_status, validate_revision
from .references import at_path


def workflow_definition(definition, loaded, visible=()):
    """Keep hidden capabilities available to planning without duplicating schemas.

    Source identifiers can be supplied by object/inputs, so the planning schema
    must not require the model to invent them. Wire validation stays unchanged.
    """
    if definition["function"]["name"] != "remember":
        return definition
    if "WorkflowStep" not in definition["function"]["parameters"].get("$defs", {}):
        return definition
    catalogue = []
    for tool in loaded.values():
        if tool.alias in visible:
            continue
        descriptor = profile(tool)
        bound = descriptor.bind
        schema = deepcopy(tool.schema)
        if "required" in schema:
            schema["required"] = [name for name in schema["required"] if name not in bound]
        for name in bound:
            field = schema.get("properties", {}).get(name)
            if isinstance(field, dict):
                field["description"] = "Runtime-bound identifier. OMIT from arguments when using object or inputs; do not invent a placeholder."
        item = {"tool": tool.alias, "description": tool.description, "arguments_schema": schema,
            "object_bindings": bound}
        if descriptor.routing:
            item["operations"] = descriptor.routing.operations
            item["outputs"] = descriptor.routing.outputs
        catalogue.append(item)
    if not catalogue:
        return definition
    definition = deepcopy(definition)
    definition["function"]["description"] += (
        " Capabilities below are available inside plan.steps (business arguments only). "
        "For a dependency use object=source_step_key and OMIT its object_bindings parameters from arguments; "
        "runtime supplies the real identifiers. For an individual result value use inputs={parameter:{step,path}}. "
        "Do not invent identifiers or copy placeholder/null values. Other loaded MCP tools may also be used in steps. Catalogue: " + encode(catalogue))
    return definition


def _dependency_blocked(operation):
    return (operation["state"] == "unavailable" and operation.get("unavailable_dependency")
        and not operation["attempts"])


def compile_workflow(workflow, tools, previous=None):
    """Compile intent to the existing strict DAG, without changing business values.

    Only adapter-declared file references may be connected implicitly. Multiple
    sources, collection members and arbitrary scalar inputs require explicit refs.
    """
    resolved = {call.key: resolve_tool(call.tool, tools.loaded) for call in workflow.steps}
    descriptors = {key: profile(tool) for key, tool in resolved.items()}
    old = Plan.model_validate(previous["spec"]) if previous else None
    old_steps = {step.key: step for step in old.steps} if old else {}
    old_outcomes = {outcome.key: outcome for outcome in old.outcomes} if old else {}

    def source(step_key):
        descriptor = descriptors[step_key]
        path = descriptor.artifact.path if descriptor.artifact else descriptor.object
        if path is None:
            raise QAError("invalid_parameters", "来源步骤需要明确的对象位置", detail={
                "step": step_key, "guidance": "Use object={step: supplied_step_key, path: grounded_JSON_pointer}; do not guess a collection member."})
        return FromStep(step=step_key, path=path)

    steps = []
    for call in workflow.steps:
        tool, descriptor = resolved[call.key], descriptors[call.key]
        arguments, bindings = deepcopy(call.arguments), deepcopy(call.inputs)
        validator = Draft202012Validator(tool.schema)
        fields = tool.schema.get("properties", {})
        # A clearly typed reference in the argument slot is the same dependency
        # as inputs[name]. Valid business objects are always kept as literals.
        for name, value in list(arguments.items()):
            if (name not in fields or not isinstance(value, dict)
                    or validator.evolve(schema=fields[name]).is_valid(value)):
                continue
            try:
                ref = FromStep.model_validate(value)
            except ValidationError:
                continue  # Ordinary invalid values retain normal schema diagnostics.
            if name in bindings and bindings[name] != ref:
                raise QAError("invalid_parameters", "同一参数声明了不同的来源", detail={"step": call.key, "path": [name]})
            bindings[name] = ref
            del arguments[name]
        target = call.object
        if isinstance(target, str) and target in resolved:
            target = source(target)
        elif isinstance(target, FromStep) and target.step in resolved and "path" not in target.model_fields_set:
            target = source(target.step)
        consume = descriptor.artifact.consume if descriptor.artifact else None
        # Null is not a placeholder when the business schema accepts it. Only
        # discard a non-nullable placeholder with a declared source binding.
        for name, value in list(arguments.items()):
            if (value is None and name in fields and not validator.evolve(schema=fields[name]).is_valid(None)
                    and (name in bindings or (target is not None and name in descriptor.bind))):
                del arguments[name]
        implicit_placeholder = (consume in arguments and arguments[consume] is None and consume in fields
            and not validator.evolve(schema=fields[consume]).is_valid(None))
        if (target is None and consume and (consume not in arguments or implicit_placeholder) and consume not in bindings
                and consume in descriptor.bind):
            candidates = [step.key for step in steps
                if resolved[step.key].server == tool.server and descriptors[step.key].artifact]
            if len(candidates) > 1:
                raise QAError("invalid_parameters", "存在多个可用来源，请在计划中明确选择", detail={
                    "step": call.key, "sources": candidates, "guidance": "Set this step's object to the intended source step key. No data operation has run."})
            if candidates:
                target = source(candidates[0])
                arguments.pop(consume, None)
        prior = old_steps.get(call.key)
        tool_name = prior.tool if prior and resolve_tool(prior.tool, tools.loaded).alias == tool.alias else tool.alias
        intent = {name: getattr(prior, name) if prior and name not in call.model_fields_set else getattr(call, name)
            for name in ("operation", "output_format")}
        steps.append(Step(key=call.key, tool=tool_name, arguments=arguments, fresh=call.fresh,
            object=target, inputs=bindings, depends_on=list(call.depends_on), **intent))
    consumed = set().union(*(step.dependencies() for step in steps))
    outcomes = []
    for call, step in zip(workflow.steps, steps):
        if call.deliver is True or (call.deliver is None and call.key not in consumed):
            descriptor = descriptors[call.key]
            prior = old_steps.get(step.key)
            step.produces = list(prior.produces) if prior and prior.produces else [call.key]
            for key in step.produces:
                outcome = Outcome(key=key, description=call.description or descriptor.label or resolved[call.key].title,
                    kind=descriptor.result.kind if descriptor.result else resolved[call.key].name,
                    constraints=list(call.constraints), checks=list(call.checks), targets=list(call.targets))
                if key in old_outcomes:
                    # Revision input need not repeat runtime-owned identities or
                    # checks. Existing requirements can be strengthened, never erased.
                    original = old_outcomes[key]
                    if not call.description:
                        outcome.description = original.description
                    for field in ("constraints", "checks", "targets"):
                        values = getattr(outcome, field)
                        values[:0] = [value for value in getattr(original, field) if value not in values]
                outcomes.append(outcome)
        elif call.checks or call.targets:
            raise QAError("invalid_parameters", "来源结果的验收条件需要关联到该结果", detail={
                "step": call.key, "guidance": "Set deliver=true to assess this prerequisite as an outcome; do not silently drop its checks."})
    plan = Plan(outcomes=outcomes, steps=steps)  # Validate references/cycles before traversing ancestors.
    by_key = {step.key: step for step in plan.steps}
    by_outcome = {outcome.key: outcome for outcome in plan.outcomes}
    for step in plan.steps:
        if not step.produces:
            continue
        ancestors = step.dependencies()
        while (expanded := ancestors | set().union(*(by_key[key].dependencies() for key in ancestors))) != ancestors:
            ancestors = expanded
        inherited = [value for call in workflow.steps if call.key in ancestors for value in call.constraints]
        for key in step.produces:
            by_outcome[key].constraints = list(dict.fromkeys([*by_outcome[key].constraints, *inherited]))
    return Plan.model_validate(plan.model_dump())


async def install_plan(service, user, sid, plan, tools, execution, payload, context):
    if isinstance(plan, Workflow):
        plan = compile_workflow(plan, tools, payload.get("plan"))
    plan = plan.model_copy(deep=True)
    for step in plan.steps:
        tool = resolve_tool(step.tool, tools.loaded)
        contract = profile(tool).result
        if contract and step.produces:
            for argument, path in contract.argument_paths.items():
                if argument in step.inputs:
                    continue  # Checked against the resolved value at the shared execution boundary.
                parameter = tool.schema.get("properties", {}).get(argument, {})
                if argument not in step.arguments and "default" not in parameter:
                    continue
                value = step.arguments.get(argument, parameter.get("default"))
                if isinstance(value, (dict, list)):
                    continue  # Structured values use the same runtime contract, without growing plan context.
                check = Check(path=path, test="equals", value=value)
                for outcome in plan.outcomes:
                    if outcome.key not in step.produces:
                        continue
                    existing = [item for item in outcome.checks if item.path == path and item.test == "equals"]
                    if any(not Draft202012Validator({"const": value}).is_valid(item.value) for item in existing):
                        raise QAError("invalid_parameters", "终端步骤参数与成果要求不一致，请保留请求要求修订步骤")
                    if not any(not item.optional for item in existing):
                        outcome.checks.append(check)
        if contract and contract.target_paths:
            for outcome in plan.outcomes:
                if outcome.key in step.produces:
                    soft = [check for check in outcome.checks if check.path in contract.target_paths and check.test == "at_least"]
                    outcome.targets.extend(check for check in soft if check not in outcome.targets)
                    outcome.checks = [check for check in outcome.checks if check not in soft]
                    for index, check in enumerate(outcome.checks):
                        if check.path in contract.target_paths and check.test == "equals" and type(check.value) in {int, float}:
                            value = int(check.value) if isinstance(check.value, float) and check.value.is_integer() else check.value
                            target = Check(path=check.path, test="at_least", value=value)
                            if target not in outcome.targets:
                                outcome.targets.append(target)
                            outcome.checks[index] = Check(path=check.path, test="at_most", value=value)
    plan = Plan.model_validate(plan.model_dump())  # Adapter-derived checks obey the same bounded contract.
    previous = payload.get("plan")
    validate_revision(previous, plan)
    previous_spec = Plan.model_validate(previous["spec"]).model_dump() if previous else None
    spec = plan.model_dump()
    requested = [step.object for step in plan.steps if isinstance(step.object, str)]
    handles = await service._object_index(user, sid, context, payload, requested)
    operations = Operations(execution.operations.items)
    same_targets = not previous or all(not isinstance(step.object, str)
        or (operations.get(previous["operations"].get(step.key)) or {}).get("target") == handles.get(step.object)
        for step in plan.steps)
    if previous and same_identity(previous_spec, spec) and same_targets:
        return  # Identical bookkeeping is not a new revision or a new review.
    revision = previous["revision"]+1 if previous else 1
    if revision > service.gateway.limits.max_corrections+1:
        raise QAError("invalid_parameters", "计划修订达到本轮预算，请依据已有成果完成答复")
    mapping, contracts, reusable = {}, {}, {}
    outcomes = {outcome.key: outcome for outcome in plan.outcomes}
    old_steps = {step["key"]: step for step in (previous_spec or {}).get("steps", [])}
    for step in plan.steps:
        tool = resolve_tool(step.tool, tools.loaded)
        descriptor = profile(tool)
        contract = descriptor.result or ResultContract(kind=tool.name)
        if any(outcomes[key].kind != contract.kind for key in step.produces):
            raise QAError("invalid_parameters", "步骤的返回类型不能满足所需成果", detail={"step": step.key, "kind": contract.kind})
        contracts[step.key] = contract.model_dump()
        if any(key in step.arguments for key in (OBJECT, SUPPORTING, GOAL)):
            raise QAError("invalid_parameters", "计划应使用对象和成果字段，不需要重复填写执行控制参数")
        directive = step.arguments.get(TASK)
        if directive is not None and not isinstance(directive, dict):
            raise QAError("invalid_parameters", "步骤任务参数须符合工具定义")
        if (directive or {}).get("complete_request") is True:
            raise QAError("invalid_parameters", "多步骤计划由成果验收完成，单个步骤不能声明完成整个请求")
        target = None
        if isinstance(step.object, str):
            if step.object not in handles:
                raise QAError("invalid_parameters", "计划对象须引用已提供的来源", detail={"object": step.object})
            target = handles[step.object]
            await service._target_record(user, sid, target)
        if set(step.inputs) & set(step.arguments) or any(key not in tool.schema.get("properties", {}) for key in step.inputs):
            raise QAError("invalid_parameters", "来源绑定须使用工具参数名，且不能覆盖已给出的参数")
        # No prerequisite should run merely to discover that an already known
        # format, bound or required argument was invalid. Source-dependent and
        # cross-field constraints still receive full validation before dispatch.
        deferred = set(step.inputs)
        if isinstance(step.object, FromStep):
            if not descriptor.bind:
                raise QAError("invalid_parameters", "此能力未声明对象参数绑定，请使用明确的输入参数引用")
            deferred.update(descriptor.bind)
        record = await service._target_record(user, sid, target) if target else None
        concrete = inputs(tool, step.arguments, record)
        concrete = {key: value for key, value in concrete.items() if key not in deferred or key in step.arguments}
        try:
            format_inputs = {name for name, path in contract.argument_paths.items()
                if descriptor.artifact and path == descriptor.artifact.path + "/format"}
            validate_intent(tool, step, None if format_inputs & deferred else concrete)
            tools.validate(tool.alias, concrete, deferred=deferred)
        except QAError as exc:
            exc.detail = {**(exc.detail or {}), "step": step.key, "tool": tool.alias,
                "phase": "plan_validation", "dispatched": False}
            raise
        if descriptor.bind and step.object is None:
            grounded = set(step.inputs) | set(request_identifiers(tool, concrete, payload.get("message", "")))
            missing = set(descriptor.bind) - grounded
            if missing:
                candidates = [other.key for other in plan.steps if other.key != step.key
                    and resolve_tool(other.tool, tools.loaded).server == tool.server
                    and profile(resolve_tool(other.tool, tools.loaded)).artifact]
                raise QAError("invalid_parameters", "计划中的操作尚未绑定可信来源，尚未执行任何新步骤", detail={
                    "step": step.key, "fields": sorted(missing), "source_steps": candidates,
                    "available_objects": list(handles)[:12],
                    "phase": "plan_validation", "dispatched": False,
                    "guidance": "Revise this step: set object to the intended source step key (or a supplied object handle) and remove its bound identifiers from arguments. For a scalar use inputs={parameter:{step,path}}. Keep completed steps unchanged; do not call MCP directly."})
        signature = fingerprint({**step.model_dump(exclude={"key", "produces", "fresh"}),
            "tool": [tool.server, tool.name], "arguments": concrete,
            "object": target if isinstance(step.object, str) else step.model_dump()["object"]})
        old_id = (previous or {}).get("operations", {}).get(step.key)
        old = operations.get(old_id) if old_id else None
        changed = False
        if old is not None:
            old_execution = {key: value for key, value in old_steps[step.key].items() if key != "produces"}
            new_execution = step.model_dump(exclude={"produces"})
            if not same_identity(old_execution, new_execution) or (isinstance(step.object, str) and old.get("target") != target):
                changed = True
                rejected = all(attempt["state"] == "rejected" for attempt in old["attempts"])
                safe_failure = (old["state"] == "failed" and old["attempts"]
                    and old["attempts"][-1].get("retry_safe") is True)
                if not (((old["state"] == "pending" or _dependency_blocked(old)) and rejected) or safe_failure):
                    raise QAError("invalid_parameters", "已执行的步骤不能改写；保留其证据并为必要的新操作添加步骤")
                if list(previous["operations"].values()).count(old_id) > 1:
                    # A revised consumer must not mutate a shared receipt or
                    # change another consumer's still-valid input binding.
                    old = None
        if old is not None:
            if changed:
                old.update(capability={"server": tool.server, "name": tool.name}, target=target,
                    state="pending", plan_retry=revision)
                old.pop("unavailable_dependency", None)
            operation_id = old_id
        elif Execution.reusable(tool) and not step.fresh and signature in reusable:
            operation_id = reusable[signature]
        else:
            if len(operations.items) >= 16:
                raise QAError("invalid_parameters", "本轮步骤较多，请分批处理")
            operation_id = "op"+str(len(operations.items)+1)
            while operations.get(operation_id):
                operation_id += "_"
            operations.items.append({"id": operation_id, "description": tool.title,
                "capability": {"server": tool.server, "name": tool.name}, "target": target,
                "output": "result", "direct": False, "planned": True, "required": bool(step.produces),
                "state": "pending", "attempts": [], "plan_step": step.key})
        item = operations.get(operation_id)
        item["public_label"] = descriptor.label or tool.title
        item["plan_fresh"] = step.fresh
        if not step.inputs and not isinstance(step.object, FromStep) and not item["attempts"]:
            invocation = fingerprint([tool.server, tool.name, concrete])
            if operations.blocked_receipt(invocation):
                try:
                    operations.start(operation_id, fingerprint([operation_id, tool.alias, concrete]),
                        {"server": tool.server, "name": tool.name}, Execution.reusable(tool), invocation)
                except QAError:
                    pass  # Retain the original failed receipt; installing a plan never retries it.
        mapping[step.key] = operation_id
        if Execution.reusable(tool) and not step.fresh:
            reusable[signature] = operation_id
    for operation_id in set(mapping.values()):
        produced = [key for step in plan.steps if mapping[step.key] == operation_id for key in step.produces]
        item = operations.get(operation_id)
        item.update(required=bool(produced), plan_step=next(step.key for step in plan.steps if mapping[step.key] == operation_id),
            description="；".join(outcomes[key].description for key in produced)[:240] or item["description"])
    # A revision may remove unused unexecuted auxiliary steps, but not silently
    # erase previously declared user work or receipts still needed by a source.
    for item in operations.required:
        if item["id"] not in mapping.values():
            if item["id"] in (previous or {}).get("operations", {}).values():
                # Outcomes and constraints were retained above. A superseded
                # producer remains an immutable auxiliary receipt, not a goal.
                item["required"] = False
            else:
                raise QAError("invalid_parameters", "新计划遗漏了已登记的必要操作，请保留原有成果")
    execution.operations = operations
    payload["operations"] = operations.items
    labels = deepcopy((previous or {}).get("labels", {}))
    if not payload.get("diagnostics_exposed"):
        labels.update({outcome.key: outcome.description for outcome in plan.outcomes})
    payload["plan"] = {"version": 1, "revision": revision, "spec": spec,
        "operations": mapping, "contracts": contracts, "labels": labels}
    logging.getLogger("flow.dataset_qa").info("Plan installed: revision=%s sources=%s", revision,
        encode([{"step": step.key, "tool": step.tool, "depends_on": sorted(step.dependencies()),
            "object": step.object.model_dump() if isinstance(step.object, FromStep) else bool(step.object),
            "inputs": sorted(step.inputs), "arguments": sorted(step.arguments)} for step in plan.steps]))


def confirm_plan(payload, values):
    saved = payload.get("plan")
    if (not saved or values.revision != saved["revision"]
            or len(values.covered) != len(set(values.covered))
            or set(values.covered) != {item["key"] for item in saved["spec"]["outcomes"]}):
        raise QAError("invalid_parameters", "请对照原请求逐项核对当前计划的全部成果")
    saved["reviewed"] = saved["revision"]
    return {"reviewed": True, "revision": saved["revision"]}


def scheduled_reply(saved, execution, tools, limit):
    """Return ready work only. No model calls, retries, or speculative sources."""
    if not saved:
        return None, {}
    plan = Plan.model_validate(saved["spec"])
    by_key = {step.key: step for step in plan.steps}
    operations = execution.operations
    cards = {card["result_id"]: card for card in execution.cards.values()}
    saved["acceptance"] = outcome_status(saved, operations, cards.values())
    calls, bindings = [], {}

    # Dependency blockage is derived from current receipts, not an execution
    # receipt itself. A repaired/replaced upstream can reopen unexecuted work.
    # Never reset a step with its own attempt, including an uncertain write.
    for step in plan.steps:
        operation = operations.get(saved["operations"][step.key])
        if _dependency_blocked(operation):
            operation["state"] = "pending"
            operation.pop("unavailable_dependency")

    # Close descendants only when a prerequisite is terminally unavailable.
    # Incomplete/ambiguous evidence stays open for a meaningful correction.
    for _ in plan.steps:
        changed = False
        for step in plan.steps:
            operation = operations.get(saved["operations"][step.key])
            if operation["state"] != "pending" or operation["attempts"]:
                continue
            for key in step.dependencies():
                dependency = operations.get(saved["operations"][key])
                ids = operations.result_ids(dependency)
                contract = ResultContract.model_validate(saved["contracts"][key])
                unavailable = dependency["state"] in {"failed", "unknown", "unavailable"}
                unavailable |= bool(dependency["state"] == "succeeded" and ids and all(
                    rid in cards and contract.assess(cards[rid].get("data")) == "unavailable" for rid in ids))
                if unavailable:
                    operation.update(state="unavailable", unavailable_dependency=dependency["id"])
                    changed = True
                    break
        if not changed:
            break
    saved["acceptance"] = outcome_status(saved, operations, cards.values())
    if saved.get("reviewed") != saved["revision"]:
        return None, {}  # Dependency status is derived even before approval; execution is not.

    def source(ref):
        operation = operations.get(saved["operations"][ref.step])
        ids = operations.result_ids(operation)
        if len(ids) != 1 or ids[0] not in cards:
            raise QAError("invalid_parameters", "依赖步骤的来源不唯一，请先明确需要使用的结果")
        value = at_path(cards[ids[0]].get("data"), ref.path)
        return value, {"result_id": ids[0], "path": ref.path, "kind": "object"}

    for step in plan.steps:
        operation = operations.get(saved["operations"][step.key])
        if operation["id"] in bindings.values():
            continue
        if operation["state"] != "pending" or (operation["attempts"] and operation.get("plan_retry") != saved["revision"]):
            continue
        dependencies = [operations.get(saved["operations"][key]) for key in step.dependencies()]
        if any(item["state"] != "succeeded" or (item.get("search") and not item["search"]["done"]) for item in dependencies):
            continue
        usable = True
        for key in step.dependencies():
            # A successful receipt can still violate a declared hard check.
            # Gate only consumers of that step, not independent work or soft
            # quantity targets. Shared receipts retain each step's own checks.
            if any(saved["acceptance"][outcome]["state"] != "accepted" for outcome in by_key[key].produces):
                usable = False
            contract = ResultContract.model_validate(saved["contracts"][key])
            ids = operations.result_ids(operations.get(saved["operations"][key]))
            if not ids or any(rid not in cards or contract.assess(cards[rid].get("data")) != "accepted" for rid in ids):
                usable = False
        if not usable:
            continue
        tool = resolve_tool(step.tool, tools.loaded)
        arguments = deepcopy(step.arguments)
        try:
            for name, ref in step.inputs.items():
                arguments[name] = source(ref)[0]
            if isinstance(step.object, FromStep):
                _, operation["target"] = source(step.object)
        except QAError as exc:
            # Hand only this decision back to ReAct. Independent ready steps may
            # still run; the same missing pointer is never polled automatically.
            saved.setdefault("decisions", {})[step.key] = {"code": exc.code,
                "guidance": "Read the actual dependency result and revise this unexecuted step's source pointer or ask for the unresolved choice."}
            continue
        call_id = f"plan-{saved['revision']}-{step.key}"
        calls.append({"id": call_id, "name": tool.alias, "args": arguments})
        bindings[call_id] = operation["id"]
        if len(calls) >= limit:
            break
    return (AIMessage(content="", tool_calls=calls), bindings) if calls else (None, {})
