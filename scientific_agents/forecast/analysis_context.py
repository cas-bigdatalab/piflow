"""Open-ended report context. No domain routing or prediction configuration changes."""
from pydantic import Field

from ..contracts import StrictModel


class Reference(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=3000)
    source: str = Field(min_length=1, max_length=1000)


class DomainContext(StrictModel):
    domain: str = Field(default="", max_length=200)
    subject: str = Field(default="", max_length=500)
    objective: str = Field(default="", max_length=1000)
    background: str = Field(default="", max_length=4000)
    references: list[Reference] = Field(default_factory=list, max_length=10)


class UserContext(StrictModel):
    """User assertions, never promoted to validated observations or warning rules."""
    subject: str = Field(default="", max_length=500)
    objective: str = Field(default="", max_length=1000)
    background: str = Field(default="", max_length=4000)


def snapshot(registry, case_ids, user_context=None, messages=()):
    cases = []
    for key in case_ids:
        case = registry.cases[key]
        source = next(s for s in registry.source_specs if s.id == registry.case_sources[key])
        cases.append({"case_id": key, "label": case.label,
            "target": {"name": case.target.name, "unit": case.target.unit,
                       "description": case.target.description, "aggregation": case.target.aggregation},
            "covariates": [{"name": v.name, "unit": v.unit, "description": v.description} for v in case.covariates],
            "context": case.analysis_context.model_dump(mode="json"),
            "source": {"id": source.id, "version": source.version, "citation": source.citation}})
    return {"version": "1.0", "cases": cases,
            "user": UserContext.model_validate(user_context or {}).model_dump(),
            "recent_user_messages": [str(m["content"])[:2000] for m in messages if m.get("role") == "user"][-6:]}
