"""PostgreSQL repository for chemical node persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from psycopg2.extras import Json, RealDictCursor

from database.postgres import get_connection


CHEMICAL_NODE_TABLE = "chemical_nodes"
CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE = "chemical_node_software_instances"


@dataclass(frozen=True)
class ChemicalNodeRecord:
    name: str
    ip: str
    port: int
    software: tuple[str, ...]
    cpu_cores: float | None = None
    memory_gb: float | None = None
    free_disk_gb: float | None = None
    hostname: str = ""
    status: str = "unknown"
    error_message: str = ""
    last_refreshed_at: str | None = None
    software_instances: dict[str, int] | None = None


def ensure_schema(connection=None) -> None:
    conn = connection or get_connection()
    should_close = connection is None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {CHEMICAL_NODE_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    ip TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    software JSONB NOT NULL DEFAULT '[]'::jsonb,
                    cpu_cores DOUBLE PRECISION,
                    memory_gb DOUBLE PRECISION,
                    free_disk_gb DOUBLE PRECISION,
                    hostname TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'unknown',
                    error_message TEXT NOT NULL DEFAULT '',
                    last_refreshed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    node_name TEXT NOT NULL REFERENCES {CHEMICAL_NODE_TABLE}(name) ON DELETE CASCADE,
                    software TEXT NOT NULL,
                    running_count INTEGER NOT NULL DEFAULT 0 CHECK (running_count >= 0),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (node_name, software)
                )
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE}_node_name
                ON {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE}(node_name)
                """
            )
    finally:
        if should_close:
            conn.commit()
            conn.close()


def sync_config_nodes(connection, nodes: Iterable[dict[str, Any]]) -> None:
    with connection.cursor() as cursor:
        for node in nodes:
            cursor.execute(
                f"""
                INSERT INTO {CHEMICAL_NODE_TABLE} (
                    name, ip, port, software, updated_at
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
                """,
                (
                    node["name"],
                    node["ip"],
                    node["port"],
                    Json(list(node["software"])),
                ),
            )


def ensure_software_instances(connection, nodes: Iterable[dict[str, Any]]) -> None:
    with connection.cursor() as cursor:
        for node in nodes:
            node_name = node["name"]
            for software in node["software"]:
                cursor.execute(
                    f"""
                    INSERT INTO {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE} (
                        node_name, software, running_count, updated_at
                    )
                    VALUES (%s, %s, 0, CURRENT_TIMESTAMP)
                    ON CONFLICT (node_name, software) DO NOTHING
                    """,
                    (node_name, str(software)),
                )


def fetch_node_records(connection) -> list[dict[str, Any]]:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT
                n.name,
                n.ip,
                n.port,
                n.software,
                n.cpu_cores,
                n.memory_gb,
                n.free_disk_gb,
                n.hostname,
                n.status,
                n.error_message,
                n.last_refreshed_at,
                COALESCE(
                    jsonb_object_agg(s.software, s.running_count) FILTER (WHERE s.software IS NOT NULL),
                    '{{}}'::jsonb
                ) AS software_instances
            FROM {CHEMICAL_NODE_TABLE} n
            LEFT JOIN {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE} s
              ON s.node_name = n.name
            GROUP BY
                n.id, n.name, n.ip, n.port, n.software, n.cpu_cores, n.memory_gb,
                n.free_disk_gb, n.hostname, n.status, n.error_message, n.last_refreshed_at
            ORDER BY n.name
            """
        )
        return list(cursor.fetchall())


def fetch_node_record(connection, node_name: str) -> dict[str, Any] | None:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT
                n.name,
                n.ip,
                n.port,
                n.software,
                n.cpu_cores,
                n.memory_gb,
                n.free_disk_gb,
                n.hostname,
                n.status,
                n.error_message,
                n.last_refreshed_at,
                COALESCE(
                    jsonb_object_agg(s.software, s.running_count) FILTER (WHERE s.software IS NOT NULL),
                    '{{}}'::jsonb
                ) AS software_instances
            FROM {CHEMICAL_NODE_TABLE} n
            LEFT JOIN {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE} s
              ON s.node_name = n.name
            WHERE n.name = %s
            GROUP BY
                n.id, n.name, n.ip, n.port, n.software, n.cpu_cores, n.memory_gb,
                n.free_disk_gb, n.hostname, n.status, n.error_message, n.last_refreshed_at
            LIMIT 1
            """,
            (node_name,),
        )
        return cursor.fetchone()


def update_node_resource(
    connection,
    *,
    node_name: str,
    cpu_cores: float | None,
    memory_gb: float | None,
    free_disk_gb: float | None,
    hostname: str,
    status: str,
    error_message: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {CHEMICAL_NODE_TABLE}
            SET cpu_cores = %s,
                memory_gb = %s,
                free_disk_gb = %s,
                hostname = %s,
                status = %s,
                error_message = %s,
                last_refreshed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE name = %s
            """,
            (
                cpu_cores,
                memory_gb,
                free_disk_gb,
                hostname,
                status,
                error_message,
                node_name,
            ),
        )


def has_software(connection, *, node_name: str, software: str) -> bool:
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT software
            FROM {CHEMICAL_NODE_TABLE}
            WHERE name = %s
            """,
            (node_name,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(f"chemical node not found: {node_name}")
        node_software = _decode_software_list(row.get("software"))
        return str(software).strip() in node_software


def set_running_count(connection, *, node_name: str, software: str, count: int) -> None:
    if count < 0:
        raise ValueError("software instance count must not be negative")
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE}
            SET running_count = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE node_name = %s
              AND software = %s
            """,
            (count, node_name, software),
        )
        if cursor.rowcount == 0:
            raise KeyError(f"software '{software}' is not configured on node '{node_name}'")


def change_running_count(connection, *, node_name: str, software: str, delta: int) -> None:
    if delta == 0:
        return
    with connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            UPDATE {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE}
            SET running_count = running_count + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE node_name = %s
              AND software = %s
              AND running_count + %s >= 0
            RETURNING running_count
            """,
            (delta, node_name, software, delta),
        )
        row = cursor.fetchone()
        if row is None:
            with connection.cursor(cursor_factory=RealDictCursor) as check_cursor:
                check_cursor.execute(
                    f"""
                    SELECT running_count
                    FROM {CHEMICAL_NODE_SOFTWARE_INSTANCE_TABLE}
                    WHERE node_name = %s
                      AND software = %s
                    """,
                    (node_name, software),
                )
                existing = check_cursor.fetchone()
            if existing is None:
                raise KeyError(f"software '{software}' is not configured on node '{node_name}'")
            raise ValueError("software instance count must not be negative")


def _decode_software_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        parsed = json.loads(value)
    else:
        parsed = value
    if isinstance(parsed, (list, tuple)):
        return tuple(str(item) for item in parsed)
    raise TypeError("software field must decode to a sequence")
