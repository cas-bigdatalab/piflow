"""Schedule and locally submit a chemical frontend DAG JSON.

Run from the project root:

    python -m chemical.demo.transform_demo

The demo creates the chemical physical DAG, then submits it to the local
PiFlow runner. Nodes transformed to ``ChemicalRemotePipelineStop`` will
contact their target chemical nodes during local execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from chemical import ChemicalConfig, schedule_chemical_dag_file
from runtime.piflow_adapter import submit_frontend_dag


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "chemical" / "config.example.yaml"
DEFAULT_DAG_PATH = PROJECT_ROOT / "chemical" / "乙酸分子量子化学计算与波函数分析流水线.json"
DEFAULT_SCHEDULED_DAG_PATH = PROJECT_ROOT / "workspace" / "chemical_scheduled_dag.json"
DEFAULT_WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
LOCAL_OPENBABEL_SKILL_PATH = (
    "/Users/renhao/PycharmProjects/flow-deepagents-0408/"
    "workspace/skills/openBabel_skill/skill.json"
)
REMOTE_OPENBABEL_SKILL_PATH = (
    "/data/flow-deepagent/chemical/flow-deepagents-0408/"
    "workspace/skills/openBabel_skill/skill.json"
)


def replace_openbabel_skill_path(value: Any) -> int:
    """Replace the temporary local OpenBabel skill path in a DAG object."""

    if isinstance(value, dict):
        replaced = 0
        for key, item in value.items():
            if isinstance(item, str) and item == LOCAL_OPENBABEL_SKILL_PATH:
                value[key] = REMOTE_OPENBABEL_SKILL_PATH
                replaced += 1
            else:
                replaced += replace_openbabel_skill_path(item)
        return replaced

    if isinstance(value, list):
        return sum(replace_openbabel_skill_path(item) for item in value)

    return 0


def submit_scheduled_dag(
    dag_definition: dict,
    *,
    workspace_root: str | Path,
) -> Any:
    """Submit a scheduled frontend DAG to the local PiFlow runner."""

    return submit_frontend_dag(
        definition_json=dag_definition,
        workspace_root=workspace_root,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Schedule and submit a chemical DAG JSON."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Chemical config path, default: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument(
        "--dag",
        type=Path,
        default=DEFAULT_DAG_PATH,
        help=f"Frontend DAG JSON path, default: {DEFAULT_DAG_PATH}",
    )
    parser.add_argument(
        "--dump-scheduled-dag",
        type=Path,
        default=DEFAULT_SCHEDULED_DAG_PATH,
        help=f"Path for the scheduled DAG JSON, default: {DEFAULT_SCHEDULED_DAG_PATH}",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=f"Local PiFlow workspace root, default: {DEFAULT_WORKSPACE_ROOT}",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Return after local submission instead of waiting for completion.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = args.config.expanduser().resolve()
    dag_path = args.dag.expanduser().resolve()
    scheduled_dag_path = args.dump_scheduled_dag.expanduser().resolve()
    workspace_root = args.workspace_root.expanduser().resolve()

    config = ChemicalConfig.from_file(config_path)
    plan = schedule_chemical_dag_file(dag_path, config=config)
    replaced_openbabel_paths = replace_openbabel_skill_path(plan.dag_definition)

    scheduled_dag_path.parent.mkdir(parents=True, exist_ok=True)
    scheduled_dag_path.write_text(
        json.dumps(plan.dag_definition, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    process = submit_scheduled_dag(
        plan.dag_definition,
        workspace_root=workspace_root,
    )

    transformed_count = sum(
        1 for decision in plan.decisions if decision.transformed
    )
    print(f"scheduled nodes: {len(plan.decisions)}")
    print(f"remote nodes: {transformed_count}")
    print(f"replaced OpenBabel skill paths: {replaced_openbabel_paths}")
    print(f"scheduled DAG: {scheduled_dag_path}")
    print(f"local workspace: {workspace_root}")
    print(f"submitted local process_id: {process.pid()}")

    if not args.no_wait:
        process.await_termination()
        print(f"local process completed: {process.pid()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
