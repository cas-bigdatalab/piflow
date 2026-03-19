from pathlib import Path
import os


def load_dotenv_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a .env file into process env."""
    env_path = Path(path)
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
