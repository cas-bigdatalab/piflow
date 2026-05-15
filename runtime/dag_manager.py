import json
import uuid
from contextlib import closing
from typing import List, Optional, Dict

import psycopg2
from psycopg2.extras import RealDictCursor
from database.postgres import get_connection
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

        # dag_execution_node 存节点执行记录
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

        # dag_node
        """
        CREATE TABLE IF NOT EXISTS dag_node (
            id BIGSERIAL PRIMARY KEY,
            node_id VARCHAR(128) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            skill_id VARCHAR(128) NOT NULL,
            node_name VARCHAR(255) NOT NULL,
            input_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            node_type VARCHAR(64) NOT NULL DEFAULT 'default',
            position_x DOUBLE PRECISION NOT NULL DEFAULT 0,
            position_y DOUBLE PRECISION NOT NULL DEFAULT 0
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_node_node_id ON dag_node(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_node_task_id ON dag_node(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_node_skill_id ON dag_node(skill_id)",

        # dag_param_binding
        """
        CREATE TABLE IF NOT EXISTS dag_param_binding (
            id BIGSERIAL PRIMARY KEY,
            binding_id VARCHAR(128) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            from_node_id VARCHAR(128) NOT NULL,
            from_param_name VARCHAR(255) NOT NULL,
            to_node_id VARCHAR(128) NOT NULL,
            to_param_name VARCHAR(255) NOT NULL
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_param_binding_binding_id ON dag_param_binding(binding_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_param_binding_task_id ON dag_param_binding(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_param_binding_from_node ON dag_param_binding(from_node_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_param_binding_to_node ON dag_param_binding(to_node_id)",

        # dag_edge
        """
        CREATE TABLE IF NOT EXISTS dag_edge (
            id BIGSERIAL PRIMARY KEY,
            edge_id VARCHAR(128) NOT NULL,
            dag_task_id VARCHAR(128) NOT NULL,
            from_node_id VARCHAR(128) NOT NULL,
            to_node_id VARCHAR(128) NOT NULL,
            from_port VARCHAR(128),
            to_port VARCHAR(128)
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_edge_edge_id ON dag_edge(edge_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_edge_task_id ON dag_edge(dag_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_edge_from_node ON dag_edge(from_node_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_edge_to_node ON dag_edge(to_node_id)",

        # dag_task_execution_history
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
            description TEXT,
            file_path TEXT NOT NULL,
            input_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            output_params JSONB NOT NULL DEFAULT '{}'::jsonb,
            skill_type VARCHAR(128),
            language VARCHAR(64) NOT NULL,
            command TEXT NOT NULL,
            icon_path TEXT,
            version VARCHAR(64),
            create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_deleted INT NOT NULL DEFAULT 0
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_dag_skills_skill_id ON dag_skills(skill_id)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_skill_name ON dag_skills(skill_name)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_skill_type ON dag_skills(skill_type)",
        "CREATE INDEX IF NOT EXISTS idx_dag_skills_language ON dag_skills(language)",

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

    conn.commit()
    cursor.close()
    conn.close()


def insert_dag_skill(
    skill_name: str,
    description: str,
    file_path: str,
    input_params: dict,
    output_params: dict,
    skill_type: str,
    language: str,
    command: str,
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
                            skill_id, skill_name, description, file_path,
                            input_params, output_params, skill_type,
                            language, command, icon_path, version
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s)
                        RETURNING id, skill_id
                        """,
                        (
                            skill_id, skill_name, description, file_path,
                            psycopg2.extras.Json(input_params),
                            psycopg2.extras.Json(output_params),
                            skill_type, language, command, icon_path, version,
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


def insert_dag_node(
    dag_task_id: str,
    skill_id: str,
    node_name: str,
    input_params: dict = None,
    node_type: str = "default",
    position_x: float = 0,
    position_y: float = 0,
):
    node_id = uuid.uuid4().hex

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO dag_node (
                            node_id, dag_task_id, skill_id, node_name,
                            input_params, node_type, position_x, position_y
                        )
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                        RETURNING id, node_id
                        """,
                        (
                            node_id, dag_task_id, skill_id, node_name,
                            psycopg2.extras.Json(input_params),
                            node_type, position_x, position_y,
                        ),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {"id": row[0], "node_id": row[1]}
    except Exception as e:
        raise RuntimeError("insert_dag_node failed") from e


def update_dag_node(
    node_id: str,
    dag_task_id: str = None,
    skill_id: str = None,
    node_name: str = None,
    input_params: dict = None,
    node_type: str = None,
    position_x: float = None,
    position_y: float = None,
):
    updates = []
    set_clauses = []
    params = []

    if dag_task_id is not None:
        updates.append((
            "dag_task_id = %s",
            dag_task_id,
        ))

    if skill_id is not None:
        updates.append((
            "skill_id = %s",
            skill_id,
        ))

    if node_name is not None:
        updates.append((
            "node_name = %s",
            node_name,
        ))

    if input_params is not None:
        updates.append((
            "input_params = %s::jsonb",
            psycopg2.extras.Json(input_params),
        ))

    if node_type is not None:
        updates.append((
            "node_type = %s",
            node_type,
        ))

    if position_x is not None:
        updates.append((
            "position_x = %s",
            position_x,
        ))

    if position_y is not None:
        updates.append((
            "position_y = %s",
            position_y,
        ))

    set_clauses = [x[0] for x in updates]
    params = [x[1] for x in updates]

    if not set_clauses:
        return None

    params.append(node_id)

    sql = f"""
        UPDATE dag_node
        SET {', '.join(set_clauses)}
        WHERE node_id = %s
        """

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.rowcount > 0
    except Exception as e:
        raise RuntimeError("update_dag_node failed") from e


def insert_dag_param_binding(
    dag_task_id: str,
    from_node_id: str,
    from_param_name: str,
    to_node_id: str,
    to_param_name: str,
):
    binding_id = uuid.uuid4().hex

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO dag_param_binding (
                            binding_id, dag_task_id,
                            from_node_id, from_param_name,
                            to_node_id, to_param_name
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, binding_id
                        """,
                        (binding_id, dag_task_id, from_node_id, from_param_name, to_node_id, to_param_name),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {"id": row[0], "binding_id": row[1]}
    except Exception as e:
        raise RuntimeError("insert_dag_param_binding failed") from e


def insert_dag_edge(
    dag_task_id: str,
    from_node_id: str,
    to_node_id: str,
    from_port: str = None,
    to_port: str = None,
):
    edge_id = uuid.uuid4().hex

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO dag_edge (
                            edge_id, dag_task_id,
                            from_node_id, to_node_id,
                            from_port, to_port
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, edge_id
                        """,
                        (edge_id, dag_task_id, from_node_id, to_node_id, from_port, to_port),
                    )
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {"id": row[0], "edge_id": row[1]}
    except Exception as e:
        raise RuntimeError("insert_dag_edge failed") from e

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
                    SELECT id, skill_id, skill_name, description, file_path,
                           input_params, output_params, skill_type,
                           language, command, icon_path, version,
                           create_time, update_time, is_deleted
                    FROM dag_skills
                    WHERE skill_id = %s AND is_deleted = 0
                    """,
                    (skill_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return DagSkill(
                    skill_id=row["skill_id"],
                    skill_name=row["skill_name"],
                    version=row.get("version", "1.0.0"),
                    description=row.get("description"),
                    file_path=row.get("file_path"),
                    input_params=row.get("input_params"),
                    output_params=row.get("output_params"),
                    skill_type=row.get("skill_type"),
                    language=row.get("language"),
                    command=row.get("command"),
                    icon_path=row.get("icon_path"),
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
                    SELECT id, skill_id, skill_name, description, file_path,
                           input_params, output_params, skill_type,
                           language, command, icon_path, version,
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
                        version=row.get("version", "1.0.0"),
                        description=row.get("description"),
                        file_path=row.get("file_path"),
                        input_params=row.get("input_params"),
                        output_params=row.get("output_params"),
                        skill_type=row.get("skill_type"),
                        language=row.get("language"),
                        command=row.get("command"),
                        icon_path=row.get("icon_path"),
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


def get_dag_node_by_node_id(node_id: str) -> Optional[DagNode]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT n.id, n.node_id, n.dag_task_id, n.skill_id, n.node_name,
                           n.input_params AS node_input, n.node_type, n.position_x, n.position_y,
                           s.skill_name, s.version, s.description,
                           s.file_path, s.input_params AS skill_input, s.output_params,
                           s.skill_type, s.language, s.command, s.icon_path,
                           s.create_time AS skill_create_time,
                           s.update_time AS skill_update_time,
                           s.is_deleted AS skill_is_deleted
                    FROM dag_node n
                    LEFT JOIN dag_skills s ON n.skill_id = s.skill_id AND s.is_deleted = 0
                    WHERE n.node_id = %s
                    """,
                    (node_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                skill = DagSkill(
                    skill_id=row["skill_id"],
                    skill_name=row.get("skill_name") or row["skill_id"],
                    version=row.get("version", "1.0.0"),
                    description=row.get("description"),
                    file_path=row.get("file_path"),
                    input_params=row.get("skill_input"),
                    output_params=row.get("output_params"),
                    skill_type=row.get("skill_type"),
                    language=row.get("language"),
                    command=row.get("command"),
                    icon_path=row.get("icon_path"),
                ) if row.get("skill_name") else None

                return DagNode(
                    node_id=row["node_id"],
                    node_name=row["node_name"],
                    skill_id=row["skill_id"],
                    node_type=row["node_type"],
                    position_x=row["position_x"],
                    position_y=row["position_y"],
                    input_params=_parse_input_params_from_db(row.get("node_input")),
                    skill=skill,
                    db_id=row["id"],
                    dag_task_id=row["dag_task_id"],
                    update_time=row.get("update_time"),
                )
    except Exception as e:
        raise RuntimeError("get_dag_node_by_node_id failed") from e

def get_dag_nodes_by_task_id(dag_task_id: str) -> List[DagNode]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT n.id, n.node_id, n.dag_task_id, n.skill_id, n.node_name,
                           n.input_params AS node_input, n.node_type, n.position_x, n.position_y,
                           s.skill_name, s.version, s.description,
                           s.file_path, s.input_params AS skill_input, s.output_params,
                           s.skill_type, s.language, s.command, s.icon_path,
                           s.create_time AS skill_create_time,
                           s.update_time AS skill_update_time,
                           s.is_deleted AS skill_is_deleted
                    FROM dag_node n
                    LEFT JOIN dag_skills s ON n.skill_id = s.skill_id AND s.is_deleted = 0
                    WHERE n.dag_task_id = %s
                    ORDER BY n.id
                    """,
                    (dag_task_id,),
                )
                rows = cursor.fetchall()

                nodes = []
                for row in rows:
                    skill = DagSkill(
                        skill_id=row["skill_id"],
                        skill_name=row.get("skill_name") or row["skill_id"],
                        version=row.get("version", "1.0.0"),
                        description=row.get("description"),
                        file_path=row.get("file_path"),
                        input_params=row.get("skill_input"),
                        output_params=row.get("output_params"),
                        skill_type=row.get("skill_type"),
                        language=row.get("language"),
                        command=row.get("command"),
                        icon_path=row.get("icon_path"),
                    ) if row.get("skill_name") else None

                    nodes.append(DagNode(
                        node_id=row["node_id"],
                        node_name=row["node_name"],
                        skill_id=row["skill_id"],
                        node_type=row["node_type"],
                        position_x=row["position_x"],
                        position_y=row["position_y"],
                        input_params=_parse_input_params_from_db(row.get("node_input")),
                        skill=skill,
                        db_id=row["id"],
                        dag_task_id=row["dag_task_id"],
                        update_time=row.get("update_time"),
                    ))
                return nodes
    except Exception as e:
        raise RuntimeError("get_dag_nodes_by_task_id failed") from e

def get_dag_edge_by_edge_id(edge_id: str) -> Optional[DagEdge]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, edge_id, dag_task_id,
                           from_node_id, to_node_id, from_port, to_port
                    FROM dag_edge
                    WHERE edge_id = %s
                    """,
                    (edge_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return DagEdge(
                    edge_id=row["edge_id"],
                    from_node_id=row["from_node_id"],
                    to_node_id=row["to_node_id"],
                    from_port=row.get("from_port"),
                    to_port=row.get("to_port"),
                    db_id=row["id"],
                    dag_task_id=row["dag_task_id"],
                )
    except Exception as e:
        raise RuntimeError("get_dag_edge_by_edge_id failed") from e

def get_dag_edges_by_task_id(dag_task_id: str) -> List[DagEdge]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, edge_id, dag_task_id,
                           from_node_id, to_node_id, from_port, to_port
                    FROM dag_edge
                    WHERE dag_task_id = %s
                    ORDER BY id
                    """,
                    (dag_task_id,),
                )
                rows = cursor.fetchall()
                return [
                    DagEdge(
                        edge_id=row["edge_id"],
                        from_node_id=row["from_node_id"],
                        to_node_id=row["to_node_id"],
                        from_port=row.get("from_port"),
                        to_port=row.get("to_port"),
                        db_id=row["id"],
                        dag_task_id=row["dag_task_id"],
                    )
                    for row in rows
                ]
    except Exception as e:
        raise RuntimeError("get_dag_edges_by_task_id failed") from e

def get_dag_param_binding_by_binding_id(binding_id: str) -> Optional[DagParamBinding]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, binding_id, dag_task_id,
                           from_node_id, from_param_name,
                           to_node_id, to_param_name, create_time
                    FROM dag_param_binding
                    WHERE binding_id = %s
                    """,
                    (binding_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return DagParamBinding(
                    binding_id=row["binding_id"],
                    from_node_id=row["from_node_id"],
                    from_param_name=row["from_param_name"],
                    to_node_id=row["to_node_id"],
                    to_param_name=row["to_param_name"],
                    db_id=row["id"],
                    dag_task_id=row["dag_task_id"],
                    create_time=row.get("create_time"),
                )
    except Exception as e:
        raise RuntimeError("get_dag_param_binding_by_binding_id failed") from e

def get_dag_bindings_by_task_id(dag_task_id: str) -> List[DagParamBinding]:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, binding_id, dag_task_id,
                           from_node_id, from_param_name,
                           to_node_id, to_param_name, create_time
                    FROM dag_param_binding
                    WHERE dag_task_id = %s
                    ORDER BY id
                    """,
                    (dag_task_id,),
                )
                rows = cursor.fetchall()
                return [
                    DagParamBinding(
                        binding_id=row["binding_id"],
                        from_node_id=row["from_node_id"],
                        from_param_name=row["from_param_name"],
                        to_node_id=row["to_node_id"],
                        to_param_name=row["to_param_name"],
                        db_id=row["id"],
                        dag_task_id=row["dag_task_id"],
                        create_time=row.get("create_time"),
                    )
                    for row in rows
                ]
    except Exception as e:
        raise RuntimeError("get_dag_bindings_by_task_id failed") from e

def generate_dag_json(dag_task_id: str) -> dict:
    """
    根据 dag_task_id 查询相关的节点、边和参数绑定，生成 DAG 的 JSON 表示。
    """

    # 首先查询task信息
    dag_task = get_dag_task(dag_task_id)

    # 根据 task_id 查询所有节点
    dag_nodes = get_dag_nodes_by_task_id(dag_task_id)

    # 根据 task_id 查询所有边
    dag_edges = get_dag_edges_by_task_id(dag_task_id)

    # 根据 task_id 查询所有参数绑定
    dag_bindings = get_dag_bindings_by_task_id(dag_task_id)

    # 生成 DAG JSON
    dag_json = DagObs(task=dag_task,nodes=dag_nodes,edges=dag_edges,bindings=dag_bindings).to_json()
    print("生成的 DAG JSON:", json.dumps(dag_json, ensure_ascii=False, indent=2))

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

            task_id = uuid.uuid4().hex

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

            return task_id

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

# def test_insert_skills():
#     insert_dag_skill(
#         "DC1_Blank_Line_Clean",
#         "本skill用于读取结构化数据文件，删除其中所有列为空的行（空行），然后输出为相同格式的文件。",
#         "workspace/skills/DC1_Blank_Line_Clean/scripts/DC1_Blank_Line_Clean.py",
#         {"params": [
#             {
#                 "name": "input",
#                 "type": "String",
#                 "description": "需要清洗文件的路径",
#                 "required": True
#             },
#             {
#                 "name": "output",
#                 "type": "String",
#                 "description": "清洗后文件的输出路径",
#                 "required": True
#             }
#         ]},
#         {"params": [
#             {
#                 "name": "output",
#                 "type": "String",
#                 "description": "清洗后文件的输出路径",
#                 "required": True
#             }
#         ]},
#         skill_type="清洗",
#         language="Python",
#         command="python DC1_Blank_Line_Clean.py --input <输入文件路径> --output <输出文件路径>",
#         icon_path="storage/skills/DC1_Blank_Line_Clean.png",
#         version="1.0.0",
#     )
#
#     insert_dag_skill(
#         "DC2_SpaceCleaning",
#         "本skill用于读取结构化数据文件，检查所有字符串类型（object类型）字段，删除字段值前后多余的空格，然后输出为相同格式的文件。",
#         "workspace/skills/DC2_SpaceCleaning/scripts/DC2_SpaceCleaning.py",
#         {"params": [
#             {
#                 "name": "input_path",
#                 "type": "String",
#                 "description": "输入文件路径（需要清理的文件）",
#                 "required": True
#             },
#             {
#                 "name": "output_path",
#                 "type": "String",
#                 "description": "输出文件路径（清理后的文件）",
#                 "required": True
#             }
#         ]},
#         {"params": [
#             {
#                 "name": "output_path",
#                 "type": "String",
#                 "description": "输出文件路径（清理后的文件）",
#                 "required": True
#             }
#         ]},
#         skill_type="清洗",
#         language="Python",
#         command="python DC2_SpaceCleaning.py --input_path <输入文件路径> --output_path <输出文件路径>",
#         icon_path="storage/skills/DC2_SpaceCleaning.png",
#         version="1.0.0",
#     )
#
# def test_insert_task():
#     insert_dag_task(
#         dag_task_name="csv空行、空格清洗任务",
#         message_id="test_message_id_123",
#         description="对csv文件的空行和字段值前后空格进行清洗",
#         create_user_id="test_user_id",
#     )
#
# # 模拟创建节点，连线,填写参数，绑定参数的全过程
# def test_insert_node_edge_and_binding():
#     dag_task_id = "b3691c8a124d4c619a77904f7422465e"
#
#     # 先创建节点
#     # 节点1的参数：全部手动填写
#     node1_params = DagNodeInputParamSet()
#     node1_params.add_param(DagNodeManualParam("input", "String", "workspace/temp/森林每木调查数据-blank-line-space.csv","local_file"))
#     node1_params.add_param(DagNodeManualParam("output", "String", "workspace/outputs/森林每木调查数据-blank-space.csv","local_file"))
#
#     node1_info = insert_dag_node(
#         dag_task_id=dag_task_id,
#         skill_id="5b80cadba9c44ac0b7fe0c136291d0e4",
#         node_name="空行清洗节点",
#         input_params=node1_params.to_json_dict(),
#         node_type="default",
#         position_x=100,
#         position_y=200,
#     )
#
#     # 节点2的参数：一个引用（临时占位），一个手动填写
#     node2_params = DagNodeInputParamSet()
#     node2_params.add_param(DagNodeReferenceParam("input_path", ""))
#     node2_params.add_param(DagNodeManualParam("output_path", "String", "workspace/outputs/森林每木调查数据-clean.csv","local_file"))
#
#     node2_info = insert_dag_node(
#         dag_task_id=dag_task_id,
#         skill_id="485ecf9d51814566a1b8ab93423ce3c8",
#         node_name="空格清洗节点",
#         input_params=node2_params.to_json_dict(),
#         node_type="default",
#         position_x=400,
#         position_y=200,
#     )
#
#     edge_info = insert_dag_edge(
#         dag_task_id=dag_task_id,
#         from_node_id=node1_info["node_id"],
#         to_node_id=node2_info["node_id"]
#     )
#
#     # 创建参数绑定关系
#     binding_info = insert_dag_param_binding(
#         dag_task_id=dag_task_id,
#         from_node_id=node1_info["node_id"],
#         from_param_name="output",
#         to_node_id=node2_info["node_id"],
#         to_param_name="input_path",
#     )
#
#     # 更新节点2的 binding_id 为真实值
#     node2_update_params = DagNodeInputParamSet()
#     node2_update_params.add_param(DagNodeReferenceParam("input_path", binding_info["binding_id"]))
#     node2_update_params.add_param(DagNodeManualParam("output_path", "String", "workspace/outputs/森林每木调查数据-clean.csv","local_file"))
#
#     update_dag_node(
#         node_id=node2_info["node_id"],
#         input_params=node2_update_params.to_json_dict(),
#     )
#
# test_task_id = "b3691c8a124d4c619a77904f7422465e"
#
# def test_get_dag_task():
#     task = get_dag_task(test_task_id)
#     print(task.to_json() if task else "Task not found")
#
# def test_get_dag_skill():
#     skill = get_dag_skill("5b80cadba9c44ac0b7fe0c136291d0e4")
#     print(skill.to_json() if skill else "Skill not found")
#
# def test_get_dag_node_by_node_id():
#     node1 = get_dag_node_by_node_id("ce210222c87f45908f53f96e51837c0f")
#     print(node1.to_json() if node1 else "Node1 not found")
#
#     node2 = get_dag_node_by_node_id("e40864c715e84cebb1c6aa240141a659")
#     print(node2.to_json() if node2 else "Node2 not found")
#
# def test_get_dag_node_by_task_id():
#     nodes = get_dag_nodes_by_task_id(test_task_id)
#     for node in nodes:
#         print(node.to_json())
#
# def test_get_dag_edge_by_edge_id():
#     edge = get_dag_edge_by_edge_id("30770092489045e0971b278df883b835")
#     print(edge.to_json() if edge else "Edge not found")
#
# def test_get_dag_edges_by_task_id():
#     edges = get_dag_edges_by_task_id(test_task_id)
#     for edge in edges:
#         print(edge.to_json())
#
# def test_get_dag_binding_by_binding_id():
#     binding = get_dag_param_binding_by_binding_id("fb117d7c547b4245be28ace6fd745c7a")
#     print(binding.to_json() if binding else "Binding not found")
#
# def test_get_dag_bindings_by_task_id():
#     bindings = get_dag_bindings_by_task_id(test_task_id)
#     for binding in bindings:
#         print(binding.to_json())
#
# def test_get_dag_json():
#     generate_dag_json(test_task_id)

def test_insert_dag_definition():
    insert_dag_definition(
        dag_task_id="b3691c8a124d4c619a77904f7422465e",
        create_user_id="52d1f9857e2946f8aa9994a4a3f05bb3",
        revision=1,
        definition_json={
  "dsl_version":"1.0",
  "task": {
    "task_id": "b3691c8a124d4c619a77904f7422465e",
    "task_name": "csv空行、空格清洗任务",
    "description": "对csv文件的空行和字段值前后空格进行清洗",
    "message_id": "test_message_id_123"
  },
  "nodes": [
    {
      "node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8",
      "node_name": "空行清洗节点",
      "node_type": "default",
      "skill": {
        "skill_id": "5b80cadba9c44ac0b7fe0c136291d0e4",
        "version": "1.0.0"
      },
      "position": {
        "x": 100.0,
        "y": 200.0
      },
      "input_params": [
        {
          "param_name": "input",
          "value_mode": "manual",
          "param_type": "String",
          "value_source": "local_file",
          "param_value": "workspace/temp/森林每木调查数据-blank-line-space.csv"
        },
        {
          "param_name": "output",
          "value_mode": "manual",
          "param_type": "String",
          "value_source": "local_file",
          "param_value": "workspace/outputs/森林每木调查数据-blank-space.csv"
        }
      ]
    },
    {
      "node_id": "593a473d01ef4f5da0c93db24441a1cc",
      "node_name": "空格清洗节点",
      "node_type": "default",
      "skill": {
        "skill_id": "485ecf9d51814566a1b8ab93423ce3c8",
        "version": "1.0.0"
      },
      "position": {
        "x": 400.0,
        "y": 200.0
      },
      "input_params": [
        {
          "param_name": "input_path",
          "value_mode": "reference",
          "param_type": "String",
          "binding_id": "c3bfd56347804535889f84300c437816"
        },
        {
          "param_name": "output_path",
          "value_mode": "manual",
          "param_type": "String",
          "value_source": "local_file",
          "param_value": "workspace/outputs/森林每木调查数据-clean.csv"
        }
      ]
    }
  ],
  "edges": [
    {
      "edge_id": "e666d658c2614f5085ce112707647965",
      "from_node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8",
      "to_node_id": "593a473d01ef4f5da0c93db24441a1cc",
    }
  ],
  "bindings": [
    {
      "binding_id": "c3bfd56347804535889f84300c437816",
      "from_node_id": "e1f6a960c5454e1b92d7e1bdb2a680e8",
      "from_param_name": "output",
      "to_node_id": "593a473d01ef4f5da0c93db24441a1cc",
      "to_param_name": "input_path"
    }
  ]
},
    )

if __name__ == '__main__':
    try:
        init_dag_db()
        print("DAG database initialized successfully.")
    except Exception as e:
        print(f"Error initializing DAG database: {str(e)}")