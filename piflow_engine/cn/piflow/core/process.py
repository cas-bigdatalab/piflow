from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from piflow_engine.cn.piflow.core.flow import Flow


class Process(ABC):

    @abstractmethod
    def pid(self) -> str:
        ...

    @abstractmethod
    def await_termination(self, timeout: float | None = None) -> None:
        ...

    @abstractmethod
    def get_flow(self) -> "Flow":
        ...

    @abstractmethod
    def stop(self) -> None:
        ...
