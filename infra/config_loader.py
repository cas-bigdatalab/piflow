from pathlib import Path

import yaml

from infra.settings import DatabaseConfig, PolicyConfig, Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(path: Path):
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> Settings:
    app_config = load_yaml(CONFIG_DIR / "app.yaml")
    llm_config = load_yaml(CONFIG_DIR / "llm.yaml")
    mcp_config = load_yaml(CONFIG_DIR / "mcp_servers.yaml")
    policy_config = load_yaml(CONFIG_DIR / "policy.yaml")
    database_config = load_yaml(CONFIG_DIR / "database.yaml")
    default_user_config = load_yaml(CONFIG_DIR / "default_user.yaml")
    workspace_config = app_config.get("workspace", {})
    minio_config = app_config.get("minio", {})
    mineru_config = load_yaml(CONFIG_DIR / "mineru.yaml")

    config = {
        **app_config,
        **llm_config,
        "workspace": workspace_config,
        "minio": minio_config,
        "mcp": mcp_config,
        **default_user_config,
        "policy": PolicyConfig(**policy_config.get("policy", {})),
        "database": DatabaseConfig(**database_config),
        "mineru": mineru_config,
    }

    return Settings(**config)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings

    if _settings is None:
        _settings = load_settings()

    return _settings


def resolve_workspace_root(root: str | Path | None = None) -> Path:
    raw_root = Path(root if root is not None else get_settings().workspace.root)
    if raw_root.is_absolute():
        return raw_root.resolve()
    return (PROJECT_ROOT / raw_root).resolve()
