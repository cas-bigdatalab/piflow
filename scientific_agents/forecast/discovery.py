"""File-format discovery and immutable local snapshots; no model or dialogue calls."""
from contextlib import contextmanager
from hashlib import sha256
import io
import json
from pathlib import Path
import threading

import numpy as np
import pandas as pd

from .config import Case, Variable
from .providers import read_csv_series


def describe(source, data, filename, metadata=None):
    """Known metadata wins; otherwise numeric columns become independent targets."""
    metadata = metadata or {}
    time_column = metadata.get("time_column", "timestamp")
    if time_column not in data:
        raise ValueError(f"{filename}: 缺少时间列 {time_column}，请提供 forecast-source.json")
    timezone = metadata.get("timezone", "UTC")
    known, targets = {}, {}
    for case in source.cases:
        for variable in [case.target, *case.covariates]:
            if (not filename or variable.file == filename):
                known[variable.value_column] = variable
        column = case.target.value_column
        if not filename or case.target.file == filename:
            targets[column] = case
    excluded = {time_column, "station_id", "id", *metadata.get("exclude", [])}
    excluded.update(v.quality_column for v in known.values())
    excluded.update(v.available_at_column for v in known.values())
    output = []
    for column in data.columns:
        if column in excluded or column.endswith("__qc"):
            continue
        values = pd.to_numeric(data[column], errors="coerce")
        if not values.notna().any():
            continue
        observed = data[column].notna() & data[column].astype(str).ne("")
        if (observed & values.isna()).any():
            continue  # Text/flags are not forecast targets; explicitly declared fields fail validation on read.
        if column in targets:
            case = targets[column].model_copy(deep=True)
            if column in metadata.get("variables", {}):
                case.target = Variable.model_validate({**case.target.model_dump(), **metadata["variables"][column]})
        else:
            overrides = metadata.get("variables", {}).get(column, {})
            variable = known.get(column) or Variable(name=column, file=filename, value_column=column,
                time_column=time_column, timezone=timezone, unit="原始单位", aliases=[column])
            variable = Variable.model_validate({**variable.model_dump(), **overrides})
            identity = sha256(f"{source.id}\0{filename}\0{column}".encode()).hexdigest()[:20]
            station = metadata.get("station_id", source.id if not filename else f"{source.id}/{Path(filename).stem}")
            case = Case(id=f"series_{identity}", station_id=station, target=variable,
                        label=f"{metadata.get('display_name') or source.display_name or station} · {variable.description or variable.name}")
        if "location" in metadata:
            from .config import Location
            case.location = Location.model_validate(metadata["location"])
        if case.target.semantics == "circular_degrees":
            case.target = case.target.model_copy(update={"name": case.target.name + "_unwrapped",
                "semantics": "scalar", "transform": "unwrap_degrees", "minimum": None, "maximum": None})
            case.label += "（连续角度）"
        index = pd.DatetimeIndex(pd.to_datetime(data[case.target.time_column], errors="raise"))
        if index.tz is None:
            index = index.tz_localize(case.target.timezone)
        index = index.tz_convert("UTC")
        if index.hasnans or index.has_duplicates:
            raise ValueError(f"{filename}: 时间戳缺失或重复")
        finite = np.isfinite(values.to_numpy(dtype=float))
        valid = index[finite].sort_values()
        differences = pd.Series(index.sort_values()).diff().dropna().dt.total_seconds()
        minutes = float(differences.mode().iloc[0] / 60) if len(differences) else 0
        if minutes < 1 or not minutes.is_integer():
            raise ValueError(f"{filename}: 无法识别整分钟采样频率")
        case.covariates = []  # Combination belongs to a request, not catalogue registration.
        info = dict(first_observation=valid.min().isoformat() if len(valid) else None,
                    latest_observation=valid.max().isoformat() if len(valid) else None,
                    rows=len(valid), frequency_minutes=int(minutes), state="ready")
        info.update({k: metadata[k] for k in ("mode", "default_replay_origin") if k in metadata})
        output.append((case, info))
    return output


class DirectoryProvider:
    """Wide CSV / JSONL: one timestamp column and numeric observation columns per file.

    Only changed files are parsed. Copied bytes and their descriptors are content-addressed.
    A refresh publishes one complete revision; readers retain their pinned revision.
    """
    align_history = True

    def __init__(self, source, settings):
        self.source = source
        self.directory = Path(source.path)
        key = sha256(f"{source.id}\0{self.directory.resolve()}".encode()).hexdigest()[:20]
        self.root = settings.root / "catalog" / key
        self.lock, self.thread = threading.RLock(), threading.local()
        self.current, self.entries = {}, []
        self.status = {"state": "not_scanned"}

    def discover(self):
        with self.lock:
            root = self.directory.resolve(strict=True)
            spec_path = root / "forecast-source.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8-sig")) if spec_path.exists() else {}
            self.root.mkdir(parents=True, exist_ok=True)
            cache_path = self.root / "index.json"
            cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
            mapping, entries, updated = {}, [], {}
            processed = 0
            for path in sorted(root.rglob("*")):
                if path.suffix.lower() not in {".csv", ".jsonl"} or not path.is_file():
                    continue
                if root not in path.resolve().parents:
                    raise ValueError("数据文件超出配置目录")
                name = path.relative_to(root).as_posix()
                meta = {**spec, **spec.get("files", {}).get(name, {})}
                signature = [path.stat().st_size, path.stat().st_mtime_ns]
                identity = sha256(json.dumps([signature, meta, self.source.model_dump(mode="json"), 2], sort_keys=True).encode()).hexdigest()
                old = cache.get(name, {})
                if old.get("identity") == identity and Path(old["snapshot"]).exists():
                    item = old
                else:
                    content = path.read_bytes()
                    if signature != [path.stat().st_size, path.stat().st_mtime_ns] or len(content) != signature[0]:
                        raise ValueError(f"{name} 正在写入，请稍后刷新")
                    data = (pd.read_csv(io.BytesIO(content)) if path.suffix.lower() == ".csv"
                            else pd.read_json(io.StringIO(content.decode("utf-8-sig")), lines=True, convert_dates=False))
                    descriptions = describe(self.source, data, name, meta)
                    revision = sha256(content).hexdigest()
                    snapshot = self.root / f"{revision}.csv"
                    if not snapshot.exists():
                        temporary = snapshot.with_suffix(".tmp")
                        data.to_csv(temporary, index=False)
                        temporary.replace(snapshot)
                    item = dict(identity=identity, snapshot=str(snapshot), revision=revision,
                                entries=[dict(case=c.model_dump(mode="json"), info=i) for c, i in descriptions])
                    processed += 1
                updated[name] = item
                mapping[name] = (item["snapshot"], item["revision"])
                entries.extend((Case.model_validate(e["case"]), e["info"]) for e in item["entries"])
            temporary = cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(updated, ensure_ascii=False), encoding="utf-8")
            temporary.replace(cache_path)
            self.current, self.entries = mapping, entries
            self.status = dict(state="ready", files=len(mapping), variables=len(entries), processed_files=processed,
                               scanned_at=pd.Timestamp.now(tz="UTC").isoformat())
            return entries

    def catalog_status(self):
        return dict(self.status)

    @contextmanager
    def snapshot(self):
        previous = getattr(self.thread, "snapshot", None)
        self.thread.snapshot = dict(self.current)
        try:
            yield
        finally:
            self.thread.snapshot = previous

    def read(self, case, variable):
        mapping = getattr(self.thread, "snapshot", None) or self.current
        path, revision = mapping[variable.file]
        return read_csv_series(path, variable, dict(source_id=self.source.id, dataset_id=self.source.id,
            revision=revision, license=self.source.license, citation=self.source.citation, asset_origin="local"))


def common_history_end(series, origin, frequency):
    """Find the last common usable target-grid instant across independent sources."""
    from .analytics import resample_variable
    common = None
    for raw, variable in series:
        values = raw.values.loc[raw.values.index <= origin]
        if raw.available_at is not None:
            values = values.loc[raw.available_at.reindex(values.index) <= origin]
        index = resample_variable(values, frequency, variable).dropna().index
        common = index if common is None else common.intersection(index)
    if common is None or common.empty:
        raise ValueError("目标与辅助变量没有共同可用的历史时间窗口")
    return common.max()
