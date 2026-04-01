import os
import shlex
import subprocess
import time
from datetime import datetime

from langchain.tools import tool


REAL_ROOT_DIR = r"D:\hqr\projects\python\new-flow-deepagents\flow-deepagents\workspace"
VENV_PYTHON = r"D:\hqr\software\miniforge3\envs\test-whl\python.exe"


@tool
def exec_shell(command: str):
    """
    执行终端命令
    """

    def convert_path(path: str):
        # 把 agent 看到的 /xxx 映射到真实 workspace 根目录
        if path.startswith("/"):
            rel = path.lstrip("/")
            return os.path.normpath(os.path.join(REAL_ROOT_DIR, rel))
        return path

    started_at = datetime.now()
    started_perf = time.perf_counter()
    print(f"[exec_shell][start {started_at.strftime('%Y-%m-%d %H:%M:%S')}] {command}")

    cwd = None

    if "&&" in command:
        left, right = command.split("&&", 1)

        left_parts = shlex.split(left.strip())
        right_parts = shlex.split(right.strip())

        if left_parts and left_parts[0] == "cd" and len(left_parts) > 1:
            cwd = convert_path(left_parts[1])

        parts = right_parts
    else:
        parts = shlex.split(command)

    parts = [convert_path(part) if part.startswith("/") else part for part in parts]

    if cwd is None and parts and parts[0] in ("python", "python3") and len(parts) > 1:
        script_path = parts[1]
        cwd = os.path.dirname(script_path)

    if parts and parts[0] in ("python", "python3"):
        parts[0] = VENV_PYTHON

    print(f"[exec_shell] -> parts={parts}")
    print(f"[exec_shell] -> cwd={cwd}")

    if cwd and not os.path.isdir(cwd):
        return f"cwd 不存在: {cwd}"

    if parts and parts[0] in ("python", "python3") and len(parts) > 1:
        if not os.path.isfile(parts[1]):
            return f"脚本不存在: {parts[1]}"

    result = subprocess.run(
        parts,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=120,
    )
    finished_at = datetime.now()
    elapsed = time.perf_counter() - started_perf
    print(
        f"[exec_shell][end {finished_at.strftime('%Y-%m-%d %H:%M:%S')}] "
        f"elapsed={elapsed:.2f}s returncode={result.returncode}"
    )

    return f"""
命令: {' '.join(parts)}
cwd: {cwd}
started_at: {started_at.strftime('%Y-%m-%d %H:%M:%S')}
finished_at: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}
elapsed_seconds: {elapsed:.2f}

stdout:
# {result.stdout}

stderr:
{result.stderr}

returncode: {result.returncode}
"""
