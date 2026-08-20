"""真实语料目录 -> 意图/DAG -> 跨域分段 -> 远端执行的完整 demo。

与旧的手写三数据集 demo 不同，本脚本不包含 connectorId、IP 或 dataset_id；
注册信息变化后仍从实时目录发现。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.cross_dag.pipeline import run_cross_dag_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request",
        required=True,
        help="自然语言任务，例如：选择三份相关语料并合并为 result.tar",
    )
    parser.add_argument("--plan-only", action="store_true", help="只规划，不提交")
    parser.add_argument("--download-to", default="workspace/corpus_tar_result.tar")
    parser.add_argument("--timeout-seconds", type=float, default=3600)
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument(
        "--dump-plan",
        default="workspace/corpus_cross_dag_plan.json",
        help="完整计划落盘位置",
    )
    args = parser.parse_args()

    events: list[dict] = []

    def on_stage(stage: str, payload: dict) -> None:
        events.append({"stage": stage, **payload})
        status = payload.get("status", "")
        print(f"[{stage}] {status}")

    result = run_cross_dag_pipeline(
        args.request,
        submit=not args.plan_only,
        wait=not args.plan_only,
        download_to=None if args.plan_only else args.download_to,
        poll_interval_seconds=args.poll_interval_seconds,
        timeout_seconds=args.timeout_seconds,
        on_stage=on_stage,
    )

    dump_path = Path(args.dump_plan).expanduser().resolve()
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    dump_path.write_text(
        json.dumps(
            {"plan": result.plan.to_json(), "events": events},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"plan_id: {result.plan.plan_id}")
    print(f"mode: {result.plan.mode}")
    print(f"validation_ok: {result.plan.validation.ok}")
    print(f"plan_dump: {dump_path}")
    if result.submission is not None:
        print(f"execution_center: {result.submission.execution_node_id}")
        print(f"run_id: {result.submission.process_id}")
        print(f"submit_status: {result.submission.status}")
    if result.result_path is not None:
        print(f"result: {result.result_path}")


if __name__ == "__main__":
    main()
