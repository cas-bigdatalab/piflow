from contextlib import closing

import psycopg2
from psycopg2._json import Json
from psycopg2.extras import RealDictCursor

from database.postgres import get_connection
from enums.workflow_template_enums import TemplatePublisher


def init_workflow_template_db():
    conn = get_connection()
    cursor = conn.cursor()

    ddl_statements = [
    # workflow_template 表
        """
        CREATE TABLE IF NOT EXISTS workflow_template (
            id BIGSERIAL PRIMARY KEY,
            template_id VARCHAR(128) UNIQUE NOT NULL,
            template_name VARCHAR(256) NOT NULL,
            description TEXT,
            template_json JSONB,
            disciplinary_field VARCHAR(128),
            publisher VARCHAR(128),
            tags JSONB,
            author_id VARCHAR(128),
            author_name VARCHAR(128),
            version VARCHAR(32) NOT NULL,
            is_deleted INT NOT NULL DEFAULT 0,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_template_id ON workflow_template (template_id)",
        "CREATE INDEX IF NOT EXISTS idx_template_name ON workflow_template (template_name)",
        "CREATE INDEX IF NOT EXISTS idx_template_disciplinary_field ON workflow_template (disciplinary_field)",
    ]

    for ddl in ddl_statements:
        cursor.execute(ddl)

    conn.commit()
    cursor.close()
    conn.close()

def insert_workflow_template(
        user_id: str,
        user_name: str,
        template_name: str,
        description: str,
        template_json: dict,
        disciplinary_field: str,
        publisher: str,
        tags: list,
        version: str = "1.0.0",
):
    if template_name == "" or template_name is None or user_id == "" or user_id is None:
        raise ValueError("template_name and user_id is required")
    template_id = f"{template_name}_{version}_{user_id}"
    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor() as cursor:
                    insert_query = """
                        INSERT INTO workflow_template (
                            template_id, template_name, description, template_json, disciplinary_field,
                            publisher, tags, author_id, author_name, version
                        ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                        
                        ON CONFLICT (template_id) 
                        
                        DO UPDATE SET
                            template_name = EXCLUDED.template_name,
                            description = EXCLUDED.description,
                            template_json = EXCLUDED.template_json,
                            disciplinary_field = EXCLUDED.disciplinary_field,
                            tags = EXCLUDED.tags,
                            author_name = EXCLUDED.author_name,
                            version = EXCLUDED.version,
                            update_time = CURRENT_TIMESTAMP,
                            is_deleted = 0
                        RETURNING id, template_id
                    """
                    cursor.execute(
                        insert_query,
                        (
                            template_id,
                            template_name,
                            description,
                            psycopg2.extras.Json(template_json),
                            disciplinary_field,
                            publisher,
                            Json(tags),
                            user_id,
                            user_name,
                            version,
                        ),
                    )
                    row = cursor.fetchone()

                    if not row:
                        return None

                    return {
                        "id": row[0],
                        "template_id": row[1],
                    }
    except Exception as e:
        raise RuntimeError("insert_workflow_template failed") from e

def list_workflow_template_by_condition(
        page: int= None,
        page_size: int= None,
        keyword: str= None,
        version: str= None,
        disciplinary_field: str= None,
        publisher: str= None,
        tags: list= None,
        user_name: str= None,
        user_id: str= None,
        is_get_json: bool= False
) -> dict:
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                conditions = []
                params = []

                conditions.append(
                    "(publisher IN (%s, %s) OR (publisher = %s AND author_id = %s AND is_deleted = 0))"
                )
                params.extend([
                    TemplatePublisher.OFFICIAL_COMMUNITY.value,
                    TemplatePublisher.ORG_SHARED.value,
                    TemplatePublisher.PERSONAL.value,
                    user_id,
                ])

                if keyword:
                    conditions.append("(template_name LIKE %s)")
                    params.append(f"%{keyword}%")

                if version:
                    conditions.append("(version = %s)")
                    params.append(version)

                if disciplinary_field:
                    conditions.append("(disciplinary_field = %s)")
                    params.append(disciplinary_field)

                if publisher:
                    conditions.append("(publisher = %s)")
                    params.append(publisher)

                if tags:
                    conditions.append("(tags ?& %s)")
                    params.append(tags)

                if user_name:
                    conditions.append("(author_name = %s)")
                    params.append(user_name)

                if user_id:
                    conditions.append("(author_id = %s)")
                    params.append(user_id)

                where = " AND ".join(conditions)

                columns = (
                    "id, template_id, template_name, description, disciplinary_field, "
                    "publisher, tags, author_id, author_name, version, is_deleted, create_time, update_time"
                )
                if is_get_json:
                    columns += ", template_json"

                get_total_sql = "SELECT COUNT(*) as total FROM workflow_template"
                get_sql = f"SELECT {columns} FROM workflow_template"
                if conditions:
                    get_total_sql += f" WHERE {where}"
                    get_sql += f" WHERE {where}"

                cursor.execute(get_total_sql, params)
                total = cursor.fetchone()["total"]

                order_sql = f"ORDER BY disciplinary_field asc"
                sql = f"{get_sql} {order_sql}"
                if page is not None and page_size is not None:
                    offset = (page - 1) * page_size
                    sql += " LIMIT %s OFFSET %s "
                    cursor.execute(sql, params + [page_size, offset])
                else:
                    cursor.execute(sql, params)
                rows = cursor.fetchall()

                group = {}
                for row in rows:
                    field = row["disciplinary_field"] or "基础"
                    if field not in group:
                        group[field] = []
                    group[field].append(row)

                group_list = sorted(
                    [
                        {"disciplinary_field": field, "templateList": templates}
                        for field, templates in group.items()
                    ],
                    key=lambda g: len(g["templateList"]),
                    reverse=True
                )

                result = {
                    "total": total,
                    "data": group_list
                }

                if page is not None and page_size is not None:
                    result["page"] = page
                    result["page_size"] = page_size
                return result
    except Exception as e:
        raise RuntimeError("list_workflow_template_by_condition failed") from e

def get_workflow_template_by_template_id(template_id: str, user_id: str = None) -> dict:
    if template_id == "" or template_id is None:
        return {}
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = (
                    "SELECT * FROM workflow_template "
                    "WHERE template_id = %s "
                    "AND (publisher IN (%s, %s) OR (publisher = %s AND author_id = %s AND is_deleted = 0))"
                )
                cursor.execute(
                    sql,
                    (
                        template_id,
                        TemplatePublisher.OFFICIAL_COMMUNITY.value,
                        TemplatePublisher.ORG_SHARED.value,
                        TemplatePublisher.PERSONAL.value,
                        user_id,
                    ),
                )
                row = cursor.fetchone()
                return row
    except Exception as e:
        raise RuntimeError("get_workflow_template_by_template_id failed") from e

def get_workflow_field_count(user_id: str = None):
    try:
        with closing(get_connection()) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT disciplinary_field, COUNT(*) AS count
                    FROM workflow_template
                    WHERE (publisher IN (%s, %s) OR (publisher = %s AND author_id = %s AND is_deleted = 0))
                    GROUP BY disciplinary_field
                    ORDER BY count DESC
                """, (
                    TemplatePublisher.OFFICIAL_COMMUNITY.value,
                    TemplatePublisher.ORG_SHARED.value,
                    TemplatePublisher.PERSONAL.value,
                    user_id,
                ))
                rows = cursor.fetchall()
                return [
                    {
                        "disciplinary_field": row["disciplinary_field"] or "基础",
                        "count": row["count"]
                    }
                    for row in rows
                ]
    except Exception as e:
        raise RuntimeError("get_workflow_field_count failed") from e

def delete_workflow_template_by_template_id(template_id: str, user_id) -> bool:
    if template_id == "" or template_id is None or user_id == "" or user_id is None:
        return False
    try:
        with closing(get_connection()) as conn:
            with conn.cursor() as cursor:
                sql = (
                    "UPDATE workflow_template "
                    "SET is_deleted = 1, update_time = CURRENT_TIMESTAMP "
                    "WHERE template_id = %s AND (publisher IN (%s, %s) OR (publisher = %s AND author_id = %s))"
                )
                cursor.execute(sql, (
                    template_id,
                    TemplatePublisher.OFFICIAL_COMMUNITY.value,
                    TemplatePublisher.ORG_SHARED.value,
                    TemplatePublisher.PERSONAL.value,
                    user_id,))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        raise RuntimeError("delete_workflow_template_by_template_id failed") from e
