import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional

from infra.config_loader import resolve_workspace_root

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = resolve_workspace_root() / "skills"


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


def _load_skill_type_mapping() -> Dict[str, str]:
    """
    从 docs/skill分类.txt 解析技能分类映射
    """
    classification_file = PROJECT_ROOT / "docs" / "skill分类.txt"
    if not classification_file.exists():
        return {}

    type_mapping = {}
    current_type = ""

    try:
        content = classification_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()

            if line.startswith("## "):
                current_type = line.replace("##", "").strip()
            elif line.startswith("- **"):
                parts = line.split("**")
                if len(parts) >= 3:
                    skill_name = parts[1]
                    type_mapping[skill_name] = current_type
    except Exception:
        pass

    return type_mapping


def init_skills_to_database():
    """
    初始化本地所有 skills 到数据库
    从 workspace/skills 读取信息，从 docs/skill分类.txt 获取类型
    版本号默认 1.0.0
    """
    from runtime.chat_store import insert_skill

    type_mapping = _load_skill_type_mapping()

    all_skills = get_all_skills_list()

    count = 0
    for skill in all_skills:
        skill_name = skill.get("name", "")
        description = skill.get("description", "")
        icon_path = skill.get("icon")

        skill_type = type_mapping.get(skill_name, "其他")

        insert_skill(
            name=skill_name,
            description=description or "",
            icon_path=icon_path,
            type=skill_type,
            version="1.0.0",
        )
        count += 1

    return count


def get_skills_grouped_by_type() -> List[Dict]:
    """
    获取所有 skill 分类及每个分类的 skills 数量
    """
    from runtime.chat_store import list_skills as db_list_skills

    result = db_list_skills(limit=10000, offset=0, keyword="")

    type_count: Dict[str, int] = {}

    for r in result.get("data", []):
        skill_type = r.get("type") or "未分类"
        type_count[skill_type] = type_count.get(skill_type, 0) + 1

    grouped = []
    for type_name, count in sorted(type_count.items(), key=lambda x: x[0]):
        grouped.append(
            {
                "type": type_name,
                "count": count,
            }
        )

    return grouped


if __name__ == "__main__":
    import json

    result = get_skills_list(page=1, page_size=10, keyword="")
    print(json.dumps(result, ensure_ascii=False, indent=2))
