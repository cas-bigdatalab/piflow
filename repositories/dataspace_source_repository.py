from __future__ import annotations

import uuid
from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def initialize_dataspace_source_schema() -> None:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS piflow_dataspace_source (
                        id BIGSERIAL PRIMARY KEY,
                        source_id TEXT NOT NULL UNIQUE,
                        base_url TEXT NOT NULL,
                        app_id TEXT NOT NULL,
                        auth_code TEXT NOT NULL,
                        space_name TEXT NOT NULL,
                        space_id TEXT NOT NULL,
                        ftp_user TEXT NOT NULL,
                        ftp_password TEXT NOT NULL,
                        ftp_link TEXT NOT NULL DEFAULT '',
                        webdav_link TEXT NOT NULL DEFAULT '',
                        root_path TEXT NOT NULL DEFAULT '',
                        logo TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_piflow_dataspace_source_space_name
                    ON piflow_dataspace_source(space_name)
                    """
                )


def insert_dataspace_source(
    *,
    base_url: str,
    app_id: str,
    auth_code: str,
    space_name: str,
    space_id: str,
    ftp_user: str,
    ftp_password: str,
    ftp_link: str,
    webdav_link: str,
    root_path: str,
    logo: str,
) -> dict[str, Any]:
    initialize_dataspace_source_schema()
    source_id = uuid.uuid4().hex
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO piflow_dataspace_source (
                        source_id,
                        base_url,
                        app_id,
                        auth_code,
                        space_name,
                        space_id,
                        ftp_user,
                        ftp_password,
                        ftp_link,
                        webdav_link,
                        root_path,
                        logo
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        source_id,
                        base_url,
                        app_id,
                        auth_code,
                        space_name,
                        space_id,
                        ftp_user,
                        ftp_password,
                        ftp_link,
                        webdav_link,
                        root_path,
                        logo,
                        created_at,
                        updated_at
                    """,
                    (
                        source_id,
                        base_url,
                        app_id,
                        auth_code,
                        space_name,
                        space_id,
                        ftp_user,
                        ftp_password,
                        ftp_link,
                        webdav_link,
                        root_path,
                        logo,
                    ),
                )
                return cursor.fetchone()


def get_dataspace_source_by_id(source_id: str) -> dict[str, Any] | None:
    initialize_dataspace_source_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    source_id,
                    base_url,
                    app_id,
                    auth_code,
                    space_name,
                    space_id,
                    ftp_user,
                    ftp_password,
                    ftp_link,
                    webdav_link,
                    root_path,
                    logo,
                    created_at,
                    updated_at
                FROM piflow_dataspace_source
                WHERE source_id = %s
                """,
                (source_id,),
            )
            return cursor.fetchone()


def list_dataspace_sources() -> list[dict[str, Any]]:
    initialize_dataspace_source_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    source_id,
                    base_url,
                    app_id,
                    auth_code,
                    space_name,
                    space_id,
                    ftp_user,
                    ftp_password,
                    ftp_link,
                    webdav_link,
                    root_path,
                    logo,
                    created_at,
                    updated_at
                FROM piflow_dataspace_source
                ORDER BY created_at DESC
                """
            )
            return list(cursor.fetchall())

