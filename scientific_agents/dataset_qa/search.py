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
        description="For broad discovery supply four distinct, relevant keyword phrases, including the first query. Runtime searches and paginates until six unique candidates or four completed keywords. Omit/null for an exact lookup or a non-search operation.")

    @model_validator(mode="after")
    def valid_keywords(self):
        if self.keywords is not None:
            if any(not value.strip() or len(value)>2000 for value in self.keywords):
                raise ValueError("Keywords must be non-empty phrases of at most 2000 characters.")
            if len({normalize_keyword(value) for value in self.keywords})!=len(self.keywords):
                raise ValueError("Supply distinct keywords; case and whitespace variations are the same keyword.")
        return self


def normalize_keyword(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


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
            "queried_keywords": state.get("queried", []),
            "keywords": state["keywords"], "completed_keywords": state["completed"],
            "remaining_keywords": self.maximum_keywords-len(state["keywords"]),
            "done": state["done"], "stop": state["stop"],
            "guidance": ("The discovery policy is complete; do not expand this search." if state["done"] else
                "Continue this same search outcome with the remaining distinct keywords. Paging and retries do not count as new keywords. Do not register another goal or declare no matches before the policy completes.")}
