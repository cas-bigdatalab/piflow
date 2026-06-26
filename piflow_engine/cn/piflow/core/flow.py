from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from piflow_engine.cn.piflow.core.path import Edge, Path
from piflow_engine.cn.piflow.core.stop import Stop


class Flow(ABC):
    @abstractmethod
    def add_stop(self, stop_id: str, stop: Stop) -> "Flow":
        ...

    @abstractmethod
    def add_path(self, path: Path) -> "Flow":
        ...

    @abstractmethod
    def get_stop(self, stop_id: str) -> Stop:
        ...

    @abstractmethod
    def get_stop_names(self) -> list[str]:
        ...

    @abstractmethod
    def show(self) -> None:
        ...


@dataclass
class FlowImpl(Flow):
    name: str = ""
    uuid: str = ""
    edges: list[Edge] = field(default_factory=list)
    stops: dict[str, Stop] = field(default_factory=dict)
    stop_name_index: dict[str, str] = field(default_factory=dict)
    run_mode: str = ""
    flow_json: str = ""

    def add_stop(self, stop_id: str, stop: Stop) -> "FlowImpl":
        self.stops[stop_id] = stop
        stop_name = str(getattr(stop, "piflow_stop_name", ""))
        if stop_name:
            self.stop_name_index[stop_name] = stop_id
        return self

    def add_path(self, path: Path) -> "FlowImpl":
        self.edges.extend(self._resolve_edges_to_stop_ids(path.to_edges()))
        return self

    def get_stop(self, stop_id: str) -> Stop:
        if stop_id in self.stops:
            return self.stops[stop_id]
        return self.stops[self.stop_name_index[stop_id]]

    def resolve_stop_id(self, stop_id: str) -> str:
        if stop_id in self.stops:
            return stop_id
        if stop_id in self.stop_name_index:
            return self.stop_name_index[stop_id]
        raise KeyError(f"unknown stop id or name: {stop_id}")

    def get_stop_names(self) -> list[str]:
        return list(self.stops.keys())

    def show(self) -> None:
        for edge in self.edges:
            print(str(edge))

    def _resolve_edges_to_stop_ids(self, edges: list[Edge]) -> list[Edge]:
        return [
            Edge(
                stop_from=self.resolve_stop_id(edge.stop_from),
                stop_to=self.resolve_stop_id(edge.stop_to),
                out_port=edge.out_port,
                in_port=edge.in_port,
            )
            for edge in edges
        ]
