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
        self.remote_grpc_target = ""
        self.cpu_cores = 0.0
        self.memory_gb = 0.0
        self.free_disk_gb = 0.0

    def set_properties(self, properties: dict[str, Any]) -> None:
        super().set_properties(properties)
        raw_node_id = properties.get("node_id", "")
        if not isinstance(raw_node_id, str):
            raise TypeError("remote source property 'node_id' must be a string")
        self.node_id = raw_node_id.strip()
        if not self.node_id:
            raise ValueError("remote source property 'node_id' must not be empty")
        raw_remote_grpc_target = properties.get("remote_grpc_target", "")
        if not isinstance(raw_remote_grpc_target, str):
            raise TypeError("remote source property 'remote_grpc_target' must be a string")
        self.remote_grpc_target = raw_remote_grpc_target.strip()
        self.cpu_cores = _read_non_negative_float(
            properties,
            key="cpu_cores",
            legacy_keys=("cpu",),
        )
        self.memory_gb = _read_non_negative_float(
            properties,
            key="memory_gb",
            legacy_keys=("memory",),
        )
        self.free_disk_gb = _read_non_negative_float(
            properties,
            key="free_disk_gb",
            legacy_keys=("disk", "disk_gb", "available_disk_gb"),
        )


def _read_non_negative_float(
    properties: dict[str, Any],
    *,
    key: str,
    legacy_keys: tuple[str, ...] = (),
) -> float:
    for candidate_key in (key, *legacy_keys):
        if candidate_key not in properties:
            continue
        raw_value = properties.get(candidate_key)
        if raw_value in (None, ""):
            return 0.0
        if isinstance(raw_value, bool):
            raise TypeError(f"remote source property '{key}' must be numeric")
        if isinstance(raw_value, (int, float)):
            value = float(raw_value)
        elif isinstance(raw_value, str):
            try:
                value = float(raw_value.strip())
            except ValueError as exc:
                raise TypeError(f"remote source property '{key}' must be numeric") from exc
        else:
            raise TypeError(f"remote source property '{key}' must be numeric")
        if value < 0:
            raise ValueError(f"remote source property '{key}' must be non-negative")
        return value
    return 0.0
