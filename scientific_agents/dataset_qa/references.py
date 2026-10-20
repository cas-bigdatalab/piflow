"""Small, source-checked conversation references; never a business object catalogue."""
from copy import deepcopy

from pydantic import BaseModel, ConfigDict, Field

from .context import SECRET_KEYS, encode
from .contracts import QAError


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result_id: str = Field(min_length=1, max_length=180)
    path: str = Field(default="", max_length=2000, description="JSON Pointer within saved data, not the frontend envelope.")
    kind: str = Field(default="object", min_length=1, max_length=80, description="Semantic object type, independent of presentation view_type.")


class ReferenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current: Reference | None = Field(default=None, description="Object explicitly discussed or selected. Omit if unchanged; null clears it.")
    candidates: Reference | None = Field(default=None, description="Ordered object list actually displayed. Omit if unchanged; null clears it.")
    selected: list[Reference] | None = Field(default=None, max_length=32,
        description="Complete explicitly confirmed object set. Omit if unchanged; null clears it. Viewing another object does not discard prior selections.")


def at_path(data, path):
    if not path:
        return data
    if not path.startswith("/"):
        raise QAError("invalid_pointer", "引用路径须为JSON Pointer")
    try:
        for token in path[1:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            if isinstance(data, list):
                if not key.isdigit():
                    raise KeyError(key)
                data = data[int(key)]
            else:
                data = data[key]
    except (KeyError, IndexError, TypeError) as exc:
        raise QAError("result_not_found", "来源结果中不存在该对象引用", 404) from exc
    return data


def all_references(state):
    return [ref for ref in [state.get("current"), state.get("candidates"), *(state.get("selected") or [])] if ref]


def apply_update(state, patch, cards):
    """Validate sources before changing state. A summary cannot manufacture a reference."""
    result = deepcopy(state)
    for key, value in patch.items():
        refs = value if key=="selected" and value is not None else [value]
        for ref in refs:
            if ref is None:
                continue
            if ref["result_id"] not in cards:
                raise QAError("result_not_found", "对象引用不属于当前会话", 404)
            data = at_path(cards[ref["result_id"]].get("data"), ref.get("path", ""))
            if not isinstance(data, list if key=="candidates" else dict):
                raise QAError("invalid_parameters", "候选引用须指向列表，对象引用须指向完整记录")
        if value is None:
            result.pop(key, None)
        else:
            result[key] = deepcopy(value)
    return result


def display_list(card):
    """Recognize only the existing surface list envelope, not arbitrary nested arrays."""
    data = card.get("data")
    path = "" if isinstance(data, list) else "/items" if isinstance(data, dict) and isinstance(data.get("items"), list) else None
    if path is not None:
        return {"result_id": card["result_id"], "path": path, "kind": "object"}


def matching_objects(card, identifier, reference=None):
    """Find exact scalar matches in one source scope, preserving original list positions."""
    surface = display_list(card)
    scope = {**(surface or {}), **(reference or {})}
    path = scope.get("path", "")
    kind = reference.get("kind", "object") if reference else "object"
    matches = []

    def is_identifier(key, value):
        if isinstance(value, str):
            return value==identifier
        # A numeric transport code or pagination count is not an object ID.
        key = str(key)
        return isinstance(value, int) and not isinstance(value, bool) and str(value)==identifier and (
            key.lower() in {"id", "identifier", "reference", "key"} or key.endswith(("_id", "Id", "ID")))

    def visit(value, pointer, depth=0):
        if depth>12 or len(matches)>1:
            return
        if isinstance(value, dict):
            if any(is_identifier(key, child)
                   for key, child in value.items() if str(key).lower() not in SECRET_KEYS):
                matches.append({"result_id": card["result_id"], "path": pointer, "kind": kind})
                return  # A nested raw mirror is not another object.
            entries = value.items()
        elif isinstance(value, list):
            entries = enumerate(value)
        else:
            return
        for key, child in entries:
            if str(key).lower() not in SECRET_KEYS:
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                visit(child, pointer+"/"+escaped, depth+1)
    visit(at_path(card.get("data"), path), path)
    return matches


def compact_record(value, limit):
    """Keep whole short scalar fields. Never shorten an identifier to fit the prompt."""
    result = {}
    entries = [(key, child) for key, child in value.items()
        if str(key).lower() not in SECRET_KEYS and key not in {"base64", "blob"}
        and not isinstance(child, (dict, list))]
    entries.sort(key=lambda pair: (pair[0] not in {"title", "id"}, len(encode(pair[1]))))
    for key, child in entries:
        candidate = {**result, key: child}
        if len(encode(candidate))<=limit:
            result = candidate
    return result


def preview(state, cards, limit=4000):
    """A bounded model view. Full references and artifacts remain persisted."""
    result = {}
    content_limit = max(0, limit-40) if state.get("selected") else limit
    for key in ("current", "candidates", "selected"):
        refs = state.get(key)
        if refs is None:
            continue
        views = []
        for ref in refs if key=="selected" else [refs]:
            value = at_path(cards[ref["result_id"]].get("data"), ref.get("path", ""))
            view = dict(ref)
            if key=="candidates":
                view.update(total=len(value), items=[])
                for index, row in enumerate(value):
                    if not isinstance(row, dict):
                        break
                    item = {"path": ref.get("path", "")+"/"+str(index), "value": compact_record(row, 480)}
                    candidate = {**view, "items": [*view["items"], item]}
                    if len(encode({**result, key: candidate}))+40>content_limit:
                        break
                    view = candidate
                if len(view["items"])<len(value):
                    view["next_offset"] = len(view["items"])
            else:
                available = max(0, content_limit-len(encode(result))-len(encode(view))-80)
                view["value"] = compact_record(value, min(available, 600 if key=="current" else 240))
            candidate = {**result, key: [*views, view] if key=="selected" else view}
            if len(encode(candidate))>content_limit:
                if key=="selected":
                    if len(encode({**result, "selected_total": len(refs)}))<=limit:
                        result["selected_total"] = len(refs)
                break
            views.append(view)
            result = candidate
    return result
