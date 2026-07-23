from __future__ import annotations

from typing import Any

from piflow_engine.cn.piflow.engine.local.source_file_stop import SourceFileStop


class RemoteSourceStop(SourceFileStop):
    author_email = ""
    description = (
        "Source stop with a scheduler-visible node_id. At runtime it behaves like "
        "a local SourceFileStop after the scheduler chooses the execution node."
    )

    def __init__(self) -> None:
        super().__init__()
        self.node_id = ""

    def set_properties(self, properties: dict[str, Any]) -> None:
        super().set_properties(properties)
        raw_node_id = properties.get("node_id", "")
        if not isinstance(raw_node_id, str):
            raise TypeError("remote source property 'node_id' must be a string")
        self.node_id = raw_node_id.strip()
        if not self.node_id:
            raise ValueError("remote source property 'node_id' must not be empty")
