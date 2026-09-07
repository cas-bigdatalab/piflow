import json
import uuid
from contextlib import closing
from typing import List, Optional, Dict

import psycopg2
from psycopg2.extras import RealDictCursor
from database.postgres import get_connection
from runtime.skill_manage import init_dag_skills_to_database
from schemas.dag.dag_edge_schema import DagEdge
from schemas.dag.dag_node_input_param import DagNodeInputParamSet, DagNodeReferenceParam, DagNodeManualParam
from schemas.dag.dag_node_schema import DagNode
from schemas.dag.dag_obs import DagObs
from schemas.dag.dag_param_binding_schema import DagParamBinding
from schemas.dag.dag_skill_schema import DagSkill
from schemas.dag.dag_task_schema import DagTask


def init_dag_db():
    conn = get_connection()
    cursor = conn.cursor()

    ddl_statements = [
        # dag_task
        """
        CREATE TABLE IF NOT EXISTS dag_task (
            id BIGSERIAL PRIMARY KEY,
            dag_task_id VARCHAR(128) NOT NULL,
            dag_task_name VARCHAR(255) NOT NULL,
            message_id VARCHAR(128),
            description TEXT,
            create_user_id VARCHAR(128) NOT NULL, 
            is_deleted INT NOT NULL DEFAULT 0,
            dag_task_type INT NOT NULL DEFAULT 0,
            create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_task_task_id ON dag_task(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_task_message_id ON dag_task(message_id)",

        # dag_definition 用来存前端给的画板DSL Json
        """
        CREATE TABLE IF NOT EXISTS dag_definition (
            id BIGSERIAL PRIMARY KEY,
            definition_id VARCHAR(128) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            revision INT NOT NULL DEFAULT 1,
            dsl_version VARCHAR(32) NOT NULL DEFAULT '1.0',
            definition_json JSONB NOT NULL,
            create_user_id VARCHAR(128) NOT NULL,
            is_current SMALLINT NOT NULL DEFAULT 1,
            create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_definition_definition_id ON dag_definition(definition_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_definition_task_id ON dag_definition(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_definition_revision ON dag_definition(dag_task_id, revision)",
        "CREATE INDEX IF NOT EXISTS idx_dag_definition_current ON dag_definition(dag_task_id, is_current)",
        "CREATE INDEX IF NOT EXISTS idx_dag_definition_user ON dag_definition(create_user_id)",

        # Deprecated: legacy execution-node tracking. New DAG runs use
        # piflow_stop_job_run managed by piflow-python.
        """
        CREATE TABLE IF NOT EXISTS dag_execution_node (
            id BIGSERIAL PRIMARY KEY,
            execution_node_id VARCHAR(128) NOT NULL,
            execution_id VARCHAR(128) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            node_id VARCHAR(128) NOT NULL,
            node_name VARCHAR(255) NOT NULL,
            skill_id VARCHAR(128),
            status VARCHAR(32) NOT NULL,
            input_snapshot JSONB,
            output_snapshot JSONB,
            error_message TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_dag_execution_node_execution_node_id
        ON dag_execution_node(execution_node_id);
        
        CREATE INDEX IF NOT EXISTS
        idx_dag_execution_node_execution_id
        ON dag_execution_node(execution_id);
        
        CREATE INDEX IF NOT EXISTS
        idx_dag_execution_node_task_id
        ON dag_execution_node(dag_task_id);
        
        CREATE INDEX IF NOT EXISTS
        idx_dag_execution_node_node_id
        ON dag_execution_node(node_id);
        
        CREATE INDEX IF NOT EXISTS
        idx_dag_execution_node_status
        ON dag_execution_node(status);
        """


        # Deprecated: legacy task execution history. New DAG runs use
        # piflow_flow_run managed by piflow-python.
        """
        CREATE TABLE IF NOT EXISTS dag_task_execution_history (
            id BIGSERIAL PRIMARY KEY,
            execution_id VARCHAR(128) NOT NULL,
            execution_name VARCHAR(255) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            dag_task_name VARCHAR(255) NOT NULL,
            status VARCHAR(32) NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_task_execution_execution_id ON dag_task_execution_history(execution_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_task_execution_task_id ON dag_task_execution_history(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_task_execution_status ON dag_task_execution_history(status)",

        # dag_skills
        """
        CREATE TABLE IF NOT EXISTS dag_skills (
            id BIGSERIAL PRIMARY KEY,
            skill_id VARCHAR(128) NOT NULL,
            skill_name VARCHAR(255) NOT NULL,
            name_zh TEXT,
            description TEXT,
            skill_path TEXT,
            file_path TEXT,
            input_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            output_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            skill_type VARCHAR(128),
            language VARCHAR(64),
            command TEXT,
            icon_path TEXT,
            version VARCHAR(64),
            disciplinary_field VARCHAR(255),
            publisher VARCHAR(32) NOT NULL DEFAULT 'PRIVATE',
            create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted INT NOT NULL DEFAULT 0
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_skills_skill_id ON dag_skills(skill_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_skill_name ON dag_skills(skill_name)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_skill_type ON dag_skills(skill_type)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_language ON dag_skills(language)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_skills_name_version ON dag_skills(skill_name, version)",

        # user
        """
        CREATE TABLE IF NOT EXISTS sys_user (
            id BIGSERIAL PRIMARY KEY,
            
            user_id VARCHAR(64) NOT NULL UNIQUE,
            
            username VARCHAR(128) NOT NULL UNIQUE,
            
            password_hash VARCHAR(255) NOT NULL,
            
            nickname VARCHAR(128),
            
            is_admin SMALLINT NOT NULL DEFAULT 0,
            
            is_deleted SMALLINT NOT NULL DEFAULT 0,
            
            create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_sys_user_user_id ON sys_user(user_id)",
    ]

    for ddl in ddl_statements:
        cursor.execute(ddl)

    # init_schedule_tables(cursor)

    # 执行数据库迁移
    migrate_dag_skills(cursor)

    conn.commit()
    cursor.close()
    conn.close()

def migrate_dag_skills(cursor):
    """
    对 dag_skills 表进行增量迁移。
    可重复执行，不会影响已迁移的数据库。
    """

    # 新增 disciplinary_field
    cursor.execute("""
        ALTER TABLE dag_skills
        ADD COLUMN IF NOT EXISTS disciplinary_field VARCHAR(255);
    """)

    # 新增 publisher
    cursor.execute("""
        ALTER TABLE dag_skills
        ADD COLUMN IF NOT EXISTS publisher VARCHAR(32)
        NOT NULL DEFAULT 'PRIVATE';
    """)

    # （可选）确保 publisher 默认值正确
    cursor.execute("""
        ALTER TABLE dag_skills
        ALTER COLUMN publisher SET DEFAULT 'PRIVATE';
    """)

def insert_dag_task(
    dag_task_name: str,
    message_id: str = None,
    description: str = None,
    create_user_id: str = None,
    dag_task_type: int = 0,
):
    dag_task_id = uuid.uuid4().hex

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO dag_task (
                            dag_task_id, dag_task_name, message_id,
                            description, create_user_id, dag_task_type
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, dag_task_id
                        """,
                        (dag_task_id, dag_task_name, message_id, description, create_user_id, dag_task_type),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {"id": row[0], "dag_task_id": row[1]}
    except Exception as e:
        raise RuntimeError("insert_dag_task failed") from e

# 画板记录新增
def insert_dag_definition(
    conn,
    dag_task_id: str,
    create_user_id: str,
    revision: int = 1,
    definition_json: dict = None,
):
    definition_id = uuid.uuid4().hex

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dag_definition(
                    definition_id,
                    dag_task_id,
                    revision,
                    definition_json,
                    create_user_id,
                    is_current
                )
                VALUES(%s, %s, %s,  %s::jsonb, %s, 1)
                """,
                (definition_id, dag_task_id, revision,  psycopg2.extras.Json(definition_json), create_user_id,),
            )
            return definition_id
    except Exception as e:
        raise RuntimeError("insert_dag_definition failed") from e

def _parse_input_params_from_db(raw: Optional[dict]) -> DagNodeInputParamSet:
    param_set = DagNodeInputParamSet()
    if raw is None:
        return param_set
    items = raw.get("input_params") or []
    for item in items:
        if item.get("value_mode") == "reference":
            param_set.add_param(DagNodeReferenceParam(
                param_name=item["param_name"],
                binding_id=item["binding_id"],
            ))
        else:
            param_set.add_param(DagNodeManualParam(
                param_name=item["param_name"],
                param_type=item.get("param_type", "String"),
                param_value=item.get("param_value", ""),
                value_source=item.get("value_source", "local_file"),
            ))
    return param_set

def get_dag_task(dag_task_id: str) -> Optional[DagTask]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, dag_task_id, dag_task_name, message_id,
                           description, create_user_id, is_deleted,
                           dag_task_type, create_time, update_time
                    FROM dag_task
                    WHERE dag_task_id = %s AND is_deleted = 0
                    """,
                    (dag_task_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return DagTask(
                    dag_task_id=row["dag_task_id"],
                    dag_task_name=row["dag_task_name"],
                    message_id=row.get("message_id"),
                    description=row.get("description"),
                    create_user_id=row.get("create_user_id"),
                    db_id=row["id"],
                    is_deleted=row["is_deleted"],
                    dag_task_type=row.get("dag_task_type", 0),
                    create_time=row.get("create_time"),
                    update_time=row.get("update_time"),
                )
    except Exception as e:
        raise RuntimeError("get_dag_task failed") from e

def list_dag_tasks(
    create_user_id: str,
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
) -> dict:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                conditions = ["is_deleted = 0", "create_user_id = %s"]
                params = [create_user_id]

                if keyword:
                    conditions.append("dag_task_name LIKE %s")
                    params.append(f"%{keyword}%")

                where = " AND ".join(conditions)

                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM dag_task WHERE {where}",
                    params,
                )
                total = cursor.fetchone()["total"]

                offset = (page - 1) * page_size
                cursor.execute(
                    f"""
                    SELECT id, dag_task_id, dag_task_name, message_id,
                           description, create_user_id, is_deleted,
                           dag_task_type, create_time, update_time
                    FROM dag_task
                    WHERE {where}
                    ORDER BY update_time DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [page_size, offset],
                )
                rows = cursor.fetchall()

                tasks = [
                    DagTask(
                        dag_task_id=row["dag_task_id"],
                        dag_task_name=row["dag_task_name"],
                        message_id=row.get("message_id"),
                        description=row.get("description"),
                        # create_user_id=row.get("create_user_id"),
                        db_id=row["id"],
                        # is_deleted=row["is_deleted"],
                        dag_task_type=row.get("dag_task_type", 0),
                        create_time=row.get("create_time"),
                        update_time=row.get("update_time"),
                    )
                    for row in rows
                ]

                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": tasks,
                }
    except Exception as e:
        raise RuntimeError("list_dag_tasks failed") from e

def get_dag_skill(skill_id: str) -> Optional[DagSkill]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, skill_id, skill_name, name_zh, description, skill_path, file_path,
                           input_params, output_params, skill_type,
                           language, command, icon_path, version,
                           disciplinary_field, publisher,
                           create_time, update_time, is_deleted
                    FROM dag_skills
                    WHERE skill_id = %s AND (publisher = 'COMMUNITY' OR is_deleted = 0)
                    """,
                    (skill_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return DagSkill(
                    skill_id=row["skill_id"],
                    skill_name=row["skill_name"],
                    name_zh=row.get("name_zh"),
                    version=row.get("version", "1.0.0"),
                    description=row.get("description"),
                    skill_path=row.get("skill_path"),
                    file_path=row.get("file_path"),
                    input_params=row.get("input_params"),
                    output_params=row.get("output_params"),
                    skill_type=row.get("skill_type"),
                    language=row.get("language"),
                    command=row.get("command"),
                    icon_path=row.get("icon_path"),
                    disciplinary_field=row.get("disciplinary_field"),
                    publisher=row.get("publisher"),
                    db_id=row["id"],
                    create_time=row.get("create_time"),
                    update_time=row.get("update_time"),
                    is_deleted=row["is_deleted"],
                )
    except Exception as e:
        raise RuntimeError("get_dag_skill failed") from e

def list_dag_skills(
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
    skill_type: str = None,
    version: str = None,
) -> dict:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                conditions = ["is_deleted = 0"]
                params = []

                if keyword:
                    conditions.append("skill_name LIKE %s")
                    params.append(f"%{keyword}%")

                if skill_type:
                    conditions.append("skill_type = %s")
                    params.append(skill_type)

                if version:
                    conditions.append("version = %s")
                    params.append(version)

                where = " AND ".join(conditions)

                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM dag_skills WHERE {where}",
                    params,
                )
                total = cursor.fetchone()["total"]

                offset = (page - 1) * page_size
                cursor.execute(
                    f"""
                    SELECT id, skill_id, skill_name, name_zh, description, skill_path, file_path,
                           input_params, output_params, skill_type,
                           language, command, icon_path, version,
                           disciplinary_field, publisher,
                           create_time, update_time, is_deleted
                    FROM dag_skills
                    WHERE {where}
                    ORDER BY skill_name
                    LIMIT %s OFFSET %s
                    """,
                    params + [page_size, offset],
                )
                rows = cursor.fetchall()

                skills = [
                    DagSkill(
                        skill_id=row["skill_id"],
                        skill_name=row["skill_name"],
                        name_zh=row.get("name_zh"),
                        version=row.get("version", "1.0.0"),
                        description=row.get("description"),
                        skill_path=row.get("skill_path"),
                        file_path=row.get("file_path"),
                        input_params=row.get("input_params"),
                        output_params=row.get("output_params"),
                        skill_type=row.get("skill_type"),
                        language=row.get("language"),
                        command=row.get("command"),
                        icon_path=row.get("icon_path"),
                        disciplinary_field=row.get("disciplinary_field"),
                        publisher=row.get("publisher"),
                        db_id=row["id"],
                        create_time=row.get("create_time"),
                        update_time=row.get("update_time"),
                        is_deleted=row["is_deleted"],
                    )
                    for row in rows
                ]

                return {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "data": skills,
                }
    except Exception as e:
        raise RuntimeError("list_dag_skills failed") from e


def list_dag_skills_by_type(
    page: int = None,
    page_size: int = None,
    keyword: str = None,
    skill_type: str = None,
    version: str = None,
    disciplinary_field: str = None,
    publisher: str = None,
) -> dict:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                conditions = ["(publisher = 'COMMUNITY' OR is_deleted = 0)"]
                params = []

                if keyword:
                    conditions.append("(skill_name LIKE %s OR name_zh LIKE %s)")
                    params.append(f"%{keyword}%")
                    params.append(f"%{keyword}%")

                if skill_type:
                    conditions.append("skill_type = %s")
                    params.append(skill_type)

                if version:
                    conditions.append("version = %s")
                    params.append(version)

                if disciplinary_field:
                    conditions.append("disciplinary_field = %s")
                    params.append(disciplinary_field)

                if publisher:
                    conditions.append("publisher = %s")
                    params.append(publisher)

                where = " AND ".join(conditions)

                cursor.execute(
                    f"SELECT COUNT(*) AS total FROM dag_skills WHERE {where}",
                    params,
                )
                total = cursor.fetchone()["total"]

                if page is not None and page_size is not None:
                    offset = (page - 1) * page_size
                    cursor.execute(
                        f"""
                        SELECT id, skill_id, skill_name, name_zh, description, skill_path, file_path,
                               input_params, output_params, skill_type,
                               language, command, icon_path, version,
                               disciplinary_field, publisher,
                               create_time, update_time, is_deleted
                        FROM dag_skills
                        WHERE {where}
                        ORDER BY skill_type, skill_name
                        LIMIT %s OFFSET %s
                        """,
                        params + [page_size, offset],
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT id, skill_id, skill_name, name_zh, description, skill_path, file_path,
                               input_params, output_params, skill_type,
                               language, command, icon_path, version,
                               disciplinary_field, publisher,
                               create_time, update_time, is_deleted
                        FROM dag_skills
                        WHERE {where}
                        ORDER BY skill_type, skill_name
                        """,
                        params,
                    )
                rows = cursor.fetchall()

                groups = {}
                for row in rows:
                    st = row["skill_type"] or "未分类"
                    if st not in groups:
                        groups[st] = []
                    groups[st].append(
                        DagSkill(
                            skill_id=row["skill_id"],
                            skill_name=row["skill_name"],
                            name_zh=row.get("name_zh"),
                            version=row.get("version", "1.0.0"),
                            description=row.get("description"),
                            skill_path=row.get("skill_path"),
                            file_path=row.get("file_path"),
                            input_params=row.get("input_params"),
                            output_params=row.get("output_params"),
                            skill_type=row["skill_type"],
                            language=row.get("language"),
                            command=row.get("command"),
                            icon_path=row.get("icon_path"),
                            disciplinary_field=row.get("disciplinary_field"),
                            publisher=row.get("publisher"),
                            db_id=row["id"],
                            create_time=row.get("create_time"),
                            update_time=row.get("update_time"),
                            is_deleted=row["is_deleted"],
                        )
                    )

                group_list = sorted(
                    [
                        {"groupName": t, "DagSkillInfoList": skills}
                        for t, skills in groups.items()
                    ],
                    key=lambda g: len(g["DagSkillInfoList"]),
                    reverse=True,
                )

                result = {
                    "total": total,
                    "data": group_list,
                }
                if page is not None and page_size is not None:
                    result["page"] = page
                    result["page_size"] = page_size
                return result
    except Exception as e:
        raise RuntimeError("list_dag_skills_by_type failed") from e


# 创建或更新任务信息
def create_or_update_task(
    conn,
    task: Dict,
    create_user_id: str,
) -> str:

    dag_task_id = task.get("dag_task_id")

    dag_task_name = task.get("dag_task_name")
    description = task.get("description")
    message_id = task.get("message_id")

    with conn.cursor(
            cursor_factory=RealDictCursor
    ) as cursor:

        # task不存在 → 新建
        if not dag_task_id:

            dag_task_id = uuid.uuid4().hex

            cursor.execute(
                """
                INSERT INTO dag_task(
                    dag_task_id,
                    dag_task_name,
                    message_id,
                    description,
                    create_user_id
                )
                VALUES(
                    %s,%s,%s,%s,%s
                )
                """,
                (
                    dag_task_id,
                    dag_task_name,
                    message_id,
                    description,
                    create_user_id,
                )
            )

            return dag_task_id

        # 查询task是否存在
        cursor.execute(
            """
            SELECT id
            FROM dag_task
            WHERE dag_task_id=%s
            AND create_user_id=%s
            AND is_deleted=0
            """,
            (
                dag_task_id,
                create_user_id,
            )
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"task not found: {dag_task_id}"
            )

        # 更新任务信息
        cursor.execute(
            """
            UPDATE dag_task
            SET
                dag_task_name=%s,
                description=%s,
                message_id=%s,
                update_time=CURRENT_TIMESTAMP
            WHERE
                dag_task_id=%s
            """,
            (
                dag_task_name,
                description,
                message_id,
                dag_task_id,
            )
        )

        return dag_task_id

# 获取画板下一个版本号
def get_next_revision(
    conn,
    dag_task_id: str,
    create_user_id: str,
) -> int:

    with conn.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                COALESCE(MAX(revision),0)
            FROM dag_definition
            WHERE
                dag_task_id=%s
            AND
                create_user_id=%s
            """,
            (
                dag_task_id,
                create_user_id,
            )
        )

        row = cursor.fetchone()

        current_revision = row[0]

        return current_revision + 1

# 画板旧版本失效
def disable_current_definition(
    conn,
    dag_task_id: str,
    create_user_id: str,
):

    with conn.cursor() as cursor:

        cursor.execute(
            """
            UPDATE dag_definition
            SET
                is_current=0
            WHERE
                dag_task_id=%s
            AND
                create_user_id=%s
            AND
                is_current=1
            """,
            (
                dag_task_id,
                create_user_id,
            )
        )


def delete_dag_task(
    conn,
    dag_task_id: str,
    create_user_id: str,
):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE dag_task
            SET
                is_deleted=1,
                update_time=CURRENT_TIMESTAMP
            WHERE
                dag_task_id=%s
            AND
                create_user_id=%s
            AND
                is_deleted=0
            """,
            (
                dag_task_id,
                create_user_id,
            )
        )
        if cursor.rowcount == 0:
            raise ValueError(f"task not found or already deleted: {dag_task_id}")

# 根据用户id与任务id查询DSL Json
def get_dag_definition_json(create_user_id: str, dag_task_id: str):
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT definition_json
                    FROM dag_definition
                    WHERE dag_task_id = %s AND create_user_id = %s AND is_current = 1
                    """,
                    (dag_task_id, create_user_id),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return row["definition_json"]
    except Exception as e:
        raise RuntimeError("get_dag_definition_json failed") from e

def get_dag_task_id_by_message_id(message_id: str) -> Optional[str]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT dag_task_id
                    FROM dag_task
                    WHERE message_id = %s AND is_deleted = 0
                    """,
                    (message_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return row["dag_task_id"]
    except Exception as e:
        raise RuntimeError("get_dag_task_id_by_message_id failed") from e

def get_skill_type_counts() -> list:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT skill_type, COUNT(*) AS count
                    FROM dag_skills
                    WHERE is_deleted = 0
                    GROUP BY skill_type
                    ORDER BY count desc
                    """,
                )
                rows = cursor.fetchall()
                return [
                    {
                        "type": row["skill_type"] or "未分类",
                        "count": row["count"],
                    }
                    for row in rows
                ]
    except Exception as e:
        raise RuntimeError("get_skill_type_counts failed") from e

if __name__ == '__main__':
    try:
        init_dag_db()
        init_dag_skills_to_database()
        print("DAG database initialized successfully.")
    except Exception as e:
        print(f"Error initializing DAG database: {str(e)}")
