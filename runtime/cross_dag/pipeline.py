"""数据源注册、规划、分段和远程提交的一体化入口。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.distributed_dag_submitter import CrossDomainSubmitResult

from .config import CrossDcConfig
from .engine import plan_cross_dag
from .executor import (
    download_cross_dag_result,
    submit_cross_dag_plan,
    wait_for_cross_dag_run,
)
from .registry_stub import DatasourceRegistry
from .schema import MODE_COMPOSITION, CrossDagPlan, IntentSpec


@dataclass(frozen=True)
class CrossDagPipelineResult:
    plan: CrossDagPlan
    submission: CrossDomainSubmitResult | None = None
    result_path: Path | None = None


def run_cross_dag_pipeline(
    user_request: str,
    *,
    llm: Any = None,
    registry: DatasourceRegistry | None = None,
    config: CrossDcConfig | None = None,
    intent: IntentSpec | None = None,
    planning_json: dict[str, Any] | None = None,
    submit: bool = True,
    wait: bool = False,
    download_to: str | Path | None = None,
    poll_interval_seconds: float = 1.0,
    timeout_seconds: float | None = None,
    on_stage: Any = None,
) -> CrossDagPipelineResult:
    """运行完整流水线；所有目录和拓扑信息都来自注入/默认注册表。

    ``intent`` 和 ``planning_json`` 是确定性测试入口，生产调用只传自然语言即可。
    direct/unavailable 计划没有 DAG，会原样返回而不会误提交。
    """
    plan = plan_cross_dag(
        user_request,
        llm=llm,
        registry=registry,
        config=config,
        intent=intent,
        planning_json=planning_json,
        on_stage=on_stage,
    )
    if not submit or plan.mode != MODE_COMPOSITION:
        return CrossDagPipelineResult(plan=plan)

    submission = submit_cross_dag_plan(plan)
    if wait or download_to is not None:
        wait_for_cross_dag_run(
            submission,
            poll_interval_seconds=poll_interval_seconds,
            timeout_seconds=timeout_seconds,
        )

    result_path = None
    if download_to is not None:
        result_path = download_cross_dag_result(submission, download_to)

    return CrossDagPipelineResult(
        plan=plan,
        submission=submission,
        result_path=result_path,
    )
