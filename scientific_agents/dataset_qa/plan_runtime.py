"""Bridge declarative plans to the existing validated MCP execution pipeline."""
from copy import deepcopy

from langchain_core.messages import AIMessage

from .capabilities import OBJECT, SUPPORTING, GOAL, TASK, inputs, profile, resolve_tool
from .contracts import QAError
from .operations import Operations
from .execution import Execution, fingerprint
from .planning import FromStep, Plan, ResultContract, outcome_status, validate_revision
from .references import at_path


async def install_plan(service, user, sid, plan, tools, execution, payload, context):
    previous = payload.get("plan")
    validate_revision(previous, plan)
    spec = plan.model_dump()
    requested = [step.object for step in plan.steps if isinstance(step.object, str)]
    handles = await service._object_index(user, sid, context, payload, requested)
    operations = Operations(execution.operations.items)
    same_targets = not previous or all(not isinstance(step.object, str)
        or (operations.get(previous["operations"].get(step.key)) or {}).get("target") == handles.get(step.object)
        for step in plan.steps)
    if previous and previous["spec"] == spec and same_targets:
        return  # Identical bookkeeping is not a new revision or a new review.
    revision = previous["revision"]+1 if previous else 1
    if revision > service.gateway.limits.max_corrections+1:
        raise QAError("invalid_parameters", "计划修订达到本轮预算，请依据已有成果完成答复")
    mapping, contracts, reusable = {}, {}, {}
    outcomes = {outcome.key: outcome for outcome in plan.outcomes}
    old_steps = {step["key"]: step for step in (previous or {}).get("spec", {}).get("steps", [])}
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
        # Validate concrete arguments now; delayed parameters are validated after
        # their actual source exists, through the same dispatch path as ReAct.
        concrete = step.arguments
        if not step.inputs and not isinstance(step.object, FromStep):
            record = await service._target_record(user, sid, target) if target else None
            concrete = inputs(tool, step.arguments, record)
            tools.validate(tool.alias, concrete)
        signature = fingerprint({**step.model_dump(exclude={"key", "produces", "fresh"}),
            "tool": [tool.server, tool.name], "arguments": concrete,
            "object": target if isinstance(step.object, str) else step.model_dump()["object"]})
        old_id = (previous or {}).get("operations", {}).get(step.key)
        old = operations.get(old_id) if old_id else None
        changed = False
        if old is not None:
            old_execution = {key: value for key, value in old_steps[step.key].items() if key != "produces"}
            new_execution = step.model_dump(exclude={"produces"})
            if old_execution != new_execution or (isinstance(step.object, str) and old.get("target") != target):
                changed = True
                rejected = all(attempt["state"] == "rejected" for attempt in old["attempts"])
                safe_failure = (old["state"] == "failed" and old["attempts"]
                    and old["attempts"][-1].get("retry_safe") is True)
                if not ((old["state"] == "pending" and rejected) or safe_failure):
                    raise QAError("invalid_parameters", "已执行的步骤不能改写；保留其证据并为必要的新操作添加步骤")
                if list(previous["operations"].values()).count(old_id) > 1:
                    # A revised consumer must not mutate a shared receipt or
                    # change another consumer's still-valid input binding.
                    old = None
        if old is not None:
            if changed:
                old.update(capability={"server": tool.server, "name": tool.name}, target=target,
                    state="pending", plan_retry=revision)
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
        mapping[step.key] = operation_id
        if Execution.reusable(tool) and not step.fresh:
            reusable[signature] = operation_id
    for operation_id in set(mapping.values()):
        produced = [key for step in plan.steps if mapping[step.key] == operation_id for key in step.produces]
        item = operations.get(operation_id)
        item.update(required=bool(produced),
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
    if not saved or saved.get("reviewed") != saved["revision"]:
        return None, {}
    plan = Plan.model_validate(saved["spec"])
    operations = execution.operations
    cards = {card["result_id"]: card for card in execution.cards.values()}
    saved["acceptance"] = outcome_status(saved, operations, cards.values())
    calls, bindings = [], {}

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
