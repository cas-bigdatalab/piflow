from __future__ import annotations

import argparse
import time
from concurrent import futures
from typing import TYPE_CHECKING
from typing import Iterator

import grpc

try:
    from .proto import remote_execution_pb2, remote_execution_pb2_grpc
    from .result_resolver import RemoteExecutionError
except ImportError:  # pragma: no cover - compatibility for direct script execution
    from proto import remote_execution_pb2, remote_execution_pb2_grpc
    from result_resolver import RemoteExecutionError

if TYPE_CHECKING:
    from .facade import RemoteExecutionFacade


_ERROR_CODE_MAP = {
    "INVALID_ARGUMENT": grpc.StatusCode.INVALID_ARGUMENT,
    "RUN_NOT_FOUND": grpc.StatusCode.NOT_FOUND,
    "RUN_NOT_FINISHED": grpc.StatusCode.FAILED_PRECONDITION,
    "RESULT_NOT_FOUND": grpc.StatusCode.NOT_FOUND,
    "RESULT_FILE_NOT_FOUND": grpc.StatusCode.NOT_FOUND,
    "INTERNAL_ERROR": grpc.StatusCode.INTERNAL,
}


class RemoteExecutionService(remote_execution_pb2_grpc.RemoteExecutionServiceServicer):
    def __init__(self, facade: "RemoteExecutionFacade | None" = None, *, chunk_size: int = 1024 * 1024):
        if facade is None:
            from .facade import RemoteExecutionFacade

            facade = RemoteExecutionFacade()
        self._facade = facade
        self._chunk_size = chunk_size

    def SubmitDag(self, request, context):
        try:
            run_id, status = self._facade.submit_dag(request.dag_definition_json)
            return remote_execution_pb2.SubmitDagResponse(
                run_id=run_id,
                status=status,
                message="",
            )
        except Exception as exc:
            self._abort(context, exc)

    def GetRunStatus(self, request, context):
        try:
            run_id, status, message = self._facade.get_run_status(request.run_id)
            return remote_execution_pb2.GetRunStatusResponse(
                run_id=run_id,
                status=status,
                message=message,
            )
        except Exception as exc:
            self._abort(context, exc)

    def GetRunResultMeta(self, request, context):
        try:
            meta = self._facade.get_run_result_meta(
                run_id=request.run_id,
                result_node_id=request.result_node_id,
                result_output_name=request.result_output_name,
            )
            return remote_execution_pb2.GetRunResultMetaResponse(
                status=meta.status,
                file_name=meta.file_name,
                file_size=meta.file_size,
                mime_type=meta.mime_type,
            )
        except Exception as exc:
            self._abort(context, exc)

    def DownloadResult(self, request, context) -> Iterator[remote_execution_pb2.DownloadResultChunk]:
        try:
            file_obj = self._facade.open_result_file(
                run_id=request.run_id,
                result_node_id=request.result_node_id,
                result_output_name=request.result_output_name,
            )
        except Exception as exc:
            self._abort(context, exc)
            return

        with file_obj:
            while True:
                chunk = file_obj.read(self._chunk_size)
                if not chunk:
                    break
                yield remote_execution_pb2.DownloadResultChunk(content=chunk)

    def _abort(self, context, exc: Exception):
        if isinstance(exc, RemoteExecutionError):
            status_code = _ERROR_CODE_MAP.get(exc.code, grpc.StatusCode.UNKNOWN)
            context.abort(status_code, f"{exc.code}: {exc.message}")
        context.abort(grpc.StatusCode.INTERNAL, f"INTERNAL_ERROR: {exc}")


def create_server(
    *,
    facade: "RemoteExecutionFacade | None" = None,
    max_workers: int = 10,
    chunk_size: int = 1024 * 1024,
) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    remote_execution_pb2_grpc.add_RemoteExecutionServiceServicer_to_server(
        RemoteExecutionService(facade=facade, chunk_size=chunk_size),
        server,
    )
    return server


def serve(
    *,
    host: str = "0.0.0.0",
    port: int = 50061,
    facade: "RemoteExecutionFacade | None" = None,
    max_workers: int = 10,
) -> grpc.Server:
    server = create_server(facade=facade, max_workers=max_workers)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    return server


def main() -> None:
    from .facade import RemoteExecutionFacade

    parser = argparse.ArgumentParser(description="Start the PiFlow remote execution gRPC server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=50061)
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--user-id", default=None)
    parser.add_argument("--python-home", default=None)
    args = parser.parse_args()

    facade = RemoteExecutionFacade(
        workspace_root=args.workspace_root,
        user_id=args.user_id,
        python_home=args.python_home,
    )
    server = serve(host=args.host, port=args.port, facade=facade)
    try:
        while True:
            time.sleep(60 * 60)
    except KeyboardInterrupt:
        server.stop(grace=5)


if __name__ == "__main__":
    main()
