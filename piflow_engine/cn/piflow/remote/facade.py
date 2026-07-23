from __future__ import annotations

import json
from typing import BinaryIO

from runtime.piflow_adapter import submit_frontend_dag
from runtime.piflow_run_query import get_piflow_run_progress

from .result_resolver import RemoteExecutionError, ResultMeta, ResultResolver


class RemoteExecutionFacade:
    def __init__(
        self,
        *,
        workspace_root: str | None = None,
        user_id: str | None = None,
        python_home: str | None = None,
        result_resolver: ResultResolver | None = None,
    ):
        self._workspace_root = workspace_root
        self._user_id = user_id
        self._python_home = python_home
        self._result_resolver = result_resolver or ResultResolver()

    def submit_dag(self, dag_definition_json: str) -> tuple[str, str]:
        try:
            definition = json.loads(dag_definition_json)
        except json.JSONDecodeError as exc:
            raise RemoteExecutionError("INVALID_ARGUMENT", "dag_definition_json must be valid json") from exc

        if not isinstance(definition, dict):
            raise RemoteExecutionError("INVALID_ARGUMENT", "dag_definition_json must decode to a json object")

        try:
            process = submit_frontend_dag(
                definition_json=definition,
                workspace_root=self._workspace_root,
                user_id=self._user_id,
                python_home=self._python_home,
            )
        except Exception as exc:
            raise RemoteExecutionError("INTERNAL_ERROR", f"submit dag failed: {exc}") from exc

        return str(process.pid()), "SUBMITTED"

    def get_run_status(self, run_id: str) -> tuple[str, str, str]:
        if not run_id.strip():
            raise RemoteExecutionError("INVALID_ARGUMENT", "run_id is required")

        try:
            result = get_piflow_run_progress(run_id)
        except Exception as exc:
            raise RemoteExecutionError("INTERNAL_ERROR", f"query run status failed: {exc}") from exc

        if result is None:
            raise RemoteExecutionError("RUN_NOT_FOUND", f"run not found: {run_id}")

        return (
            str(result.get("process_id") or run_id),
            str(result.get("status") or ""),
            str(result.get("error_message") or ""),
        )

    def get_run_result_meta(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
    ) -> ResultMeta:
        return self._result_resolver.get_result_meta(
            run_id=run_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )

    def open_result_file(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
    ) -> BinaryIO:
        return self._result_resolver.open_result_file(
            run_id=run_id,
            result_node_id=result_node_id,
            result_output_name=result_output_name,
        )
