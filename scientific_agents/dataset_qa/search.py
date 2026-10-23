"""Bounded discovery policy, separate from MCP transport retries and planning."""
from copy import deepcopy
from hashlib import sha256
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .context import encode
from .contracts import QAError
from .references import at_path


class SearchProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    page: str | None = None
    page_size: str | None = None
    total: str | None = None
    identity: list[str] = Field(default_factory=list, max_length=8)
    # Opaque classifications are not free-text search fields. Adapters expose
    # these only for exact operations with independently grounded parameters.
    opaque_filters: list[str] = Field(default_factory=list, max_length=16)


class TaskDirective(BaseModel):
    model_config = ConfigDict(extra="forbid")
    complete_request: bool = Field(description="True only if this operation completes the entire current request. False for a prerequisite of subsequent processing or another requested operation.")
    keywords: list[str] | None = Field(default=None, min_length=1, max_length=4,
        description="Complete discovery plan: original phrases first, then rewrites, synonyms or translations, at most four distinct phrases in total. Runtime stops at six unique candidates or four completed keywords. Null for an exact lookup.")
    original_keywords: list[str] | None = Field(default=None, min_length=1, max_length=4,
        description="Subject phrases copied from the user's request before rewriting; keep the user's wording and language. For a follow-up, explicit subjects from prior user messages may be used. Supply all original phrases first, include them in keywords; null for an exact lookup.")

    @model_validator(mode="after")
    def valid_keywords(self):
        for phrases in (self.keywords, self.original_keywords):
            if phrases is None:
                continue
            if any(not value.strip() or len(value)>2000 for value in phrases):
                raise ValueError("Keywords must be non-empty phrases of at most 2000 characters.")
            if len({normalize_keyword(value) for value in phrases})!=len(phrases):
                raise ValueError("Supply distinct keywords; case and whitespace variations are the same keyword.")
        if self.original_keywords and self.keywords is None:
            raise ValueError("Original keywords require a discovery keyword plan.")
        return self


def normalize_keyword(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def ordered_keywords(keywords, originals, request, history=(), previous=None):
    """Ground extraction in user text, then order the bounded query plan.

    No vocabulary or topic-specific rewrite rules live in the runtime. The
    model extracts subjects; literal source checking prevents translations
    from being passed off as original wording.
    """
    previous = previous or {}
    sources = [normalize_keyword(request), *(normalize_keyword(text) for text in history)]
    old = previous.get("original_keywords", [])
    if originals is None:
        # Compatibility with saved/older calls: infer provenance only where
        # the phrase is actually present in user text, never from a tool reply.
        originals = old or [word for word in keywords if any(normalize_keyword(word) in text for text in sources)]
    old_keys = {normalize_keyword(word) for word in old}
    if not originals or any(normalize_keyword(word) not in old_keys
            and not any(normalize_keyword(word) in text for text in sources) for word in originals):
        raise QAError("invalid_parameters", "请先从用户原请求提取主题词，再补充改写词", detail={
            "guidance": "original_keywords must quote subject phrases from the current request or explicit prior user requests. Do not translate, invent categories, or copy tool output into original_keywords."})
    # A verbatim current-request phrase must not be scheduled after rewrites
    # merely because the model omitted it from its provenance annotation.
    originals = list(originals)
    original_keys = {normalize_keyword(word) for word in originals}
    for word in keywords:
        key = normalize_keyword(word)
        if key in sources[0] and key not in original_keys:
            originals.append(word)
            original_keys.add(key)
    if old and original_keys!={normalize_keyword(word) for word in old}:
        raise QAError("invalid_parameters", "已有检索的原词已确定，请继续其改写词计划")
    # Keep original request phrases ahead of historical context, preserving
    # the model's extraction order within each source group.
    originals = sorted(originals, key=lambda word: normalize_keyword(word) not in sources[0])
    unique = {}
    for word in [*originals, *keywords]:
        unique.setdefault(normalize_keyword(word), word.strip())
    values = list(unique.values())
    ordered = [word for word in values if normalize_keyword(word) in original_keys]
    ordered.extend(word for word in values if normalize_keyword(word) not in original_keys)
    if len({normalize_keyword(word) for word in [*previous.get("keywords", []), *ordered]})>4:
        raise QAError("invalid_parameters", "原词和改写词合计最多四个不同关键词")
    return ordered, [word.strip() for word in originals]


def record_key(row, paths=()):
    for path in paths:
        try:
            value = at_path(row, path)
        except QAError:
            continue
        if isinstance(value, (str, int)) and not isinstance(value, bool) and value!="":
            return encode([path, value])
    return "record:"+sha256(encode(row).encode()).hexdigest()


class SearchRun:
    """Serializable progress; only successful, validated pages advance a query."""
    minimum = 6
    maximum_keywords = 4

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

    def extend(self, arguments, keywords):
        descriptor = self.descriptor
        base = {key: value for key, value in arguments.items() if key not in {descriptor.query, descriptor.page}}
        if base!=self.state["base"]:
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
            raise QAError("invalid_parameters", "本次检索最多使用四个不同关键词", detail={"keywords": self.state["keywords"]})
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
        keys = list(dict.fromkeys(record_key(row, descriptor.identity) for row in rows))
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
