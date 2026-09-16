"""Fixed TimesFM implementation; checkpoint directory is deployment configuration."""
from typing import Protocol
import numpy as np


class Predictor(Protocol):
    def predict(self, inputs: list[dict], steps: int) -> list[np.ndarray]: ...
    def metadata(self) -> dict: ...


def create_predictor(settings):
    from .timesfm import TimesFMPredictor
    return TimesFMPredictor(settings)
