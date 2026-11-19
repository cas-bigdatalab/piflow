"""Optional capability routing; the transport server is not a data source."""
from pydantic import BaseModel, ConfigDict, Field


class Routing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group: str = Field(min_length=1, max_length=80)
    source: str = Field(default="", max_length=80)
    operations: list[str] = Field(default_factory=list, max_length=12)
    inputs: list[str] = Field(default_factory=list, max_length=12)
    outputs: list[str] = Field(default_factory=list, max_length=12)


def _routing_terms(text):
    from .mcp import terms

    # Keep exact identifiers while also matching ordinary words in snake_case.
    return terms(text) | terms(str(text).replace("_", " "))


def _schema_words(schema):
    """Read advertised input vocabulary, excluding examples and defaults."""
    if not isinstance(schema, dict):
        return
    for key in ("title", "description"):
        if isinstance(schema.get(key), str):
            yield schema[key]
    yield from (value for value in schema.get("enum", []) if isinstance(value, str))
    for key in ("properties", "$defs", "definitions"):
        for name, child in schema.get(key, {}).items():
            if key == "properties":
                yield name
            yield from _schema_words(child)
    for key in ("items", "additionalProperties", "contains", "not", "if", "then", "else"):
        yield from _schema_words(schema.get(key))
    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        for child in schema.get(key, []):
            yield from _schema_words(child)


def resource_candidate(tool, resources):
    """Recall consumers in the resource's authority; dispatch still binds it."""
    from .capabilities import profile

    descriptor = profile(tool)
    return bool(descriptor.artifact and descriptor.artifact.consume
        and descriptor.artifact.consume in descriptor.bind
        and any(row.get("server") == tool.server and row.get("kind") == "record_resource" for row in resources))


def select_tools(items, query, *, group=None, recent=(), resources=()):
    from .capabilities import profile
    from .mcp import terms

    items = list(items)
    wanted, previous = _routing_terms(query), set(recent)
    candidates = [(tool, None if isinstance(tool, dict) else profile(tool).routing) for tool in items]
    # Match complete advertised source names, not incidental words in tool
    # descriptions. Source-neutral transforms remain available in this scope.
    sources = {routing.source for _, routing in candidates
        if routing and routing.source and terms(routing.source) <= wanted}
    scored = []
    for index, (tool, routing) in enumerate(candidates):
        if isinstance(tool, dict):
            if not group:
                scored.append((0, -len(wanted & _routing_terms(tool["name"])), True, index, tool))
            continue
        if group and (routing is None or routing.group != group):
            continue
        # A source mention is a retrieval hint, not a semantic decision or an
        # authorization boundary. Keep other sources reachable through paging;
        # only an explicitly requested group filters the catalogue.
        outside = bool(not group and sources and routing and routing.source and routing.source not in sources)
        vocabulary = " ".join([tool.name, tool.title, tool.description, *_schema_words(tool.schema)])
        if routing:
            vocabulary += " " + " ".join([routing.group, routing.source,
                *routing.operations, *routing.inputs, *routing.outputs])
        score = len(wanted & _routing_terms(vocabulary))
        # History breaks a relevance tie; it cannot override this request.
        scored.append((outside, -score, (tool.server, tool.name) not in previous, index, tool))
    ranked = [row[-1] for row in sorted(scored, key=lambda row: row[:4])]
    # Keep the request's leading candidate, while reserving one early slot for
    # a consumer of an actually delivered resource. This is candidate recall,
    # not an implicit focus switch or permission to reuse an old query.
    for index, tool in enumerate(ranked):
        if isinstance(tool, dict):
            continue
        if resource_candidate(tool, resources):
            if index > 1:
                ranked.insert(1, ranked.pop(index))
            break
    return ranked
