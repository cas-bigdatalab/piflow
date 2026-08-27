"""多孔材料比表面积跨域计算组配 demo。

本脚本与服务接口使用相同的自然语言规划路径：不传固定 intent、planning_json、
数据集 ID、副本、中心 IP 或 DAG。默认请求只使用数据目录中的真实数据集名称，
验证“数据源发现 → Skill 规划 → 副本绑定 → 跨域划分 → 执行 → 下载”完整链路。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.cross_dag.pipeline import run_cross_dag_pipeline


DEFAULT_REQUEST = (
    "我在做多孔材料的跨场景性能对比，想比较催化材料和超级电容器电极材料的比表面积水平。"
    "请从合成气催化转化反应过程数据整编语料中选出BET比表面积最高的30条记录，从超级电容器"
    "性能参数中选出比表面积最高的30条记录，统一换算为m²/g，分别计算有效样本数、平均值、"
    "最小值和最大值，并计算超级电容器材料相对于催化材料的平均比表面积差值（超级电容器减"
    "催化材料）和比值（超级电容器除以催化材料），输出"
    "porous_material_surface_area_comparison.csv。"
)

DEMO_SKILLS = (
    "numeric_metric_topn_summary",
    "metric_summary_compare",
)

# 这些 Skill 属于本 Demo 的旧版实现，目录删除后数据库里的注册记录不会自动失效。
# 这里只定向清理已确认退役的 Demo Skill，避免影响算子库里的其他 Skill。
RETIRED_DEMO_SKILLS = (
    "corpus_knowledge_table",
    "table_row_filter",
    "table_query_aggregate",
)


def _remove_retired_demo_skills() -> list[str]:
    """将已从 workspace 删除的旧 Demo Skill 标记为下架。"""
    from services.dag_panel_service import remove_local_skill

    retired: list[str] = []
    for skill_name in RETIRED_DEMO_SKILLS:
        # 只处理已经从磁盘移除的旧 Skill；若目录仍存在则停止，避免误删文件。
        candidates = (
            PROJECT_ROOT / "workspace" / "skills" / skill_name,
            PROJECT_ROOT / "workspace" / "skills" / "generated" / skill_name,
        )
        existing = next((path for path in candidates if path.exists()), None)
        if existing is not None:
            raise RuntimeError(
                f"退役 Demo Skill 目录仍然存在，拒绝自动下架: {existing}"
            )

        skill_id = f"{skill_name}_1.0.0"
        result = remove_local_skill(skill_id)
        if result.get("success"):
            retired.append(skill_id)
            continue

        # 已经下架或从未注册都视为同步完成，保证 Demo 可以重复运行。
        if str(result.get("message") or "").startswith("skill not found:"):
            continue
        raise RuntimeError(
            f"退役 Demo Skill 下架失败: {skill_id}: {result.get('message', '')}"
        )
    return retired


def _register_demo_skills() -> list[str]:
    """同步服务实际使用的 Skill 元数据；不注入或固定规划结果。"""
    from runtime.skill_manage import init_skill_to_database

    registered: list[str] = []
    for skill_name in DEMO_SKILLS:
        skill_dir = PROJECT_ROOT / "workspace" / "skills" / skill_name
        result = init_skill_to_database(
            skill_dir,
            version="1.0.0",
            path_prefix="skills",
            publisher="PRIVATE",
        )
        if not result or not result.get("skill_id"):
            raise RuntimeError(f"Demo Skill 注册失败: {skill_name}")
        registered.append(str(result["skill_id"]))
    return registered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", default=DEFAULT_REQUEST, help="可覆盖的自然语言请求")
    parser.add_argument("--plan-only", action="store_true", help="只生成动态计划，不提交执行")
    parser.add_argument(
        "--download-to",
        default="workspace/porous_material_surface_area_comparison.csv",
    )
    parser.add_argument("--timeout-seconds", type=float, default=3600)
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument(
        "--dump-plan",
        default="workspace/porous_material_surface_area_plan.json",
        help="完整动态计划落盘位置",
    )
    args = parser.parse_args()

    retired_skills = _remove_retired_demo_skills()
    if retired_skills:
        print(f"[skills] retired: {', '.join(retired_skills)}")

    registered_skills = _register_demo_skills()
    print(f"[skills] registered: {', '.join(registered_skills)}")

    events: list[dict] = []
    dump_path = Path(args.dump_plan).expanduser().resolve()

    def on_stage(stage: str, payload: dict) -> None:
        events.append({"stage": stage, **payload})
        print(f"[{stage}] {payload.get('status', '')}")

    def dump_plan(plan) -> None:
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_path.write_text(
            json.dumps(
                {"plan": plan.to_json(), "events": events},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    try:
        result = run_cross_dag_pipeline(
            args.request,
            submit=not args.plan_only,
            wait=not args.plan_only,
            download_to=None if args.plan_only else args.download_to,
            poll_interval_seconds=args.poll_interval_seconds,
            timeout_seconds=args.timeout_seconds,
            on_stage=on_stage,
            on_plan=dump_plan,
        )
    except Exception:
        if dump_path.is_file():
            print(f"plan_dump: {dump_path}", file=sys.stderr)
        raise

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
