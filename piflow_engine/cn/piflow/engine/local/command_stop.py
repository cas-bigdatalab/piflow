from __future__ import annotations

import json
import uuid
from pathlib import Path
import shutil
from typing import Any

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.runtime_keys import (
    RUN_CONTEXT_STDERR_LOG_PATH,
    RUN_CONTEXT_STDOUT_LOG_PATH,
)
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.engine.local.constants import (
    RUNNER_CONTEXT_DOCKER_CPUS,
    RUNNER_CONTEXT_DOCKER_IMAGE,
    RUNNER_CONTEXT_DOCKER_MEMORY,
    RUNNER_CONTEXT_DOCKER_NETWORK_ENABLED,
    RUNNER_CONTEXT_DOCKER_PIDS_LIMIT,
    RUNNER_CONTEXT_DOCKER_TIMEOUT_SECONDS,
    RUNNER_CONTEXT_PYTHON_HOME,
    RUNNER_CONTEXT_SANDBOX_BACKEND,
    RUNNER_CONTEXT_WORKSPACE_ROOT,
)
from piflow_engine.cn.piflow.engine.local.command_invocation_parser import (
    CommandInvocationParser,
)
from piflow_engine.cn.piflow.engine.local.sandbox import (
    DockerSandboxPolicy,
    DockerSandboxRunner,
    LocalSandboxRunner,
    SandboxResult,
    WorkspacePathMapper,
)


class CommandStop(ConfigurableStop):
    def __init__(self, parser: CommandInvocationParser) -> None:
        super().__init__()
        self._parser = parser
        self.spec = parser.spec
        self.properties: dict[str, Any] = {}
        self._workspace_root: Path | None = None
        self._python_home: Path | None = None
        self._sandbox_backend = "local"
        self._local_runner = LocalSandboxRunner()
        self._docker_runner: DockerSandboxRunner | None = None
        self._timeout_seconds: int | None = None

    def set_properties(self, properties: dict[str, Any]) -> None:
        self.properties = dict(properties)

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)
        python_home = ctx.get(RUNNER_CONTEXT_PYTHON_HOME, None)
        if python_home:
            self._python_home = Path(str(python_home)).resolve()
        self._sandbox_backend = str(
            ctx.get(RUNNER_CONTEXT_SANDBOX_BACKEND, "local")
        ).lower()
        self._timeout_seconds = _optional_int(
            ctx.get(RUNNER_CONTEXT_DOCKER_TIMEOUT_SECONDS, None)
        )
        if self._sandbox_backend == "docker":
            policy = DockerSandboxPolicy(
                image=str(
                    ctx.get(RUNNER_CONTEXT_DOCKER_IMAGE, "piflow-python-runner:3.11")
                ),
                timeout_seconds=int(ctx.get(RUNNER_CONTEXT_DOCKER_TIMEOUT_SECONDS, 300)),
                memory=str(ctx.get(RUNNER_CONTEXT_DOCKER_MEMORY, "512m")),
                cpus=str(ctx.get(RUNNER_CONTEXT_DOCKER_CPUS, "1")),
                pids_limit=int(ctx.get(RUNNER_CONTEXT_DOCKER_PIDS_LIMIT, 128)),
                network_enabled=_as_bool(
                    ctx.get(RUNNER_CONTEXT_DOCKER_NETWORK_ENABLED, False)
                ),
            )
            self._docker_runner = DockerSandboxRunner(self._workspace_root, policy)
        elif self._sandbox_backend != "local":
            raise ValueError(f"unsupported sandbox backend: {self._sandbox_backend}")

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        workspace = self._prepare_workspace(ctx)
        invocation = self._parser.parse(inputs, workspace, self.properties)
        command = list(invocation.command)
        if self._sandbox_backend == "docker":
            self._validate_docker_paths(workspace, invocation.output_files.values())
            result = self._run_docker(command)
        else:
            result = self._local_runner.run(
                self._normalize_command(command),
                cwd=self.spec.base_dir,
                timeout_seconds=self._timeout_seconds,
            )
        stdout_log_path, stderr_log_path = self._write_logs(
            workspace,
            result.command or command,
            result,
            invocation.resolved_values,
        )
        ctx.put(RUN_CONTEXT_STDOUT_LOG_PATH, str(stdout_log_path))
        ctx.put(RUN_CONTEXT_STDERR_LOG_PATH, str(stderr_log_path))

        if result.returncode != 0:
            raise RuntimeError(
                f"command stop '{ctx.get_stop_job().get_stop_name()}' failed with exit code {result.returncode}"
            )

        for key, output_path in invocation.output_files.items():
            outputs.write(FileArtifact(path=str(output_path)), key)

    def _prepare_workspace(self, ctx: JobContext) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = ctx.get_stop_job().get_stop_name()
        job_id = ctx.get_stop_job().jid()
        workspace = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
        )
        for name in ("input", "output", "meta"):
            (workspace / name).mkdir(parents=True, exist_ok=True)
        return workspace

    def _write_logs(
        self,
        workspace: Path,
        command: list[str],
        result: SandboxResult,
        values: dict[str, str],
    ) -> tuple[Path, Path]:
        meta_dir = workspace / "meta"
        stdout_log_path = meta_dir / "stdout.log"
        stderr_log_path = meta_dir / "stderr.log"
        stdout_log_path.write_text(result.stdout, encoding="utf-8")
        stderr_log_path.write_text(result.stderr, encoding="utf-8")
        execution_meta = {
            "command": command,
            "cwd": str(self.spec.base_dir),
            "returncode": result.returncode,
            "resolved_values": values,
            "spec_source": self.spec.source,
        }
        (meta_dir / "execution.json").write_text(
            json.dumps(execution_meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return stdout_log_path, stderr_log_path

    def _run_docker(self, command: list[str]) -> SandboxResult:
        if self._docker_runner is None:
            raise RuntimeError("docker sandbox runner is not initialized")
        return self._docker_runner.run(command, cwd=self.spec.base_dir)

    def _validate_docker_paths(
        self,
        workspace: Path,
        output_paths: Any,
    ) -> None:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")
        mapper = WorkspacePathMapper(self._workspace_root)
        mapper.validate_in_workspace(self.spec.base_dir)
        mapper.validate_in_workspace(self.spec.base_dir / self.spec.script_path)
        output_root = (workspace / "output").resolve()
        for output_path in output_paths:
            Path(str(output_path)).resolve().relative_to(output_root)

    def _normalize_command(self, command: list[str]) -> list[str]:
        if not command:
            raise ValueError("command_template must not be empty")

        executable = command[0]
        if executable == "python":
            python_executable = self._resolve_python_executable()
            if python_executable is not None:
                command[0] = python_executable
        return command

    def _resolve_python_executable(self) -> str | None:
        if self._python_home is not None:
            if self._python_home.is_file():
                return str(self._python_home)

            for relative_path in ("bin/python", "bin/python3"):
                candidate = self._python_home / relative_path
                if candidate.exists():
                    return str(candidate)

            direct_candidates = [
                self._python_home / "python",
                self._python_home / "python3",
            ]
            for candidate in direct_candidates:
                if candidate.exists():
                    return str(candidate)

            raise FileNotFoundError(
                f"python executable not found under python home: {self._python_home}"
            )

        python_path = shutil.which("python")
        if python_path is not None:
            return python_path

        return shutil.which("python3")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
