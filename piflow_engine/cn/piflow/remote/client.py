from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import grpc

from .proto import remote_execution_pb2, remote_execution_pb2_grpc


class RemoteExecutionClient:
    def __init__(self, target: str):
        self._channel = grpc.insecure_channel(target)
        self._stub = remote_execution_pb2_grpc.RemoteExecutionServiceStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def submit_remote_subdag(self, dag_definition_json: str) -> remote_execution_pb2.SubmitDagResponse:
        # Used by scheduler-generated remote branch execution. Callers are
        # expected to pass a self-contained sub-DAG whose result will later be
        # materialized back into the parent flow as a file artifact.
        return self._submit_remote_dag(
            dag_definition_json,
            submission_kind="subdag",
        )

    def submit_remote_root_dag(self, dag_definition_json: str) -> remote_execution_pb2.SubmitDagResponse:
        # Used when the scheduled root DAG should execute on a remote primary
        # node. Node selection and DAG rewriting should already be completed
        # before this call, so this method only performs remote submission.
        # The long-term direction is to evolve this root submission path toward
        # an async run-handle model with richer execution metadata.
        return self._submit_remote_dag(
            dag_definition_json,
            submission_kind="root_dag",
        )

    def submit_dag(self, dag_definition_json: str) -> remote_execution_pb2.SubmitDagResponse:
        return self._submit_remote_dag(
            dag_definition_json,
            submission_kind="generic",
        )

    def _submit_remote_dag(
        self,
        dag_definition_json: str,
        *,
        submission_kind: Literal["generic", "subdag", "root_dag"],
    ) -> remote_execution_pb2.SubmitDagResponse:
        # The current RPC contract only accepts a raw DAG JSON payload, so all
        # submission kinds share the same transport today. Keep the semantic
        # entry points separate so we can later add kind-specific validation,
        # routing, telemetry, or richer async root-run handling without
        # changing callers.
        parsed = json.loads(dag_definition_json)
        if not isinstance(parsed, dict):
            raise ValueError("dag_definition_json must decode to a json object")

        return self._stub.SubmitDag(
            remote_execution_pb2.SubmitDagRequest(dag_definition_json=dag_definition_json)
        )

    def get_run_status(self, run_id: str) -> remote_execution_pb2.GetRunStatusResponse:
        return self._stub.GetRunStatus(remote_execution_pb2.GetRunStatusRequest(run_id=run_id))

    def get_run_result_meta(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
    ) -> remote_execution_pb2.GetRunResultMetaResponse:
        return self._stub.GetRunResultMeta(
            remote_execution_pb2.GetRunResultMetaRequest(
                run_id=run_id,
                result_node_id=result_node_id,
                result_output_name=result_output_name,
            )
        )

    def download_result(
        self,
        *,
        run_id: str,
        result_node_id: str = "",
        result_output_name: str = "",
        target_path: str | Path,
    ) -> str:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        stream = self._stub.DownloadResult(
            remote_execution_pb2.DownloadResultRequest(
                run_id=run_id,
                result_node_id=result_node_id,
                result_output_name=result_output_name,
            )
        )
        with target.open("wb") as fp:
            for chunk in stream:
                if chunk.content:
                    fp.write(chunk.content)
        return str(target)
