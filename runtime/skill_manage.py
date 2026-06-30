import re
import shutil
import uuid
from contextlib import closing
import psycopg2
from psycopg2.extras import RealDictCursor
import yaml
from pathlib import Path
from typing import List, Dict, Optional

from database.postgres import get_connection
from infra.config_loader import resolve_workspace_root

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = resolve_workspace_root()
SKILLS_DIR = WORKSPACE_ROOT / "skills"
GENERATED_SKILLS_DIR = SKILLS_DIR / "generated"
DAG_SYSTEM_NODE_DIR = WORKSPACE_ROOT / "dag_system_node"
STORAGE_DIR = PROJECT_ROOT / "storage"
STORAGE_SKILLS_DIR = STORAGE_DIR / "skills"
DEFAULT_COMMON_ICON = "/storage/common/common.png"


def _normalize_param_container(raw_params) -> Dict[str, List[Dict]]:
    """归一化技能参数容器，兼容历史坏数据与生成器误产出的对象形状。"""
    if not raw_params:
        return {"params": []}

    if isinstance(raw_params, list):
        return {"params": [item for item in raw_params if isinstance(item, dict)]}

    if not isinstance(raw_params, dict):
        return {"params": []}

    params = raw_params.get("params", raw_params)
    normalized: List[Dict] = []

    if isinstance(params, list):
        normalized = [item for item in params if isinstance(item, dict)]
    elif isinstance(params, dict):
        # 历史脏数据可能是 {"params": {...}} 或 {"params": {"foo": {...}}}
        if isinstance(params.get("name"), str):
            normalized = [params]
        else:
            for name, value in params.items():
                if isinstance(value, dict):
                    entry = dict(value)
                    entry.setdefault("name", str(name))
                    normalized.append(entry)
    return {"params": normalized}


def ensure_storage_dirs():
    STORAGE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)


def _public_skill_icon_path(skill_folder: str) -> str:
    return f"/storage/skills/{skill_folder}.png"


def _skill_icon_source_path(skill_folder: str) -> Path:
    return SKILLS_DIR / skill_folder / "assets" / "icon.png"


def _skill_icon_storage_path(skill_folder: str) -> Path:
    return STORAGE_SKILLS_DIR / f"{skill_folder}.png"


def sync_skill_icon_to_storage(skill_folder: str) -> Optional[str]:
    source = _skill_icon_source_path(skill_folder)
    if not source.exists():
        return None

    ensure_storage_dirs()
    target = _skill_icon_storage_path(skill_folder)
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists() or source.stat().st_mtime_ns != target.stat().st_mtime_ns:
        shutil.copy2(source, target)

    return _public_skill_icon_path(skill_folder)


def normalize_skill_icon_path(icon_path: str | None = None, skill_folder: str | None = None) -> Optional[str]:
    raw_path = (icon_path or "").strip()

    if raw_path.startswith(("http://", "https://", "data:")):
        return raw_path

    if raw_path.startswith("/storage/"):
        return raw_path

    if raw_path.startswith("storage/"):
        return f"/{raw_path.lstrip('/')}"

    if skill_folder:
        return sync_skill_icon_to_storage(skill_folder) or DEFAULT_COMMON_ICON

    return DEFAULT_COMMON_ICON


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

    icon_relative = sync_skill_icon_to_storage(skill_name) or DEFAULT_COMMON_ICON

    return {
        "name": name,
        "description": description,
        "icon": icon_relative,
    }

def get_all_skills_list() -> List[Dict[str, Optional[str]]]:
    """
    获取所有 skills 列表（不分页），用于兼容旧逻辑。
    """
    if not SKILLS_DIR.exists():
        return []

    results = []

    for base_dir in (SKILLS_DIR, GENERATED_SKILLS_DIR):
        if not base_dir.exists():
            continue

        for skill_dir in base_dir.iterdir():
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


def insert_dag_skill(
    skill_name: str,
    description: str,
    name_zh: str = None,
    skill_path: str = "",
    file_path: str = "",
    input_params: dict = None,
    output_params: dict = None,
    skill_type: str = "",
    language: str = "",
    command: str = "",
    icon_path: str = None,
    version: str = None,
):
    skill_id = uuid.uuid4().hex

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO dag_skills (
                            skill_id, skill_name, name_zh, description, skill_path, file_path,
                            input_params, output_params, skill_type,
                            language, command, icon_path, version
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s)
                        
                        
                        ON CONFLICT (skill_name, version)

                        DO UPDATE SET
                            skill_name = EXCLUDED.skill_name,
                            name_zh = EXCLUDED.name_zh,
                            description = EXCLUDED.description,
                            skill_path = EXCLUDED.skill_path,
                            file_path = EXCLUDED.file_path,
                            input_params = EXCLUDED.input_params,
                            output_params = EXCLUDED.output_params,
                            skill_type = EXCLUDED.skill_type,
                            language = EXCLUDED.language,
                            command = EXCLUDED.command,
                            icon_path = EXCLUDED.icon_path,
                            version = EXCLUDED.version
                        
                        RETURNING id, skill_id
                        """,
                        (
                            skill_id, skill_name, name_zh, description, skill_path or "", file_path or "",
                            psycopg2.extras.Json(input_params or {}),
                            psycopg2.extras.Json(output_params or {}),
                            skill_type, language or "", command or "", icon_path, version,
                        ),
                    )
                    row = cursor.fetchone()

                    if not row:
                        return None

                    return {
                        "id": row[0],
                        "skill_id": row[1],
                    }


    except Exception as e:
        raise RuntimeError("insert_dag_skill failed") from e


def _parse_dag_skill_frontmatter(skill_dir: Path) -> Optional[dict]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 2:
            return None

        frontmatter = yaml.safe_load(parts[1])
        if not frontmatter:
            return None

        name = frontmatter.get("name", skill_dir.name)
        description = frontmatter.get("description", "")
        tag = frontmatter.get("tag", "")

        raw_inputs = frontmatter.get("input_params") or []
        raw_outputs = frontmatter.get("output_params") or []

        input_params = {"params": []}
        promoted_output_params = []
        for p in raw_inputs:
            role = p.get("role", "data")
            entry = {
                "name": p.get("name", ""),
                "type": p.get("type", "String"),
                "role": role,
                "description": p.get("description", ""),
                "required": p.get("required", False),
            }
            if "default" in p:
                entry["default_value"] = p["default"]
            if role == "output_data":
                promoted_output_params.append(
                    {
                        "name": entry["name"],
                        "type": entry["type"],
                        "role": "output_data",
                        "description": entry["description"],
                    }
                )
            else:
                input_params["params"].append(entry)

        output_params = {"params": []}
        for p in raw_outputs:
            entry = {
                "name": p.get("name", ""),
                "type": p.get("type", "String"),
                "role": p.get("role", "output_data"),
                "description": p.get("description", ""),
            }
            output_params["params"].append(entry)
        existing_output_names = {p["name"] for p in output_params["params"]}
        for entry in promoted_output_params:
            if entry["name"] not in existing_output_names:
                output_params["params"].append(entry)

        return {
            "name": name,
            "name_zh": frontmatter.get("name_zh", ""),
            "description": description,
            "tag": tag,
            "input_params": _normalize_param_container(input_params),
            "output_params": _normalize_param_container(output_params),
        }
    except Exception:
        return None


def _find_skill_script_path(skill_dir: Path) -> str:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return ""

    py_files = sorted(scripts_dir.glob("*.py"))
    if not py_files:
        return ""

    script_file = py_files[0]
    return str(script_file.relative_to(WORKSPACE_ROOT)).replace("\\", "/")


def _extract_command_from_skill_md(skill_dir: Path, skill_name: str, input_params: dict) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ""

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception:
        return ""

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
        else:
            body = content
    else:
        body = content

    bash_blocks = re.findall(r"```(?:bash|shell)\s*\n(.*?)```", body, re.DOTALL)
    for block in bash_blocks:
        for line in block.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line

    return ""


def _process_skill_dirs(base_dir: Path, path_prefix: str) -> int:
    if not base_dir.exists():
        return 0

    count = 0
    for skill_dir in sorted(base_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name == "__init__":
            continue

        info = _parse_dag_skill_frontmatter(skill_dir)
        if info is None:
            continue

        skill_name = info["name"]
        name_zh = info.get("name_zh", "")
        description = info["description"]
        skill_type = info["tag"]
        input_params = info["input_params"]
        output_params = info["output_params"]

        output_names = {p["name"] for p in output_params.get("params", [])}
        input_params["params"] = [
            p for p in input_params.get("params", []) if p["name"] not in output_names
        ]

        skill_path = f"{path_prefix}/{skill_dir.name}"

        file_path = _find_skill_script_path(skill_dir)

        language = "Python" if file_path else ""

        command = _extract_command_from_skill_md(skill_dir, skill_name, input_params)

        icon_path = f"/storage/{path_prefix}/{skill_dir.name}.png"

        insert_dag_skill(
            skill_name=skill_name,
            name_zh=name_zh,
            description=description,
            skill_path=skill_path,
            file_path=file_path,
            input_params=input_params,
            output_params=output_params,
            skill_type=skill_type,
            language=language,
            command=command,
            icon_path=icon_path,
            version="1.0.0",
        )
        count += 1

    return count


def init_dag_skills_to_database() -> int:
    count = _process_skill_dirs(SKILLS_DIR, "skills")
    count += _process_skill_dirs(GENERATED_SKILLS_DIR, "skills/generated")
    count += _process_skill_dirs(DAG_SYSTEM_NODE_DIR, "dag_system_node")
    return count
