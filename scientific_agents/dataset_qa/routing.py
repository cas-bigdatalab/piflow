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

    wanted, previous = terms(query), set(recent)
    scored = []
    for index, tool in enumerate(items):
        if isinstance(tool, dict):
            if not group:
                scored.append((-len(wanted & terms(tool["name"])), True, index, tool))
            continue
        routing = profile(tool).routing
        if group and (routing is None or routing.group != group):
            continue
        vocabulary = tool.name + " " + tool.description
        if routing:
            vocabulary += " " + " ".join([routing.group, routing.source,
                *routing.operations, *routing.inputs, *routing.outputs])
        score = len(wanted & terms(vocabulary))
        # History breaks a relevance tie; it cannot override this request.
        scored.append((-score, (tool.server, tool.name) not in previous, index, tool))
    return [row[-1] for row in sorted(scored, key=lambda row: row[:3])]
