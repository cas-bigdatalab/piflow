from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PathBean:
    from_stop: str = ""
    out_port: str = ""
    in_port: str = ""
    to_stop: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathBean":
        out_port = data["outport"] if "outport" in data else data.get("out_port", "")
        in_port = data["inport"] if "inport" in data else data.get("in_port", "")

        return cls(
            from_stop=str(data.get("from", "")),
            out_port="" if out_port is None else str(out_port),
            in_port="" if in_port is None else str(in_port),
            to_stop=str(data.get("to", "")),
        )
