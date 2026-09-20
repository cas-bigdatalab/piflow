from datetime import date, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field, field_validator
from .config import StrictModel
from ..contracts import TurnInput
from .warning.contracts import Assessment
from .warning.analysis import WarningAnalysis
from .analysis_context import UserContext


class SessionCreateRequest(StrictModel):
    request_id: str = Field(default_factory=lambda: uuid4().hex, min_length=1, max_length=160, pattern=r"\S")
    title: str = Field(default="", max_length=255)


class TaskParams(StrictModel):
    case_ids: list[str] = Field(min_length=1)
    # None preserves saved legacy tasks. New requests explicitly use [] for univariate forecasts.
    auxiliary_case_ids: list[str] | None = None
    origin: datetime
    # Model inputs stop here when the requested forecast window starts later (e.g. tomorrow).
    history_cutoff: datetime | None = None
    # Explicit input interval (history_start, history_cutoff], on the existing sample grid.
    history_start: datetime | None = None
    horizon_hours: int = Field(gt=0)
    history_hours: int | None = Field(default=None, gt=0)
    origin_mode: Literal["explicit", "now", "replay", "tomorrow"] | None = None
    # None preserves the mode of legacy saved tasks; new plans set this per request.
    forecast_mode: Literal["current", "historical_replay"] | None = None

    @field_validator("origin", "history_cutoff", "history_start")
    @classmethod
    def aware(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("预测起点必须包含时区，例如 2025-07-04T02:00:00Z")
        return value


class TaskReference(StrictModel):
    order: Literal["first", "latest", "match"] = "match"
    index: int = Field(default=1, ge=1)
    created_date: date | None = None  # Calendar date in UTC, supplied explicitly or relative to prompt's UTC clock.
    case_id: str | None = None
    horizon_hours: int | None = Field(default=None, gt=0)


class Intent(StrictModel):
    action: Literal["predict", "reuse", "explain", "compare", "report", "status", "cancel", "retry", "help", "clarify", "unsupported"] = "predict"
    case_ids: list[str] | None = None
    auxiliary_case_ids: list[str] | None = Field(default=None, max_length=16)
    origin: str | None = None
    horizon_hours: int | None = None
    run_ids: list[str] = Field(default_factory=list, max_length=2)
    references: list[TaskReference] = Field(default_factory=list, max_length=2)
    origin_mode: Literal["explicit", "now", "replay", "tomorrow"] | None = None
    history_hours: int | None = Field(default=None, gt=0)
    history_start: str | None = None
    history_cutoff: str | None = None
    history_mode: Literal["auto", "explicit"] | None = None
    requested_area: str | None = None
    requested_variable: str | None = None
    requested_hazard: str | None = None
    wants_probability: bool = False
    analysis_context: UserContext | None = None


class ForecastPoint(StrictModel):
    timestamp: str
    prediction: float
    q10: float
    q90: float


class SeriesResult(StrictModel):
    case_id: str
    label: str
    variable: str
    unit: str
    history: list[dict[str, Any]]
    predictions: list[ForecastPoint]
    # Predicted bridge from history to origin; draw with predictions, exclude from window statistics/CSV.
    forecast_context: list[ForecastPoint] = Field(default_factory=list)
    observations: list[dict[str, Any]]
    quality: dict[str, Any]
    summary: dict[str, Any]
    evaluation: dict[str, Any]
    provenance: dict[str, Any]
    assessment: Assessment | None = None
    history_window: dict[str, Any] = Field(default_factory=dict)
    postprocessing: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForecastResult(StrictModel):
    presentation: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    computation_version: str = "1.0"
    run_id: str
    task: TaskParams
    model: dict[str, Any]
    series: list[SeriesResult]
    timings_seconds: dict[str, float] = Field(default_factory=dict)
    facts: dict[str, str] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    warning_analysis: WarningAnalysis | None = None
    analysis_context: dict[str, Any] = Field(default_factory=dict)
    research: dict[str, Any] = Field(default_factory=dict)
    report_status: Literal["pending", "completed", "failed"] = "pending"
