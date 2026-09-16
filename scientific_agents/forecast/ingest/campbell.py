"""Incremental Campbell JSONL -> immutable CSV snapshots, outside model logic."""
from contextlib import closing, contextmanager
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import sqlite3
import threading
import time

import pandas as pd
from pydantic import Field

from ...contracts import StrictModel
from ..feedback import ForecastError
from ..providers import read_csv_series
from . import campbell_source


class Options(StrictModel):
    register_all_variables: bool = False
    case_prefix: str = "campbell"
    bridge_delayed_observations: bool = True
    directory: str = "/mnt/corpus/corpus/ST001-CAMPBELL-B001"
    scan_interval_seconds: float = Field(default=60, ge=0)
    # Maximum wait for another local scanner's SQLite transaction.
    timeout_seconds: float = Field(default=20, gt=0, le=120)
    missing_values: list[str] = ["", "NAN", "NULL", "NONE", "-9999", "-9999.0", "-6999", "-7999"]


class CampbellProvider:
    @staticmethod
    def configure(source, scenarios):
        """Normalize only this format; IDs and registered observation semantics stay stable."""
        from .campbell_registry import expand
        if source.get("path"):
            source["options"] = {**source.get("options", {}), "directory": source["path"]}
        expand(source, scenarios)

    @staticmethod
    def auxiliary_variable(variable):
        """Resolve the legacy virtual channel to its observed column before role conversion."""
        if variable.value_column == "WD_Unwrapped":
            return variable.model_copy(update={"value_column": "WD_Avg", "transform": "unwrap_degrees"})
        return variable

    def __init__(self, source, settings):
        self.source = source
        self.options = Options.model_validate(source.options)
        # Changes to paths, timezone or variable mapping require a fresh conversion cache.
        identity = {"source": source.model_dump(mode="json"), "processor": 1}
        key = sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
        self.root = settings.root / "ingest" / "campbell" / key
        self.variables = {}
        for case in source.cases:
            for variable in [case.target, *case.covariates]:
                if variable.value_column == "WD_Unwrapped":
                    continue  # Derived causally from the shared raw wind-direction column at read time.
                if variable.time_column != "timestamp" or variable.available_at_column or variable.quality_column:
                    raise ValueError("Campbell 输入仅支持观测时间；质量检查由入口转换执行")
                previous = self.variables.setdefault(variable.value_column, variable)
                if previous.model_dump(exclude={"aliases", "description", "attention"}) != variable.model_dump(exclude={"aliases", "description", "attention"}):
                    raise ValueError("同一 Campbell 列不能配置不同的转换语义")
        if len({v.timezone for v in self.variables.values()}) != 1:
            raise ValueError("Campbell 同一台站的变量必须配置相同的时区")
        self.lock, self.thread = threading.RLock(), threading.local()
        self.last_scan, self.current, self.status = float("-inf"), None, {"state": "not_scanned"}

    def _rows(self, name, content):
        lines = content.splitlines(keepends=True)
        rows, invalid, pending = [], 0, 0
        missing = {v.upper() for v in self.options.missing_values}
        missing_numbers = set()
        for value in missing:
            try:
                missing_numbers.add(float(value))
            except ValueError:
                pass
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # Writers may be midway through the last record; do not invent a value.
                if index == len(lines) - 1 and not line.endswith(("\n", "\r")):
                    pending += 1
                    continue
                raise ValueError(f"JSONL 格式错误：{name}:{index + 1}")
            timestamp = pd.Timestamp(record["timestamp"])
            if pd.isna(timestamp) or timestamp.second or timestamp.microsecond or timestamp.nanosecond or timestamp.minute % 30:
                raise ValueError(f"时间戳未对齐半小时：{name}:{index + 1}")
            if str(timestamp.date()) != name.split("/")[0]:
                raise ValueError(f"记录日期与目录不一致：{name}:{index + 1}")
            # Each variable currently has the same explicitly registered station timezone.
            timezone = next(iter(self.variables.values())).timezone
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize(timezone, ambiguous="raise", nonexistent="raise")
            values = {}
            from ..config import Variable
            columns = dict(self.variables)
            if self.source.discover:
                columns.update({k: Variable(name=k, unit="原始单位", timezone=timezone) for k in record
                                if k != "timestamp" and k not in columns})
            for column, variable in columns.items():
                value = record.get(column)
                try:
                    if str(value).upper() in missing:
                        raise ValueError()
                    number = float(value)
                    scaled = number * variable.scale
                    if (number in missing_numbers or not math.isfinite(scaled) or
                            variable.minimum is not None and scaled < variable.minimum or
                            variable.maximum is not None and scaled > variable.maximum):
                        raise ValueError()
                    values[column] = number
                except (ValueError, TypeError, OverflowError):
                    values[column] = None
                    invalid += 1
            rows.append((timestamp.tz_convert("UTC").isoformat(), json.dumps(values, allow_nan=False)))
        if len({t for t, _ in rows}) != len(rows):
            raise ValueError("文件内存在重复观测时间：" + name)
        return rows, invalid, pending

    def refresh(self, *, force=False):
        with self.lock:
            if not force and time.monotonic() - self.last_scan < self.options.scan_interval_seconds:
                if self.status["state"] == "error":
                    raise ForecastError("data_unavailable", self.status["message"], stage="data")
                return self.current
            try:
                self.current, self.status = self._refresh()
                return self.current
            except Exception as exc:
                self.status = {"state": "error", "message": f"ST001-CAMPBELL-B001 数据同步失败：{exc}"}
                raise ForecastError("data_unavailable", self.status["message"], stage="data") from exc
            finally:
                self.last_scan = time.monotonic()

    def _refresh(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.root / "index.sqlite", timeout=self.options.timeout_seconds)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS files (name TEXT PRIMARY KEY, signature TEXT, invalid INTEGER, pending INTEGER)")
            db.execute("CREATE TABLE IF NOT EXISTS rows (file TEXT, time TEXT PRIMARY KEY, payload TEXT)")
            db.execute("CREATE INDEX IF NOT EXISTS rows_file ON rows(file)")
            db.execute("BEGIN IMMEDIATE")
            known = {name: json.loads(sig) for name, sig in db.execute("SELECT name, signature FROM files")}
            scan = campbell_source.collect(self.options.directory, known)
            removed = set(known) - set(scan["signatures"])
            for name in removed | set(scan["changed"]):
                db.execute("DELETE FROM rows WHERE file=?", (name,))
                db.execute("DELETE FROM files WHERE name=?", (name,))
            for name, content in scan["changed"].items():
                rows, invalid, pending = self._rows(name, content)
                db.executemany("INSERT INTO rows VALUES (?, ?, ?)", [(name, *r) for r in rows])
                db.execute("INSERT INTO files VALUES (?, ?, ?, ?)",
                           (name, json.dumps(scan["signatures"][name]), invalid, pending))
            count, first, latest = db.execute("SELECT COUNT(*), MIN(time), MAX(time) FROM rows").fetchone()
            if not count:
                raise ValueError("没有可发布的完整观测记录")
            revision = sha256(json.dumps(scan["signatures"], sort_keys=True).encode()).hexdigest()
            path = self.root / (revision + ".csv")
            if not path.exists():
                output = io.StringIO(newline="")
                columns = set(self.variables)
                for payload, in db.execute("SELECT payload FROM rows"):
                    columns.update(json.loads(payload))
                writer = csv.DictWriter(output, fieldnames=["timestamp", *sorted(columns)])
                writer.writeheader()
                for timestamp, payload in db.execute("SELECT time, payload FROM rows ORDER BY time"):
                    writer.writerow({"timestamp": timestamp, **json.loads(payload)})
                temporary = path.with_suffix(".tmp")
                temporary.write_text(output.getvalue(), encoding="utf-8", newline="")
                temporary.replace(path)
            invalid, pending = db.execute("SELECT SUM(invalid), SUM(pending) FROM files").fetchone()
            status = {"state": "ready", "rows": count, "files": len(scan["signatures"]),
                      "processed_files": len(scan["changed"]), "removed_files": len(removed),
                      "invalid_values": invalid, "pending_lines": pending, "first_observation": first,
                      "latest_observation": latest, "scanned_at": pd.Timestamp.now(tz="UTC").isoformat(),
                      "revision": revision}
        return (path, status), status

    def catalog_status(self):
        try:
            self.refresh()
        except ForecastError:
            pass  # An offline station must not hide other registered data sources.
        return dict(self.status)

    def discover(self):
        from ..discovery import describe
        path, status = self.refresh(force=True)
        cached = getattr(self, "_description_cache", None)
        if cached and cached[0] == status["revision"]:
            return cached[1]
        data = pd.read_csv(path)
        # Discovery uses the virtual target's public name; the immutable snapshot
        # and read() retain the original channel and causal transformation.
        if any(c.target.value_column == "WD_Unwrapped" for c in self.source.cases):
            data = data.rename(columns={"WD_Avg": "WD_Unwrapped"})
        entries = describe(self.source, data, "", {"timezone": next(iter(self.variables.values())).timezone})
        for case, _ in entries:
            if case.target.value_column == "WD_Unwrapped":
                case.target = case.target.model_copy(update={"transform": "unwrap_degrees"})
        self._description_cache = status["revision"], entries
        return entries

    @contextmanager
    def snapshot(self):
        previous = getattr(self.thread, "snapshot", None)
        self.thread.snapshot = self.refresh(force=True)
        try:
            yield
        finally:
            self.thread.snapshot = previous

    def read(self, case, variable):
        path, status = getattr(self.thread, "snapshot", None) or self.refresh()
        column = self.auxiliary_variable(variable)
        provenance = {"source_id": self.source.id, "dataset_id": self.source.id,
                      "revision": status["revision"], "license": self.source.license,
                      "citation": self.source.citation, "asset_origin": "local",
                      "preprocessing": "campbell-1", "ingestion": dict(status),
                      "metadata_assumptions": "单位、时区和时段口径采用注册配置，待台站确认"}
        return read_csv_series(path, column, provenance)

    def history_end(self, case, origin, frequency, series):
        """Use the latest common observed instant; never synthesize rainfall records."""
        if not self.options.bridge_delayed_observations:
            return origin
        common = None
        for raw in series.values():
            valid = raw.values.notna() & (raw.values.index <= origin)
            if raw.available_at is not None:
                valid &= (raw.available_at <= origin).to_numpy()
            index = raw.values.index[valid]
            common = index if common is None else common.intersection(index)
        if common is None or common.empty:
            raise ForecastError("data_quality", "台站没有目标与辅助变量共同可用的观测时刻。", stage="data")
        end = common.max()
        if end != end.floor(f"{frequency}min"):
            raise ForecastError("data_quality", "台站最新共同观测时刻未对齐预测采样频率。", stage="data")
        return end


def main():
    """One-shot scan for deployment checks or an external scheduled job."""
    import argparse
    from ..config import load_settings

    parser = argparse.ArgumentParser(description="增量转换 Campbell 台站数据，不调用预测模型")
    parser.add_argument("--config", help="forecast.yaml 路径")
    parser.add_argument("--directory", help="仅本次扫描改用指定本地目录；不修改配置")
    args = parser.parse_args()
    settings = load_settings(args.config)
    source = next(s for s in settings.sources if s.id == "ST001-CAMPBELL-B001")
    if args.directory:
        source = source.model_copy(update={"options": {**source.options,
                                   "directory": str(Path(args.directory).resolve())}})
    provider = CampbellProvider(source, settings)
    provider.refresh(force=True)
    print(json.dumps(provider.status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
