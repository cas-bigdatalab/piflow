"""Finite, versioned contracts. A statistical forecast is not a disaster probability."""
from typing import Literal
from datetime import datetime

from pydantic import Field, model_validator

from ...contracts import StrictModel


class Condition(StrictModel):
    variable: str
    unit: str
    case_id: str | None = None  # Explicit reference to another selected prediction target.
    statistic: Literal["value", "mean", "max", "min", "sum", "rate"] = "value"
    window_steps: int = Field(default=1, ge=1, le=10000)
    operator: Literal["gt", "ge", "lt", "le"]
    threshold: float = Field(allow_inf_nan=False)
    # Rate integrates an explicitly per-hour measurement; sum requires interval totals.
    input_kind: Literal["instant", "interval_total", "rate_per_hour"] = "instant"
    output_unit: str | None = None

    @model_validator(mode="after")
    def meaningful(self):
        if self.statistic == "sum" and self.input_kind == "instant":
            raise ValueError("累计规则必须声明区间总量或每小时速率")
        if self.statistic == "sum" and self.input_kind == "rate_per_hour" and not self.output_unit:
            raise ValueError("速率积分必须声明输出单位")
        return self


class Rule(StrictModel):
    id: str
    version: str
    label: str
    source: str = Field(min_length=1)
    approved: bool = False
    level: str | None = None
    severity: int = Field(default=0, ge=0, le=10)
    basis: Literal["median", "q10", "q90"] = "median"
    combine: Literal["all", "any"] = "all"
    duration_minutes: int = Field(default=0, ge=0)
    conditions: list[Condition] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def quantile_scope(self):
        if self.basis != "median" and any(c.statistic != "value" for c in self.conditions):
            raise ValueError("不支持把逐点分位数累加或差分作为联合预测分位数")
        return self


class Scenario(StrictModel):
    use_history_screening: bool = False
    use_standard: bool = True
    case_id: str
    version: str
    area: str
    hazard_type: str
    aliases: list[str] = Field(default_factory=list)
    hazard_aliases: list[str] = Field(default_factory=list)
    mode: Literal["historical_replay", "current"] = "historical_replay"
    frequency_minutes: int | None = Field(default=None, ge=1)
    context_steps: int | None = Field(default=None, ge=8, le=15360)
    default_replay_origin: datetime | None = None
    horizons_hours: list[int] | None = None
    # Optional fixed override; otherwise choose by forecast horizon, not wording.
    max_data_age_minutes: int | None = Field(default=None, ge=1)
    hourly_max_data_age_minutes: int = Field(default=360, ge=1)
    daily_max_data_age_minutes: int = Field(default=2880, ge=1)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    rules: list[Rule] = Field(default_factory=list, max_length=64)

    def data_age_limit(self, horizon_hours: int) -> int:
        if self.max_data_age_minutes is not None:
            return self.max_data_age_minutes
        return self.daily_max_data_age_minutes if horizon_hours >= 24 else self.hourly_max_data_age_minutes

    @model_validator(mode="after")
    def unique_rules(self):
        if self.default_replay_origin is not None:
            if self.default_replay_origin.tzinfo is None or self.mode != "historical_replay":
                raise ValueError("默认回放时点必须包含时区，且只能配置在历史回放场景")
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("规则编号不能重复")
        if self.horizons_hours is not None and (not self.horizons_hours or any(h <= 0 for h in self.horizons_hours)):
            raise ValueError("场景预测时长必须为正")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("经纬度必须同时提供")
        return self


class Probability(StrictModel):
    available: bool = False
    value: float | None = Field(default=None, ge=0, le=1)
    reason_code: str = "probability_provider_not_configured"

    @model_validator(mode="after")
    def no_fabrication(self):
        if self.available or self.value is not None:
            raise ValueError("当前版本未实现外部概率提供器，不能声明灾害概率")
        return self


class Assessment(StrictModel):
    method: Literal["registered_rules", "historical_screening", "none"] = "none"
    schema_version: str = "1.0"
    mode: Literal["historical_replay", "current"]
    capability: Literal["indicator_forecast", "rule_assessment"]
    status: Literal["triggered", "not_triggered", "indeterminate", "not_assessed"]
    area: str
    hazard_type: str
    scenario_version: str
    window_start: str
    window_end: str
    level: str | None = None
    probability: Probability = Field(default_factory=Probability)
    evidence: list[dict] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    location: dict | None = None
