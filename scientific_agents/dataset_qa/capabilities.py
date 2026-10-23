"""Declarative QA adapters; MCP schemas remain authoritative at dispatch.

New services can supply the same descriptor in ``meta.piflow.qa``. These
profiles adapt existing services without changing their wire protocol. They
describe fields and output shapes, never user wording or domain keywords.
"""
from copy import deepcopy
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .contracts import QAError
from .context import pointer_tokens
from .references import at_path, identifier_in_request
from .search import SearchProfile, TaskDirective


PROFILES = {
    ("piflow-corpus", "search_corpus_datasets"): {"label": "候选数据集", "collection": "/items", "search": {
        "query": "query", "page": "page", "page_size": "page_size", "total": "/pagination/total",
        "identity": ["/cstr", "/id"], "opaque_filters": ["field", "subject", "title"]}},
    ("piflow-corpus", "get_corpus_dataset_detail"): {"label": "数据集详情", "atomic": True, "object": "", "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "get_corpus_dataset_directory"): {"label": "数据预览", "atomic": True, "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "sample_corpus_dataset"): {"label": "采样结果", "atomic": True, "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
}
OBJECT = "__qa_object"
SUPPORTING = "__qa_supporting"
GOAL = "__qa_goal"
TASK = "__qa_task"


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str | None = Field(default=None, min_length=1, max_length=80,
        description="User-facing capability name, independent of execution diagnostics.")
    bind: dict[str, list[str]] = Field(default_factory=dict, max_length=16)
    collection: str | None = None
    object: str | None = None
    atomic: bool = False
    search: SearchProfile | None = None


def profile(tool):
    metadata = tool.meta.get("piflow", {})
    value = metadata.get("qa", PROFILES.get((tool.server, tool.name), {})) if isinstance(metadata, dict) else {}
    try:
        result = Profile.model_validate(value)
    except ValidationError as exc:
        raise QAError("invalid_schema", "服务的对象绑定定义无效", 502) from exc
    properties = tool.schema.get("properties", {})
    if any(key not in properties or not paths
            for key, paths in result.bind.items()):
        raise QAError("invalid_schema", "服务的对象绑定字段或来源路径无效", 502)
    if result.search:
        search = result.search
        if result.collection is None or any(key not in properties for key in
                [search.query, *[value for value in (search.page, search.page_size) if value]]):
            raise QAError("invalid_schema", "检索能力的输入或列表定义无效", 502)
        if (search.page is None)!=(search.page_size is None):
            raise QAError("invalid_schema", "分页能力须同时声明页码和页面大小参数", 502)
    try:
        for path in [result.collection, result.object, *(path for paths in result.bind.values() for path in paths)]:
            if path is not None:
                pointer_tokens(path)
        if result.search:
            for path in [*result.search.identity, *([result.search.total] if result.search.total is not None else [])]:
                pointer_tokens(path)
    except QAError as exc:
        raise QAError("invalid_schema", "服务的对象来源路径须为有效JSON Pointer", 502) from exc
    return result


def resolve_tool(name, loaded):
    matches = [tool for tool in loaded.values() if name in {tool.alias, tool.name, tool.server+"/"+tool.name}]
    if len(matches)!=1:
        raise QAError("invalid_parameters", "所需能力尚未加载或存在同名能力，请从当前能力中明确选择", detail={"tool": name,
            "available": [tool.alias for tool in loaded.values()]})
    return matches[0]


def adapted(tool):
    return tool.schema.get("type")=="object" and not ({OBJECT, SUPPORTING, GOAL, TASK} & tool.schema.get("properties", {}).keys())


def request_identifiers(tool, arguments, message):
    """Return only explicitly supplied bound IDs with complete input evidence."""
    return {key: arguments[key] for key in profile(tool).bind
        if key in arguments and identifier_in_request(arguments[key], message, key)}


def identifiers_from_request(tool, arguments, message):
    """A new identity must ground every component of its declared binding."""
    binding = profile(tool).bind
    return bool(binding) and set(request_identifiers(tool, arguments, message))==set(binding)


def definition(tool):
    schema = deepcopy(tool.schema)
    if adapted(tool):
        schema.setdefault("properties", {}).update({
            SUPPORTING: {"type": ["boolean", "null"], "default": False, "description": "True for an auxiliary lookup rather than a requested outcome."},
        })
        descriptor = profile(tool)
        bound = descriptor.bind
        if bound:
            schema["properties"][OBJECT] = {"type": ["string", "null"], "description": "Supplied object handle. Omit to use current focus. Runtime binds its identifiers."}
            schema["required"] = [key for key in schema.get("required", []) if key not in bound]
        if descriptor.search or descriptor.atomic:
            task = TaskDirective.model_json_schema()
            if descriptor.search:
                task["required"].extend(["keywords", "original_keywords"])
                query = schema["properties"][descriptor.search.query]
                query["description"] = query.get("description", "")+(
                    " For broad discovery quote the user's subject in __qa_task.original_keywords; "
                    "the complete keywords plan must search these original phrases before rewrites. "
                    "For an exact lookup set keywords and original_keywords to null and supply this argument normally.")
            else:
                task["properties"].pop("keywords", None)
                task["properties"].pop("original_keywords", None)
            schema["properties"][TASK] = task
            schema.setdefault("required", []).append(TASK)
    return {"type": "function", "function": {"name": tool.alias,
        "description": tool.description, "parameters": schema}}


def inputs(tool, arguments, record=None):
    """Bind only declared source fields; conflicting explicit values are rejected."""
    values = deepcopy(arguments)
    if adapted(tool):
        values.pop(OBJECT, None)
        values.pop(SUPPORTING, None)
        values.pop(GOAL, None)
        values.pop(TASK, None)
    binding = profile(tool).bind
    if record is not None:
        from jsonschema import Draft202012Validator

        validator = Draft202012Validator(tool.schema)
        for key, paths in binding.items():
            field_validator = validator.evolve(schema=tool.schema.get("properties", {}).get(key, {}))
            candidates = []
            for path in paths:
                try:
                    value = at_path(record, path)
                except QAError:
                    continue
                if value is not None and value!="":
                    value = normalize_identity(value, field_validator)
                    if not any(same_identity(value, previous) for previous in candidates):
                        candidates.append(value)
            if len(candidates)>1:
                raise QAError("invalid_parameters", "对象来源中的标识存在冲突，请先确认目标", detail={"field": key})
            if not candidates:
                # Missing evidence must not be replaced with a model-invented ID.
                raise QAError("invalid_parameters", "当前对象缺少此操作所需的标识", detail={"field": key,
                    "guidance": "The selected source record lacks this identifier. Repeating the call or changing focus to the same record cannot supply it. Never substitute another identifier field. Deliver the existing candidates if the user only requested search; otherwise obtain a source that supplies the required identifier or explain the available findings and the unavailable requested content."})
            explicit = normalize_identity(values[key], field_validator) if key in values else None
            if explicit is not None and not same_identity(explicit, candidates[0]):
                raise QAError("invalid_parameters", "调用参数与所选对象不一致，尚未执行", detail={
                    "field": key, "expected": candidates[0], "guidance": "Use the selected object's identifier or explicitly choose another supplied object handle."})
            values[key] = candidates[0]
    for key, field in tool.schema.get("properties", {}).items():
        if key not in values and isinstance(field, dict) and "default" in field:
            values[key] = deepcopy(field["default"])
    return values


def same_identity(left, right):
    """JSON equality without Python's boolean/number identity collision."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left==right
    if isinstance(left, dict) or isinstance(right, dict):
        return isinstance(left, dict) and isinstance(right, dict) and left.keys()==right.keys() and all(
            same_identity(left[key], right[key]) for key in left)
    if isinstance(left, list) or isinstance(right, list):
        return isinstance(left, list) and isinstance(right, list) and len(left)==len(right) and all(
            same_identity(a, b) for a, b in zip(left, right))
    return left==right


def normalize_identity(value, validator):
    """Reconcile only lossless integer/string wire representations.

    Keep valid values untouched, including union types. Do not trim text,
    remove leading zeroes, coerce booleans or guess domain-specific formats.
    The complete authoritative tool schema is still checked at dispatch.
    """
    if validator.is_valid(value):
        return value
    if type(value) is int:
        candidate = str(value)
    elif isinstance(value, str) and re.fullmatch(r"0|-?[1-9][0-9]*", value):
        try:
            candidate = int(value)
        except ValueError:
            return value
    else:
        return value
    return candidate if validator.is_valid(candidate) else value
