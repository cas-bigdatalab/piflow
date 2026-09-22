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
    return bool(query) and any(target_name(query) == target_name(v)
                               for v in values(case, "variable", "variable_aliases"))


def target_name(value):
    # Strip presentation wording, not physical distinctions (e.g. min/max, depth).
    return re.sub(r"(?:的)?(?:变化(?:趋势|情况)?|预测(?:结果|情况)?|趋势)$", "", normalized(value))


def _mentioned_name(message, names):
    """Longest non-overlapping registered names; multiple mentions stay with the parser."""
    # Preserve word boundaries in sentences, while allowing whitespace within aliases.
    text = re.sub(r"[·•・]", " ", unicodedata.normalize("NFKC", message).casefold())
    spans = set()
    for token in {normalized(name) for name in names if name and normalized(name)}:
        pattern = (r"(?<![a-z0-9_])" if token[0].isascii() and token[0].isalnum() else "") + r"\s*".join(map(re.escape, token))
        if token[-1].isascii() and token[-1].isalnum():
            pattern += r"(?![a-z0-9_])"
        spans.update((m.start(), m.end(), token) for m in re.finditer(pattern, text))
    longest = {name for start, end, name in spans if not any(
        left <= start and right >= end and (left < start or right > end) for left, right, _ in spans)}
    return next(iter(longest)) if len(longest) == 1 else None


def grounded_scope(message, cases, parsed=None):
    """Keep literal catalogue names instead of a model's invented channel selection.

    This is supplementary evidence, not a free-text intent parser. Unrecognized or
    multiple names remain with the intent parser; explicit UI payloads are untouched.
    """
    if message.lstrip().startswith("{"):
        return {}
    scope = {}
    area = _mentioned_name(message, (v for case in cases for v in area_names(case)))
    target = _mentioned_name(message, (v for case in cases for v in values(case, "variable", "variable_aliases")))
    if area:
        scope["requested_area"] = area
    # A bare alias embedded in e.g. 'maximum temperature' must not erase the statistic.
    if target and target_statistic(unicodedata.normalize("NFKC", message).casefold()) == target_statistic(target):
        scope["requested_variable"] = target
    for field, literal in list(scope.items()):
        supplied = (parsed or {}).get(field)
        if not supplied:
            continue
        supplied = normalized(supplied)
        match = matches_area if field == "requested_area" else matches_target
        # Do not shorten an explicit but unregistered place/measurement to a known
        # substring (e.g. sea temperature -> temperature, or a subregion -> province).
        if (literal in supplied and supplied != literal and supplied in normalized(message)) or not any(
                match(case, supplied) for case in cases):
            scope.pop(field)
    return scope


def area_names(case):
    yield from values(case, "area", "aliases", "station_id", "source_name")
    location = case.get("location") or {}
    yield from (location.get("name", ""), location.get("address", ""))


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
    return any(re.search(pattern, normalized(v)) for v in area_names(case) if v)


def candidates(cases, scope):
    area, target, hazard = (scope.get(key) for key in ("requested_area", "requested_variable", "requested_hazard"))
    # Older clients/models put a variable into requested_hazard. Resolve it against
    # registered targets, not source-specific synonyms or covariate descriptions.
    legacy_target = not target and hazard and any(matches_target(c, hazard) for c in cases)
    return [c for c in cases
            if (not area or matches_area(c, area))
            and (not target or matches_target(c, target))
            # A risk label is not a prerequisite for forecasting an explicit variable.
            and (target or not hazard or (matches_target(c, hazard) if legacy_target else
                 any(normalized(hazard) == normalized(v) for v in values(c, "hazard_type", "hazard_aliases"))))]


class AreaChoice(Exception):
    """Multiple matching registered objects require an explicit selection."""
    def __init__(self, options, fields=None):
        self.options = options
        self.fields = fields or ["requested_area"]


def area_score(query, case):
    if matches_area(case, query):
        return 1.0
    query = re.sub(r"(?:地区|区域)$", "", normalized(query))
    if len(query) < 2:
        return 0.0
    scores = []
    for name in area_names(case):
        name = normalized(name)
        if not name:
            continue
        # Never suggest a different numbered station/device as a spelling correction.
        if re.findall(r"\d+", query) != re.findall(r"\d+", name):
            continue
        # Administrative abbreviations contribute to candidate ranking.
        short_query = re.sub(r"[省市县区]", "", query)
        short_name = re.sub(r"[省市县区]", "", name)
        if len(short_query) >= 3 and short_query in short_name:
            scores.append(0.95)
        scores.append(SequenceMatcher(None, query, name, autojunk=False).ratio())
    return max(scores, default=0.0)


def target_score(query, case):
    if matches_target(case, query):
        return 1.0
    query = target_name(query)
    return max((SequenceMatcher(None, query, target_name(name), autojunk=False).ratio()
                for name in values(case, "variable", "variable_aliases") if name
                and len(query) >= 3 and re.findall(r"\d+", query) == re.findall(r"\d+", target_name(name))
                and target_statistic(query) == target_statistic(target_name(name))), default=0.0)


def target_statistic(name):
    """Similarity must not turn a named statistic into a different measurement."""
    patterns = (r"最高|最大|(?<![a-z])max(?:imum)?(?![a-z])",
                r"最低|最小|(?<![a-z])min(?:imum)?(?![a-z])",
                r"平均|(?<![a-z])(?:mean|average|avg)(?![a-z])",
                r"累计|累积|(?<![a-z])(?:sum|total)(?![a-z])",
                r"中位|(?<![a-z])median(?![a-z])")
    return tuple(bool(re.search(pattern, name)) for pattern in patterns)


def area_suggestions(cases, scope, limit=5):
    """Rank eligible objects; limit=None returns the full set for uniqueness checks."""
    if candidates(cases, scope):
        return []
    # Preserve independently recognized constraints: a place spelling difference
    # must not broaden an exact variable, or replace an explicitly matched place.
    area_query, target_query = scope.get("requested_area"), scope.get("requested_variable")
    exact_area = bool(area_query) and any(matches_area(c, area_query) for c in cases)
    exact_target = bool(target_query) and any(matches_target(c, target_query) for c in cases)
    ranked = []
    for case in cases:
        if exact_target and not matches_target(case, target_query):
            continue
        if exact_area and not matches_area(case, area_query):
            continue
        area = area_score(scope["requested_area"], case) if scope.get("requested_area") else 1.0
        target = target_score(scope["requested_variable"], case) if scope.get("requested_variable") else 1.0
        other = {k: v for k, v in scope.items() if k not in {"requested_area", "requested_variable"}}
        if scope.get("requested_variable"):
            other["requested_variable"] = case["variable"]
        if area >= 0.8 and target >= 0.8 and candidates([case], other):
            ranked.append((area + target, case))
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
