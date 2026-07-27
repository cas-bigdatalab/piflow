from __future__ import annotations

from contextlib import closing
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from database.postgres import get_connection


DATASPACE_TYPE_CODE = "dataspace"


def initialize_datasource_catalog_schema() -> None:
    with closing(get_connection()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS piflow_datasource_type (
                        id BIGSERIAL PRIMARY KEY,
                        type_code TEXT NOT NULL UNIQUE,
                        type_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        logo TEXT NOT NULL DEFAULT '',
                        enabled BOOLEAN NOT NULL DEFAULT TRUE,
                        sort_order INTEGER NOT NULL DEFAULT 0,
                        capabilities_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                        init_fields_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                        extra_meta_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_piflow_datasource_type_enabled_sort
                    ON piflow_datasource_type(enabled, sort_order)
                    """
                )
                _seed_builtin_dataspace_type(cursor)


def list_datasource_types() -> list[dict[str, Any]]:
    initialize_datasource_catalog_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    type_code,
                    type_name,
                    category,
                    description,
                    logo,
                    enabled,
                    sort_order,
                    capabilities_json,
                    init_fields_json,
                    extra_meta_json,
                    created_at,
                    updated_at
                FROM piflow_datasource_type
                ORDER BY sort_order ASC, created_at ASC
                """
            )
            return list(cursor.fetchall())


def get_datasource_type_by_code(type_code: str) -> dict[str, Any] | None:
    initialize_datasource_catalog_schema()
    with closing(get_connection()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    type_code,
                    type_name,
                    category,
                    description,
                    logo,
                    enabled,
                    sort_order,
                    capabilities_json,
                    init_fields_json,
                    extra_meta_json,
                    created_at,
                    updated_at
                FROM piflow_datasource_type
                WHERE type_code = %s
                """,
                (type_code,),
            )
            return cursor.fetchone()


def _seed_builtin_dataspace_type(cursor) -> None:
    init_fields = [
        {
            "name": "base_url",
            "label": "服务地址",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入 Dataspace 服务地址",
            "secret": False,
            "options": [],
            "description": "Dataspace 开放接口服务地址",
        },
        {
            "name": "app_id",
            "label": "应用ID",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入应用ID",
            "secret": False,
            "options": [],
            "description": "Dataspace 开放接口应用ID",
        },
        {
            "name": "auth_code",
            "label": "授权码",
            "type": "password",
            "required": True,
            "default": "",
            "placeholder": "请输入授权码",
            "secret": True,
            "options": [],
            "description": "Dataspace 开放接口授权码",
        },
        {
            "name": "space_name",
            "label": "数据空间名称",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入数据空间名称",
            "secret": False,
            "options": [],
            "description": "系统将根据空间名称自动解析 space_id",
        },
        {
            "name": "ftp_user",
            "label": "FTP用户名",
            "type": "string",
            "required": True,
            "default": "",
            "placeholder": "请输入FTP用户名",
            "secret": False,
            "options": [],
            "description": "用于访问 Dataspace FTP 目录",
        },
        {
            "name": "ftp_password",
            "label": "FTP密码",
            "type": "password",
            "required": True,
            "default": "",
            "placeholder": "请输入FTP密码",
            "secret": True,
            "options": [],
            "description": "用于访问 Dataspace FTP 目录",
        },
        {
            "name": "logo",
            "label": "Logo",
            "type": "string",
            "required": False,
            "default": "",
            "placeholder": "可选，未填写时默认使用空间Logo",
            "secret": False,
            "options": [],
            "description": "可选的 Base64 Logo 字符串",
        },
    ]
    capabilities = ["list", "download", "upload"]
    extra_meta = {
        "builtin": True,
        "instance_api_prefix": "/dataspace/source",
        "supports_validation": True,
    }

    cursor.execute(
        """
        INSERT INTO piflow_datasource_type (
            type_code,
            type_name,
            category,
            description,
            logo,
            enabled,
            sort_order,
            capabilities_json,
            init_fields_json,
            extra_meta_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (type_code) DO UPDATE SET
            type_name = EXCLUDED.type_name,
            category = EXCLUDED.category,
            description = EXCLUDED.description,
            logo = EXCLUDED.logo,
            enabled = EXCLUDED.enabled,
            sort_order = EXCLUDED.sort_order,
            capabilities_json = EXCLUDED.capabilities_json,
            init_fields_json = EXCLUDED.init_fields_json,
            extra_meta_json = EXCLUDED.extra_meta_json,
            updated_at = now()
        """,
        (
            DATASPACE_TYPE_CODE,
            "DataSpace",
            "file",
            "Dataspace 数据空间类型，用于访问空间目录并进行文件下载与上传。",
            "",
            True,
            1,
            Json(capabilities),
            Json(init_fields),
            Json(extra_meta),
        ),
    )
