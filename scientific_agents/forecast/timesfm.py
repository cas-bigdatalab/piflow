"""Pinned TimesFM 3 CPU inference, no fine-tuning and no cross-case channel mixing."""
import threading
import time
import json

import numpy as np

from .files import file_hash

SOURCE_COMMIT = "8cb7eda91c2b416b37e99a979afc50f2a18e1791"


class TimesFMPredictor:
    def __init__(self, settings):
        self.settings, self._pipeline = settings, None
        self._lock = threading.Lock()
        self.load_seconds, self._identity = None, None

    def _load(self):
        if self._pipeline is None:
            import torch
            from timesfm3 import TimesFM3Evaluator, ModelConfig
            started = time.monotonic()
            directory = self.settings.model_dir.resolve()
            for name in ("config.json", "model.safetensors"):
                path = directory / name
                if not path.is_file() or not path.stat().st_size:
                    raise FileNotFoundError(f"TimesFM本地模型缺少{name}：{directory}；请设置FORECAST_MODEL_DIR或model_dir")
            json.loads((directory / "config.json").read_text(encoding="utf-8"))
            identity = {name: file_hash(directory / name) for name in ("config.json", "model.safetensors")}
            torch.set_num_threads(self.settings.cpu_threads)
            self._pipeline = TimesFM3Evaluator(ModelConfig(checkpoint_path=str(directory), device="cpu",
                local_files_only=True, per_core_batch_size=1))
            self._identity = identity
            self.load_seconds = time.monotonic() - started

    def warmup(self):
        self.predict([{"target": np.arange(64, dtype=np.float32)}], 4)

    def predict(self, inputs, steps):
        import torch
        if not 1 <= steps <= 1024:
            raise ValueError("TimesFM服务单次预测限制为1至1024点")
        result = []
        with self._lock, torch.inference_mode():
            self._load()
            for item in inputs:
                target = np.asarray(item["target"], dtype=np.float32)
                if target.ndim != 1 or not 8 <= len(target) <= 15360 or not np.isfinite(target).all():
                    raise ValueError("TimesFM目标输入必须是8至15360点的完整一维序列")
                def covariates(key, length):
                    arrays = [np.asarray(v, dtype=np.float32) for _, v in sorted(item.get(key, {}).items())]
                    if any(a.shape != (length,) or not np.isfinite(a).all() for a in arrays):
                        raise ValueError("TimesFM辅助变量长度或数值不合法")
                    return np.stack(arrays) if arrays else None
                output = list(self._pipeline.predict_batch(contexts=[target], horizon=steps,
                    past_only_covariates=[covariates("past_covariates", len(target))],
                    past_future_covariates=[covariates("future_covariates", len(target) + steps)],
                    return_quantiles=True, use_symmetric_averaging=False, make_positive=False,
                    sort_quantiles=True, use_znorm=False))
                if len(output) != 1:
                    raise ValueError("TimesFM返回数量不符")
                q = np.asarray(output[0].quantiles, dtype=np.float64)
                if q.shape != (steps, 9) or not np.isfinite(q).all() or np.any(np.diff(q, axis=1) < 0):
                    raise ValueError("TimesFM分位数形状、数值或顺序不合法")
                result.append(q[:, [0, 4, 8]])
        return result

    def metadata(self):
        import importlib.metadata
        with self._lock:
            self._load()
        return {"id": "timesfm3", "revision": (self._identity or {}).get("model.safetensors"),
            "files_sha256": self._identity,
            "source_commit": SOURCE_COMMIT, "package_version": importlib.metadata.version("timesfm"),
            "device": "cpu", "dtype": "float32", "cpu_threads": self.settings.cpu_threads,
            "quantiles": [0.1, 0.5, 0.9], "cross_learning": False, "training": False,
            "asset_origin": "local", "load_seconds": self.load_seconds,
            "postprocessing": "official quantile sorting enabled; no positivity clipping, symmetric averaging or z-normalization"}
