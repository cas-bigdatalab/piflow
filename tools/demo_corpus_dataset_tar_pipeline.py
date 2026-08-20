from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.request import urlopen

from runtime.distributed_dag_submitter import submit_cross_domain_dag


CORPUS_ROUTE_BASE_URL = "http://10.0.82.213:7003"
CORPUS_SOURCE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop.CorpusDatasetSourceStop"
)
TAR_MERGE_BUNDLE = (
    "piflow_engine.cn.piflow.engine.local.tar_archive_merge_stop.TarArchiveMergeStop"
)

DEFAULT_DATASET_IDS = [
    "6a744595d38ea034d388c7b4",
    "6a6ab4da15840cf004056867",
    "6a389e3e3e0635e899d50cd0",
]


def build_demo_dag(dataset_specs: list[dict[str, str]], *, output_file_name: str = "result.tar") -> dict:
    nodes = []
    edges = []
    bindings = []

    for index, spec in enumerate(dataset_specs, start=1):
        source_node_id = f"corpus-source-{index}"
        input_port = f"data{index}"
        nodes.append(
            {
                "node_id": source_node_id,
                "node_name": f"Corpus Source {index}",
                "skill": {
                    "skill_id": CORPUS_SOURCE_BUNDLE,
                    "skill_name": "corpus_dataset_source_stop",
                },
                "input_params": [
                    _manual_param("dataset_id", spec["dataset_id"]),
                ],
                "out_params": [{"param_name": "output", "param_type": "file_artifact"}],
            }
        )
        edges.append(
            {
                "edge_id": f"edge-{source_node_id}-merge",
                "from_node_id": source_node_id,
                "to_node_id": "tar-merge",
            }
        )
        bindings.append(
            {
                "binding_id": f"binding-{source_node_id}-merge",
                "from_node_id": source_node_id,
                "from_param_name": "output",
                "to_node_id": "tar-merge",
                "to_param_name": input_port,
            }
        )

    nodes.append(
        {
            "node_id": "tar-merge",
            "node_name": "Tar Archive Merge",
            "skill": {
                "skill_id": TAR_MERGE_BUNDLE,
                "skill_name": "tar_archive_merge_stop",
            },
            "input_params": [
                _manual_param("output_file_name", output_file_name),
            ],
            "out_params": [{"param_name": "output", "param_type": "file_artifact"}],
        }
    )

    return {
        "task": {
            "dag_task_id": "corpus-tar-demo",
            "dag_task_name": "Corpus tar archive demo",
        },
        "nodes": nodes,
        "edges": edges,
        "bindings": bindings,
    }


def _fetch_dataset_spec(dataset_id: str) -> dict[str, str]:
    detail = _fetch_json(f"{CORPUS_ROUTE_BASE_URL}/dataset/queryDataset?id={dataset_id}")
    if int(detail.get("code", 0) or 0) != 200:
        raise ValueError(f"failed to query dataset detail for {dataset_id}: {detail.get('message', '')}")
    dataset = detail.get("data") or {}
    if not isinstance(dataset, dict):
        raise ValueError(f"dataset detail response invalid for {dataset_id}")

    cstr = str(dataset.get("cstr", "") or "").strip()
    connector_id = str(dataset.get("connectorId", "") or "").strip()
    if not cstr:
        raise ValueError(f"dataset {dataset_id} missing cstr")
    if not connector_id:
        raise ValueError(f"dataset {dataset_id} missing connectorId")

    return {
        "dataset_id": dataset_id,
        "connector_id": connector_id,
        "cstr": cstr,
    }


def _fetch_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError(f"unexpected json payload from {url}")
    return data


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
    from piflow_engine.cn.piflow.remote.client import RemoteExecutionClient

    client = RemoteExecutionClient(remote_grpc_target)
    try:
        while True:
            status = client.get_run_status(run_id)
            if status.status == "SUCCESS":
                break
            if status.status in {"FAILED", "CANCELLED"}:
                raise RuntimeError(f"remote run failed: {status.status} {status.message}")
            time.sleep(poll_interval_seconds)

        meta = client.get_run_result_meta(run_id=run_id, result_node_id="", result_output_name="")
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
    parser = argparse.ArgumentParser(description="Submit a corpus dataset tar aggregation demo DAG.")
    parser.add_argument("--root-target", default="10.0.82.213:50061")
    parser.add_argument("--dataset-id", action="append", dest="dataset_ids", default=None)
    parser.add_argument("--output-file-name", default="result.tar")
    parser.add_argument("--download-to", default="workspace/corpus_tar_demo_result.tar")
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument(
        "--dump-scheduled-dag",
        default="workspace/corpus_tar_demo_scheduled_dag.json",
    )
    args = parser.parse_args()

    dataset_ids = args.dataset_ids or DEFAULT_DATASET_IDS
    if len(dataset_ids) != 3:
        raise ValueError("this demo expects exactly 3 dataset ids")

    dataset_specs = [_fetch_dataset_spec(dataset_id) for dataset_id in dataset_ids]
    dag_definition = build_demo_dag(dataset_specs, output_file_name=args.output_file_name)

    submit_result = submit_cross_domain_dag(
        dag_definition,
        remote_grpc_target=args.root_target,
        execution_node_id=dataset_specs[0]["connector_id"],
    )

    scheduled_dag_path = Path(args.dump_scheduled_dag).expanduser().resolve()
    scheduled_dag_path.parent.mkdir(parents=True, exist_ok=True)
    scheduled_dag_path.write_text(
        json.dumps(submit_result.dag_definition, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"submitted run_id: {submit_result.process_id}")
    print(f"root remote target: {submit_result.remote_grpc_target}")
    print(f"scheduled DAG dumped to: {scheduled_dag_path}")

    downloaded = wait_and_download_result(
        remote_grpc_target=submit_result.remote_grpc_target,
        run_id=submit_result.process_id,
        local_output_path=Path(args.download_to).expanduser().resolve(),
        poll_interval_seconds=args.poll_interval_seconds,
    )
    print(f"final downloaded path: {downloaded}")


if __name__ == "__main__":
    main()
