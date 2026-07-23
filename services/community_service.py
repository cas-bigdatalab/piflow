import logging
import shutil
import zipfile
from contextlib import closing
from pathlib import Path

import requests
from psycopg2.extras import RealDictCursor

from database.postgres import get_connection
from infra.config_loader import get_settings, resolve_workspace_root
from runtime.skill_manage import (
    init_skill_to_database,
)

log = logging.getLogger("flow.community")

REQUEST_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 120
UPLOAD_TIMEOUT = 120

WORKSPACE_ROOT = resolve_workspace_root()
TEMP_COMMUNITY_SKILLS_DIR = WORKSPACE_ROOT / "temp_community_skills"
SKILLS_DIR = WORKSPACE_ROOT / "skills"


def _build_base_url() -> str:
    settings = get_settings()
    base_url = settings.community_server.base_url.rstrip("/")
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"
    return base_url


def list_community_skills(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    language: str = "",
    disciplinary_field: str = "",
) -> dict:
    base_url = _build_base_url()
    url = f"{base_url}/skills/list_skill"

    params = {
        "page": page,
        "page_size": page_size,
    }
    if keyword:
        params["keyword"] = keyword
    if language:
        params["language"] = language
    if disciplinary_field:
        params["disciplinary_field"] = disciplinary_field

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.exception("list_community_skills request failed: %s", url)
        return {
            "code": 502,
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "message": f"community server request failed: {e}",
        }


def get_community_skill_by_name(skill_name: str) -> dict:
    base_url = _build_base_url()
    url = f"{base_url}/skills/detail/name/{skill_name}"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.exception("get_community_skill_by_name request failed: %s", url)
        return {
            "code": 502,
            "data": None,
            "message": f"community server request failed: {e}",
        }


def get_community_skill_by_id(skill_id: str) -> dict:
    base_url = _build_base_url()
    url = f"{base_url}/skills/detail/id/{skill_id}"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log.exception("get_community_skill_by_id request failed: %s", url)
        return {
            "code": 502,
            "data": None,
            "message": f"community server request failed: {e}",
        }


def _download_skill_zip(skill_id: str, zip_filename: str, user_id: int | None = None) -> Path:
    base_url = _build_base_url()
    url = f"{base_url}/skills/download/id/{skill_id}"

    params = {}
    if user_id is not None:
        params["user_id"] = user_id

    TEMP_COMMUNITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_COMMUNITY_SKILLS_DIR / zip_filename

    resp = requests.get(url, params=params, timeout=DOWNLOAD_TIMEOUT, stream=True)
    resp.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return zip_path


def install_community_skill(skill_id: str, user_id: int | None = None) -> dict:
    detail_resp = get_community_skill_by_id(skill_id)
    if detail_resp.get("code") != 200:
        return {
            "success": False,
            "message": detail_resp.get("message", "failed to get skill detail"),
        }

    skill = detail_resp["data"]
    skill_name = skill["skill_name"]
    version = skill["version"]
    zip_filename = f"{skill_name}_{version}.zip"
    skill_dir = SKILLS_DIR / skill_name

    if skill_dir.exists() and skill_dir.is_dir():
        result = init_skill_to_database(skill_dir, version, path_prefix="skills", publisher="COMMUNITY")
        if result:
            return {
                "success": True,
                "skill_id": result["skill_id"],
                "skill_name": skill_name,
                "version": version,
                "source": "local_cache",
            }

    cached_zip = TEMP_COMMUNITY_SKILLS_DIR / zip_filename
    if not cached_zip.exists():
        try:
            _download_skill_zip(skill_id, zip_filename, user_id=user_id)
        except requests.RequestException as e:
            log.exception("download skill zip failed: skill_id=%s", skill_id)
            return {
                "success": False,
                "message": f"download skill zip failed: {e}",
            }

    try:
        with zipfile.ZipFile(cached_zip, "r") as zf:
            zf.extractall(SKILLS_DIR)
    except zipfile.BadZipFile as e:
        log.exception("extract skill zip failed: %s", cached_zip)
        return {
            "success": False,
            "message": f"invalid zip file: {e}",
        }

    result = init_skill_to_database(skill_dir, version, path_prefix="skills", publisher="COMMUNITY")
    if not result:
        return {
            "success": False,
            "message": "failed to parse SKILL.md or init skill to database",
        }

    return {
        "success": True,
        "skill_id": result["skill_id"],
        "skill_name": skill_name,
        "version": version,
        "source": "community_server",
    }


def remove_community_skill(skill_id: str) -> dict:
    detail_resp = get_community_skill_by_id(skill_id)
    if detail_resp.get("code") != 200:
        return {
            "success": False,
            "message": detail_resp.get("message", "failed to get skill detail"),
        }

    skill = detail_resp["data"]
    skill_name = skill["skill_name"]
    version = skill["version"]

    try:
        with closing(get_connection()) as conn:
            with conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        UPDATE dag_skills
                        SET is_deleted = 1, update_time = CURRENT_TIMESTAMP
                        WHERE skill_name = %s AND version = %s AND is_deleted = 0
                        RETURNING id, skill_id
                        """,
                        (skill_name, version),
                    )
                    row = cursor.fetchone()

                    if not row:
                        return {
                            "success": False,
                            "message": f"skill not found in local database: {skill_name} v{version}",
                        }
    except Exception as e:
        log.exception("remove_community_skill db update failed: skill_name=%s version=%s", skill_name, version)
        return {
            "success": False,
            "message": f"database update failed: {e}",
        }

    skill_dir = SKILLS_DIR / skill_name
    if skill_dir.exists() and skill_dir.is_dir():
        try:
            shutil.rmtree(skill_dir)
        except Exception as e:
            log.warning("failed to remove skill dir %s: %s", skill_dir, e)

    return {
        "success": True,
        "skill_name": skill_name,
        "version": version,
    }


GENERATED_SKILLS_DIR = SKILLS_DIR / "generated"


def upload_community_skill(skill_id: str, author_email: str, uploader_id: str) -> dict:
    try:
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

                    if row["publisher"] != "PRIVATE":
                        return {
                            "success": False,
                            "message": f"only PRIVATE skills can be uploaded, current publisher: {row['publisher']}",
                        }

                    skill_name = row["skill_name"]
                    version = row["version"]
    except Exception as e:
        log.exception("upload_community_skill db query failed: skill_id=%s", skill_id)
        return {
            "success": False,
            "message": f"database query failed: {e}",
        }

    skill_dir = GENERATED_SKILLS_DIR / skill_name
    if not skill_dir.exists() or not skill_dir.is_dir():
        return {
            "success": False,
            "message": f"skill directory not found in generated: {skill_name}",
        }

    zip_filename = f"{skill_name}_{version}.zip"
    TEMP_COMMUNITY_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = TEMP_COMMUNITY_SKILLS_DIR / zip_filename

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in skill_dir.rglob("*"):
                if file.is_file():
                    arcname = f"{skill_name}/{file.relative_to(skill_dir)}"
                    zf.write(file, arcname)
    except Exception as e:
        log.exception("upload_community_skill zip failed: %s", skill_dir)
        return {
            "success": False,
            "message": f"failed to create zip: {e}",
        }

    base_url = _build_base_url()
    url = f"{base_url}/skills/upload_skill_package"

    try:
        with open(zip_path, "rb") as f:
            resp = requests.post(
                url,
                data={
                    "uploader_id": uploader_id,
                    "author_email": author_email,
                    "skill_name": skill_name,
                    "version": version,
                },
                files={"file": (zip_filename, f, "application/zip")},
                timeout=UPLOAD_TIMEOUT,
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("code") == 200:
                return {
                    "success": True,
                    "data": body.get("data"),
                    "message": body.get("message", ""),
                }
            else:
                return {
                    "success": False,
                    "message": body.get("message", "unknown error"),
                }
    except requests.RequestException as e:
        log.exception("upload_community_skill request failed: %s", url)
        return {
            "success": False,
            "message": f"community server upload failed: {e}",
        }
