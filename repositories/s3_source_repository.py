from __future__ import annotations

import uuid
from contextlib import closing
from typing import Any

from psycopg2.extras import RealDictCursor

from database.postgres import get_connection


def initialize_s3_source_schema() -> None:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS piflow_s3_source (
                        id BIGSERIAL PRIMARY KEY,
                        source_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL DEFAULT '',
                        endpoint TEXT NOT NULL,
                        access_key TEXT NOT NULL,
                        secret_key TEXT NOT NULL,
                        secure BOOLEAN NOT NULL DEFAULT FALSE,
                        bucket TEXT NOT NULL,
                        base_prefix TEXT NOT NULL DEFAULT '',
                        logo TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_piflow_s3_source_bucket
                    ON piflow_s3_source(bucket)
                    """
                )


def insert_s3_source(
    *,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
    base_prefix: str,
    logo: str,
) -> dict[str, Any]:
    initialize_s3_source_schema()
    source_id = uuid.uuid4().hex
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO piflow_s3_source (
                        source_id,
                        name,
                        endpoint,
                        access_key,
                        secret_key,
                        secure,
                        bucket,
                        base_prefix,
                        logo
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        source_id,
                        name,
                        endpoint,
                        access_key,
                        secret_key,
                        secure,
                        bucket,
                        base_prefix,
                        logo,
                        created_at,
                        updated_at
                    """,
                    (
                        source_id,
                        name,
                        endpoint,
                        access_key,
                        secret_key,
                        secure,
                        bucket,
                        base_prefix,
                        logo,
                    ),
                )
                return cursor.fetchone()


def get_s3_source_by_id(source_id: str) -> dict[str, Any] | None:
    initialize_s3_source_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    source_id,
                    name,
                    endpoint,
                    access_key,
                    secret_key,
                    secure,
                    bucket,
                    base_prefix,
                    logo,
                    created_at,
                    updated_at
                FROM piflow_s3_source
                WHERE source_id = %s
                """,
                (source_id,),
            )
            return cursor.fetchone()


def update_s3_source(
    *,
    source_id: str,
    name: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    secure: bool,
    bucket: str,
    base_prefix: str,
    logo: str,
) -> dict[str, Any] | None:
    initialize_s3_source_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE piflow_s3_source
                    SET
                        name = %s,
                        endpoint = %s,
                        access_key = %s,
                        secret_key = %s,
                        secure = %s,
                        bucket = %s,
                        base_prefix = %s,
                        logo = %s,
                        updated_at = now()
                    WHERE source_id = %s
                    RETURNING
                        source_id,
                        name,
                        endpoint,
                        access_key,
                        secret_key,
                        secure,
                        bucket,
                        base_prefix,
                        logo,
                        created_at,
                        updated_at
                    """,
                    (
                        name,
                        endpoint,
                        access_key,
                        secret_key,
                        secure,
                        bucket,
                        base_prefix,
                        logo,
                        source_id,
                    ),
                )
                return cursor.fetchone()


def delete_s3_source(source_id: str) -> bool:
    initialize_s3_source_schema()
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM piflow_s3_source
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )
                return cursor.rowcount > 0


def list_s3_sources() -> list[dict[str, Any]]:
    initialize_s3_source_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    source_id,
                    name,
                    endpoint,
                    access_key,
                    secret_key,
                    secure,
                    bucket,
                    base_prefix,
                    logo,
                    created_at,
                    updated_at
                FROM piflow_s3_source
                ORDER BY created_at DESC
                """
            )
            return list(cursor.fetchall())
