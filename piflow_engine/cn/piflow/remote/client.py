from __future__ import annotations

from pathlib import Path

import grpc

from .proto import remote_execution_pb2, remote_execution_pb2_grpc


class RemoteExecutionClient:
    def __init__(self, target: str):
        self._channel = grpc.insecure_channel(target)
        self._stub = remote_execution_pb2_grpc.RemoteExecutionServiceStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def submit_dag(self, dag_definition_json: str) -> remote_execution_pb2.SubmitDagResponse:
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
