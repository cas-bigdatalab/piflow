from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str] = field(default_factory=list)
