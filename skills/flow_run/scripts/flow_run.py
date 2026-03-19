"""
flow_run skill with 3 top-level functions:
1) aes_encrypt
2) loginIn
3) run_flow
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import requests

from runtime.workspace_manager import WorkspaceManager


def aes_encrypt(plain_text: str) -> str:
    try:
        from Crypto.Cipher import AES  # type: ignore
        from Crypto.Util.Padding import pad  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "pycryptodome is required for Conet password encryption. "
            "Install with: pip install pycryptodome"
        ) from exc

    if not plain_text:
        raise ValueError("password is empty")

    key = "ABCDEFGHIJKL_key".encode("utf-8")
    iv = "ABCDEFGHIJKLM_iv".encode("utf-8")
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def loginIn(username: str, password: str, base_url: str = "http://conet.rdcn.link") -> str:
    url = f"{base_url.rstrip('/')}/piflow-web/jwtLogin"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": "Bearer false",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": base_url.rstrip("/"),
        "Referer": f"{base_url.rstrip('/')}/login",
        "User-Agent": "Mozilla/5.0",
    }
    data = {"username": username, "password": password}

    response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"Conet login failed, HTTP {response.status_code}")

    payload = response.json()
    if payload.get("code") != 200:
        raise RuntimeError(f"Conet login failed: {payload.get('errorMsg') or payload}")

    token = payload.get("token")
    if not token:
        raise RuntimeError("Conet login succeeded but token is missing")
    return str(token)


def _normalize_flow_json_text(raw_text: str) -> str:
    """Normalize flow JSON text to {'flow': {...}} payload expected by Conet."""
    text = raw_text.strip()
    if not text:
        return text

    try:
        parsed = json.loads(text)
    except Exception:
        return text

    if isinstance(parsed, dict):
        if isinstance(parsed.get("flow"), dict):
            return json.dumps({"flow": parsed["flow"]}, ensure_ascii=False)
        if "stops" in parsed and "paths" in parsed:
            return json.dumps({"flow": parsed}, ensure_ascii=False)

    return text


def run_flow(
    flow_session_id: str | None = None,
    temp_json_file: str | None = None,
    flow_json_text: str | None = None,
    run_label: str = "",

) -> dict:


    conet_username = "netuser1"
    conet_password = "cnic$@Nzlh1"
    conet_base_url = "http://conet.rdcn.link"


    # Prefer path input; if missing, infer /temp path from flow_session_id.
    relative_path = temp_json_file
    if not relative_path and flow_session_id and flow_session_id.strip():
        relative_path = f"/temp/dam_flow_{flow_session_id.strip()}.json"

    resolved_flow_json_text = flow_json_text

    if not resolved_flow_json_text and relative_path:
        workspace = WorkspaceManager()
        workspace.ensure_workspace()

        if relative_path.startswith("/temp/"):
            file_path = workspace.temp / relative_path.split("/temp/", 1)[1]
        else:
            candidate = Path(relative_path)
            if candidate.is_absolute():
                file_path = candidate
            else:
                file_path = workspace.temp / relative_path

        if file_path.exists():
            resolved_flow_json_text = file_path.read_text(encoding="utf-8")

    if resolved_flow_json_text:
        resolved_flow_json_text = _normalize_flow_json_text(resolved_flow_json_text)

    # Placeholder mode: return mock process id only.
    if not (conet_username and conet_password and resolved_flow_json_text):
        return {
            "status": "submitted_placeholder",
            "process_id": "mock_process_id",
            "flow_session_id": flow_session_id,
            "received_flow_json_text": bool(resolved_flow_json_text),
            "run_label": run_label,
        }

    encrypted_password = aes_encrypt(conet_password)
    token = loginIn(conet_username, encrypted_password, conet_base_url)

    url = f"{conet_base_url.rstrip('/')}/piflow-web/flow/startFlowByFlowJson"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": conet_base_url.rstrip("/"),
        "Referer": f"{conet_base_url.rstrip('/')}/flowTask",
        "User-Agent": "Mozilla/5.0",
    }
    data = {"flowJson": resolved_flow_json_text}

    response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"Conet startFlowByFlowJson failed, HTTP {response.status_code}")

    conet_result = response.json()
    if not (conet_result.get("code") == 200 or "success" in str(conet_result).lower()):
        raise RuntimeError(f"Conet startFlowByFlowJson failed: {conet_result}")

    process_id = None
    for key in ("processId", "process_id", "processInstanceId", "taskId", "id", "appId", "app_id"):
        value = conet_result.get(key)
        if value is not None and str(value).strip():
            process_id = str(value).strip()
            break
    if process_id is None:
        data_value = conet_result.get("data")
        if isinstance(data_value, dict):
            for key in ("processId", "process_id", "processInstanceId", "taskId", "id", "appId", "app_id"):
                value = data_value.get(key)
                if value is not None and str(value).strip():
                    process_id = str(value).strip()
                    break
        elif data_value is not None and str(data_value).strip():
            process_id = str(data_value).strip()
    if not process_id:
        raise RuntimeError(
            "Conet startFlowByFlowJson succeeded but no process id-like field was returned. "
            f"response={conet_result}"
        )

    return {
        "status": "submitted_remote",
        "process_id": process_id,
        "flow_session_id": flow_session_id,
        "received_flow_json_text": bool(resolved_flow_json_text),
        "run_label": run_label,
        "conet_result": conet_result,
    }
