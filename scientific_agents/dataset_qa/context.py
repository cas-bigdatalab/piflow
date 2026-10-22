"""Structure-preserving projections and JSON-pointer access to saved results."""
import json
import re

from .contracts import QAError

SECRET_KEYS = {"password", "token", "api_key", "authorization", "secret"}
OMIT = object()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def project(value, limit):
    def clean(node, depth=0):
        if depth>12:
            return OMIT
        if not isinstance(node, (dict, list)):
            return node
        result = {} if isinstance(node, dict) else []
        entries = node.items() if isinstance(node, dict) else enumerate(node)
        for key, child in entries:
            if isinstance(node, dict) and (str(key).lower() in SECRET_KEYS
                    or key in {"base64", "blob"}
                    or (key=="data" and node.get("type") in {"image", "audio"})):
                continue
            item = clean(child, depth+1)
            if item is OMIT:
                if isinstance(node, list):
                    break  # Never shift an array's JSON-pointer positions.
                continue
            if isinstance(node, dict):
                result[str(key)] = item
            else:
                result.append(item)
        return result

    def priority(entry):
        key, child, size = entry
        if not isinstance(child, (dict, list)):
            if key in {"title", "id"}:
                return 0, 0
            if size<=128:
                return 1, 0
        return 2, size

    def trim(node, budget):
        if budget<4:
            return OMIT
        if len(encode(node))<=budget:
            return node  # Already bounded summaries must not lose more fields.
        if isinstance(node, str):
            if atomic_string(node):
                return OMIT  # A shortened URL/base64 string is never usable.
            text = node[:max(0, budget-4)]
            while text and len(encode(text+"…"))>budget:
                text = text[:len(text)//2]
            return text+"…" if text else OMIT
        if isinstance(node, (dict, list)):
            result = {} if isinstance(node, dict) else []
            pairs = node.items() if isinstance(node, dict) else enumerate(node)
            entries = [(key, child, len(encode(child))) for key, child in pairs]
            if isinstance(node, dict):
                entries.sort(key=priority)
            remaining = budget-2
            for index, (key, child, size) in enumerate(entries):
                overhead = len(encode(str(key)))+2 if isinstance(node, dict) else 1
                if isinstance(node, dict) and priority((key, child, size))[0]<2:
                    # Names and short metadata are useful only when kept whole.
                    item = child if size<=remaining-overhead else OMIT
                else:
                    share = max(128, (remaining-overhead)//max(1, len(entries)-index))
                    item = trim(child, min(remaining-overhead, share))
                if item is OMIT:
                    if isinstance(node, list):
                        break
                    continue
                cost = overhead+len(encode(item))
                if cost>remaining:
                    break
                if isinstance(node, dict):
                    result[str(key)] = item
                else:
                    result.append(item)
                remaining -= cost
            return result
        return OMIT

    # Filtering precedes fit checks, even for tiny payloads and large budgets.
    result = trim(clean(value), max(4, limit))
    result = None if result is OMIT else result
    return result, result != value


def atomic_string(value):
    # Opaque tokens (IDs, filenames, hashes, signed URLs) cannot be used after
    # shortening. Only prose has a meaningful abbreviated representation.
    return value.startswith(("http://", "https://", "data:", "mcp://")) or (
        value.isascii() and not any(character.isspace() for character in value))


def redact(value):
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items() if str(k).lower() not in SECRET_KEYS}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def public_result(card, limit=None, *, normalize=True):
    # Frontend artifacts are already bounded at ingestion. Only model previews
    # have a character budget; images, tables and signed URLs must remain intact.
    result = {key: card[key] for key in ("result_id", "view_type", "title")}
    if "data" in card:
        data = redact(card["data"])
        if limit is not None:
            data, cut = project(data, limit)
            if cut:
                result["truncated"] = True
        result["data"] = data
    if normalize:
        # One frontend list path; existing list envelopes keep their pagination.
        data = result.get("data")
        if not (isinstance(data, dict) and isinstance(data.get("items"), list)):
            items = data if isinstance(data, list) else ([] if data is None else [data])
            result["data"] = {"items": items}
    if card.get("content") and limit is None:
        result["content"] = redact(card["content"])
    return result


def pointer_tokens(path):
    """Decode the JSON string form of RFC 6901 without permissive aliases."""
    if not isinstance(path, str) or (path and not path.startswith("/")) or re.search(r"~(?![01])", path):
        raise QAError("invalid_pointer", "引用路径须为有效JSON Pointer")
    return [token.replace("~1", "/").replace("~0", "~") for token in path[1:].split("/")] if path else []


def at_pointer(value, path):
    """Shared resolver for evidence reads, bindings and persisted references."""
    for key in pointer_tokens(path):
        if isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", key):
                raise QAError("invalid_pointer", "列表引用须使用从零开始且不含前导零的整数索引")
            # Compare before int(): very long valid digit strings should yield
            # a normal missing-reference response, never Python's int limit.
            maximum = str(len(value)-1)
            if not value or len(key)>len(maximum) or (len(key)==len(maximum) and key>maximum):
                raise QAError("result_not_found", "来源结果中不存在该对象引用", 404)
            value = value[int(key)]
        elif isinstance(value, dict) and key in value:
            value = value[key]
        else:
            raise QAError("result_not_found", "来源结果中不存在该对象引用", 404)
    return value


def slice_result(value, path="", offset=0, limit=20):
    # Selecting a leaf must not bypass the key-based redaction applied to an
    # entire public result. Internal source bindings use at_pointer directly.
    if any(token.lower() in SECRET_KEYS for token in pointer_tokens(path)):
        raise QAError("invalid_pointer", "该路径指向不可展示的敏感字段", 403)
    # Public dictionary offsets count accessible fields. Redact before slicing
    # so field indexes never advertise hidden keys; array positions stay intact.
    value = redact(at_pointer(value, path))
    if isinstance(value, list):
        return value[offset:offset+limit], offset+limit<len(value)
    if isinstance(value, dict):
        pairs = list(value.items())
        return dict(pairs[offset:offset+limit]), offset+limit<len(pairs)
    return value, False


def contains(value, reference):
    if isinstance(value, dict):
        return any(contains(v, reference) for v in value.values())
    if isinstance(value, list):
        return any(contains(v, reference) for v in value)
    return isinstance(value, (str, int)) and not isinstance(value, bool) and str(value)==reference
