from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from cn.piflow.engine.local.sandbox import (
    DockerSandboxPolicy,
    DockerSandboxRunner,
    WorkspacePathMapper,
)


def test_workspace_path_mapper_converts_only_workspace_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    script = workspace / "skills" / "demo" / "scripts" / "run.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('ok')", encoding="utf-8")

    mapper = WorkspacePathMapper(workspace)

    assert mapper.to_container_path(script) == "/workspace/skills/demo/scripts/run.py"
    with pytest.raises(ValueError):
        mapper.to_container_path(tmp_path / "outside.py")


def test_docker_runner_builds_sandboxed_docker_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    skill_dir = workspace / "skills" / "demo"
    script = skill_dir / "scripts" / "run.py"
    input_path = workspace / "process_1" / "job_1" / "input" / "input.txt"
    output_path = workspace / "process_1" / "job_1" / "output" / "output.txt"
    script.parent.mkdir(parents=True)
    input_path.parent.mkdir(parents=True)
    output_path.parent.mkdir(parents=True)
    script.write_text("print('ok')", encoding="utf-8")
    input_path.write_text("hello", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    runner = DockerSandboxRunner(
        workspace,
        DockerSandboxPolicy(
            image="piflow-test:3.11",
            timeout_seconds=10,
            memory="256m",
            cpus="0.5",
            pids_limit=64,
        ),
    )

    result = runner.run(
        [
            "python",
            str(script),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=skill_dir,
    )

    command = captured["command"]
    assert result.returncode == 0
    assert command == [
        "docker",
        "run",
        "--rm",
        "--memory",
        "256m",
        "--cpus",
        "0.5",
        "--pids-limit",
        "64",
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        f"{workspace.resolve()}:/workspace:rw",
        "-w",
        "/workspace/skills/demo",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=64m",
        "--network",
        "none",
        "piflow-test:3.11",
        "python",
        "/workspace/skills/demo/scripts/run.py",
        "--input",
        "/workspace/process_1/job_1/input/input.txt",
        "--output",
        "/workspace/process_1/job_1/output/output.txt",
    ]
    assert captured["kwargs"]["timeout"] == 10


def test_docker_runner_rejects_absolute_paths_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    skill_dir = workspace / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    runner = DockerSandboxRunner(workspace, DockerSandboxPolicy())

    with pytest.raises(ValueError):
        runner.run(["python", str(tmp_path / "outside.py")], cwd=skill_dir)
