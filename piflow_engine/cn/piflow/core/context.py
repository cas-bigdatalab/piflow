from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Context(ABC):

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        raise KeyError(f"context key not found: {key}")

    @abstractmethod
    def put(self, key: str, value: Any) -> "Context":
        raise NotImplementedError

    def contains(self, key: str) -> bool:
        try:
            self.get(key)
            return True
        except KeyError:
            return False


class CascadeContext(Context):
    """
    Context implementation with parent-child cascading lookup.

    Lookup order:
    1. current context
    2. parent context
    3. raise KeyError or return provided default
    """

    _MISSING = object()

    def __init__(self, parent: Context | None = None):
        self.parent = parent
        self._values: dict[str, Any] = {}

    def get(self, key: str, default: Any = _MISSING) -> Any:
        if key in self._values:
            return self._values[key]

        if self.parent is not None:
            return self.parent.get(key, default)

        if default is not self._MISSING:
            return default

        raise KeyError(f"context key not found: {key}")

    def put(self, key: str, value: Any) -> "CascadeContext":
        self._values[key] = value
        return self

    def local_contains(self, key: str) -> bool:
        return key in self._values

    def local_values(self) -> dict[str, Any]:
        return dict(self._values)
