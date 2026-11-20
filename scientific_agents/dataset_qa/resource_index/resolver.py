"""Bridge indexed locations to session-owned evidence without changing focus."""
import asyncio
from copy import deepcopy
import json

from ..context import project, same_identity
from ..contracts import QAError
from ..references import at_path, identifier_in_request
from .model import DirectorySpec, source_identity, valid_identifier


def directory_receipt(tool, source, arguments):
    """Private provenance for the original result, independent of index success."""
    from ..capabilities import profile

    spec = profile(tool).directory
    return {"scope": spec.scope_key(tool.server, source, tool.name, arguments),
        "parent": deepcopy(arguments.get(spec.parent))}


async def bind_parent(service, user, sid, tool, arguments, message, *, source=None):
    """Accept roots or exact parent IDs grounded in the request or directory evidence."""
    from jsonschema import Draft202012Validator
    from ..capabilities import profile

    spec = profile(tool).directory
    values = deepcopy(arguments)
    parent = values.get(spec.parent)
    if parent is None:
        return values
    detail = {"field": spec.parent, "path": [spec.parent], "origin": "directory_parent",
        "dispatched": False,
        "guidance": "For the dataset root omit this parameter or use JSON null. For a child directory use its original identifier from a directory receipt for this same dataset and source, or an explicit user-supplied parameter assignment. Names and paths are not identifiers; do not stringify null or guess replacements."}
    parent_schema = tool.schema["properties"][spec.parent]
    if Draft202012Validator(tool.schema).evolve(schema=parent_schema).is_valid(None):
        detail["root_arguments"] = {**values, spec.parent: None}
        detail["root_guidance"] = "Use root_arguments only for the dataset root; for a child resolve its verified directory-node ID."
    if not valid_identifier(parent):
        raise QAError("invalid_parameters", "目录父节点须为真实标识；根层请省略该参数或使用 null", detail=detail)
    if identifier_in_request(parent, message, spec.parent, labelled_only=True):
        return values
    if source is None:
        source = source_identity(service.gateway.configured_servers()[tool.server])
    scope = directory_receipt(tool, source, values)["scope"]
    # Prefer an exact, local observation in long sessions. Index failure or
    # absence falls back to immutable receipts without refresh or waiting.
    index = service.resources.store
    if index is not None:
        try:
            observed = await asyncio.to_thread(index.directory_parent, user, tool, source, values, parent)
        except Exception:
            observed = None
        if observed is not None:
            values[spec.parent] = observed
            return values
    before = None
    while True:
        cards, before = await asyncio.to_thread(service.store.directory_receipts, user, sid, scope, before=before)
        for card in cards:
            if card.get("directory_receipt", {}).get("scope")!=scope:
                continue
            try:
                rows = spec.rows(card.get("data"))
            except QAError:
                continue  # Malformed/failed listings cannot establish a parent.
            for row in rows:
                if row["kind"]=="directory" and same_identity(parent, row["identity"]):
                    values[spec.parent] = deepcopy(row["identity"])
                    return values
        if before is None:
            break
    raise QAError("invalid_parameters", "尚无此数据集目录节点的来源证据，请使用已返回的目录标识", detail=detail)


async def resolve(service, user, sid, tid, values, context, payload):
    index = service.resources
    sources = index.sources()
    scope_id, parent = None, None
    handles = await service._object_index(user, sid, context, payload, [values.scope])
    selected = values.scope or ("current" if "current" in handles and values.dataset is None else None)
    if values.scope and selected not in handles:
        raise QAError("invalid_parameters", "请从已提供的对象中选择定位范围")
    if selected:
        ref = handles[selected]
        card = (await asyncio.to_thread(service.store.selected_results, user, sid, [ref["result_id"]]))[0]
        metadata = card.get("resource")
        if metadata:
            scope_id = metadata["scope"]
            await asyncio.to_thread(index.store.scope, user, scope_id, sources)
            parent = metadata["node"] if metadata["kind"]=="directory" else None
        else:
            record = at_path(card.get("data"), ref.get("path", ""))
            scopes = await asyncio.to_thread(index.store.scopes_for, user, sources, record=record)
            if len(scopes)==1:
                scope_id = scopes[0]["id"]
            else:
                return {"status": "needs_scope", "executed": False,
                    "guidance": "Retrieve the selected dataset's directory as an auxiliary prerequisite, then locate the file. Do not broaden to other datasets or ask the user to manage preparation."}
    elif values.dataset is not None:
        scopes = await asyncio.to_thread(index.store.scopes_for, user, sources, dataset=values.dataset)
        if len(scopes)!=1:
            return {"status": "needs_scope", "executed": False,
                "guidance": "Identify the requested dataset from tools or evidence and retrieve its directory as an auxiliary prerequisite. Ask only if the dataset choice is genuinely ambiguous."}
        scope_id = scopes[0]["id"]
    elif payload.get("params", {}).get("result_id"):
        return {"status": "needs_scope", "executed": False,
            "guidance": "The request pins a result. Select a supplied source object before locating files."}

    # A model retry in the same turn does not repeatedly refresh or wait.
    cache = payload.setdefault("resource_lookups", {})
    key = json.dumps([values.name, scope_id, parent, values.kind, values.refresh], ensure_ascii=False)
    if key in cache:
        return cache[key]
    result = await index.lookup(user, values.name, scope_id=scope_id, parent=parent,
        kind=values.kind, refresh=values.refresh)
    items = result["items"]
    value = {"status": "not_found", "executed": False, "more": result["more"],
        "items": [{"name": row["name"], "path": row["path"], "kind": row["kind"],
            "server": row["server"], "dataset": project(row["dataset"], 500)[0]} for row in items]}
    if not result["scopes"]:
        value.update(status="needs_directory", guidance="Identify the dataset and retrieve its directory as an auxiliary prerequisite; continue the file request in this turn without explaining internal preparation.")
    elif not result["complete"]:
        value.update(status="unavailable", items=[],
            guidance="No verified file content is available for this request. Do not infer that the file is absent, select a partial match, or repeat this lookup. Answer about the requested content only; no implementation details or request to wait/retry.")
    elif len(items)>1 or result["more"]:
        value.update(status="ambiguous", guidance="Ask which dataset or relative path the user means, then resolve again. No file has been selected.")
    elif items and not items[0]["fresh"]:
        value.update(status="unavailable", items=[], guidance="No current file access location could be verified. Do not use an old URL or explain internal preparation; answer about the requested content only.")
    elif items:
        item = items[0]
        raw = json.loads(item["record"])
        spec = DirectorySpec.model_validate(item["descriptor"])
        if item["kind"]=="file" and spec.download_url:
            try:
                url = at_path(raw, spec.download_url)
            except QAError:
                url = None
            if not isinstance(url, str) or not url:
                value.update(status="unavailable", guidance="The directory identifies this file but supplies no download location. Explain that its schema/records cannot be retrieved from this entry yet; do not construct a URL.")
                cache[key] = value
                await service._write(user, sid, tid, payload=payload)
                return value
        metadata = {"scope": item["scope"], "server": item["server"], "source": item["source"],
            "node": item["key"], "generation": item["generation"], "kind": item["kind"], "path": item["path"]}
        dataset = await asyncio.to_thread(service.store.save_resource, user, sid, tid,
            item["dataset"], {**metadata, "kind": "dataset"})
        metadata["parent_dataset"] = {"result_id": dataset["result_id"], "path": "", "kind": "object"}
        card = await asyncio.to_thread(service.store.save_resource, user, sid, tid, raw, metadata)
        objects = service._register_source_objects(card, payload, "", False)
        value.update(status="resolved", object=objects[0]["handle"],
            guidance="Use this object handle for the requested file MCP. Only its location has been resolved; schema and records have not been retrieved.")
    else:
        value["guidance"] = "No exact file match in the checked datasets. Ask for a dataset/path only if needed. This does not prove absence from other datasets."
    cache[key] = value
    await service._write(user, sid, tid, payload=payload)
    return value


async def bind_target(service, user, sid, tool, descriptor, target, *, validate=False):
    if target is None or not target["result_id"].startswith("resource-"):
        return target
    card = (await asyncio.to_thread(service.store.selected_results, user, sid, [target["result_id"]]))[0]
    metadata = card.get("resource")
    if metadata is None:
        return target
    if metadata["server"]!=tool.server or service.resources.sources().get(tool.server)!=metadata["source"]:
        raise QAError("invalid_parameters", "文件引用与当前服务来源不一致，请重新定位")
    if descriptor.target_kind=="dataset" and metadata["kind"] in {"file", "directory"}:
        return metadata["parent_dataset"]
    if descriptor.target_kind=="file" and metadata["kind"]!="file":
        raise QAError("invalid_parameters", "此操作需要具体文件，请先定位文件")
    if validate and descriptor.target_kind=="file":
        found = await service.resources.lookup(user, metadata["path"], scope_id=metadata["scope"])
        if (not found["complete"] or len(found["items"])!=1 or not found["items"][0]["fresh"]
                or found["items"][0]["key"]!=metadata["node"]
                or json.loads(found["items"][0]["record"])!=card["data"]):
            raise QAError("invalid_parameters", "文件位置已变化或尚待确认，请重新使用resolve_resource定位")
    return target
