"""Deterministic calculations. No LLM access and no domain-specific risk labels."""
import numpy as np
import pandas as pd


def constrain_forecast(quantiles, bounds):
    """Apply declared physical support after validating raw output; never infer it.

    Snapshots retain raw model quantiles. All published metrics/rules use this same
    constrained array. Clipping is a validity repair, not an accuracy correction.
    """
    raw = np.asarray(quantiles, dtype=np.float64)
    if raw.ndim != 2 or raw.shape[1] != 3 or not np.isfinite(raw).all():
        raise ValueError("non-finite or malformed model output")
    if np.any(np.diff(raw, axis=1) < 0):
        raise ValueError("crossed quantiles; output rejected, not silently reordered")
    lo, hi = bounds.get("minimum"), bounds.get("maximum")
    if any(v is not None and not np.isfinite(v) for v in (lo, hi)) or (lo is not None and hi is not None and lo >= hi):
        raise ValueError("invalid physical bounds")
    values = np.clip(raw, -np.inf if lo is None else lo, np.inf if hi is None else hi)
    return values, {"method": "declared_physical_bounds", "minimum": lo, "maximum": hi,
                    "adjusted_values": int((raw != values).sum()),
                    "adjusted_medians": int((raw[:, 1] != values[:, 1]).sum()),
                    "raw_minimum": float(raw.min()), "raw_maximum": float(raw.max())}


def evaluate(prediction, observation, lower, upper, baseline: float) -> dict:
    p, y, lo, hi = (np.asarray(x, dtype=np.float64) for x in (prediction, observation, lower, upper))
    if not (p.shape == y.shape == lo.shape == hi.shape) or p.ndim != 1:
        raise ValueError("evaluation arrays must have identical one-dimensional shapes")
    if not np.isfinite(p).all() or not np.isfinite(lo).all() or not np.isfinite(hi).all():
        raise ValueError("non-finite model output")
    if np.any(lo > p) or np.any(p > hi):
        raise ValueError("crossed quantiles; output rejected, not silently reordered")
    valid = np.isfinite(y)
    result = {"available": bool(valid.any()), "valid_points": int(valid.sum()),
              "expected_points": len(p), "coverage_fraction": float(valid.mean()) if len(p) else 0,
              "bias_definition": "prediction - observation", "baseline": "last observed value",
              "interval": "q10-q90; nominal 80%, not calibrated confidence"}
    if not valid.any():
        return {**result, "reason": "没有可对齐的真实观测，无法评价本次预测。"}
    error = p[valid] - y[valid]
    base_error = baseline - y[valid]
    mae, base_mae = float(np.abs(error).mean()), float(np.abs(base_error).mean())
    return {**result, "mae": mae, "rmse": float(np.sqrt(np.mean(error ** 2))),
            "mean_bias": float(error.mean()), "baseline_mae": base_mae,
            "baseline_rmse": float(np.sqrt(np.mean(base_error ** 2))),
            "mae_skill": 1 - mae / base_mae if base_mae > 0 else None,
            "mae_skill_reason": None if base_mae > 0 else "基线误差为零，无法计算相对改善率。",
            "empirical_interval_coverage": float(((y[valid] >= lo[valid]) & (y[valid] <= hi[valid])).mean())}


def summarize(points: list[dict], last_observation: float) -> dict:
    values = np.asarray([p["prediction"] for p in points], dtype=np.float64)
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("empty or non-finite prediction")
    maximum, minimum = int(values.argmax()), int(values.argmin())
    return {"max": float(values[maximum]), "max_time": points[maximum]["timestamp"],
            "min": float(values[minimum]), "min_time": points[minimum]["timestamp"],
            "mean": float(values.mean()), "last_observation": float(last_observation),
            "end_minus_origin": float(values[-1] - last_observation),
            "mean_interval_width": float(np.mean([p["q90"] - p["q10"] for p in points])),
            "ties": "first occurrence", "change_definition": "final forecast minus last historical observation"}


def resample(values: pd.Series, minutes: int, aggregation: str) -> pd.Series:
    if values.index.has_duplicates:
        raise ValueError("检测到重复时间戳，请修正数据源后重试。")
    if np.isinf(values.to_numpy()).any():
        raise ValueError("输入包含无穷数值。")
    # Each timestamp labels the END of (t-frequency, t]. No future point enters a past bin.
    grouped = values.resample(f"{minutes}min", closed="right", label="right", origin="epoch")
    return grouped.sum(min_count=1) if aggregation == "sum" else grouped.agg(aggregation)


def resample_variable(values, minutes, variable):
    if variable.semantics == "circular_degrees" and variable.aggregation == "mean":
        angle = np.deg2rad(values)
        sine = resample(np.sin(angle), minutes, "mean")
        cosine = resample(np.cos(angle), minutes, "mean")
        return (np.rad2deg(np.arctan2(sine, cosine)) % 360).where(np.hypot(sine, cosine) > 1e-8)
    return resample(values, minutes, variable.aggregation)
