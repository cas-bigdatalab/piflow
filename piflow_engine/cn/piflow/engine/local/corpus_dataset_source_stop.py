from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from piflow_engine.cn.piflow.core.artifact import FileArtifact
from piflow_engine.cn.piflow.core.runtime_context import JobContext, ProcessContext
from piflow_engine.cn.piflow.core.stop import ConfigurableStop
from piflow_engine.cn.piflow.core.stream import JobInputStream, JobOutputStream
from piflow_engine.cn.piflow.runtime.logging.path_utils import safe_name

try:
    from infra.config_loader import get_settings as _get_settings
except Exception:  # pragma: no cover - optional during isolated unit tests
    _get_settings = None


RUNNER_CONTEXT_WORKSPACE_ROOT = "local.workspace_root"


class CorpusDatasetSourceStop(ConfigurableStop):
    author_email = ""
    description = "Download one corpus dataset file by dataset id and expose it as a FileArtifact on output."
    inport_list: list[str] = []
    outport_list: list[str] = ["output"]
    is_data_source = True

    def __init__(self) -> None:
        super().__init__()
        self.dataset_id = ""
        self.file_name = ""
        self._workspace_root: Path | None = None
        self._base_url = ""

    def set_properties(self, properties: dict[str, Any]) -> None:
        raw_dataset_id = properties.get("dataset_id", "")
        if not isinstance(raw_dataset_id, str):
            raise TypeError("corpus dataset source property 'dataset_id' must be a string")
        self.dataset_id = raw_dataset_id.strip()
        if not self.dataset_id:
            raise ValueError("corpus dataset source property 'dataset_id' must not be empty")

        raw_file_name = properties.get("fileName", properties.get("file_name", ""))
        if raw_file_name is None:
            raw_file_name = ""
        if not isinstance(raw_file_name, str):
            raise TypeError("corpus dataset source property 'fileName' must be a string")
        self.file_name = raw_file_name.strip()

    def initialize(self, ctx: ProcessContext) -> None:
        workspace_root = ctx.get(RUNNER_CONTEXT_WORKSPACE_ROOT, ".piflow/workspace")
        self._workspace_root = Path(str(workspace_root)).expanduser().resolve()
        self._workspace_root.mkdir(parents=True, exist_ok=True)

        if _get_settings is None:
            raise RuntimeError("settings loader is unavailable")
        base_url = str(_get_settings().corpus_route.base_url or "").strip().rstrip("/")
        if not base_url:
            raise ValueError("settings.corpus_route.base_url must not be empty")
        self._base_url = base_url

    def perform(
        self,
        inputs: JobInputStream,
        outputs: JobOutputStream,
        ctx: JobContext,
    ) -> None:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")
        if not self._base_url:
            raise RuntimeError("corpus route base url is not initialized")

        dataset = self._fetch_dataset_detail(self.dataset_id)
        cstr = str(dataset.get("cstr", "")).strip()
        if not cstr:
            raise ValueError(f"dataset detail does not contain cstr for dataset_id={self.dataset_id}")

        records = self._fetch_download_urls(cstr, dataset=dataset)
        if not records:
            raise ValueError(f"no dataset file url found for dataset_id={self.dataset_id}, cstr={cstr}")

        output_dir = self._prepare_output_dir(ctx)
        selected_record = self._select_record(records)
        file_name = selected_record["fileName"]
        downloaded_path = self._download_file(
            download_url=selected_record["downloadUrl"],
            target_path=output_dir / file_name,
        )
        artifact = FileArtifact(path=str(downloaded_path)).with_metadata(
            datasetId=self.dataset_id,
            cstr=cstr,
            title=str(dataset.get("title", "")).strip(),
            connectorId=str(dataset.get("connectorId", "")).strip(),
            fromName=str(dataset.get("fromName", "")).strip(),
            fileName=file_name,
            downloadUrl=selected_record["downloadUrl"],
            size=dataset.get("size"),
        )
        outputs.write(artifact, "output")

    def _select_record(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        seen_file_names: set[str] = set()
        for record in records:
            file_name = record["fileName"]
            if file_name in seen_file_names:
                raise ValueError(f"duplicate dataset fileName returned for dataset_id={self.dataset_id}: {file_name}")
            seen_file_names.add(file_name)

        if not self.file_name:
            return records[0]

        for record in records:
            if record["fileName"] == self.file_name:
                return record

        raise ValueError(
            f"requested fileName not found for dataset_id={self.dataset_id}: {self.file_name}"
        )

    def _fetch_dataset_detail(self, dataset_id: str) -> dict[str, Any]:
        detail_url = f"{self._base_url}/dataset/queryDataset?id={dataset_id}"
        try:
            with urlopen(detail_url, timeout=30) as response:
                payload_text = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"failed to fetch corpus dataset detail for dataset_id={dataset_id}: {exc}") from exc

        payload = _decode_json(payload_text, context=f"dataset detail for dataset_id={dataset_id}")
        if not isinstance(payload, dict):
            raise ValueError(f"dataset detail response must be a json object for dataset_id={dataset_id}")
        if int(payload.get("code", 0) or 0) != 200:
            raise ValueError(
                f"dataset detail request failed for dataset_id={dataset_id}: {payload.get('message', '')}"
            )
        data = payload.get("data") or {}
        if not isinstance(data, dict):
            raise ValueError(f"dataset detail response data must be an object for dataset_id={dataset_id}")
        return data

    def _fetch_download_urls(self, cstr: str, *, dataset: dict[str, Any]) -> list[dict[str, Any]]:
        download_urls_url = f"{self._base_url}/dataset/downloadDatasetFileUrls/{cstr}"
        try:
            with urlopen(download_urls_url, timeout=30) as response:
                payload_text = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"failed to fetch corpus dataset download urls for cstr={cstr}: {exc}") from exc

        payload = _decode_json(payload_text, context=f"download urls for cstr={cstr}")
        if not isinstance(payload, dict):
            raise ValueError(f"download urls response must be a json object for cstr={cstr}")
        if int(payload.get("code", 0) or 0) != 200:
            raise ValueError(f"download urls request failed for cstr={cstr}: {payload.get('message', '')}")

        data = payload.get("data") or []
        if not isinstance(data, list):
            raise ValueError(f"download urls response data must be a list for cstr={cstr}")

        records: list[dict[str, Any]] = []
        for download_url in data:
            if not isinstance(download_url, str):
                continue
            normalized = download_url.strip()
            if not normalized:
                continue
            file_name = Path(normalized).name
            if not file_name:
                continue
            records.append(
                {
                    "fileName": file_name,
                    "downloadUrl": normalized,
                    "dataset": dataset,
                }
            )
        return records

    def _download_file(self, *, download_url: str, target_path: Path) -> Path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urlopen(download_url, timeout=300) as response:
                bytes_written = 0
                with target_path.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        bytes_written += len(chunk)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"failed to download corpus dataset file from {download_url}: {exc}") from exc

        if bytes_written <= 0:
            raise ValueError(f"downloaded empty corpus dataset file from {download_url}")
        return target_path.resolve()

    def _prepare_output_dir(self, ctx: JobContext) -> Path:
        if self._workspace_root is None:
            raise RuntimeError("workspace root is not initialized")

        process_id = ctx.get_process_context().get_process().pid()
        stop_name = safe_name(ctx.get_stop_job().get_stop_name())
        job_id = ctx.get_stop_job().jid()
        output_dir = (
            self._workspace_root
            / process_id
            / f"{stop_name}_{job_id}_{uuid.uuid4().hex[:8]}"
            / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


def _decode_json(payload_text: str, *, context: str) -> dict[str, Any] | list[Any]:
    try:
        return json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid json response for {context}: {exc}") from exc
