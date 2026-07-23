from __future__ import annotations

from pathlib import Path

import grpc
import pytest

from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient
from piflow_engine.cn.piflow.remote.result_resolver import RemoteExecutionError, ResultMeta
from piflow_engine.cn.piflow.remote.server import create_server


class _FakeFacade:
    def __init__(self, result_file: Path):
        self.result_file = result_file

    def submit_dag(self, dag_definition_json: str):
        assert dag_definition_json == '{"nodes":[]}'
        return "process-1", "SUBMITTED"

    def get_run_status(self, run_id: str):
        if run_id != "process-1":
            raise RemoteExecutionError("RUN_NOT_FOUND", "run not found")
        return run_id, "SUCCESS", ""

    def get_run_result_meta(self, *, run_id: str, result_node_id: str, result_output_name: str):
        if run_id != "process-1":
            raise RemoteExecutionError("RUN_NOT_FOUND", "run not found")
        if result_node_id not in {"", "node-1"}:
            raise RemoteExecutionError("RESULT_NOT_FOUND", "result not found")
        return ResultMeta(
            status="SUCCESS",
            file_name=self.result_file.name,
            file_size=self.result_file.stat().st_size,
            mime_type="text/plain",
        )

    def open_result_file(self, *, run_id: str, result_node_id: str, result_output_name: str):
        if run_id != "process-1":
            raise RemoteExecutionError("RUN_NOT_FOUND", "run not found")
        if result_node_id not in {"", "node-1"}:
            raise RemoteExecutionError("RESULT_NOT_FOUND", "result not found")
        return self.result_file.open("rb")


@pytest.fixture
def grpc_target(tmp_path: Path):
    result_file = tmp_path / "result.txt"
    result_file.write_text("hello remote execution", encoding="utf-8")

    server = create_server(facade=_FakeFacade(result_file))
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()
    try:
        yield f"127.0.0.1:{port}", result_file
    finally:
        server.stop(grace=None)


def test_remote_execution_client_roundtrip(grpc_target, tmp_path: Path):
    target, result_file = grpc_target
    client = RemoteExecutionClient(target)
    try:
        submit_resp = client.submit_dag('{"nodes":[]}')
        assert submit_resp.run_id == "process-1"
        assert submit_resp.status == "SUBMITTED"

        status_resp = client.get_run_status("process-1")
        assert status_resp.status == "SUCCESS"

        meta_resp = client.get_run_result_meta(
            run_id="process-1",
            result_node_id="",
            result_output_name="",
        )
        assert meta_resp.file_name == result_file.name
        assert meta_resp.file_size == result_file.stat().st_size

        local_copy = tmp_path / "downloaded.txt"
        downloaded_path = client.download_result(
            run_id="process-1",
            result_node_id="",
            result_output_name="",
            target_path=local_copy,
        )
        assert Path(downloaded_path).read_text(encoding="utf-8") == "hello remote execution"
    finally:
        client.close()


def test_remote_execution_server_maps_not_found(grpc_target):
    target, _ = grpc_target
    client = RemoteExecutionClient(target)
    try:
        with pytest.raises(grpc.RpcError) as exc_info:
            client.get_run_result_meta(
                run_id="process-1",
                result_node_id="missing-node",
                result_output_name="output_path",
            )
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND
        assert "RESULT_NOT_FOUND" in exc_info.value.details()
    finally:
        client.close()
