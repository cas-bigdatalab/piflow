"""Compile versioned research screening profiles into the existing rule engine."""
from typing import Literal

from pydantic import Field, model_validator

from ...contracts import StrictModel
from .contracts import Condition, Rule


class StandardRule(StrictModel):
    id: str
    label: str
    severity: int = Field(ge=1, le=4)
    statistic: Literal["value", "sum", "change"] = "value"
    window_hours: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    operator: Literal["gt", "ge", "lt", "le"]
    threshold: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def window_required(self):
        if (self.statistic == "value") != (self.window_hours is None):
            raise ValueError("累计和变化规则必须指定窗口，瞬时规则不能指定窗口")
        return self


class RiskProfile(StrictModel):
    id: str
    variables: list[str] = Field(min_length=1)
    units: list[str] = Field(min_length=1)
    aggregations: list[Literal["mean", "sum", "last"]] = Field(min_length=1)
    semantics: Literal["scalar", "rolling_total"] = "scalar"
    window_minutes: int | None = Field(default=None, ge=1)
    reference: str = Field(min_length=1)
    rules: list[StandardRule] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def unique_and_meaningful(self):
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("标准规则编号不能重复")
        if self.semantics == "rolling_total" and self.window_minutes is None:
            raise ValueError("滑动累计量必须注明时间窗口")
        if any(r.statistic == "sum" for r in self.rules) and (self.semantics != "scalar" or self.aggregations != ["sum"]):
            raise ValueError("累计标准仅用于sum聚合的区间总量，不能重复累加滑动量")
        return self


class RiskStandard(StrictModel):
    version: str = Field(min_length=1)
    profiles: list[RiskProfile] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_profiles(self):
        if len({p.id for p in self.profiles}) != len(self.profiles):
            raise ValueError("标准配置编号不能重复")
        return self

    def rules_for(self, variable, frequency):
        """Use exact metadata, never infer thresholds from station/column substrings."""
        levels = {1: "R1 留意", 2: "R2 关注", 3: "R3 重点关注", 4: "R4 优先核查"}
        result = []
        for profile in self.profiles:
            if (not ({variable.name, *variable.aliases} & set(profile.variables)) or variable.unit not in profile.units
                    or variable.aggregation not in profile.aggregations or variable.semantics != profile.semantics
                    or variable.window_minutes != profile.window_minutes):
                continue
            for template in profile.rules:
                steps = (template.window_hours * 60 / frequency) if template.window_hours else 1
                if int(steps) != steps:
                    continue  # Never round a 3-hour rule to a different sampling window.
                if not 1 <= steps <= 10000:
                    continue
                condition = Condition(variable=variable.name, unit=variable.unit,
                    statistic={"value": "value", "sum": "sum", "change": "rate"}[template.statistic],
                    window_steps=int(steps), operator=template.operator,
                    threshold=template.threshold / template.window_hours if template.statistic == "change" else template.threshold,
                    input_kind="interval_total" if template.statistic == "sum" else "instant")
                result.append(Rule(id=f"standard.{profile.id}.{template.id}", version=self.version,
                    label=template.label, source=f"项目研究标准 {self.version}（非官方预警）；{profile.reference}",
                    approved=True, level=levels[template.severity], severity=template.severity, conditions=[condition]))
        return result
