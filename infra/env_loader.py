import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_env_path(path: str) -> Path:
    env_path = Path(path)

    if env_path.is_absolute():
        return env_path

    cwd_path = Path.cwd() / env_path
    if cwd_path.exists():
        return cwd_path

    return PROJECT_ROOT / env_path


def load_dotenv_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a .env file into process env."""
    env_path = _resolve_env_path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and ((value[0] == value[-1]) and value[0] in {"'", '"'}):
            value = value[1:-1]

        # Keep already exported env vars as higher priority.
        os.environ.setdefault(key, value)
