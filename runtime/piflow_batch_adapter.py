from __future__ import annotations

import copy
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from repositories.piflow_batch_store import (
    create_batch,
    get_definition_for_batch,
    update_batch,
    update_batch_item,
)
from runtime.piflow_adapter import submit_frontend_dag
from runtime.workspace_manager import WorkspaceManager


DEFAULT_MAX_PARALLEL = 5
DEFAULT_RETRY_COUNT = 1
DEFAULT_OUTPUT_DIR = "batch_outputs"


def _find_single_stop(definition_json: dict[str, Any], skill_name: str) -> dict[str, Any]:
    nodes = [
        node
        for node in definition_json.get("nodes", [])
        if node.get("skill_name") == skill_name
    ]
    if len(nodes) != 1:
        raise ValueError(
            f"batch pipeline must contain exactly one {skill_name}, found {len(nodes)}"
        )
    return nodes[0]


def _build_item_definition(
    definition_json: dict[str, Any],
    *,
    source_path: str,
    output_path: str,
) -> dict[str, Any]:
    item_definition = copy.deepcopy(definition_json)
    source_stop = _find_single_stop(item_definition, "source_stop")
    sink_stop = _find_single_stop(item_definition, "sink_stop")

    source_stop.setdefault("params", {})["file_path"] = source_path
    sink_stop.setdefault("params", {})["path"] = output_path
    sink_stop["params"]["overwrite"] = True
    return item_definition


def _list_input_files(input_dir: Path) -> list[Path]:
    # Directory inputs and hidden entries are intentionally ignored.
    return sorted(
        (
            path
            for path in input_dir.iterdir()
            if not path.name.startswith(".") and path.is_file()
        ),
        key=lambda path: path.name,
    )


def _run_one_item(
    definition_json: dict[str, Any],
    *,
    batch_id: str,
    item_index: int,
    input_virtual_path: str,
    output_path: Path,
    output_virtual_path: str,
    user_id: str,
    workspace_root: Path,
    python_home: str | None,
    retry_count: int,
) -> None:
    for attempt in range(retry_count + 1):
        attempts = attempt + 1
        update_batch_item(
            batch_id,
            item_index,
            status="RUNNING",
            attempts=attempts,
            error_message=None,
        )
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            process = submit_frontend_dag(
                _build_item_definition(
                    definition_json,
                    source_path=input_virtual_path,
                    output_path=output_virtual_path,
                ),
                workspace_root=workspace_root,
                user_id=user_id,
                python_home=python_home,
            )
            process_id = str(process.pid())
            update_batch_item(batch_id, item_index, process_id=process_id)
            process.await_termination()
            update_batch_item(batch_id, item_index, status="COMPLETED")
            return
        except Exception as exc:
            if attempt == retry_count:
                update_batch_item(
                    batch_id,
                    item_index,
                    status="FAILED",
                    attempts=attempts,
                    error_message=str(exc),
                )
                return


def submit_batch_frontend_dag(
    definition_id: str,
    *,
    input_dir: str | Path,
    user_id: str,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
    retry_count: int = DEFAULT_RETRY_COUNT,
    stop_on_failure: bool = False,
    output_dir: str | Path | None = None,
    workspace_root: str | Path | None = None,
    python_home: str | None = None,
) -> dict[str, Any]:
    """Create a persisted batch and return before background execution starts."""
    if max_parallel < 1:
        raise ValueError("max_parallel must be at least 1")
    if retry_count < 0:
        raise ValueError("retry_count must be non-negative")

    workspace = WorkspaceManager()
    if workspace_root is not None:
        # Keep the same workspace-root behavior as the single-run adapter.
        workspace = WorkspaceManager()
        resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    else:
        resolved_workspace_root = Path(workspace.root).resolve()

    workspace.ensure_user_workspace(user_id)
    definition = get_definition_for_batch(
        definition_id=definition_id,
        user_id=user_id,
    )
    if definition is None:
        raise ValueError("definition not found or does not belong to user")
    definition_json = definition["definition_json"]
    _find_single_stop(definition_json, "source_stop")
    _find_single_stop(definition_json, "sink_stop")

    input_path = workspace.resolve_user_virtual_path(user_id, str(input_dir))
    if not input_path.is_dir():
        raise ValueError(f"input_dir is not a directory: {input_path}")

    batch_id = f"batch_{uuid.uuid4().hex}"
    output_relative_dir = str(output_dir).strip() if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_base = workspace.resolve_user_virtual_path(
        user_id,
        f"{output_relative_dir.rstrip('/')}/{batch_id}",
    )
    output_base.mkdir(parents=True, exist_ok=True)

    input_files = _list_input_files(input_path)
    item_specs = []
    for index, file_path in enumerate(input_files, start=1):
        input_virtual_path = workspace.to_user_virtual_path(
            user_id,
            str(file_path.relative_to(workspace.get_user_root(user_id))),
        )
        output_name = f"{index:04d}_{file_path.name}"
        output_path = output_base / output_name
        output_virtual_path = workspace.to_user_virtual_path(
            user_id,
            str(output_path.relative_to(workspace.get_user_root(user_id))),
        )
        item_specs.append({
            "item_index": index,
            "input_name": file_path.name,
            "input_path": input_virtual_path,
            "output_path": output_virtual_path,
            "_filesystem_input": file_path,
            "_filesystem_output": output_path,
        })

    create_batch(
        batch_id=batch_id,
        user_id=user_id,
        dag_task_id=definition["dag_task_id"],
        definition_id=definition_id,
        input_dir=str(input_dir),
        output_dir=output_relative_dir,
        max_parallel=max_parallel,
        retry_count=retry_count,
        stop_on_failure=stop_on_failure,
        items=item_specs,
    )

    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix=f"piflow-batch-{batch_id}",
    )
    executor.submit(
        _execute_batch,
        batch_id,
        definition_json,
        item_specs,
        user_id=user_id,
        workspace_root=resolved_workspace_root,
        python_home=python_home,
        max_parallel=max_parallel,
        retry_count=retry_count,
        stop_on_failure=stop_on_failure,
    )
    executor.shutdown(wait=False)

    return {
        "batch_id": batch_id,
        "total": len(input_files),
        "status": "PENDING",
    }


def _execute_batch(
    batch_id: str,
    definition_json: dict[str, Any],
    item_specs: list[dict[str, Any]],
    *,
    user_id: str,
    workspace_root: Path,
    python_home: str | None,
    max_parallel: int,
    retry_count: int,
    stop_on_failure: bool,
) -> None:
    update_batch(batch_id, status="RUNNING")
    next_index = 0
    stopped = False
    pending = set()

    def submit_item(executor: ThreadPoolExecutor, spec: dict[str, Any]):
        return executor.submit(
            _run_one_item,
            definition_json,
            batch_id=batch_id,
            item_index=spec["item_index"],
            input_virtual_path=spec["input_path"],
            output_path=spec["_filesystem_output"],
            output_virtual_path=spec["output_path"],
            user_id=user_id,
            workspace_root=workspace_root,
            python_home=python_home,
            retry_count=retry_count,
        )

    try:
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            while next_index < len(item_specs) and len(pending) < max_parallel:
                pending.add(submit_item(executor, item_specs[next_index]))
                next_index += 1
                update_batch(batch_id, submitted_count=next_index)

            while pending:
                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    future.result()
                if stop_on_failure:
                    # The database is authoritative for whether a completed item failed.
                    from repositories.piflow_batch_store import get_batch
                    current = get_batch(batch_id, user_id)
                    stopped = any(item["status"] == "FAILED" for item in current["items"])
                if stopped:
                    remaining = len(item_specs) - next_index
                    for spec in item_specs[next_index:]:
                        update_batch_item(
                            batch_id,
                            spec["item_index"],
                            status="SKIPPED",
                        )
                    update_batch(
                        batch_id,
                        skipped_count=remaining,
                        status="STOPPED",
                    )
                    break
                while next_index < len(item_specs) and len(pending) < max_parallel:
                    pending.add(submit_item(executor, item_specs[next_index]))
                    next_index += 1
                    update_batch(batch_id, submitted_count=next_index)

        current = get_batch(batch_id, user_id)
        if current is None:
            raise RuntimeError(f"batch not found: {batch_id}")
        completed = sum(item["status"] == "COMPLETED" for item in current["items"])
        failed = sum(item["status"] == "FAILED" for item in current["items"])
        skipped = sum(item["status"] == "SKIPPED" for item in current["items"])
        status = "COMPLETED" if failed == 0 and skipped == 0 else "PARTIAL_FAILED"
        if stopped:
            status = "STOPPED"
        update_batch(
            batch_id,
            completed_count=completed,
            failed_count=failed,
            skipped_count=skipped,
            status=status,
        )
    except Exception as exc:
        update_batch(batch_id, status="FAILED", error_message=str(exc))
