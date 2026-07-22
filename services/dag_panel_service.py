import logging
import shutil
from contextlib import closing
from typing import Dict, List
from pathlib import Path

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection
from infra.config_loader import resolve_workspace_root
from runtime.dag_manager import list_dag_tasks, create_or_update_task, get_next_revision, disable_current_definition, \
    insert_dag_definition, get_dag_definition_json, get_dag_skill, list_dag_skills, delete_dag_task, list_dag_skills_by_type, \
    get_dag_task_id_by_message_id
from schemas.dag.dag_skill_schema import DagSkill

log = logging.getLogger("flow.dag_panel")

WORKSPACE_ROOT = resolve_workspace_root()
SKILLS_DIR = WORKSPACE_ROOT / "skills"
GENERATED_SKILLS_DIR = SKILLS_DIR / "generated"


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
            shutil.rmtree(skill_dir)

    return {
        "success": True,
        "skill_name": skill_name,
        "version": version,
        "publisher": publisher,
    }