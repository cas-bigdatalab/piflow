from __future__ import annotations

from pathlib import Path

import grpc
import pytest

from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient
from piflow_engine.cn.piflow.remote.facade import ServerResource
from piflow_engine.cn.piflow.remote.result_resolver import RemoteExecutionError, ResultMeta
from piflow_engine.cn.piflow.remote.server import create_server


class _FakeFacade:
    def __init__(self, result_file: Path, workspace_root: Path):
        self.result_file = result_file
        self._workspace_root = str(workspace_root)

    def submit_dag(self, dag_definition_json: str):
        assert dag_definition_json == '{"nodes":[]}'
        return "process-1", "SUBMITTED"

    def get_run_status(self, run_id: str):
        if run_id != "process-1":
            raise RemoteExecutionError("RUN_NOT_FOUND", "run not found")
        return run_id, "SUCCESS", ""

    def get_server_resource(self):
        return ServerResource(
            cpu_cores=8.0,
            memory_gb=16.0,
            free_disk_gb=100.0,
            hostname="test-host",
        )

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
    workspace_root = tmp_path / "workspace"
    result_file = workspace_root / "result.txt"
    workspace_root.mkdir(parents=True, exist_ok=True)
    result_file.write_text("hello remote execution", encoding="utf-8")

    server = create_server(facade=_FakeFacade(result_file, workspace_root))
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
        submit_resp = client.submit_remote_subdag('{"nodes":[]}')
        assert submit_resp.run_id == "process-1"
        assert submit_resp.status == "SUBMITTED"

        root_submit_resp = client.submit_remote_root_dag('{"nodes":[]}')
        assert root_submit_resp.run_id == "process-1"
        assert root_submit_resp.status == "SUBMITTED"

        status_resp = client.get_run_status("process-1")
        assert status_resp.status == "SUCCESS"

        resource_resp = client.get_server_resource()
        assert resource_resp.cpu_cores == 8.0
        assert resource_resp.memory_gb == 16.0
        assert resource_resp.free_disk_gb == 100.0
        assert resource_resp.hostname == "test-host"

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


def test_remote_execution_client_downloads_file(grpc_target, tmp_path: Path):
    target, _ = grpc_target
    remote_file = tmp_path / "workspace" / "remote_dir" / "nested" / "remote.txt"
    remote_file.parent.mkdir(parents=True, exist_ok=True)
    remote_file.write_text("remote file content", encoding="utf-8")

    client = RemoteExecutionClient(target)
    try:
        local_file = tmp_path / "downloaded" / "remote.txt"
        downloaded_path = client.download_file(
            file_path=str(remote_file),
            target_path=local_file,
        )

        assert Path(downloaded_path) == local_file
        assert local_file.read_text(encoding="utf-8") == "remote file content"
    finally:
        client.close()


def test_remote_execution_client_downloads_file_outside_workspace_rejected(grpc_target, tmp_path: Path):
    target, _ = grpc_target
    remote_file = tmp_path / "outside.txt"
    remote_file.write_text("nope", encoding="utf-8")

    client = RemoteExecutionClient(target)
    try:
        with pytest.raises(grpc.RpcError) as exc_info:
            client.download_file(
                file_path=str(remote_file),
                target_path=tmp_path / "downloaded" / "outside.txt",
            )
        assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED
        assert "FILE_OUTSIDE_WORKSPACE" in exc_info.value.details()
    finally:
        client.close()
