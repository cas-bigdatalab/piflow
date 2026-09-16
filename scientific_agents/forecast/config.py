from pathlib import Path
from typing import Literal
import os

import yaml
from pydantic import Field, model_validator
from ..contracts import StrictModel
from ..paths import AGENTS_ROOT, PROJECT_ROOT
from .warning.contracts import Scenario
from .warning.standard import RiskStandard
from .analysis_context import DomainContext


class Variable(StrictModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str = Field(default="", max_length=2000)
    file: str = ""
    time_column: str = "timestamp"
    value_column: str = "value"
    unit: str
    scale: float = 1.0
    aggregation: Literal["mean", "sum", "last"] = "mean"
    timezone: str = "UTC"
    available_at_column: str | None = None
    quality_column: str | None = None
    valid_quality_values: list[str] = Field(default_factory=list)
    future_known: bool = False
    # Physical support in the final unit, independent of warning thresholds.
    minimum: float | None = Field(default=None, allow_inf_nan=False)
    maximum: float | None = Field(default=None, allow_inf_nan=False)
    attention: Literal["both", "high", "low", "change"] = "both"
    # Metadata is explicit: do not infer circular angles or overlapping totals from names.
    semantics: Literal["scalar", "circular_degrees", "rolling_total"] = "scalar"
    transform: Literal["unwrap_degrees"] | None = None
    window_minutes: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def valid_bounds(self):
        if self.minimum is not None and self.maximum is not None and self.minimum >= self.maximum:
            raise ValueError("变量物理下界必须小于上界")
        if self.semantics == "rolling_total" and (not self.window_minutes or self.aggregation == "sum"):
            raise ValueError("滑动累计量须声明window_minutes并使用last或mean，不能重复求和")
        if self.semantics == "circular_degrees" and self.aggregation == "sum":
            raise ValueError("环形角度不能求和，请使用mean或last")
        return self


class Location(StrictModel):
    name: str = ""
    address: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    coordinate_system: Literal["WGS84", "GCJ02", "BD09"] = "WGS84"

    @model_validator(mode="after")
    def coordinate_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("位置经纬度必须同时填写或同时留空")
        return self


class Case(StrictModel):
    id: str
    label: str
    station_id: str
    location: Location | None = None
    directory: str = ""
    target: Variable
    covariates: list[Variable] = Field(default_factory=list)
    analysis_context: DomainContext = Field(default_factory=DomainContext)

    @model_validator(mode="after")
    def valid_variables(self):
        variables = [self.target, *self.covariates]
        if len({v.name for v in variables}) != len(variables):
            raise ValueError("变量名称不能重复")
        names = {v.name for v in variables}
        if any(v.name + suffix in names for v in variables if v.semantics == "circular_degrees" for suffix in ("__sin", "__cos")):
            raise ValueError("环形变量的派生分量名称与已有变量冲突")
        if self.target.future_known:
            raise ValueError("预测目标不能声明为已知未来变量")
        if any(v.future_known and not v.available_at_column for v in variables):
            raise ValueError("已知未来变量必须声明发布时间列")
        return self


class LocalFiles(StrictModel):
    directory: Path
    manifest: str = "manifest.json"


class Source(StrictModel):
    id: str = Field(min_length=1)
    display_name: str = ""
    location: Location | None = None
    kind: str = "local_csv"
    version: str = Field(default="auto", min_length=1)
    path: str | None = None
    discover: bool = False
    local: LocalFiles | None = None
    options: dict = Field(default_factory=dict)
    license: str = "未提供"
    citation: str = "未提供"
    cases: list[Case] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_transport(self):
        if self.kind == "local_csv" and self.local is None:
            raise ValueError("local_csv数据源必须配置local.directory")
        if self.kind == "local_csv" and any(not v.file for c in self.cases for v in [c.target, *c.covariates]):
            raise ValueError("local_csv变量必须指定CSV文件")
        if self.kind != "local_csv" and self.local is not None:
            raise ValueError("接口数据源不应包含本地文件配置")
        return self


class ExecutionLimits(StrictModel):
    queue_seconds: float = Field(default=300, gt=0)
    task_seconds: float = Field(default=600, gt=0)
    stage_seconds: float = Field(default=180, gt=0)
    cancel_grace_seconds: float = Field(default=15, gt=0)


class Settings(StrictModel):
    registry_path: Path | None = Field(default=None, exclude=True)
    risk_standard: RiskStandard | None = None
    model_dir: Path = Path("/data/models/timesfm")
    warning_scenarios: list[Scenario] = Field(default_factory=list)
    cpu_threads: int = Field(default=4, ge=1, le=32)
    frequency_minutes: int = Field(default=15, ge=1)
    context_steps: int = Field(default=96, ge=8)
    history_multiplier: int = Field(default=4, ge=1, le=16)
    horizons_hours: list[int] = [1, 3, 6]
    max_cases: int = Field(default=3, ge=1, le=10)
    max_missing_fraction: float = Field(default=0.02, ge=0, le=0.1)
    forward_fill_limit: int = Field(default=1, ge=0, le=2)
    execution: ExecutionLimits = Field(default_factory=ExecutionLimits)
    root: Path = Path("workspace/forecast_extension")
    sources: list[Source]

    @model_validator(mode="after")
    def valid_registry(self):
        if len({s.id for s in self.sources}) != len(self.sources):
            raise ValueError("source IDs must be unique")
        ids = [c.id for s in self.sources for c in s.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("case IDs must be unique")
        if not self.horizons_hours or any(h <= 0 or h * 60 % self.frequency_minutes for h in self.horizons_hours):
            raise ValueError("horizons must be positive whole forecast steps")
        return self


def load_settings(path: str | Path | None = None, *, factories=None) -> Settings:
    config_path = Path(path or os.getenv("FORECAST_CONFIG", AGENTS_ROOT / "configs" / "forecast.yaml")).expanduser().resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if "sources" in raw or "warning_scenarios" in raw:
        raise ValueError("数据源与场景只能写在独立的sources.yaml注册文件中")
    registry_path = Path(raw.pop("data_registry", "sources.yaml")).expanduser()
    if not registry_path.is_absolute():
        registry_path = config_path.parent / registry_path
    catalog = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    unknown = set(catalog) - {"sources", "scenarios", "metadata"}
    if unknown:
        raise ValueError(f"未知注册字段：{sorted(unknown)}")
    raw["sources"], raw["warning_scenarios"] = registry_entries(catalog, registry_path, factories)
    raw["registry_path"] = registry_path.resolve()
    standard_path = raw.pop("risk_standard", None)
    if standard_path:
        standard_path = Path(standard_path).expanduser()
        if not standard_path.is_absolute():
            standard_path = config_path.parent / standard_path
        raw["risk_standard"] = yaml.safe_load(standard_path.read_text(encoding="utf-8"))
    if "FORECAST_MODEL_DIR" in os.environ:
        raw["model_dir"] = os.environ["FORECAST_MODEL_DIR"]
    settings = Settings.model_validate(raw)
    settings.model_dir = settings.model_dir.expanduser()
    if not settings.model_dir.is_absolute():
        settings.model_dir = (config_path.parent / settings.model_dir).resolve()
    for source in settings.sources:
        if source.local:
            folder = source.local.directory.expanduser()
            source.local.directory = folder if folder.is_absolute() else (registry_path.parent / folder).resolve()
    settings.root = Path(os.getenv("FORECAST_ROOT", str(settings.root)))
    if not settings.root.is_absolute():
        settings.root = PROJECT_ROOT / settings.root
    return settings


def registry_entries(catalog, path, factories=None):
    """Optional legacy metadata preserves existing IDs; new sources need only a path."""
    from copy import deepcopy
    if set(catalog) - {"sources", "scenarios", "metadata"}:
        raise ValueError("数据源入口存在未知配置字段")
    ids = [s["id"] for s in catalog.get("sources", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("数据源 ID 不能重复")
    metadata = {}
    if catalog.get("metadata"):
        metadata = yaml.safe_load((path.parent / catalog["metadata"]).read_text(encoding="utf-8")) or {}
    profiles = {s["id"]: s for s in metadata.get("sources", [])}
    entries = []
    for configured in catalog.get("sources", []):
        source = deepcopy(profiles.get(configured["id"], {}))
        source.update(configured)
        if source.get("path"):
            directory = Path(source["path"]).expanduser()
            if not directory.is_absolute():
                directory = (path.parent / directory).resolve()
            source.update(path=str(directory), discover=True)
            if source.get("kind", "local_csv") in {"local_csv", "directory"}:
                source.update(kind="directory", local=None)
        entries.append(source)
    case_ids = {c["id"] for s in entries for c in s.get("cases", [])}
    scenarios = [s for s in metadata.get("scenarios", []) if s["case_id"] in case_ids]
    scenarios.extend(catalog.get("scenarios", []))
    # Format-specific configuration belongs to the registered provider, both at
    # startup and on refresh. Unknown custom kinds remain intact for plugins.
    if factories is None:
        from .providers import builtin_providers
        factories = builtin_providers()
    for source in entries:
        configure = getattr(factories.get(source.get("kind", "local_csv")), "configure", None)
        if configure:
            configure(source, scenarios)
    return entries, scenarios
