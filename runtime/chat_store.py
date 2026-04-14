import os
from typing import List, Dict

import psycopg2
from psycopg2.extras import RealDictCursor

from infra.config_loader import get_settings


def _get_connection():
    settings = get_settings()
    db = settings.database
    return psycopg2.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        dbname=db.name,
        connect_timeout=10,
    )


def create_thread(user_id: str, thread_id: str, title: str = "新对话"):
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT INTO chat_threads (thread_id, user_id, title)
    VALUES (%s, %s, %s)
    ON CONFLICT (thread_id) DO NOTHING
    """,
        (thread_id, user_id, title),
    )

    conn.commit()
    cursor.close()
    conn.close()


def update_thread_time(thread_id: str):
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    UPDATE chat_threads
    SET updated_at = CURRENT_TIMESTAMP
    WHERE thread_id = %s
    """,
        (thread_id,),
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_user_threads(user_id: str):
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        SELECT thread_id, title, updated_at
        FROM chat_threads
        WHERE user_id=%s AND deleted=FALSE
        ORDER BY updated_at DESC
    """,
        (user_id,),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in rows]


def delete_thread(user_id: str, thread_id: str):
    conn = _get_connection()
    cursor = conn.cursor()

    # 只允许删除自己的
    cursor.execute(
        """
        UPDATE chat_threads
        SET deleted = TRUE
        WHERE thread_id = %s AND user_id = %s
    """,
        (thread_id, user_id),
    )

    conn.commit()
    cursor.close()
    conn.close()


def save_message(user_id: str, thread_id: str, role: str, content: str):
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 写消息
    cursor.execute(
        """
        INSERT INTO messages (user_id, thread_id, role, content)
        VALUES (%s, %s, %s, %s)
        RETURNING id, user_id, thread_id, role, content, created_at
        """,
        (user_id, thread_id, role, content),
    )
    row = cursor.fetchone()

    # 🔥 更新会话时间（用于排序）
    cursor.execute(
        """
    UPDATE chat_threads
    SET updated_at = CURRENT_TIMESTAMP
    WHERE thread_id = %s
    """,
        (thread_id,),
    )

    conn.commit()
    cursor.close()
    conn.close()

    return dict(row) if row else None


def get_messages(thread_id: str, limit: int = 50) -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT id, role, content FROM messages WHERE thread_id=%s ORDER BY id ASC LIMIT %s",
        (thread_id, limit),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in rows]


def get_chat_files(thread_id: str) -> List[Dict]:
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        SELECT file_id, user_id, thread_id, message_id, virtual_path, original_filename, created_at
        FROM chat_files
        WHERE thread_id = %s AND deleted = FALSE
        ORDER BY file_id ASC
        """,
        (thread_id,),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in rows]


def search_threads(user_id: str, limit: int = 5) -> List[str]:
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT thread_id
    FROM messages
    WHERE user_id=%s
    GROUP BY thread_id
    ORDER BY MAX(id) DESC
    LIMIT %s
    """,
        (user_id, limit),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [r[0] for r in rows]


def list_threads(user_id: str, limit: int = 20):
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
    SELECT thread_id, title, created_at, updated_at
    FROM chat_threads
    WHERE user_id = %s
    ORDER BY updated_at DESC
    LIMIT %s
    """,
        (user_id, limit),
    )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [dict(r) for r in rows]


def update_thread_title(thread_id: str, title: str):
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    UPDATE chat_threads
    SET title = %s
    WHERE thread_id = %s
    """,
        (title, thread_id),
    )

    conn.commit()
    cursor.close()
    conn.close()


def save_chat_file(
    user_id: str,
    thread_id: str,
    message_id: str,
    virtual_path: str,
    original_filename: str,
):
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        INSERT INTO chat_files (user_id, thread_id, message_id, virtual_path, original_filename)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING file_id, user_id, thread_id, message_id, virtual_path, original_filename, created_at
        """,
        (user_id, thread_id, message_id, virtual_path, original_filename),
    )

    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return dict(row) if row else None


def insert_skill(
    name: str,
    description: str,
    icon_path: str = None,
    type: str = None,
    version: str = "1.0.0",
):
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO skills (name, description, icon_path, type, version)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET
            description = EXCLUDED.description,
            icon_path = EXCLUDED.icon_path,
            type = EXCLUDED.type,
            version = EXCLUDED.version,
            update_time = CURRENT_TIMESTAMP,
            deleted = FALSE
        """,
        (name, description, icon_path, type, version),
    )

    conn.commit()
    cursor.close()
    conn.close()


def delete_skill(name: str):
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE skills
        SET deleted = TRUE, update_time = CURRENT_TIMESTAMP
        WHERE name = %s
        """,
        (name,),
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_skill_by_name(name: str) -> Dict:
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        SELECT id, name, description, icon_path, type, version, update_time
        FROM skills
        WHERE name = %s AND deleted = FALSE
        """,
        (name,),
    )

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return dict(row) if row else None


def list_skills(
    limit: int = 100, offset: int = 0, keyword: str = "", type: str = ""
) -> Dict:
    conn = _get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    conditions = ["deleted = FALSE"]
    params = []

    if keyword:
        conditions.append("(name LIKE %s OR description LIKE %s)")
        keyword_pattern = f"%{keyword}%"
        params.extend([keyword_pattern, keyword_pattern])

    if type:
        conditions.append("type = %s")
        params.append(type)

    where_clause = " AND ".join(conditions)
    params.extend([limit, offset])

    cursor.execute(
        f"""
        SELECT id, name, description, icon_path, type, version, update_time
        FROM skills
        WHERE {where_clause}
        ORDER BY name
        LIMIT %s OFFSET %s
        """,
        params,
    )
    rows = cursor.fetchall()

    count_params = [p for p in params[:-2]]
    cursor.execute(
        f"""
        SELECT COUNT(*) as total
        FROM skills
        WHERE {where_clause}
        """,
        count_params,
    )

    total_row = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        "data": [dict(r) for r in rows],
        "total": total_row["total"] if total_row else 0,
    }
