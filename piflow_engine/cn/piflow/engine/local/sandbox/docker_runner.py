from __future__ import annotations

import os
import subprocess
from pathlib import Path

from piflow_engine.cn.piflow.engine.local.sandbox.path_mapper import WorkspacePathMapper
from piflow_engine.cn.piflow.engine.local.sandbox.policy import DockerSandboxPolicy
from piflow_engine.cn.piflow.engine.local.sandbox.result import SandboxResult


class DockerSandboxRunner:
    def __init__(self, workspace_root: Path, policy: DockerSandboxPolicy) -> None:
        self.workspace_root = workspace_root.resolve()
        self.policy = policy
        self.mapper = WorkspacePathMapper(self.workspace_root)

    def run(self, command: list[str], *, cwd: Path) -> SandboxResult:
        mapped_command = self._map_command(command)
        docker_command = self._docker_command(mapped_command, cwd=cwd)

        try:
            result = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=self.policy.timeout_seconds,
                check=False,
            )
            return SandboxResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=docker_command,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _decode_timeout_output(error.stdout)
            stderr = _decode_timeout_output(error.stderr)
            message = f"docker sandbox timed out after {self.policy.timeout_seconds} seconds"
            if stderr:
                stderr = f"{stderr}\n{message}"
            else:
                stderr = message
            return SandboxResult(
                returncode=124,
                stdout=stdout,
                stderr=stderr,
                command=docker_command,
            )

    def _docker_command(self, mapped_command: list[str], *, cwd: Path) -> list[str]:
        self.mapper.validate_in_workspace(cwd)
        container_cwd = self.mapper.container_workdir(cwd)
        docker_command = [
            "docker",
            "run",
            "--rm",
            "--memory",
            self.policy.memory,
            "--cpus",
            self.policy.cpus,
            "--pids-limit",
            str(self.policy.pids_limit),
            "--security-opt",
            "no-new-privileges",
            "--cap-drop",
            "ALL",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            "-v",
            f"{self.workspace_root}:/workspace:rw",
            "-w",
            container_cwd,
        ]
        if self.policy.readonly_rootfs:
            docker_command.extend(
                [
                    "--read-only",
                    "--tmpfs",
                    f"/tmp:rw,nosuid,nodev,size={self.policy.tmpfs_size}",
                ]
            )
        if not self.policy.network_enabled:
            docker_command.extend(["--network", "none"])
        docker_command.append(self.policy.image)
        docker_command.extend(mapped_command)
        return docker_command

    def _map_command(self, command: list[str]) -> list[str]:
        mapped: list[str] = []
        for token in command:
            path = Path(token)
            if path.is_absolute():
                mapped.append(self.mapper.to_container_path(path))
            else:
                mapped.append(token)
        return mapped


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
