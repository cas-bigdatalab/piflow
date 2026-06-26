from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DockerSandboxPolicy:
    image: str = "piflow-python-runner:3.11"
    timeout_seconds: int = 300
    memory: str = "512m"
    cpus: str = "1"
    pids_limit: int = 128
    network_enabled: bool = False
    readonly_rootfs: bool = True
    tmpfs_size: str = "64m"
