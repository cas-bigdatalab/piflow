"""Small, source-checked conversation references; never a business object catalogue."""
from copy import deepcopy
import re

from pydantic import BaseModel, ConfigDict, Field

from .context import SECRET_KEYS, at_pointer, encode
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
    return at_pointer(data, path)


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
            # Arrays establish record boundaries even inside an unfamiliar
            # service envelope. Match nested identity fields to the whole row.
            for index, row in enumerate(value):
                start = len(matches)
                row_path = pointer+"/"+str(index)
                visit(row, row_path, depth+1)
                if isinstance(row, dict) and len(matches)>start:
                    matches[start:] = [{"result_id": card["result_id"], "path": row_path, "kind": kind}]
                if len(matches)>1:
                    break
            return
        else:
            return
        for key, child in entries:
            if str(key).lower() not in SECRET_KEYS:
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                visit(child, pointer+"/"+escaped, depth+1)

    value = at_path(card.get("data"), path)
    visit(value, path)
    if reference and "path" in reference and isinstance(value, dict) and matches:
        matches = [{"result_id": card["result_id"], "path": path, "kind": kind}]
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


def pending_objects(payload, limit=32):
    """Restore only a waiting task's relevant objects in a distinct namespace.

    Source ownership is checked by the store before these references are used.
    A task with an unresolved target may also need its intermediate candidates;
    already bound targets do not pull the entire prior tool history into view.
    """
    if limit<=0:
        return {}
    goals = [item for item in payload.get("operations", [])
        if item.get("required", True) and item.get("state")!="succeeded"]
    references = [item["target"] for item in goals if item.get("target")]
    if any(not item.get("target") for item in goals):
        # Stored JSON may sort object:10 before object:2. Restore the runtime
        # ordinal, rather than letting serialization change a handle's meaning.
        for mapping in (payload.get("objects", {}), payload.get("pending_objects", {})):
            references.extend(mapping[handle] for handle in sorted(mapping, key=handle_order))
    result, seen = {}, set()
    for value in references:
        reference = Reference.model_validate(value).model_dump(mode="json")
        identity = (reference["result_id"], reference["path"], reference["kind"])
        if identity not in seen:
            result["pending:"+str(len(result)+1)] = reference
            seen.add(identity)
        if len(result)>=limit:
            break
    return result


def handle_order(handle):
    prefix, _, suffix = handle.rpartition(":")
    return prefix, int(suffix) if suffix.isdigit() else 0, handle


def scoped_preview(handles, cards, limit=1800):
    """Project scoped object handles without copying source bodies or paths."""
    result = {"items": [], "total": len(handles)}
    for handle, ref in handles.items():
        if ref["result_id"] not in cards:
            raise QAError("result_not_found", "对象引用不属于当前会话", 404)
        value = at_path(cards[ref["result_id"]].get("data"), ref.get("path", ""))
        if not isinstance(value, dict):
            raise QAError("invalid_parameters", "对象引用须指向完整记录")
        row = {"handle": handle, "value": compact_record(value, min(400, max(0, limit//3)))}
        candidate = {**result, "items": [*result["items"], row]}
        if len(encode(candidate))+40>limit:
            break
        result = candidate
    if len(result["items"])<len(handles):
        result["next_offset"] = len(result["items"])
    return result


def identifier_in_request(value, message, field=""):
    """Check a complete input identity, never an arbitrary word substring.

    This proves lexical provenance, not user intent. The semantic decision must
    still distinguish an identifier from a year, quantity or ordinal.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return False
    token = str(value)
    if not token or token!=token.strip():
        return False
    # Known field labels are evidence of an assignment even without whitespace.
    if field:
        labelled = re.compile(r"(?<![A-Za-z0-9_])"+re.escape(field)+r"\s*[=:：]\s*[\"']?"+re.escape(token), re.IGNORECASE)
        for match in labelled.finditer(message):
            if match.end()==len(message) or not _identity_character(message[match.end()], token):
                return True
    for match in re.finditer(re.escape(token), message):
        before = message[match.start()-1] if match.start() else ""
        after = message[match.end()] if match.end()<len(message) else ""
        if before and _identity_character(before, token):
            continue
        if after and _identity_character(after, token):
            # A final full stop is sentence punctuation, not an ID suffix.
            if after!="." or (match.end()+1<len(message) and _identity_character(message[match.end()+1], token)):
                continue
        return True
    return False


def _identity_character(character, token):
    if any(letter.isascii() and letter.isalnum() for letter in token):
        return character.isascii() and (character.isalnum() or character in "_-./:@%+~")
    return character.isalnum() or character in "_-./:@%+~"


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
            if key=="current":
                view["handle"] = "current"
            elif key=="selected":
                view["handle"] = "selected:"+str(len(views)+1)
            if key=="candidates":
                view.update(total=len(value), items=[])
                consumed = 0
                for index, row in enumerate(value):
                    if not isinstance(row, dict):
                        consumed = index+1
                        continue
                    item = {"handle": "candidate:"+str(index+1), "path": ref.get("path", "")+"/"+str(index), "value": compact_record(row, 480)}
                    candidate = {**view, "items": [*view["items"], item]}
                    if len(encode({**result, key: candidate}))+40>content_limit:
                        break
                    view = candidate
                    consumed = index+1
                if consumed<len(value):
                    view["next_offset"] = consumed
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
