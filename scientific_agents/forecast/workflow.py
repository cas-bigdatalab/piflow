"""Fixed PiFlow chain. The LLM never sees observations reserved for evaluation."""
from hashlib import sha256
from pathlib import Path
import json
import time
from typing import Callable

import numpy as np
import pandas as pd

from piflow_engine.cn.piflow.core.artifact import JsonArtifact
from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.path import Path as FlowPath
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop import Stop

from .analytics import evaluate, resample_variable, summarize
from .config import Settings
from .model import Predictor
from .providers import Registry
from .feedback import ForecastError, local_time
from .schema import ForecastResult, SeriesResult, TaskParams
from .planning import history_steps


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2), encoding="utf-8")
    temporary.replace(path)


class Cancelled(Exception):
    pass


class FunctionStop(Stop):
    def __init__(self, function: Callable):
        self.function = function

    def initialize(self, ctx):
        pass

    def perform(self, inputs, outputs, ctx):
        self.function()
        outputs.write(JsonArtifact(value={"complete": True}))


class ForecastWorkflow:
    def __init__(self, settings: Settings, registry: Registry, model: Predictor):
        self.settings, self.registry, self.model = settings, registry, model

    def validate(self, params: TaskParams):
        if len(params.case_ids) > self.settings.max_cases or len(set(params.case_ids)) != len(params.case_ids):
            raise ForecastError("invalid_parameters", "案例数量超限或存在重复。")
        if any(i not in self.registry.cases for i in params.case_ids):
            raise ForecastError("invalid_parameters", "案例不在当前数据源目录中。")
        origin = pd.Timestamp(params.origin).tz_convert("UTC")
        for case_id in params.case_ids:
            frequency, context, horizons = self.registry.warnings.timing(case_id)
            history_steps(params, self.registry, case_id)
            if params.horizon_hours not in horizons:
                raise ForecastError("invalid_parameters", f"{case_id}仅支持 {horizons} 小时。")
            if origin != origin.floor(f"{frequency}min"):
                raise ForecastError("invalid_parameters", f"预测起点必须对齐 {frequency} 分钟刻度。")
            if context > 15360 or params.horizon_hours * 60 // frequency > 1024:
                raise ForecastError("invalid_parameters", "请求超出固定模型的上下文或预测长度限制。")

    def prepare(self, params: TaskParams) -> list[dict]:
        if not getattr(self, "_bound", False):
            return self.bind(params).prepare(params)
        self.validate(params)
        with self.registry.read_snapshot(params.case_ids):
            return self._prepare_cases(params)

    def bind(self, params):
        self.registry.refresh()
        registry = self.registry.bind(params)
        workflow = ForecastWorkflow(self.settings, registry, self.model)
        workflow._bound = True
        return workflow

    def _prepare_cases(self, params: TaskParams) -> list[dict]:
        prepared, cache = [], {}
        for case_id in params.case_ids:
            requested, minimum = history_steps(params, self.registry, case_id)
            candidates = [requested] if params.history_hours is not None or requested == minimum else [requested, minimum]
            for context in candidates:
                try:
                    item = self._prepare(params.model_copy(update={"case_ids": [case_id]}), context, cache)[0]
                    break
                except ForecastError as exc:
                    if exc.code != "data_quality" or context == candidates[-1]:
                        raise
            frequency = item["frequency_minutes"]
            item["history_window"] = {"source": "explicit" if params.history_hours is not None else "auto",
                "requested_steps": requested, "actual_steps": context, "minimum_steps": minimum,
                "requested_hours": requested * frequency / 60, "actual_hours": context * frequency / 60,
                "start": (pd.Timestamp(item["timestamps"][-1]) - pd.Timedelta(minutes=context * frequency)).isoformat(),
                "first_timestamp": item["timestamps"][0], "end": item["timestamps"][-1],
                "adjusted": context != requested,
                "reason": "默认窗口数据不足，已使用通过质量检查的最低历史窗口。" if context != requested else "历史窗口满足数据要求。"}
            prepared.append(item)
        return prepared

    def _prepare(self, params, context, cache):
        self.validate(params)
        cfg = self.settings
        origin = pd.Timestamp(params.origin).tz_convert("UTC")
        prepared = []
        for case_id in params.case_ids:
            case = self.registry.cases[case_id]
            if case.target.semantics == "circular_degrees":
                raise ForecastError("invalid_parameters", "环形角度不能直接按标量预测。请将风向转换为风矢量分量并注册为预测目标；风向可直接作为辅助变量。")
            frequency, _, _ = self.registry.warnings.timing(case_id)
            scenario = self.registry.warnings.get(case)
            if scenario.mode == "current":
                now = pd.Timestamp.now(tz="UTC")
                if (now - origin).total_seconds() > scenario.data_age_limit(params.horizon_hours) * 60 or origin > now:
                    raise ForecastError("data_quality", "当前预测起点不符合数据时效要求，请刷新数据。", stage="data")
            history_end = (self.registry.history_end(case_id, origin, frequency, cache)
                           if scenario.mode == "current" else origin)
            gap_steps = int((origin - history_end).total_seconds() / (frequency * 60))
            if gap_steps < 0 or gap_steps * frequency * 60 != (origin - history_end).total_seconds():
                raise ForecastError("data_quality", "历史截止时刻与预测起点无法对齐。", stage="data")
            if gap_steps * frequency > scenario.data_age_limit(params.horizon_hours):
                raise ForecastError("data_quality", f"监测数据过期：所选变量最新共同观测 {local_time(history_end)}（北京时间）超过本次时效上限。", stage="data")
            if gap_steps + params.horizon_hours * 60 // frequency > 1024:
                raise ForecastError("invalid_parameters", "数据延迟加请求时长超出模型支持的预测长度，请缩短时长或更新数据。")
            if gap_steps and any(v.future_known for v in case.covariates):
                raise ForecastError("data_quality", "延迟衔接暂只支持历史辅助变量。", stage="data")
            grid = pd.date_range(end=history_end, periods=context, freq=f"{frequency}min")
            future = pd.date_range(start=origin, periods=params.horizon_hours * 60 // frequency + 1,
                                   freq=f"{frequency}min")[1:]
            frames, quality, provenance, observations = {}, {}, {}, None
            future_covariates = {}
            for variable in [case.target, *case.covariates]:
                key = (case_id, variable.name)
                if key not in cache:
                    cache[key] = self.registry.read(case_id, variable)
                raw = cache[key]
                available = raw.values
                if raw.available_at is not None:
                    eligible = (raw.available_at <= origin).to_numpy()
                    available = raw.values.iloc[np.flatnonzero(eligible)]
                    if variable.future_known:
                        dates = raw.available_at.iloc[np.flatnonzero(eligible)]
                        table = pd.DataFrame({"value": available.to_numpy(), "issued": dates.to_numpy()}, index=available.index)
                        available = table.sort_values("issued").loc[lambda t: ~t.index.duplicated(keep="last"), "value"].sort_index()
                elif variable.future_known:
                    raise ForecastError("data_quality", "已知未来变量必须提供发布时间，禁止使用未来真实观测。", stage="data")
                if scenario.mode == "current":
                    max_age_minutes = scenario.data_age_limit(params.horizon_hours)
                    observed = available.loc[available.index <= origin].dropna()
                    if observed.empty or (origin - observed.index.max()).total_seconds() > max_age_minutes * 60:
                        latest = local_time(observed.index.max()) + "（北京时间）" if not observed.empty else "无可用观测"
                        raise ForecastError("data_quality", f"监测数据过期，无法进行当前预警评估。{case_id}/{variable.name} 最新可用观测：{latest}；本次预测允许的数据时效上限为 {max_age_minutes / 60:g} 小时，需要先更新监测数据。", stage="data")
                # Split BEFORE resampling/filling. No retrospective observations enter features.
                historical = available.loc[available.index <= origin]
                history = resample_variable(historical, frequency, variable)
                values = history.reindex(grid)
                missing = int(values.isna().sum())
                if missing / len(grid) > cfg.max_missing_fraction:
                    indices = np.flatnonzero(values.isna())
                    runs = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
                    longest = max(runs, key=len)
                    raise ForecastError("data_quality",
                        f"{case_id}/{variable.name} 所需 {context * frequency / 60:g} 小时历史窗口缺测 {missing}/{len(grid)} 点，暂不能预测。"
                        f"历史检查范围：{local_time(grid[0])} 至 {local_time(grid[-1])}（北京时间）。"
                        f"最长连续缺测：{local_time(grid[longest[0]])} 至 {local_time(grid[longest[-1]])}（北京时间），"
                        f"共 {len(longest)} 点，采样间隔 {frequency} 分钟。请补充这段观测数据后刷新数据源；"
                        "如需验证模型，可明确指定数据完整的历史时段进行回放。", stage="data")
                if cfg.forward_fill_limit:
                    values = values.ffill(limit=cfg.forward_fill_limit)
                if values.isna().any():
                    raise ForecastError("data_quality", f"{case_id}/{variable.name} 缺测无法按固定规则补齐。", stage="data")
                if ((variable.minimum is not None and (values < variable.minimum).any()) or
                        (variable.maximum is not None and (values > variable.maximum).any())):
                    raise ForecastError("data_quality", f"{case_id}/{variable.name} 历史数据超出已登记的物理范围，请核查单位和数据。", stage="data")
                frames[variable.name] = values.tolist()
                quality[variable.name] = {"expected_points": len(grid), "missing_before": missing,
                                          "filled_points": missing, "fill_method": "past-only forward fill",
                                          "aggregation": variable.aggregation, "unit": variable.unit}
                if values.nunique() == 1:
                    quality[variable.name].update(constant_input=True, constant_value=float(values.iloc[0]))
                provenance[variable.name] = raw.provenance
                if variable.future_known:
                    predicted = resample_variable(available.loc[available.index > origin], frequency, variable).reindex(future)
                    if predicted.isna().any():
                        raise ForecastError("data_quality", "预测起点之前发布的辅助预报未完整覆盖预测窗口。", stage="data")
                    future_covariates[variable.name] = predicted.tolist()
                if variable == case.target:
                    truth = resample_variable(raw.values.loc[raw.values.index > origin], frequency, variable).reindex(future)
                    observations = [None if pd.isna(v) else float(v) for v in truth]
            prepared.append({"case_id": case_id, "label": case.label, "variable": case.target.name,
                             "unit": case.target.unit, "timestamps": [t.isoformat() for t in grid],
                             "future": [t.isoformat() for t in future], "target": frames.pop(case.target.name),
                             "past_covariates": frames, "observations": observations,
                             "quality": quality, "provenance": provenance, "future_covariates": future_covariates,
                             "frequency_minutes": frequency, "scenario": scenario.model_dump(mode="json")})
            prepared[-1]["bounds"] = {"minimum": case.target.minimum, "maximum": case.target.maximum}
            prepared[-1]["metadata"] = {"station_id": case.station_id,
                **self.registry.display_metadata(case_id),
                "area": scenario.area,
                "source_id": provenance[case.target.name].get("source_id", ""),
                "auxiliary_case_ids": params.auxiliary_case_ids,
                "attention": case.target.attention, "description": case.target.description,
                "semantics": case.target.semantics, "window_minutes": case.target.window_minutes,
                "transform": case.target.transform,
                "frequency_minutes": frequency,
                "circular_covariates": [v.name for v in case.covariates if v.semantics == "circular_degrees"]}
            if gap_steps:
                prepared[-1]["gap_steps"] = gap_steps
                prepared[-1]["metadata"]["data_alignment"] = {
                    "method": "forecast_across_observation_delay", "history_end": history_end.isoformat(),
                    "requested_origin": origin.isoformat(), "gap_steps": gap_steps,
                    "delay_hours": gap_steps * frequency / 60, "synthetic_observations": False}
        return prepared

    def predict_prepared(self, prepared):
        """Shared execution and benchmark path; group only compatible horizons."""
        result, groups = [None] * len(prepared), {}
        for index, item in enumerate(prepared):
            groups.setdefault(len(item["future"]) + item.get("gap_steps", 0), []).append((index, item))
        for steps, group in groups.items():
            inputs = []
            for _, item in group:
                known = item.get("future_covariates", {})
                inputs.append({"target": np.asarray(item["target"], dtype=np.float32),
                    "past_covariates": {k: np.asarray(v, dtype=np.float32) for k, v in item["past_covariates"].items() if k not in known},
                    **({"future_covariates": {k: np.asarray(item["past_covariates"][k] + v, dtype=np.float32)
                                              for k, v in known.items()}} if known else {})})
                for key in ("past_covariates", "future_covariates"):
                    for name in item.get("metadata", {}).get("circular_covariates", []):
                        if name in inputs[-1].get(key, {}):
                            angle = np.deg2rad(inputs[-1][key].pop(name))
                            inputs[-1][key][name + "__sin"] = np.sin(angle)
                            inputs[-1][key][name + "__cos"] = np.cos(angle)
            predictions = self.model.predict(inputs, steps)
            if len(predictions) != len(group):
                raise ValueError("模型返回的序列数量不符。")
            for (index, item), prediction in zip(group, predictions, strict=True):
                if item.get("gap_steps", 0) and prediction.shape != (steps, 3):
                    raise ValueError("模型返回的预测长度或分位数数量不符。")
                result[index] = prediction[item.get("gap_steps", 0):].tolist()
        return result

    def run(self, run_id: str, params: TaskParams, emit=lambda *_: None, cancelled=lambda: False, *, defer_report=False) -> ForecastResult:
        if not getattr(self, "_bound", False):
            if (self.settings.root / "runs" / run_id / "input_snapshot.json").exists():
                workflow = ForecastWorkflow(self.settings, self.registry, self.model)
                workflow._bound = True  # Resume the saved data stage, including removed source variables.
            else:
                workflow = self.bind(params)
            return workflow.run(run_id, params, emit, cancelled, defer_report=defer_report)
        from .reports import build_facts, render_report
        directory = self.settings.root / "runs" / run_id
        directory.mkdir(parents=True, exist_ok=True)
        model = self.model.metadata()
        model_identity = {k: model.get(k) for k in ("id", "revision", "files_sha256")}
        # Report descriptions do not invalidate numerical checkpoints. Excluding the
        # new optional fields also preserves the identity of pre-context tasks.
        report_fields = {"analysis_context": True, "target": {"description", "aliases"},
                         "covariates": {"__all__": {"description", "aliases"}}}
        numerical_settings = self.settings.model_dump_json(exclude={"execution": True,
            "sources": {"__all__": {"cases": {"__all__": report_fields}}}})
        fingerprint = sha256((params.model_dump_json() + numerical_settings
                              + json.dumps(model_identity, sort_keys=True)).encode()).hexdigest()
        identity = directory / "identity.json"
        if identity.exists() and json.loads(identity.read_text())["fingerprint"] != fingerprint:
            raise ValueError("任务配置版本已变化，禁止复用旧执行编号。")
        write_json(identity, {"fingerprint": fingerprint})
        state = {}
        timings = {}

        def stage(name, operation):
            def execute():
                if cancelled():
                    raise Cancelled("任务已取消。")
                emit(name, "running")
                started = time.monotonic()
                operation()
                if cancelled():
                    raise Cancelled("任务已请求停止。")
                timings[name] = time.monotonic() - started
                emit(name, "completed")
            return FunctionStop(execute)

        def load_data():
            path = directory / "input_snapshot.json"
            if path.exists():
                state["inputs"] = json.loads(path.read_text(encoding="utf-8"))
            else:
                state["inputs"] = self.prepare(params)
                write_json(path, state["inputs"])
            emit("plan", {"origin": params.origin.isoformat(), "origin_mode": params.origin_mode,
                          "history_windows": {item["case_id"]: item.get("history_window", {}) for item in state["inputs"]}})

        def predict():
            path = directory / "prediction_snapshot.json"
            if path.exists():
                snapshot = json.loads(path.read_text(encoding="utf-8"))
                state.update(snapshot)
                return
            # Deliberately build a new object: observations are never passed to the model.
            state["predictions"] = self.predict_prepared(state["inputs"])
            state["model"] = self.model.metadata()
            write_json(path, {"predictions": state["predictions"], "model": state["model"]})

        def calculate():
            items = []
            if len(state["inputs"]) != len(state["predictions"]):
                raise ValueError("模型返回的序列数量不符。")
            for source, quantiles in zip(state["inputs"], state["predictions"], strict=True):
                q = np.asarray(quantiles, dtype=np.float64)
                if q.shape != (len(source["future"]), 3):
                    raise ValueError("预测长度不符。")
                from .analytics import constrain_forecast
                q, postprocessing = constrain_forecast(q, source.get("bounds", {}))
                points = [dict(timestamp=t, q10=float(row[0]), prediction=float(row[1]), q90=float(row[2]))
                          for t, row in zip(source["future"], q, strict=True)]
                metrics = evaluate(q[:, 1], source["observations"], q[:, 0], q[:, 2], source["target"][-1])
                items.append(SeriesResult(
                    case_id=source["case_id"], label=source["label"], variable=source["variable"], unit=source["unit"],
                    history=[dict(timestamp=t, value=v) for t, v in zip(source["timestamps"], source["target"], strict=True)],
                    predictions=points,
                    observations=[dict(timestamp=t, value=v) for t, v in zip(source["future"], source["observations"], strict=True)],
                    quality=source["quality"], provenance=source["provenance"],
                    history_window=source.get("history_window", {}),
                    postprocessing=postprocessing,
                    metadata=source.get("metadata", {}),
                    summary=summarize(points, source["target"][-1]), evaluation=metrics,
                ))
            result = ForecastResult(run_id=run_id, task=params, model=state["model"], series=items,
                                    computation_version="1.1")
            state["result"] = result

        def warning():
            from .warning.engine import assess
            from .research import build_research
            related = {raw["case_id"]: (raw, [p.model_dump() for p in series.predictions])
                       for raw, series in zip(state["inputs"], state["result"].series, strict=True)}
            for source, series in zip(state["inputs"], state["result"].series, strict=True):
                if "scenario" not in source:  # Pre-upgrade snapshots keep their historical scope.
                    source = {**source, "frequency_minutes": self.settings.frequency_minutes,
                              "scenario": {"case_id": source["case_id"], "version": "legacy-1",
                                           "area": source["label"], "hazard_type": "unspecified"}}
                series.assessment = assess(source, [p.model_dump() for p in series.predictions], related)
            state["result"].research = build_research(state["result"])
            state["result"].facts = build_facts(state["result"])
            from .result_view import build
            state["result"].presentation = build(state["result"])

        def report():
            state["result"].timings_seconds = dict(timings)
            if defer_report:
                from .reports import export_predictions
                export_predictions(state["result"], directory)
                state["result"].artifacts = ["result.json", "predictions.csv"]
            else:
                render_report(state["result"], directory)
                state["result"].report_status = "completed"

        operations = [("data", load_data), ("predict", predict), ("evaluate", calculate), ("assess", warning), ("report", report)]
        flow = FlowImpl(name="Scientific forecast", uuid=run_id)
        for i, (name, operation) in enumerate(operations):
            flow.add_stop(name, stage(name, operation))
            if i:
                flow.add_path(FlowPath.from_(operations[i - 1][0]).to(name))
        process = Runner.create().start(flow)
        emit("process", process.pid())
        process.await_termination()
        if cancelled():
            raise Cancelled("任务已取消。")
        state["result"].timings_seconds = timings
        write_json(directory / "result.json", state["result"].model_dump(mode="json"))
        return state["result"]
