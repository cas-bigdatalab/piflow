"""Structure-preserving projections and JSON-pointer access to saved results."""
import json

from .contracts import QAError

SECRET_KEYS = {"password", "token", "api_key", "authorization", "secret"}
OMIT = object()


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def project(value, limit):
    def trim(node, budget, depth=0):
        if budget<4 or depth>12:
            return OMIT
        if isinstance(node, str):
            if len(encode(node))<=budget:
                return node
            if atomic_string(node):
                return OMIT  # A shortened URL/base64 string is never usable.
            text = node[:max(0, budget-4)]
            while text and len(encode(text+"…"))>budget:
                text = text[:len(text)//2]
            return text+"…" if text else OMIT
        if isinstance(node, (dict, list)):
            result = {} if isinstance(node, dict) else []
            entries = list(node.items()) if isinstance(node, dict) else list(enumerate(node))
            remaining = budget-2
            for index, (key, child) in enumerate(entries):
                if isinstance(node, dict) and str(key).lower() in SECRET_KEYS:
                    continue
                if isinstance(node, dict) and (key in {"base64", "blob"}
                        or (key=="data" and node.get("type") in {"image", "audio"})):
                    continue  # Model projections reference artifacts instead of binary payloads.
                overhead = len(encode(str(key)))+2 if isinstance(node, dict) else 1
                # Preserve small identity/metadata fields alongside large values.
                share = max(128, (remaining-overhead)//max(1, len(entries)-index))
                item = trim(child, min(remaining-overhead, share), depth+1)
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
        return node if len(encode(node))<=budget else OMIT

    result = trim(value, max(4, limit))
    result = None if result is OMIT else result
    return result, result != value


def atomic_string(value):
    return value.startswith(("http://", "https://", "data:", "mcp://"))


def redact(value):
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items() if str(k).lower() not in SECRET_KEYS}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def public_result(card, limit=None):
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
    if card.get("content") and limit is None:
        result["content"] = redact(card["content"])
    return result


def slice_result(value, path="", offset=0, limit=20):
    if path:
        if not path.startswith("/"):
            raise QAError("invalid_pointer", "path须为JSON Pointer")
        try:
            for token in path[1:].split("/"):
                key = token.replace("~1", "/").replace("~0", "~")
                if isinstance(value, list):
                    if not key.isdigit():
                        raise KeyError(key)
                    value = value[int(key)]
                else:
                    value = value[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise QAError("result_not_found", "原结果中不存在此位置", 404) from exc
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
