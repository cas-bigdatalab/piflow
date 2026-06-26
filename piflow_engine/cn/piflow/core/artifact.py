from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar


@dataclass
class Artifact:
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    artifact_type: ClassVar[str] = "object"

    @property
    def type(self) -> str:
        return self.artifact_type

    def with_metadata(self, **kwargs: Any) -> "Artifact":
        self.metadata.update(kwargs)
        return self


@dataclass
class FileArtifact(Artifact):
    path: str = ""

    artifact_type: ClassVar[str] = "file"

    def __post_init__(self) -> None:
        if self.path and self.value is None:
            self.value = self.path
        elif self.value is not None and not self.path:
            self.path = str(self.value)


@dataclass
class TableArtifact(Artifact):
    schema: dict[str, Any] = field(default_factory=dict)

    artifact_type: ClassVar[str] = "table"


@dataclass
class JsonArtifact(Artifact):
    artifact_type: ClassVar[str] = "json"


def ensure_artifact(data: Artifact | Any) -> Artifact:
    if isinstance(data, Artifact):
        return data

    if isinstance(data, Path):
        return FileArtifact(path=str(data))

    if isinstance(data, (dict, list)):
        return JsonArtifact(value=data)

    return Artifact(value=data)
