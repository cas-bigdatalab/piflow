import yaml
from pathlib import Path

from infra.settings import Settings, SkillsConfig, PolicyConfig


# 项目根目录
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
    skills_config = load_yaml(CONFIG_DIR / "skills.yaml")
    policy_config = load_yaml(CONFIG_DIR / "policy.yaml")
    workspace_config = app_config.get("workspace", {})

    # skills.yaml 结构
    skills_data = skills_config.get("skills", {})

    # 拆分 paths 和 configs
    paths = skills_data.get("paths", ["skills"])

    configs = {
        k: v for k, v in skills_data.items()
        if k != "paths"
    }

    config = {
        **app_config,
        **llm_config,
        "workspace": workspace_config,
        "mcp": mcp_config,
        "skills": SkillsConfig(paths=paths, configs=configs),
        "policy": PolicyConfig(**policy_config.get("policy", {})),
    }

    return Settings(**config)


# =========================
# 单例 Settings
# =========================

_settings: Settings | None = None


def get_settings() -> Settings:

    global _settings

    if _settings is None:
        _settings = load_settings()

    return _settings
