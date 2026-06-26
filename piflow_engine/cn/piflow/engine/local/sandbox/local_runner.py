from __future__ import annotations

import subprocess
from pathlib import Path

from piflow_engine.cn.piflow.engine.local.sandbox.result import SandboxResult


class LocalSandboxRunner:
    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout_seconds: int | None = None,
    ) -> SandboxResult:
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return SandboxResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _decode_timeout_output(error.stdout)
            stderr = _decode_timeout_output(error.stderr)
            message = f"command timed out after {timeout_seconds} seconds"
            if stderr:
                stderr = f"{stderr}\n{message}"
            else:
                stderr = message
            return SandboxResult(
                returncode=124,
                stdout=stdout,
                stderr=stderr,
                command=command,
            )


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
