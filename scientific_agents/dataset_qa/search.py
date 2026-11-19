"""Bounded discovery policy, separate from MCP transport retries and planning."""
from copy import deepcopy
from hashlib import sha256
import json
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

from .context import encode, same_identity
from .contracts import QAError
from .references import at_path
from .planning import CallIntent


class SearchPolicy(BaseModel):
    """Per-capability discovery bounds; global execution budgets still apply."""
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    candidate_stop: int = Field(default=6, ge=1, le=1000)
    keyword_limit: int = Field(default=4, ge=1, le=16)


DEFAULT_SEARCH_POLICY = SearchPolicy()


def search_policy(value=None):
    # Missing metadata/saved policy means the original behavior. Invalid
    # explicit metadata must fail validation instead of silently falling back.
    return DEFAULT_SEARCH_POLICY if value is None else SearchPolicy.model_validate(value)


class SearchProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    page: str | None = None
    page_size: str | None = None
    total: str | None = None
    identity: list[str] = Field(default_factory=list, max_length=8)
    identity_mode: Literal["fallback", "composite"] = "fallback"
    policy: SearchPolicy = Field(default_factory=SearchPolicy)
    # Opaque classifications are not free-text search fields. Adapters expose
    # these only for exact operations with independently grounded parameters.
    opaque_filters: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def composite_paths(self):
        if self.identity_mode=="composite" and (len(self.identity)<2 or len(set(self.identity))!=len(self.identity)):
            raise ValueError("Composite identity requires at least two distinct field paths.")
        return self


class TaskDirective(CallIntent):
    model_config = ConfigDict(extra="forbid")
    complete_request: bool = Field(description="True if this tool covers the whole request; false for a part or prerequisite. Declared goals govern combined completion; runtime verifies success.")
    keywords: list[str] | None = Field(default=None, min_length=1,
        description="Complete discovery plan under this capability's policy; original phrases precede rewrites. Null for an exact lookup or explicitly requested single query/page.")
    original_keywords: list[str] | None = Field(default=None, min_length=1,
        description="Subject phrases copied from the user's request before rewriting; keep the user's wording and language. For a follow-up, explicit subjects from prior user messages may be used. Supply all original phrases first, include them in keywords; null for an exact lookup.")

    @model_validator(mode="after")
    def valid_keywords(self, info: ValidationInfo):
        policy = search_policy((info.context or {}).get("search_policy"))
        for phrases in (self.keywords, self.original_keywords):
            if phrases is None:
                continue
            if len(phrases)>policy.keyword_limit:
                raise ValueError(f"This discovery allows at most {policy.keyword_limit} distinct keywords.")
            if any(not value.strip() or len(value)>2000 for value in phrases):
                raise ValueError("Keywords must be non-empty phrases of at most 2000 characters.")
            if len({normalize_keyword(value) for value in phrases})!=len(phrases):
                raise ValueError("Supply distinct keywords; case and whitespace variations are the same keyword.")
        if self.original_keywords and self.keywords is None:
            raise ValueError("Original keywords require a discovery keyword plan.")
        return self


def search_guidance(policy=None):
    policy = search_policy(policy)
    return (
        "For broad discovery extract subject phrases verbatim from the current user's request into original_keywords, preserving wording and language. "
        "For contextual follow-ups use explicit prior user subjects only when needed; current subjects take priority. Ask for a missing subject instead of inventing one. "
        "Put original phrases FIRST, then useful rewrites, synonyms or translations in keywords, and use the first original as the native query. "
        "Once started, preserve the original phrases and append rewrites to the same search. "
        "Do not use generic request verbs or guessed classification codes as subjects. "
        f"At most {policy.keyword_limit} distinct phrases TOTAL. Runtime stops after {policy.candidate_stop} actually returned unique candidates "
        f"or {policy.keyword_limit} completed keywords; paging and safe transport retries do not consume another keyword. "
        "Upstream totals do not satisfy this threshold. Do not read saved results merely to count rows or add unrequested detail/sampling calls. "
        "For a named object preserve its full supplied name in an exact lookup first; finding it does not implicitly request details, directory or samples. "
        "Set keywords and original_keywords to null for exact lookups and explicitly requested single queries/pages. "
        "Set complete_request=true only if this is the whole requested scope; use false for prerequisites, and keep independent outcomes separate. "
        "A completed discovery with positive candidates is valid even below the early-stop threshold; exhausted zero means no matches in the searched scope. "
        "An interrupted search is not evidence of no matches."
    )


def task_schema(policy=None):
    """The model's bounds and runtime validation use the same resolved policy."""
    policy = search_policy(policy)
    schema = TaskDirective.model_json_schema()
    for name in ("keywords", "original_keywords"):
        field = schema["properties"][name]
        for variant in field.get("anyOf", [field]):
            if variant.get("type")=="array":
                variant["maxItems"] = policy.keyword_limit
    schema["properties"]["keywords"]["description"] = search_guidance(policy)
    return schema


def normalize_keyword(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def ordered_keywords(keywords, originals, request, history=(), previous=None, *, policy=None):
    """Ground extraction in user text, then order the bounded query plan.

    No vocabulary or topic-specific rewrite rules live in the runtime. The
    model extracts subjects; literal source checking prevents translations
    from being passed off as original wording.
    """
    previous = previous or {}
    # An ongoing search owns its policy snapshot. Old snapshots retain the
    # legacy defaults even if newly advertised tool metadata has changed.
    policy = search_policy(previous["profile"].get("policy") if "profile" in previous else policy)
    sources = [normalize_keyword(request), *(normalize_keyword(text) for text in history)]
    old = previous.get("original_keywords", [])
    if old:
        original_keys = {normalize_keyword(word) for word in old}
        if originals is not None and {normalize_keyword(word) for word in originals}!=original_keys:
            raise QAError("invalid_parameters", "已有检索的原词已确定，请继续其改写词计划")
        # Provenance is established once. A later rewrite may itself occur in
        # the request; that does not change the accepted extraction or order.
        originals = list(old)
    else:
        if originals is None:
            # Older calls may infer provenance from user text, never tool output.
            originals = [word for word in keywords if any(normalize_keyword(word) in text for text in sources)]
        if not originals or any(not any(normalize_keyword(word) in text for text in sources) for word in originals):
            raise QAError("invalid_parameters", "请先从用户原请求提取主题词，再补充改写词", detail={
                "guidance": "original_keywords must quote subject phrases from the current request or explicit prior user requests. Do not translate, invent categories, or copy tool output into original_keywords."})
        originals = list(originals)
        original_keys = {normalize_keyword(word) for word in originals}
        # On initial extraction, current-request phrases precede rewrites even
        # when omitted from the model's provenance annotation.
        for word in keywords:
            key = normalize_keyword(word)
            if key in sources[0] and key not in original_keys:
                originals.append(word)
                original_keys.add(key)
        originals.sort(key=lambda word: normalize_keyword(word) not in sources[0])
    unique = {}
    for word in [*originals, *keywords]:
        unique.setdefault(normalize_keyword(word), word.strip())
    values = list(unique.values())
    ordered = [word for word in values if normalize_keyword(word) in original_keys]
    ordered.extend(word for word in values if normalize_keyword(word) not in original_keys)
    if len({normalize_keyword(word) for word in [*previous.get("keywords", []), *ordered]})>policy.keyword_limit:
        raise QAError("invalid_parameters", f"原词和改写词合计最多{policy.keyword_limit}个不同关键词")
    return ordered, [word.strip() for word in originals]


def record_key(row, paths=(), *, identity_mode="fallback"):
    if identity_mode not in {"fallback", "composite"}:
        raise QAError("invalid_schema", "记录身份模式无效", 502)
    components = []
    for path in paths:
        try:
            value = at_path(row, path)
        except QAError:
            if identity_mode=="composite":
                break
            continue
        if isinstance(value, (str, int)) and not isinstance(value, bool) and value!="":
            if identity_mode=="fallback":
                return encode([path, value])
            components.append([path, value])
        elif identity_mode=="composite":
            break
    if identity_mode=="composite" and paths and len(components)==len(paths):
        return "composite:"+encode(components)
    # A partial composite key is not an identity: unrelated rows sharing the
    # remaining components must stay distinct. Identical rows may still merge.
    # Canonicalize the opt-in composite fallback, including nested objects.
    # Legacy keys retain their original encoding so saved progress still matches.
    serialized = (json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        if identity_mode=="composite" else encode(row))
    return "record:"+sha256(serialized.encode()).hexdigest()


class SearchRun:
    """Serializable progress; only successful, validated pages advance a query."""
    def __init__(self, state):
        self.state = state

    @classmethod
    def create(cls, descriptor, arguments, keywords):
        base = {key: deepcopy(value) for key, value in arguments.items()
            if key not in {descriptor.query, descriptor.page}}
        return cls({"profile": descriptor.model_dump(), "base": base, "keywords": [],
            "completed": [], "queried": [], "index": 0, "page": 1, "page_records": [], "records": [],
            "result_ids": [], "done": False, "stop": None}).extend(arguments, keywords)

    @property
    def descriptor(self):
        return SearchProfile.model_validate(self.state["profile"])

    @property
    def minimum(self):
        return self.descriptor.policy.candidate_stop

    @property
    def maximum_keywords(self):
        return self.descriptor.policy.keyword_limit

    @property
    def needs_keywords(self):
        return not self.state["done"] and self.state["index"]>=len(self.state["keywords"])

    @property
    def progress(self):
        """Only completed retrieval advances progress, not queue edits or replay."""
        state = self.state
        return state["index"], state["page"], len(state["records"]), state["done"]

    def extend(self, arguments, keywords):
        descriptor = self.descriptor
        base = {key: value for key, value in arguments.items() if key not in {descriptor.query, descriptor.page}}
        if not same_identity(base, self.state["base"]):
            raise QAError("invalid_parameters", "同一检索目标的筛选条件不能在关键词扩展中悄然改变")
        values = [arguments.get(descriptor.query), *(keywords or [])]
        known = {normalize_keyword(value) for value in self.state["keywords"]}
        proposed = list(self.state["keywords"])
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise QAError("invalid_parameters", "主题检索需要非空关键词")
            normalized = normalize_keyword(value)
            if normalized not in known:
                proposed.append(value.strip())
                known.add(normalized)
        if len(proposed)>self.maximum_keywords:
            raise QAError("invalid_parameters", f"本次检索最多使用{self.maximum_keywords}个不同关键词", detail={"keywords": self.state["keywords"]})
        if any(arguments.get(key) not in (None, "", []) for key in descriptor.opaque_filters):
            raise QAError("invalid_parameters", "主题检索请使用关键词；未经确认的分类筛选不能用于扩展查询",
                detail={"query_parameter": descriptor.query, "omit": descriptor.opaque_filters})
        self.state["keywords"] = proposed
        return self

    def arguments(self):
        state, descriptor = self.state, self.descriptor
        if state["done"] or state["index"]>=len(state["keywords"]):
            return None
        value = {**deepcopy(state["base"]), descriptor.query: state["keywords"][state["index"]]}
        if descriptor.page:
            value[descriptor.page] = state["page"]
        return value

    @staticmethod
    def rows(data, collection):
        try:
            rows = at_path(data, collection)
        except QAError as exc:
            raise QAError("invalid_result", "检索结果未提供声明的数据列表", 502) from exc
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise QAError("invalid_result", "检索结果的数据列表格式不符合约定", 502)
        return rows

    def record(self, data, collection, result_id):
        state, descriptor = self.state, self.descriptor
        rows = self.rows(data, collection)
        keyword = state["keywords"][state["index"]]
        state["queried"] = list(dict.fromkeys([*state.get("queried", []), keyword]))
        keys = list(dict.fromkeys(record_key(row, descriptor.identity, identity_mode=descriptor.identity_mode) for row in rows))
        fresh = bool(set(keys)-set(state["page_records"]))
        state["page_records"] = list(dict.fromkeys([*state["page_records"], *keys]))
        state["records"] = list(dict.fromkeys([*state["records"], *keys]))
        state["result_ids"] = list(dict.fromkeys([*state["result_ids"], result_id]))
        if len(state["records"])>=self.minimum:
            state["completed"] = list(dict.fromkeys([*state["completed"], keyword]))
            state.update(done=True, stop="enough")
            return
        total = None
        if descriptor.total:
            try:
                value = at_path(data, descriptor.total)
                if type(value) is int and value>=0:
                    total = value
            except QAError:
                pass
        size = state["base"].get(descriptor.page_size) if descriptor.page_size else None
        more = (type(size) is int and size>0 and
            (total>state["page"]*size if total is not None else len(rows)>=size))
        if descriptor.page and fresh and more:
            state["page"] += 1
            return
        self.close_keyword()

    def close_keyword(self):
        state = self.state
        state["completed"].append(state["keywords"][state["index"]])
        state.update(index=state["index"]+1, page=1, page_records=[])
        if len(state["completed"])==self.maximum_keywords:
            state.update(done=True, stop="exhausted")

    def view(self):
        state = self.state
        return {"unique_count": len(state["records"]), "minimum": self.minimum,
            "original_keywords": state.get("original_keywords", []),
            "queried_keywords": state.get("queried", []),
            "keywords": state["keywords"], "completed_keywords": state["completed"],
            "remaining_keywords": self.maximum_keywords-len(state["keywords"]),
            "done": state["done"], "stop": state["stop"],
            "guidance": ("The discovery policy is complete; do not expand this search." if state["done"] else
                "Continue this same search outcome with the remaining distinct keywords. Paging and retries do not count as new keywords. Do not register another goal or declare no matches before the policy completes.")}
