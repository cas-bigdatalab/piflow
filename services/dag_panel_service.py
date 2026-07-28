import json
import logging
import shutil
import zipfile
from contextlib import closing
from typing import Dict, List
from pathlib import Path

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection
from infra.config_loader import resolve_workspace_root
from runtime.dag_manager import list_dag_tasks, create_or_update_task, get_next_revision, disable_current_definition, \
    insert_dag_definition, get_dag_definition_json, get_dag_skill, list_dag_skills, delete_dag_task, list_dag_skills_by_type, \
    get_dag_task_id_by_message_id
from runtime.skill_manage import (
    init_skill_to_database,
)
from schemas.dag.dag_skill_schema import DagSkill

log = logging.getLogger("flow.dag_panel")

WORKSPACE_ROOT = resolve_workspace_root()
SKILLS_DIR = WORKSPACE_ROOT / "skills"
GENERATED_SKILLS_DIR = SKILLS_DIR / "generated"
TEMP_COMMUNITY_SKILLS_DIR = WORKSPACE_ROOT / "temp_community_skills"


def get_user_dag_tasks(
    create_user_id: str,
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
) -> dict:
    result = list_dag_tasks(
        create_user_id=create_user_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    return result


def save_dag_panel(
    definition_json:dict,
    create_user_id:str
):

    task=definition_json["task"]

    with closing(get_connection()) as conn:
        with conn:

            task_id=create_or_update_task(
                conn,
                task,
                create_user_id
            )

            revision=get_next_revision(
                conn,
                task_id,
                create_user_id
            )

            disable_current_definition(
                conn,
                task_id,
                create_user_id
            )

            definition_id=insert_dag_definition(
                conn,
                task_id,
                create_user_id,
                revision,
                definition_json,
            )

            return {
                "task_id":task_id,
                "definition_id":definition_id,
                "revision":revision
            }

def get_panel_dag_json(create_user_id: str, dag_task_id: str) -> dict:
    result = get_dag_definition_json(create_user_id, dag_task_id)
    return result


def get_dag_json_by_message_id(create_user_id: str, message_id: str):
    dag_task_id = get_dag_task_id_by_message_id(message_id)
    if dag_task_id is None:
        return None
    return get_dag_definition_json(create_user_id, dag_task_id)

def get_skill_info_by_id(skill_id:str)->DagSkill:
    result = get_dag_skill(skill_id)
    return result


def _build_file_tree(dir_path: Path) -> dict:
    name = dir_path.name
    if dir_path.is_file():
        return {"name": name, "type": "file"}
    children = []
    for child in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name)):
        children.append(_build_file_tree(child))
    return {"name": name, "type": "directory", "children": children}


def get_skill_info_detail(skill_id: str, with_skill_json: bool = False, with_file_tree: bool = False) -> dict:
    skill = get_dag_skill(skill_id)
    if skill is None:
        return {"success": False, "message": f"skill not found: {skill_id}"}

    result = skill.__dict__

    if with_skill_json and skill.skill_path:
        skill_json_path = WORKSPACE_ROOT / skill.skill_path / "skill.json"
        if skill_json_path.exists():
            result["skill_json"] = json.loads(skill_json_path.read_text(encoding="utf-8"))

    if with_file_tree and skill.skill_path:
        skill_dir = WORKSPACE_ROOT / skill.skill_path
        if skill_dir.exists() and skill_dir.is_dir():
            result["file_tree"] = _build_file_tree(skill_dir)

    return {"success": True, "data": result}

def get_dag_skills_by_condition(
    page: int = None,
    page_size: int = None,
    keyword: str = None,
    skill_type: str = None,
    version: str = None,
    disciplinary_field: str = None,
    publisher: str = None,
) -> dict:
    result = list_dag_skills_by_type(
        page=page,
        page_size=page_size,
        keyword=keyword,
        skill_type=skill_type,
        version=version,
        disciplinary_field=disciplinary_field,
        publisher=publisher,
    )
    return result


def create_dag_task(
    create_user_id: str,
    description: str = None,
    message_id: str = None,
    task_name: str = None,
) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            task = {
                "dag_task_name": task_name,
                "description": description,
                "message_id": message_id,
            }
            dag_task_id = create_or_update_task(
                conn,
                task,
                create_user_id
            )
            return {"dag_task_id" : dag_task_id}


def update_dag_task(
    create_user_id: str,
    dag_name: str = None,
    dag_task_id: str = None,
    description: str = None,
    message_id: str = None,
) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            task = {
                "dag_task_id": dag_task_id,
                "dag_task_name": dag_name,
                "description": description,
                "message_id": message_id,
            }
            create_or_update_task(
                conn,
                task,
                create_user_id
            )
            return {}


def remove_dag_task(
    create_user_id: str,
    dag_task_id: str = None,
) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            delete_dag_task(
                conn,
                dag_task_id,
                create_user_id
            )
            return {}


def remove_local_skill(skill_id: str) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT skill_id, skill_name, version, publisher
                    FROM dag_skills
                    WHERE skill_id = %s AND is_deleted = 0
                    """,
                    (skill_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return {
                        "success": False,
                        "message": f"skill not found: {skill_id}",
                    }

                skill_name = row["skill_name"]
                version = row["version"]
                publisher = row["publisher"]

                cursor.execute(
                    """
                    UPDATE dag_skills
                    SET is_deleted = 1, update_time = CURRENT_TIMESTAMP
                    WHERE skill_id = %s AND is_deleted = 0
                    """,
                    (skill_id,),
                )

    if publisher == "PRIVATE":
        generated_dir = GENERATED_SKILLS_DIR / skill_name
        if generated_dir.exists() and generated_dir.is_dir():
            shutil.rmtree(generated_dir)
        else:
            fallback_dir = SKILLS_DIR / skill_name
            if fallback_dir.exists() and fallback_dir.is_dir():
                shutil.rmtree(fallback_dir)
    elif publisher == "COMMUNITY":
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists() and skill_dir.is_dir():
            dest = TEMP_COMMUNITY_SKILLS_DIR / skill_name
            TEMP_COMMUNITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(skill_dir), str(dest))

    return {
        "success": True,
        "skill_name": skill_name,
        "version": version,
        "publisher": publisher,
    }


def enable_local_skill(skill_id: str) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT skill_id, skill_name, version, publisher
                    FROM dag_skills
                    WHERE skill_id = %s AND is_deleted = 1
                    """,
                    (skill_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return {
                        "success": False,
                        "message": f"skill not found or already enabled: {skill_id}",
                    }

                skill_name = row["skill_name"]
                version = row["version"]
                publisher = row["publisher"]

                if publisher != "COMMUNITY":
                    return {
                        "success": False,
                        "message": f"only COMMUNITY skills can be enabled, current publisher: {publisher}",
                    }

                cursor.execute(
                    """
                    UPDATE dag_skills
                    SET is_deleted = 0, update_time = CURRENT_TIMESTAMP
                    WHERE skill_id = %s AND is_deleted = 1
                    """,
                    (skill_id,),
                )

    temp_dir = TEMP_COMMUNITY_SKILLS_DIR / skill_name
    if temp_dir.exists() and temp_dir.is_dir():
        dest = SKILLS_DIR / skill_name
        shutil.move(str(temp_dir), str(dest))

    return {
        "success": True,
        "skill_name": skill_name,
        "version": version,
    }


def download_skill_package(skill_id: str) -> dict:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT skill_name, version, skill_path, publisher
                    FROM dag_skills
                    WHERE skill_id = %s AND is_deleted = 0
                    """,
                    (skill_id,),
                )
                row = cursor.fetchone()

                if not row:
                    return {"success": False, "message": f"skill not found: {skill_id}"}

                skill_name = row["skill_name"]
                version = row["version"]
                skill_path = row["skill_path"]

    zip_name = f"{skill_name}_{version}.zip"
    zip_path = TEMP_COMMUNITY_SKILLS_DIR / zip_name

    if zip_path.exists():
        return {"success": True, "zip_path": str(zip_path), "filename": zip_name}

    skill_dir = WORKSPACE_ROOT / skill_path
    if not skill_dir.exists() or not skill_dir.is_dir():
        return {"success": False, "message": f"skill directory not found: {skill_dir}"}

    TEMP_COMMUNITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_stem = TEMP_COMMUNITY_SKILLS_DIR / f"{skill_name}_{version}"
    shutil.make_archive(str(zip_stem), "zip", str(skill_dir.parent), skill_dir.name)

    if not zip_path.exists():
        return {"success": False, "message": "failed to create zip package"}

    return {"success": True, "zip_path": str(zip_path), "filename": zip_name}


def upload_skill_package(file_bytes: bytes, filename: str) -> dict:
    TEMP_COMMUNITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_COMMUNITY_SKILLS_DIR / filename
    zip_path.write_bytes(file_bytes)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            has_skill_md = any(n.endswith("SKILL.md") for n in names)
            has_skill_json = any(n.endswith("skill.json") for n in names)

            if not has_skill_md or not has_skill_json:
                return {
                    "success": False,
                    "message": "zip must contain both SKILL.md and skill.json",
                }

            skill_json_name = next(n for n in names if n.endswith("skill.json"))
            skill_json_data = json.loads(zf.read(skill_json_name))
            skill_name = skill_json_data.get("name", "")
            version = skill_json_data.get("version", "1.0.0")

            if not skill_name:
                return {
                    "success": False,
                    "message": "skill.json missing 'name' field",
                }

            top_levels = set()
            for n in names:
                parts = n.split("/")
                if parts[0]:
                    top_levels.add(parts[0])

            has_folder_structure = len(top_levels) == 1 and skill_name in top_levels
            has_flat_structure = "SKILL.md" in names and "skill.json" in names

            if not has_folder_structure and not has_flat_structure:
                return {
                    "success": False,
                    "message": "zip structure must be either <skill_name>/SKILL.md or SKILL.md at root",
                }

            target_dir = GENERATED_SKILLS_DIR / skill_name
            if target_dir.exists():
                return {
                    "success": False,
                    "message": f"skill directory already exists: {skill_name}",
                }

            if has_flat_structure:
                target_dir.mkdir(parents=True, exist_ok=True)
                zf.extractall(target_dir)
            else:
                zf.extractall(GENERATED_SKILLS_DIR)
    except zipfile.BadZipFile as e:
        return {
            "success": False,
            "message": f"invalid zip file: {e}",
        }
    except Exception as e:
        log.exception("upload_skill_package failed: %s", filename)
        return {
            "success": False,
            "message": f"failed to process zip: {e}",
        }
    finally:
        if zip_path.exists():
            zip_path.unlink()

    result = init_skill_to_database(target_dir, version, path_prefix="skills/generated", publisher="PRIVATE")
    if not result:
        return {
            "success": False,
            "message": "failed to parse SKILL.md or init skill to database",
        }

    return {
        "success": True,
        "skill_name": skill_name,
        "version": version,
        "skill_id": result["skill_id"],
    }