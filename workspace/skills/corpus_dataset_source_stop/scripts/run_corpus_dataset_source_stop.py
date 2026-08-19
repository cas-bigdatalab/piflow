from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from piflow_engine.cn.piflow.core.flow import FlowImpl
from piflow_engine.cn.piflow.core.process_impl import ProcessImpl
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.core.stop_job import StopJobImpl
from piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop import CorpusDatasetSourceStop


def run(dataset_id: str, output_dir: str) -> None:
    workspace_root = Path(output_dir).expanduser().resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    stop = CorpusDatasetSourceStop()
    stop.set_properties({"dataset_id": dataset_id})

    runner = Runner.create().bind("local.workspace_root", str(workspace_root))
    flow = FlowImpl(name="corpus_dataset_source_stop", uuid="corpus_dataset_source_stop")
    process = ProcessImpl(flow, runner.context, runner)
    process_context = process._process_context

    stop.initialize(process_context)
    stop_job = StopJobImpl("CorpusDatasetSource", stop, process_context)
    outputs = stop_job.perform({})

    for port in outputs.ports():
        artifact = outputs.get_artifact(port)
        print(f"{port}\t{artifact.path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CorpusDatasetSourceStop.")
    parser.add_argument("--dataset_id", required=True, help="数据集唯一标识 ID")
    parser.add_argument("--output_dir", required=True, help="工作目录")
    args = parser.parse_args()
    run(dataset_id=args.dataset_id, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
