"""Optional capability routing; the transport server is not a data source."""
from pydantic import BaseModel, ConfigDict, Field


class Routing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group: str = Field(min_length=1, max_length=80)
    source: str = Field(default="", max_length=80)
    operations: list[str] = Field(default_factory=list, max_length=12)
    inputs: list[str] = Field(default_factory=list, max_length=12)
    outputs: list[str] = Field(default_factory=list, max_length=12)


def select_tools(items, query, *, group=None, recent=()):
    from .capabilities import profile
    from .mcp import terms

    items = list(items)
    wanted, previous = terms(query), set(recent)
    candidates = [(tool, None if isinstance(tool, dict) else profile(tool).routing) for tool in items]
    # Match complete advertised source names, not incidental words in tool
    # descriptions. Source-neutral transforms remain available in this scope.
    sources = {routing.source for _, routing in candidates
        if routing and routing.source and terms(routing.source) <= wanted}
    scored = []
    for index, (tool, routing) in enumerate(candidates):
        if isinstance(tool, dict):
            if not group:
                scored.append((0, -len(wanted & terms(tool["name"])), True, index, tool))
            continue
        if group and (routing is None or routing.group != group):
            continue
        # A source mention is a retrieval hint, not a semantic decision or an
        # authorization boundary. Keep other sources reachable through paging;
        # only an explicitly requested group filters the catalogue.
        outside = bool(not group and sources and routing and routing.source and routing.source not in sources)
        vocabulary = tool.name + " " + tool.description
        if routing:
            vocabulary += " " + " ".join([routing.group, routing.source,
                *routing.operations, *routing.inputs, *routing.outputs])
        score = len(wanted & terms(vocabulary))
        # History breaks a relevance tie; it cannot override this request.
        scored.append((outside, -score, (tool.server, tool.name) not in previous, index, tool))
    return [row[-1] for row in sorted(scored, key=lambda row: row[:4])]
