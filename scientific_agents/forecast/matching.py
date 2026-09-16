"""Match registered places, prediction targets and risks as separate concepts."""
import re
import unicodedata
from difflib import SequenceMatcher
import json


def normalized(value):
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(c for c in text if not c.isspace() and c not in "·•・")


def values(case, *fields):
    for field in fields:
        value = case.get(field, "")
        yield from value if isinstance(value, list) else [value]


def matches_target(case, query):
    return bool(query) and any(normalized(query) == normalized(v)
                               for v in values(case, "variable", "variable_aliases"))


def matches_area(case, query):
    query = normalized(query)
    # Descriptive suffixes are not administrative names such as 市/县/区.
    query = re.sub(r"(?:地区|区域)$", "", query)
    if not query:
        return True
    identifier = any(c.isdigit() for c in query)
    pattern = (r"(?<![a-z0-9_])" if identifier and query[0].isascii() and query[0].isalnum() else "") + re.escape(query)
    if identifier and query[-1].isascii() and query[-1].isalnum():
        pattern += r"(?![a-z0-9_])"
    return any(re.search(pattern, normalized(v)) for v in values(case, "area", "aliases", "station_id"))


def candidates(cases, scope):
    area, target, hazard = (scope.get(key) for key in ("requested_area", "requested_variable", "requested_hazard"))
    # Older clients/models put a variable into requested_hazard. Resolve it against
    # registered targets, not source-specific synonyms or covariate descriptions.
    legacy_target = not target and hazard and any(matches_target(c, hazard) for c in cases)
    return [c for c in cases
            if (not area or matches_area(c, area))
            and (not target or matches_target(c, target))
            and (not hazard or (matches_target(c, hazard) if legacy_target else
                 any(normalized(hazard) == normalized(v) for v in values(c, "hazard_type", "hazard_aliases"))))]


class AreaChoice(Exception):
    """Similar registered names require an explicit selection, never auto-routing."""
    def __init__(self, options):
        self.options = options


def area_suggestions(cases, scope, limit=5):
    """Suggest close names only after exact matching fails; keep target/risk constraints."""
    query = re.sub(r"(?:地区|区域)$", "", normalized(scope.get("requested_area") or ""))
    # Numeric station/device identities must not be silently treated as spelling errors.
    if len(query) < 3 or any(c.isdigit() for c in query) or candidates(cases, scope):
        return []
    pool = candidates(cases, {k: v for k, v in scope.items() if k != "requested_area"})
    ranked = []
    for case in pool:
        scores = [SequenceMatcher(None, query, normalized(name), autojunk=False).ratio()
                  for name in values(case, "area", "aliases", "station_id")
                  if name and len(normalized(name)) >= 3 and not any(c.isdigit() for c in normalized(name))]
        score = max(scores, default=0)
        if score >= 0.8:
            ranked.append((score, case))
    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [case for _, case in ranked[:limit]]


def area_selection(message, options):
    """Recognize explicit UI/text selections without asking an LLM to guess consent."""
    text = message.strip().rstrip("。")
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except ValueError:
            return None
        if (not isinstance(data, dict) or set(data) - {"action", "case_ids", "horizon_hours", "history_hours",
                "history_mode", "origin", "origin_mode", "auxiliary_case_ids", "analysis_context"}
                or data.get("action", "predict") != "predict"):
            return None
        ids = data.get("case_ids")
        return ids[0] if isinstance(ids, list) and len(ids) == 1 and any(c["id"] == ids[0] for c in options) else None
    if text.isdecimal():
        index = int(text) - 1
        return options[index]["id"] if 0 <= index < len(options) else None
    if text in {"是", "是的", "确认", "可以", "好的"}:
        return options[0]["id"] if len(options) == 1 else None
    text = re.sub(r"^(?:使用数据案例|选择|使用)\s*", "", text)
    matched = [case["id"] for case in options if any(normalized(text) == normalized(v)
               for v in values(case, "id", "label", "area", "aliases", "station_id") if v)]
    return matched[0] if len(matched) == 1 else None
