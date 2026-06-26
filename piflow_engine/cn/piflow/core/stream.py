from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from piflow_engine.cn.piflow.core.artifact import Artifact

DEFAULT_PORT = ""


class JobInputStream(ABC):

    @abstractmethod
    def is_empty(self) -> bool:
        ...

    @abstractmethod
    def ports(self) -> list[str]:
        ...

    @abstractmethod
    def contains(self, port: str = DEFAULT_PORT) -> bool:
        ...

    @abstractmethod
    def read(self, port: str = DEFAULT_PORT) -> Artifact:
        ...

    @abstractmethod
    def read_properties(self, port: str = DEFAULT_PORT) -> dict[str, Any]:
        ...


class JobOutputStream(ABC):

    @abstractmethod
    def ports(self) -> list[str]:
        ...

    @abstractmethod
    def contains(self, port: str = DEFAULT_PORT) -> bool:
        ...

    @abstractmethod
    def write(self, artifact: Artifact, port: str = DEFAULT_PORT) -> None:
        ...

    @abstractmethod
    def write_properties(
        self, properties: dict[str, Any], port: str = DEFAULT_PORT
    ) -> None:
        ...

    @abstractmethod
    def get_artifact(self, port: str = DEFAULT_PORT) -> Artifact:
        ...

    @abstractmethod
    def get_properties(self, port: str = DEFAULT_PORT) -> dict[str, Any]:
        ...
