from __future__ import annotations

from dataclasses import dataclass

from cn.piflow.core.artifact import Artifact


@dataclass
class TraceArtifact(Artifact):
    def __init__(self, text: str, **metadata):
        super().__init__(value=text, metadata=dict(metadata))

    @property
    def text(self) -> str:
        return str(self.value)

    def describe(self) -> str:
        return f"text={self.text}, metadata={self.metadata}"
