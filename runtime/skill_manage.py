import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / "workspace" / "skills"


def get_skills_list() -> List[Dict[str, Optional[str]]]:
    """
    获取 workspace/skills 下所有 skill 的名称、描述和 icon 路径。

    Returns:
        List[Dict]: 每个 skill 的信息，格式如下：
        [
            {
                "name": "flow_orchestrator",
                "description": "按"算法选择 -> 数据源绑定...",
                "icon": "workspace/skills/flow_orchestrator/assets/icon.png"
            },
            ...
        ]
    """
    if not SKILLS_DIR.exists():
        return []

    results = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_name = skill_dir.name

        skill_md = skill_dir / "SKILL.md"
        description = None
        name = skill_name

        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 2:
                        frontmatter = yaml.safe_load(parts[1])
                        if frontmatter:
                            name = frontmatter.get("name", skill_name)
                            description = frontmatter.get("description", "")
            except Exception:
                pass

        icon_path = skill_dir / "assets" / "icon.png"
        icon_relative = None
        if icon_path.exists():
            icon_relative = f"workspace/skills/{skill_name}/assets/icon.png"

        results.append(
            {
                "name": name,
                "description": description,
                "icon": icon_relative,
            }
        )

    return results


if __name__ == "__main__":
    import json

    skills = get_skills_list()
    print(json.dumps(skills, ensure_ascii=False, indent=2))
