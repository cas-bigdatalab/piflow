import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from langchain.tools import tool
from infra.config_loader import resolve_workspace_root

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = resolve_workspace_root()
VENV_PYTHON = sys.executable


def _convert_virtual_path(value: str) -> str:
    if not isinstance(value, str):
        return value
    if value.startswith("/"):
        rel = value.lstrip("/").replace("/", os.sep)
        return (WORKSPACE_ROOT / rel).resolve().as_posix()
    return value


def _rewrite_inline_python(code: str) -> str:
    def replace_single(match: re.Match[str]) -> str:
        return "'" + _convert_virtual_path(match.group(1)) + "'"

    def replace_double(match: re.Match[str]) -> str:
        return '"' + _convert_virtual_path(match.group(1)) + '"'

    code = re.sub(r"'(\/[^']*)'", replace_single, code)
    code = re.sub(r'"(\/[^"]*)"', replace_double, code)
    return code


def _merge_split_virtual_path_parts(parts: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0

    while index < len(parts):
        token = parts[index]

        if not token.startswith("/"):
            merged.append(token)
            index += 1
            continue

        candidate = token
        candidate_path = _convert_virtual_path(candidate)
        best_candidate = candidate
        best_path = candidate_path if os.path.exists(candidate_path) else None

        look_ahead = index + 1
        while look_ahead < len(parts):
            next_token = parts[look_ahead]
            if next_token.startswith("-") or next_token.startswith("/"):
                break

            candidate = f"{candidate} {next_token}"
            candidate_path = _convert_virtual_path(candidate)
            if os.path.exists(candidate_path):
                best_candidate = candidate
                best_path = candidate_path
                look_ahead += 1
                continue

            look_ahead += 1

        merged.append(best_candidate if best_path else token)
        index += len(best_candidate.split(" ")) if best_path else 1

    return merged


def _split_command(command: str) -> tuple[list[str], str | None]:
    cwd: str | None = None
    raw = command.strip()

    if "&&" in raw:
        left, right = raw.split("&&", 1)
        left_parts = shlex.split(left.strip())
        if left_parts and left_parts[0] == "cd" and len(left_parts) > 1:
            cwd = _convert_virtual_path(left_parts[1])
        raw = right.strip()

    parts = shlex.split(raw)
    if not parts:
        return [], cwd

    parts = _merge_split_virtual_path_parts(parts)
    parts = [_convert_virtual_path(part) if part.startswith("/") else part for part in parts]

    if parts[0] in ("python", "python3"):
        parts[0] = VENV_PYTHON
        if len(parts) > 2 and parts[1] == "-c":
            parts[2] = _rewrite_inline_python(parts[2])
            if not cwd:
                cwd = str(WORKSPACE_ROOT)
        elif len(parts) > 1 and parts[1] not in ("-m",):
            if not cwd:
                script_path = Path(parts[1])
                cwd = str(script_path.parent if script_path.parent != Path("") else WORKSPACE_ROOT)

    if cwd == "":
        cwd = None

    return parts, cwd


@tool
def exec_shell(command: str):
    """
    Execute a shell-style command inside the project workspace.
    """

    started_at = datetime.now()
    started_perf = time.perf_counter()
    print(f"[exec_shell][start {started_at.strftime('%Y-%m-%d %H:%M:%S')}] {command}")

    parts, cwd = _split_command(command)
    print(f"[exec_shell] -> parts={parts}")
    print(f"[exec_shell] -> cwd={cwd}")

    if not parts:
        return "empty command"

    if cwd and not os.path.isdir(cwd):
        return f"cwd does not exist: {cwd}"

    if parts[0] == VENV_PYTHON and len(parts) > 1 and parts[1] not in ("-c", "-m"):
        if not os.path.isfile(parts[1]):
            return f"script does not exist: {parts[1]}"
    try:
        result = subprocess.run(
            parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=120,
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            },
        )
    except Exception as e:
        return f"""command: {' '.join(parts)}
    cwd: {cwd}
    error: {type(e).__name__}: {str(e)}
    returncode: -1
    """

    finished_at = datetime.now()
    elapsed = time.perf_counter() - started_perf
    print(
        f"[exec_shell][end {finished_at.strftime('%Y-%m-%d %H:%M:%S')}] "
        f"elapsed={elapsed:.2f}s returncode={result.returncode}"
    )
    if result.returncode != 0:
        stdout_preview = (result.stdout or "").strip()
        stderr_preview = (result.stderr or "").strip()
        if stdout_preview:
            print(f"[exec_shell][stdout] {stdout_preview[:2000]}")
        if stderr_preview:
            print(f"[exec_shell][stderr] {stderr_preview[:2000]}")

    return f"""
command: {' '.join(parts)}
cwd: {cwd}
started_at: {started_at.strftime('%Y-%m-%d %H:%M:%S')}
finished_at: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}
elapsed_seconds: {elapsed:.2f}

stdout:
{result.stdout}

stderr:
{result.stderr}

returncode: {result.returncode}
"""
