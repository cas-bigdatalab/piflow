from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class InvalidPathError(ValueError):
    pass


@dataclass
class Edge:
    stop_from: str
    stop_to: str
    out_port: str = ""
    in_port: str = ""

    def __str__(self) -> str:
        return f"[{self.stop_from}]-({self.out_port})-({self.in_port})-[{self.stop_to}]"


class PathVia:
    def __init__(self, path: "Path", out_port: str, in_port: str):
        self._path = path
        self._out_port = out_port
        self._in_port = in_port

    def to(self, stop_to: str) -> "Path":
        if not self._path.edges:
            raise InvalidPathError("path must contain at least one edge before via().to()")
        last_stop = self._path.edges[-1].stop_to
        self._path.add_edge(Edge(last_stop, stop_to, self._out_port, self._in_port))
        return self._path


@dataclass
class Path:
    edges: list[Edge] = field(default_factory=list)

    def to_edges(self) -> list[Edge]:
        return list(self.edges)

    def add_edge(self, edge: Edge) -> "Path":
        self.edges.append(edge)
        return self

    def via(self, outport: str, inport: str) -> PathVia:
        return PathVia(self, outport, inport)

    def to(self, stop_to: str) -> "Path":
        if not self.edges:
            raise InvalidPathError("path must contain at least one edge before to()")
        self.edges.append(Edge(self.edges[-1].stop_to, stop_to, "", ""))
        return self

    @classmethod
    def from_(cls, stop_from: str) -> "_PathHead":
        return _PathHead(stop_from)

    @classmethod
    def of(cls, path: tuple[Any, str]) -> "Path":
        result = cls()

        def _add_edges(item: tuple[Any, str]) -> None:
            value1, value2 = item
            if isinstance(value1, str):
                result.add_edge(Edge(value1, value2, "", ""))
            elif isinstance(value1, tuple) and len(value1) == 2:
                _add_edges(value1)
                result.add_edge(Edge(value1[1], value2, "", ""))
            else:
                raise InvalidPathError(f"invalid path head: {value1}")

        _add_edges(path)
        return result


class _PathHead:
    def __init__(self, stop_from: str):
        self._stop_from = stop_from

    def via(self, outport: str, inport: str) -> PathVia:
        path = Path()
        path.add_edge(Edge(self._stop_from, "", outport, inport))
        return _PathHeadVia(path)

    def to(self, stop_to: str) -> Path:
        path = Path()
        path.add_edge(Edge(self._stop_from, stop_to, "", ""))
        return path


class _PathHeadVia(PathVia):
    def __init__(self, path: Path):
        self._path = path

    def to(self, stop_to: str) -> Path:
        if not self._path.edges:
            raise InvalidPathError("path must contain at least one edge before via().to()")
        first_edge = self._path.edges[0]
        first_edge.stop_to = stop_to
        return self._path
