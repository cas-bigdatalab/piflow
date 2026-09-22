"""Optional, file-backed replay of four XDC session demos; no engine changes.

Only successful plans and downloaded artifacts are published. Immutable result
objects keep existing task downloads valid when lookup indexes are cleared.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
import json
import logging
from pathlib import Path
import re
import shutil
import uuid

from filelock import FileLock

from infra.config_loader import PROJECT_ROOT, resolve_workspace_root
from runtime.cross_dag.session_codec import encode_pre_bind_plan, decode_pre_bind_plan

log = logging.getLogger(__name__)
CONFIG = PROJECT_ROOT / "config" / "cross_dag_demo_cache.json"
DEMO_IDS = {"earthquake", "chemistry", "earth_bundle", "surface_area"}
PREFIX = "demo-cache:"


def _root():
    return resolve_workspace_root() / "cross_dag_demo_cache"


def _normalize(text):
    return "".join(text.split())


def _digest(value):
    # Short enough for Windows workspace paths; 128 bits for four demo namespaces.
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:32]


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _remap(value, old, new):
    if isinstance(value, dict):
        return {k: _remap(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [_remap(v, old, new) for v in value]
    return value.replace(old, new) if isinstance(value, str) and old else value


def _view(value, detail, saved_at):
    result = deepcopy(value)
    if not detail:
        result.pop("detail", None)
    result.update(cache_hit=True, cache_created_at=saved_at)
    return result


def for_request(request):
    """Non-demo/disabled requests never touch the workspace or original flow."""
    try:
        config = _read(CONFIG)
        if config.get("enabled") is not True:
            return None
        normalized = _normalize(request)
        for demo_id, text in config["requests"].items():
            if demo_id in DEMO_IDS and _normalize(text) == normalized:
                key = _digest([demo_id, config["version"], normalized])
                return DemoCache(_root() / "entries" / demo_id / key)
    except Exception:
        log.warning("Demo cache config unavailable; using normal execution", exc_info=True)
    return None


@lru_cache(maxsize=32)
def _checksum(path, size, modified_ns):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _object(object_id):
    if not re.fullmatch(r"[0-9a-f]{32}", object_id):
        raise ValueError("Invalid demo artifact ID")
    folder = _root() / "objects" / object_id
    metadata = _read(folder / "result.json")
    path = folder / "artifact"
    stat = path.stat()
    if metadata["schema_version"] != 1 or stat.st_size != metadata["file_size"] or (
        _checksum(str(path), stat.st_size, stat.st_mtime_ns) != metadata["sha256"]
    ):
        raise ValueError("Demo artifact is incomplete or corrupt")
    return metadata, path


@dataclass
class ReplayPlan:
    """Only the persisted plan interface used by the session projection."""
    payload: dict

    @property
    def plan_id(self):
        return self.payload["plan_id"]

    @property
    def mode(self):
        return self.payload["mode"]

    def to_json(self):
        return deepcopy(self.payload)


@dataclass
class DemoCache:
    folder: Path

    def load_plan(self, plan_id, detail=False):
        try:
            saved = _read(self.folder / "plan.json")
            raw = _remap(saved["plan"], saved["plan"]["plan_id"], plan_id)
            plan = decode_pre_bind_plan(raw)
            if plan.mode == "unavailable" or not plan.validation.ok:
                return None
            view = _remap(saved["view"], saved["plan"]["plan_id"], plan_id)
            return plan, _view(view, detail, saved["created_at"])
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None

    def save_plan(self, plan, view):
        if plan.mode == "unavailable" or not plan.validation.ok:
            return
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            with FileLock(str(self.folder / "plan.lock"), timeout=0):
                if self.load_plan(plan.plan_id):
                    return
                raw = encode_pre_bind_plan(plan)
                view = {**view, "detail": {k: raw[k] for k in ("intent", "satisfaction", "planning_json", "logical_dag")}}
                _write(self.folder / "plan.json", {"plan": raw, "view": view,
                       "created_at": datetime.now(timezone.utc).isoformat()})
        except Exception:
            log.warning("Demo plan was not cached; original plan retained", exc_info=True)

    def result_key(self, pre_bind, selection):
        raw = _remap(encode_pre_bind_plan(pre_bind), pre_bind.plan_id, "<plan>")
        raw["intent"]["user_request"] = _normalize(raw["intent"]["user_request"])
        return _digest([raw, selection or ""])

    def _index(self, key):
        if not re.fullmatch(r"[0-9a-f]{32}", key):
            raise ValueError("Invalid demo result key")
        return self.folder / "results" / f"{key}.json"

    def replay(self, pre_bind, selection, user_id, detail=False):
        try:
            object_id = _read(self._index(self.result_key(pre_bind, selection)))["object_id"]
            saved, _ = _object(object_id)
            payload = _remap(saved["plan"], saved["plan"]["plan_id"], pre_bind.plan_id)
            view = _remap(saved["view"], saved["plan"]["plan_id"], pre_bind.plan_id)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return None
        # Register a NEW user-owned handle, never reuse another user's process.
        from runtime.cross_dag.run_store import save_cross_dag_execution
        process_id = f"xdc-demo-{uuid.uuid4().hex}"
        record = dict(process_id=process_id, plan_id=pre_bind.plan_id, user_id=str(user_id),
                      execution_center_id=saved["execution_center_id"], remote_grpc_target=PREFIX + object_id,
                      submit_status="SUCCESS")
        save_cross_dag_execution(**record)
        execution = status(record)
        return ReplayPlan(payload), _view(view, detail, saved["created_at"]), execution

    def stage(self, task, pre_bind, selection, plan, view, execution, user_id):
        """Private draft only; an accepted submission is NOT a cached result."""
        if not execution.get("process_id") or execution.get("cache_hit"):
            return
        try:
            from runtime.cross_dag.plan_view import _detail
            draft = {"task_id": task["task_id"], "user_id": str(user_id),
                     "key": self.result_key(pre_bind, selection), "plan": plan.to_json(),
                     "view": {**view, "detail": _detail(plan)},
                     "selectors": {key: execution.get(key, "") for key in ("result_node_id", "result_output_name")}}
            _write(self.folder / "drafts" / f"{_digest(execution['process_id'])}.json", draft)
        except Exception:
            log.warning("Demo execution draft not cached; original execution retained", exc_info=True)

    def capture(self, task, result, user_id):
        if result.get("status") != "SUCCESS" or not result.get("downloadable") or result.get("cache_hit"):
            return
        download = None
        try:
            draft_path = self.folder / "drafts" / f"{_digest(task['process_id'])}.json"
            if not draft_path.is_file():
                return
            draft = _read(draft_path)
            if draft["task_id"] != task["task_id"] or draft["user_id"] != str(user_id):
                return
            if any((result.get(key) or "") != (value or "") for key, value in draft["selectors"].items()):
                return  # An explicitly queried alternative output must not replace the demo result.
            index = self._index(draft["key"])
            index.parent.mkdir(parents=True, exist_ok=True)
            with FileLock(str(index.with_suffix(".lock")), timeout=0):
                try:
                    _object(_read(index)["object_id"])
                    return  # First complete successful result wins.
                except (OSError, ValueError, KeyError, TypeError):
                    pass
                from services.cross_dag_service import prepare_cross_dag_result_download
                download = prepare_cross_dag_result_download(process_id=task["process_id"], user_id=str(user_id),
                    result_node_id=result.get("result_node_id", ""), result_output_name=result.get("result_output_name", ""))
                object_id = uuid.uuid4().hex
                folder = _root() / "objects" / object_id
                folder.mkdir(parents=True)
                path = folder / "artifact"
                shutil.copyfile(download.path, path)
                stat = path.stat()
                metadata = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                    "file_name": download.file_name, "mime_type": download.media_type, "file_size": stat.st_size,
                    "sha256": _checksum(str(path), stat.st_size, stat.st_mtime_ns),
                    "plan": draft["plan"], "view": draft["view"], "execution_center_id": result.get("execution_center_id", ""),
                    "result_node_id": result.get("result_node_id", ""), "result_output_name": result.get("result_output_name", "")}
                _write(folder / "result.json", metadata)
                _write(index, {"object_id": object_id})  # Publish only after file AND metadata exist.
        except Exception:
            log.warning("Demo result not cached; successful task remains unchanged", exc_info=True)
        finally:
            if download is not None:
                try:
                    download.path.unlink(missing_ok=True)
                except OSError:
                    log.warning("Demo temporary download cleanup failed", exc_info=True)


def status(record, result_node_id="", result_output_name=""):
    """Called only AFTER the original execution ownership check."""
    target = str(record.get("remote_grpc_target", ""))
    if not target.startswith(PREFIX):
        return None
    result_file, error, saved = None, "", {}
    try:
        saved, _ = _object(target[len(PREFIX):])
        for key, supplied in (("result_node_id", result_node_id), ("result_output_name", result_output_name)):
            if supplied and supplied != saved[key]:
                raise ValueError("请求的结果节点或端口与缓存产物不一致")
        from services.cross_dag_service import _cross_dag_download_url
        result_file = {k: saved[k] for k in ("file_name", "file_size", "mime_type")}
        result_file["download_url"] = _cross_dag_download_url(record["process_id"])
    except (OSError, ValueError, KeyError, TypeError):
        error = "Demo 缓存文件不可用或结果节点不匹配，请重新运行该 Demo。"
    return {"plan_id": record["plan_id"], "process_id": record["process_id"],
            "execution_center_id": record["execution_center_id"], "status": "SUCCESS", "terminal": True,
            "message": "已复用 Demo 首次成功结果，未重新执行远端任务。", "cache_hit": True,
            "cache_created_at": saved.get("created_at"), "downloadable": result_file is not None,
            "result_file": result_file, "result_error": error,
            "result_node_id": saved.get("result_node_id", ""), "result_output_name": saved.get("result_output_name", "")}


def download(record, result_node_id="", result_output_name=""):
    cached = status(record, result_node_id, result_output_name)
    if cached is None:
        return None
    if not cached["downloadable"]:
        raise FileNotFoundError(cached["result_error"])
    saved, source = _object(record["remote_grpc_target"][len(PREFIX):])
    from services.cross_dag_service import CrossDagResultDownload
    folder = resolve_workspace_root() / "temp" / "xdc_downloads"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / uuid.uuid4().hex
    try:
        shutil.copyfile(source, target)  # Existing response cleanup must not delete the cached artifact.
        return CrossDagResultDownload(path=target, file_name=saved["file_name"], media_type=saved["mime_type"])
    except Exception:
        target.unlink(missing_ok=True)
        raise


def clear(demo_id):
    """Remove lookup indexes only; artifacts of existing tasks remain downloadable."""
    if demo_id != "all" and demo_id not in DEMO_IDS:
        raise ValueError("Unknown demo ID")
    root = (_root() / "entries").resolve()
    count = 0
    for name in DEMO_IDS if demo_id == "all" else [demo_id]:
        for pattern in ("*/plan.json", "*/results/*.json", "*/drafts/*.json"):
            for path in (root / name).glob(pattern):
                path.resolve().relative_to(root)
                with FileLock(str(path.with_suffix(".lock")), timeout=0):
                    path.unlink(missing_ok=True)
                    count += 1
    return count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clear XDC demo lookup indexes; preserve old downloads.")
    parser.add_argument("--clear", required=True, choices=sorted(DEMO_IDS) + ["all"])
    print("Cleared indexes:", clear(parser.parse_args().clear))
