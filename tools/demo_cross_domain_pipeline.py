from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient
from runtime.distributed_dag_submitter import submit_cross_domain_dag


REMOTE_SOURCE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.remote_source_stop.RemoteSourceStop"
)
TEXT_FILE_MERGE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.text_file_merge_stop.TextFileMergeStop"
)


def build_demo_dag(
    *,
    source_path: str,
    root_node_id: str,
    root_target: str,
    peer_node_id: str,
    peer_target: str,
    output_file_name: str,
) -> dict:
    return {
        "task": {
            "dag_task_id": "cross-domain-demo",
            "dag_task_name": "Cross domain demo",
        },
        "nodes": [
            _remote_source_node(
                node_id="source-root",
                node_name="Source Root",
                file_path=source_path,
                execution_node_id=root_node_id,
                remote_grpc_target=root_target,
                cpu_cores="8",
                memory_gb="32",
                free_disk_gb="200",
            ),
            _remote_source_node(
                node_id="source-peer",
                node_name="Source Peer",
                file_path=source_path,
                execution_node_id=peer_node_id,
                remote_grpc_target=peer_target,
                cpu_cores="8",
                memory_gb="32",
                free_disk_gb="200",
            ),
            {
                "node_id": "merge-text",
                "node_name": "Merge Text",
                "skill": {
                    "skill_id": TEXT_FILE_MERGE_BUNDLE,
                    "skill_name": "text_file_merge_stop",
                },
                "input_params": [
                    _manual_param("separator", "\n--- remote split ---\n"),
                    _manual_param("output_file_name", output_file_name),
                    _manual_param("encoding", "utf-8"),
                ],
                "out_params": [{"param_name": "output", "param_type": "file_artifact"}],
            },
        ],
        "edges": [
            {"edge_id": "edge-root-merge", "from_node_id": "source-root", "to_node_id": "merge-text"},
            {"edge_id": "edge-peer-merge", "from_node_id": "source-peer", "to_node_id": "merge-text"},
        ],
        "bindings": [
            {
                "binding_id": "binding-root-merge",
                "from_node_id": "source-root",
                "from_param_name": "output",
                "to_node_id": "merge-text",
                "to_param_name": "left",
            },
            {
                "binding_id": "binding-peer-merge",
                "from_node_id": "source-peer",
                "from_param_name": "output",
                "to_node_id": "merge-text",
                "to_param_name": "right",
            },
        ],
    }


def _remote_source_node(
    *,
    node_id: str,
    node_name: str,
    file_path: str,
    execution_node_id: str,
    remote_grpc_target: str,
    cpu_cores: str,
    memory_gb: str,
    free_disk_gb: str,
) -> dict:
    return {
        "node_id": node_id,
        "node_name": node_name,
        "skill": {
            "skill_id": REMOTE_SOURCE_BUNDLE,
            "skill_name": "remote_source_stop",
        },
        "input_params": [
            _manual_param("file_path", file_path),
            _manual_param("node_id", execution_node_id),
            _manual_param("remote_grpc_target", remote_grpc_target),
            _manual_param("cpu_cores", cpu_cores),
            _manual_param("memory_gb", memory_gb),
            _manual_param("free_disk_gb", free_disk_gb),
        ],
        "out_params": [{"param_name": "output", "param_type": "file_artifact"}],
    }


def _manual_param(name: str, value: str) -> dict:
    return {
        "binding_id": "",
        "param_name": name,
        "param_type": "string",
        "value_mode": "manual",
        "param_value": value,
        "value_source": "default",
    }


def wait_and_download_result(
    *,
    remote_grpc_target: str,
    run_id: str,
    local_output_path: Path,
    poll_interval_seconds: float,
) -> Path:
    client = RemoteExecutionClient(remote_grpc_target)
    try:
        while True:
            status = client.get_run_status(run_id)
            if status.status == "SUCCESS":
                break
            if status.status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(f"remote run failed: {status.status} {status.message}")
            time.sleep(poll_interval_seconds)

        meta = client.get_run_result_meta(
            run_id=run_id,
            result_node_id="",
            result_output_name="",
        )
        downloaded = client.download_result(
            run_id=run_id,
            result_node_id="",
            result_output_name="",
            target_path=local_output_path,
        )
        print(f"downloaded result file: {downloaded} ({meta.file_size} bytes)")
        return Path(downloaded)
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a two-node cross-domain demo DAG.")
    parser.add_argument("--root-target", default="10.0.87.111:50061")
    parser.add_argument("--peer-target", default="10.0.87.111:50062")
    parser.add_argument("--root-node-id", default="node-50061")
    parser.add_argument("--peer-node-id", default="node-50062")
    parser.add_argument("--source-path", default="workspace/temp/test.txt ")
    parser.add_argument("--output-file-name", default="cross_domain_demo_result.txt")
    parser.add_argument(
        "--download-to",
        default="workspace/cross_domain_demo_downloaded.txt",
        help="Local path for downloading the final merged result.",
    )
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument(
        "--dump-scheduled-dag",
        default="workspace/cross_domain_demo_scheduled_dag.json",
        help="Local path for saving the scheduled physical DAG JSON.",
    )
    args = parser.parse_args()

    dag_definition = build_demo_dag(
        source_path=args.source_path,
        root_node_id=args.root_node_id,
        root_target=args.root_target,
        peer_node_id=args.peer_node_id,
        peer_target=args.peer_target,
        output_file_name=args.output_file_name,
    )

    submit_result = submit_cross_domain_dag(
        dag_definition,
        remote_grpc_target=args.root_target,
        execution_node_id=args.root_node_id,
    )

    scheduled_dag_path = Path(args.dump_scheduled_dag).expanduser().resolve()
    scheduled_dag_path.parent.mkdir(parents=True, exist_ok=True)
    scheduled_dag_path.write_text(
        json.dumps(submit_result.dag_definition, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"submitted run_id: {submit_result.process_id}")
    print(f"scheduled execution node: {submit_result.execution_node_id}")
    print(f"root remote target: {submit_result.remote_grpc_target}")
    print(f"scheduled DAG dumped to: {scheduled_dag_path}")

    downloaded = wait_and_download_result(
        remote_grpc_target=submit_result.remote_grpc_target,
        run_id=submit_result.process_id,
        local_output_path=Path(args.download_to).expanduser().resolve(),
        poll_interval_seconds=args.poll_interval_seconds,
    )
    print(f"final downloaded path: {downloaded}")
    print("merged content preview:")
    print(downloaded.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
