import uuid

from contextlib import closing

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def get_user_by_username(username: str):
    with closing(get_connection()) as conn:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    username,
                    password_hash,
                    nickname,
                    is_admin
                FROM sys_user
                WHERE username = %s
                  AND is_deleted = 0
                """,
                (username,),
            )

            return cursor.fetchone()


def insert_user(
    username: str,
    password_hash: str,
    nickname: str | None = None,
):
    user_id = uuid.uuid4().hex

    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                cursor.execute(
                    """
                    INSERT INTO sys_user (
                        user_id,
                        username,
                        password_hash,
                        nickname
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id
                    """,
                    (
                        user_id,
                        username,
                        password_hash,
                        nickname,
                    ),
                )

                return cursor.fetchone()