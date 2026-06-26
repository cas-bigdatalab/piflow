from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream


class Stop(ABC):

    @abstractmethod
    def initialize(self, ctx: ProcessContext) -> None:
        ...

    @abstractmethod
    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        ...


class ConfigurableStop(Stop, ABC):

    author_email: str = ""
    description: str = ""
    inport_list: list[str] = []
    outport_list: list[str] = []
    is_customized: bool = False
    customized_allow_key: list[str] = []
    customized_allow_value: list[str] = []
    is_data_source: bool = False

    def __init__(self) -> None:
        self.customized_properties: dict[str, str] = {}

    @abstractmethod
    def set_properties(self, properties: dict[str, Any]) -> None:
        ...

    def set_customized_properties(self, customized_properties: dict[str, str]) -> None:
        self.customized_properties = dict(customized_properties)

    def get_customized(self) -> bool:
        return self.is_customized

    def get_is_data_source(self) -> bool:
        return self.is_data_source
