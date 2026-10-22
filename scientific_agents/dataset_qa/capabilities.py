"""Declarative QA adapters; MCP schemas remain authoritative at dispatch.

New services can supply the same descriptor in ``meta.piflow.qa``. These
profiles adapt existing services without changing their wire protocol. They
describe fields and output shapes, never user wording or domain keywords.
"""
from copy import deepcopy

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .contracts import QAError
from .references import at_path, identifier_in_request


PROFILES = {
    ("piflow-corpus", "search_corpus_datasets"): {"collection": "/items"},
    ("piflow-corpus", "get_corpus_dataset_detail"): {"object": "", "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "get_corpus_dataset_directory"): {"bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "sample_corpus_dataset"): {"bind": {"cstr": ["/cstr", "/raw/cstr"]}},
}
OBJECT = "__qa_object"
SUPPORTING = "__qa_supporting"
GOAL = "__qa_goal"


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bind: dict[str, list[str]] = Field(default_factory=dict, max_length=16)
    collection: str | None = None
    object: str | None = None


def profile(tool):
    metadata = tool.meta.get("piflow", {})
    value = metadata.get("qa", PROFILES.get((tool.server, tool.name), {})) if isinstance(metadata, dict) else {}
    try:
        result = Profile.model_validate(value)
    except ValidationError as exc:
        raise QAError("invalid_schema", "服务的对象绑定定义无效", 502) from exc
    properties = tool.schema.get("properties", {})
    if any(key not in properties or not paths or any(path and not path.startswith("/") for path in paths)
            for key, paths in result.bind.items()):
        raise QAError("invalid_schema", "服务的对象绑定字段或来源路径无效", 502)
    return result


def resolve_tool(name, loaded):
    matches = [tool for tool in loaded.values() if name in {tool.alias, tool.name, tool.server+"/"+tool.name}]
    if len(matches)!=1:
        raise QAError("invalid_parameters", "所需能力尚未加载或存在同名能力，请从当前能力中明确选择", detail={"tool": name,
            "available": [tool.alias for tool in loaded.values()]})
    return matches[0]


def adapted(tool):
    return tool.schema.get("type")=="object" and not ({OBJECT, SUPPORTING, GOAL} & tool.schema.get("properties", {}).keys())


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
        bound = profile(tool).bind
        if bound:
            schema["properties"][OBJECT] = {"type": ["string", "null"], "description": "Supplied object handle. Omit to use current focus. Runtime binds its identifiers."}
            schema["required"] = [key for key in schema.get("required", []) if key not in bound]
    return {"type": "function", "function": {"name": tool.alias,
        "description": tool.description, "parameters": schema}}


def inputs(tool, arguments, record=None):
    """Bind only declared source fields; conflicting explicit values are rejected."""
    values = deepcopy(arguments)
    if adapted(tool):
        values.pop(OBJECT, None)
        values.pop(SUPPORTING, None)
        values.pop(GOAL, None)
    binding = profile(tool).bind
    if record is not None:
        for key, paths in binding.items():
            candidates = []
            for path in paths:
                try:
                    value = at_path(record, path)
                except QAError:
                    continue
                if value is not None and value!="" and value not in candidates:
                    candidates.append(value)
            if len(candidates)>1:
                raise QAError("invalid_parameters", "对象来源中的标识存在冲突，请先确认目标", detail={"field": key})
            if not candidates:
                # Missing evidence must not be replaced with a model-invented ID.
                raise QAError("invalid_parameters", "当前对象缺少此操作所需的标识", detail={"field": key})
            if key in values and values[key] is not None and values[key]!=candidates[0]:
                raise QAError("invalid_parameters", "调用参数与所选对象不一致，尚未执行", detail={
                    "field": key, "expected": candidates[0], "guidance": "Use the selected object's identifier or explicitly choose another supplied object handle."})
            values[key] = candidates[0]
    for key, field in tool.schema.get("properties", {}).items():
        if key not in values and isinstance(field, dict) and "default" in field:
            values[key] = deepcopy(field["default"])
    return values
