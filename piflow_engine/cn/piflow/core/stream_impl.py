from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from piflow_engine.cn.piflow.core.artifact import Artifact, ensure_artifact, FileArtifact
from piflow_engine.cn.piflow.core.stream import DEFAULT_PORT, JobInputStream, JobOutputStream


@dataclass
class JobInputStreamImpl(JobInputStream):
    inputs: dict[str, Artifact] = field(default_factory=dict)

    def attach(self, inputs: dict[str, Artifact]) -> None:
        self.inputs.update(inputs)

    def is_empty(self) -> bool:
        return not self.inputs

    def ports(self) -> list[str]:
        return list(self.inputs.keys())

    def contains(self, port: str = DEFAULT_PORT) -> bool:
        return port in self.inputs

    def read(self, port: str = DEFAULT_PORT) -> Artifact:
        return self.inputs[port]

    def read_properties(self, port: str = DEFAULT_PORT) -> dict[str, Any]:
        return dict(self.read(port).metadata)


@dataclass
class JobOutputStreamImpl(JobOutputStream):
    outputs: dict[str, Artifact] = field(default_factory=dict)

    def ports(self) -> list[str]:
        return list(self.outputs.keys())

    def contains(self, port: str = DEFAULT_PORT) -> bool:
        return port in self.outputs

    def write(self, artifact: Artifact | Any, port: str = DEFAULT_PORT) -> None:
        normalized = ensure_artifact(artifact)
        if isinstance(artifact, str):
            normalized = FileArtifact(path=artifact)
        self.outputs[port] = normalized

    def write_properties(
        self, properties: dict[str, Any], port: str = DEFAULT_PORT
    ) -> None:
        if port not in self.outputs:
            self.outputs[port] = Artifact()
        self.outputs[port].metadata.update(properties)

    def get_artifact(self, port: str = DEFAULT_PORT) -> Artifact:
        return self.outputs[port]

    def get_properties(self, port: str = DEFAULT_PORT) -> dict[str, Any]:
        return dict(self.get_artifact(port).metadata)
