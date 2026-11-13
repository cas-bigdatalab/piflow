"""Declarative QA adapters; MCP schemas remain authoritative at dispatch.

New services can supply the same descriptor in ``meta.piflow.qa``. These
profiles adapt existing services without changing their wire protocol. They
describe fields and output shapes, never user wording or domain keywords.
"""
from copy import deepcopy
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .contracts import QAError
from .context import pointer_tokens, same_identity
from .references import at_path, identifier_in_request
from .search import SearchProfile, TaskDirective
from .resource_index.model import DirectorySpec
from .planning import ResultContract
from .routing import Routing
from .artifacts import ArtifactSpec


PROFILES = {
    ("piflow-corpus", "search_corpus_datasets"): {"label": "候选数据集", "collection": "/items", "search": {
        "query": "query", "page": "page", "page_size": "page_size", "total": "/pagination/total",
        "identity": ["/cstr", "/id"], "opaque_filters": ["field", "subject", "title"]}},
    ("piflow-corpus", "get_corpus_dataset_detail"): {"label": "数据集详情", "atomic": True, "object": "", "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "get_corpus_dataset_directory"): {"label": "数据预览", "atomic": True,
        "bind": {"cstr": ["/cstr", "/raw/cstr"]}, "directory": {
            "identity": ["cstr"], "parent": "file_id", "nodes": ["/data", "/data/data"],
            "node_id": "/fileId", "name": "/name", "is_file": "/isFile", "download_url": "/downloadUrl",
            "status": ["/code", "/data/code"]}},
    ("piflow-corpus", "sample_corpus_dataset"): {"label": "采样结果", "atomic": True, "bind": {"cstr": ["/cstr", "/raw/cstr"]}},
    ("piflow-corpus", "get_corpus_file_schema"): {"label": "文件字段结构", "atomic": True,
        "result": {"kind": "schema", "requires": [{"path": "/schema"},
            {"path": "/warnings", "test": "at_most", "value": 0, "optional": True}],
            "unavailable_when": [{"path": "/previewable", "test": "equals", "value": False}]},
        "target_kind": "file", "bind": {"download_url": ["/downloadUrl"]}},
    ("piflow-corpus", "read_corpus_file_records"): {"label": "文件样例记录", "atomic": True,
        "result": {"kind": "records", "requires": [{"path": "/data"},
            {"path": "/warnings", "test": "at_most", "value": 0, "optional": True}],
            "unavailable_when": [{"path": "/previewable", "test": "equals", "value": False}]},
        "target_kind": "file", "bind": {"download_url": ["/downloadUrl"]}},
}
for _name, _descriptor in PROFILES.items():
    _descriptor["routing"] = {"group": "corpus", "source": "" if _descriptor.get("target_kind") == "file" else "corpus",
        "operations": [_name[1]], "inputs": [], "outputs": []}
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
    plan_required: bool = False
    search: SearchProfile | None = None
    directory: DirectorySpec | None = None
    target_kind: Literal["dataset", "file"] = "dataset"
    result: ResultContract | None = None
    routing: Routing | None = None
    artifact: ArtifactSpec | None = None


def profile(tool):
    metadata = tool.meta.get("piflow", {})
    value = metadata.get("qa", PROFILES.get((tool.server, tool.name), {})) if isinstance(metadata, dict) else {}
    try:
        result = Profile.model_validate(value)
    except ValidationError as exc:
        raise QAError("invalid_schema", "服务的对象绑定定义无效", 502) from exc
    properties = tool.schema.get("properties", {})
    if result.artifact:
        if result.artifact.consume and result.artifact.consume not in properties:
            raise QAError("invalid_schema", "产物输入字段不在工具定义中", 502)
        if result.artifact.replay_safe and (not result.artifact.execution_context
                or tool.annotations.get("idempotentHint") is not True
                or tool.annotations.get("destructiveHint") is not False):
            raise QAError("invalid_schema", "产物重放须声明幂等执行上下文及无破坏性", 502)
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
    if result.directory and any(key not in properties for key in [*result.directory.identity, result.directory.parent]):
        raise QAError("invalid_schema", "目录索引的身份或父节点参数无效", 502)
    try:
        if result.artifact:
            pointer_tokens(result.artifact.path)
        if result.result:
            if any(key not in properties for key in result.result.argument_paths):
                raise QAError("invalid_schema", "结果校验的参数不在工具定义中", 502)
            for path in [*result.result.target_paths, *result.result.argument_paths.values()]:
                pointer_tokens(path)
        for path in [result.collection, result.object, *(path for paths in result.bind.values() for path in paths)]:
            if path is not None:
                pointer_tokens(path)
        if result.search:
            for path in [*result.search.identity, *([result.search.total] if result.search.total is not None else [])]:
                pointer_tokens(path)
        if result.directory:
            spec = result.directory
            for path in [*spec.nodes, *spec.status, spec.node_id, spec.name, spec.is_file, spec.download_url]:
                if path is not None:
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


def validate_intent(tool, intent, arguments=None):
    """Check a declared operation against its adapter, independent of tool names.

    Routing operations describe semantics, not incidental output formats. In
    particular, ``export`` preserves the input records; a filtering capability
    does not become an exporter merely because it can write the same format.
    Missing intent keeps legacy independent calls compatible.
    """
    intent = intent.model_dump() if isinstance(intent, BaseModel) else intent or {}
    descriptor = profile(tool)
    operation, fmt = intent.get("operation"), intent.get("output_format")
    routing = descriptor.routing
    if operation and (not routing or operation not in routing.operations):
        raise QAError("invalid_parameters", "所选能力与本轮操作要求不一致，尚未执行", detail={
            "operation": operation, "supported_operations": routing.operations if routing else [],
            "guidance": "Choose a capability declaring the requested operation. An output format alone does not establish its purpose. Preserve the source and current goal; do not repeat completed retrievals."})
    if not fmt:
        return
    def matches_format(value):
        return isinstance(value, str) and value.casefold() == fmt.casefold()

    spec, contract = descriptor.artifact, descriptor.result
    path = spec.path + "/format" if spec else None
    parameters = [key for key, value in contract.argument_paths.items() if value == path] if contract and path else []
    fixed = [check.value for check in contract.requires
        if check.path == path and check.test == "equals" and not check.optional] if contract and path else []
    if (not parameters and not any(map(matches_format, fixed))) or (
            routing and routing.outputs and not any(map(matches_format, routing.outputs))):
        raise QAError("invalid_parameters", "所选能力未声明所需输出格式，请选择兼容能力", detail={
            "output_format": fmt, "guidance": "Use a declared artifact format contract; a format mentioned only in prose is insufficient."})
    if arguments is not None and any(not matches_format(arguments.get(key)) for key in parameters):
        raise QAError("invalid_parameters", "导出参数与本轮要求的格式不一致，尚未执行", detail={
            "output_format": fmt, "parameters": parameters,
            "guidance": "Preserve the requested output_format and set the actual format parameter accordingly."})


def validate_export(tool, data, source):
    """A representation-only export must retain its source records and lineage."""
    descriptor = profile(tool)
    try:
        resource = at_path(data, descriptor.artifact.path)
    except QAError:
        resource = None
    if (not isinstance(resource, dict)
            or resource.get("record_count") != source["resource"]["record_count"]
            or not isinstance(data, dict) or data.get("parent_source_ref") != source["resource"]["source_ref"]):
        raise QAError("invalid_result", "导出结果尚未与原始记录核对一致", 502,
            detail={"dispatched": True, "guidance": "The export receipt must preserve the source record count and parent_source_ref. Do not report a filtered or unrelated file as the requested export."})


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
    descriptor = profile(tool)
    if adapted(tool):
        schema.setdefault("properties", {}).update({
            SUPPORTING: {"type": ["boolean", "null"], "default": False, "description": "True for an auxiliary lookup rather than a requested outcome."},
        })
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
    contract = descriptor.result
    kind = contract.kind if contract else tool.name
    description = tool.description+"\nQA outcome kind: "+kind
    if descriptor.routing and descriptor.routing.operations:
        description += "\nSupported operations: "+", ".join(descriptor.routing.operations)
    if descriptor.plan_required:
        description += ("\nPlan required: remember.plan, review_plan. Preserve CURRENT source, changed conditions, quantity and requested format; "
            "add export/conversion as needed. Intermediate files do not fulfill a different format.")
    if contract and contract.argument_paths:
        description += "\nResult fields matching inputs: "+", ".join(
            key+" -> "+path for key, path in contract.argument_paths.items())
    return {"type": "function", "function": {"name": tool.alias,
        "description": description, "parameters": schema}}


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
            supplied = key in values and (explicit is not None or field_validator.is_valid(None))
            if supplied and not same_identity(explicit, candidates[0]):
                raise QAError("invalid_parameters", "调用参数与所选对象不一致，尚未执行", detail={
                    "field": key, "path": [key], "origin": "object_binding",
                    "guidance": "The explicit argument conflicts with the selected source. If this is the intended object, omit its bound parameter so runtime supplies the real identifier. Otherwise choose the correct supplied object; never invent an identifier."})
            values[key] = candidates[0]
    for key, field in tool.schema.get("properties", {}).items():
        if key not in values and isinstance(field, dict) and "default" in field:
            values[key] = deepcopy(field["default"])
    return values


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
