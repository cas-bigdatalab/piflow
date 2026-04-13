import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROJECT_ROOT / "workspace" / "skills"


def _parse_skill_info(skill_dir: Path) -> Optional[Dict[str, Optional[str]]]:
    """
    解析单个 skill 目录，返回名称、描述和 icon 路径。
    """
    skill_name = skill_dir.name

    if skill_name == "__init__":
        return None

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

    return {
        "name": name,
        "description": description,
        "icon": icon_relative,
    }


def get_skills_list(page: int = 1, page_size: int = 20, keyword: str = "") -> Dict:
    """
    获取 workspace/skills 下所有 skill 的名称、描述和 icon 路径。

    Args:
        page: 页码，从 1 开始
        page_size: 每页数量
        keyword: 关键字模糊搜索（搜索 name 和 description）

    Returns:
        Dict: 包含 data, total, current_count
    """
    if not SKILLS_DIR.exists():
        return {
            "data": [],
            "total": 0,
            "current_count": 0,
        }

    all_skills = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_info = _parse_skill_info(skill_dir)
        if skill_info is None:
            continue

        all_skills.append(skill_info)

    total = len(all_skills)

    if keyword:
        keyword_lower = keyword.lower()
        filtered = [
            s
            for s in all_skills
            if keyword_lower in (s.get("name") or "").lower()
            or keyword_lower in (s.get("description") or "").lower()
        ]
    else:
        filtered = all_skills

    total = len(filtered)

    start = (page - 1) * page_size
    end = start + page_size
    paged_data = filtered[start:end]

    return {
        "data": paged_data,
        "total": total,
        "current_count": len(paged_data),
    }


def get_all_skills_list() -> List[Dict[str, Optional[str]]]:
    """
    获取所有 skills 列表（不分页），用于兼容旧逻辑。
    """
    if not SKILLS_DIR.exists():
        return []

    results = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_info = _parse_skill_info(skill_dir)
        if skill_info is None:
            continue

        results.append(skill_info)

    return results


if __name__ == "__main__":
    import json

    result = get_skills_list(page=1, page_size=10, keyword="")
    print(json.dumps(result, ensure_ascii=False, indent=2))
