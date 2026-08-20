"""跨域智能取数演示：五个场景跑完整链路，能执行的真丢给执行引擎跑。

意图和规划这两步用录制好的模型输出，不调真模型 —— 演示要能重复、能离线、
每次结果一样。链路的其余部分（满足分析、副本挑选、分段、嵌套、校验、执行）
全是真代码，没有任何 mock。

    python tools/demo_xdc.py

想在 Postman 上演示同样的场景，把每个场景的 `请求` 字段贴进
POST /xdc/plan 的 user_request 即可，那条路会调真模型。
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# 演示固定用桩配置和桩数据源：正式配置指向真实连接器，跑演示不该依赖它们在线，
# 也不该因为线上目录变动就演示不出预期结果。必须在导入 runtime.cross_dag 之前设。
import os
os.environ.setdefault("CROSS_DC_CONFIG", str(PROJECT_ROOT / "config" / "cross_dc.stub.yaml"))

from piflow_engine.cn.piflow.core.flow_bean import FlowBean
from piflow_engine.cn.piflow.core.frontend_dag_converter import convert_frontend_dag_to_piflow
from piflow_engine.cn.piflow.core.runner import Runner
from piflow_engine.cn.piflow.engine.local.constants import RUNNER_CONTEXT_WORKSPACE_ROOT
from runtime.cross_dag.config import get_cross_dc_config
from runtime.cross_dag.engine import plan_cross_dag
from runtime.cross_dag.plan_view import build_plan_view
from runtime.cross_dag.schema import CrossDagError, REMOTE_NODE_PREFIX

SRC = "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop"
SAVE = "piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop"
MERGE = "piflow_engine.cn.piflow.engine.local.table_merge_stop.TableMergeStop"

BJ, XJ = "10.0.1.10", "10.0.3.10"


class ScriptedLLM:
    """按顺序吐出录制好的模型输出。第一次是意图，第二次是规划。"""

    def __init__(self, *payloads):
        self._queue = list(payloads)

    def invoke(self, messages):
        payload = self._queue.pop(0)
        return type("Response", (), {"content": json.dumps(payload, ensure_ascii=False)})()


# ---- 演示数据 ---------------------------------------------------------
# 桩注册表里的 locator 指向的文件在本机并不存在，所以要真执行就得自己造几份。
# 三张表共享 站点ID + 日期 两个关联键，正好演示汇聚算子。

TABLES = {
    "obs.csv": (
        ["站点ID", "日期", "气温", "降水"],
        [["S01", "2024-01-01", "3.2", "0.0"],
         ["S01", "2024-01-02", "4.1", "2.5"],
         ["S02", "2024-01-01", "6.8", "0.0"],
         ["S02", "2024-01-02", "7.3", "1.2"]],
    ),
    "soil.csv": (
        ["站点ID", "日期", "土壤湿度"],
        [["S01", "2024-01-01", "0.31"],
         ["S01", "2024-01-02", "0.35"],
         ["S02", "2024-01-01", "0.28"],
         ["S03", "2024-01-01", "0.22"]],
    ),
    "prec.csv": (
        ["站点ID", "日期", "降水"],
        [["S01", "2024-01-01", "0.0"],
         ["S01", "2024-01-02", "2.5"]],
    ),
}


def build_workspace(root: Path) -> dict[str, str]:
    (root / "data").mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, (header, rows) in TABLES.items():
        target = root / "data" / name
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)
        paths[name] = f"/data/{name}"
    return paths


# ---- 五个场景 ---------------------------------------------------------

def scenarios(files: dict[str, str]) -> list[dict]:
    return [
        {
            "标题": "① 直接获取 —— 有现成数据集，不生成 DAG",
            "请求": "获取 2020-2025 年长江流域逐日降水数据",
            "看点": "需求四个维度全部命中 ds-prec，满足分析判定 direct，直接给访问路径",
            "意图": {
                "goal": "获取 2020-2025 年长江流域逐日降水数据",
                "requirements": [
                    {"key": "variables", "values": ["降水"]},
                    {"key": "region", "values": ["长江流域"]},
                    {"key": "time_range", "values": ["2020-2025"]},
                    {"key": "temporal_scale", "values": ["日"]},
                ],
                "datasets": [{"alias": "prec", "dataset_id": "ds-prec"}],
                "operations": [], "location_hints": [],
                "output": {"format": "csv"}, "assumptions": [], "unresolved": [],
            },
        },
        {
            "标题": "② 平台没有这份数据 —— 正常结论，不是报错",
            "请求": "获取长江流域 2020-2025 年的地下水位数据",
            "看点": "检索全部 6 个数据集后判定 unavailable，明确告诉用户缺什么",
            "意图": {
                "goal": "获取长江流域地下水位数据",
                "requirements": [{"key": "variables", "values": ["地下水位"]}],
                "datasets": [], "operations": [], "location_hints": [],
                "output": {}, "assumptions": [],
                "unresolved": ["候选数据集里没有地下水位相关的数据"],
            },
        },
        {
            "标题": "③ 多源汇聚 —— 单个数据集不够，组装一张表",
            "请求": "把长江流域的气温、降水和土壤湿度按站点和日期关联成一张表",
            "看点": "没有任何单集能覆盖三个变量，走 composition；用汇聚算子做三键关联",
            "意图": {
                "goal": "气象与土壤观测按站点日期关联",
                "requirements": [
                    {"key": "variables", "values": ["气温", "降水", "土壤湿度"]},
                    {"key": "region", "values": ["长江流域"]},
                ],
                "datasets": [
                    {"alias": "obs", "dataset_id": "ds-obs"},
                    {"alias": "soil", "dataset_id": "ds-soil"},
                ],
                "operations": [{"op": "关联", "target": "obs", "detail": "按站点与日期关联"}],
                "location_hints": [], "output": {"format": "csv", "name": "joined.csv"},
                "assumptions": [], "unresolved": [],
            },
            "规划": {
                "task": {"name": "气象土壤时空关联", "description": "两源按站点与日期内连接成一张宽表"},
                "nodes": [
                    {"node_name": "读气象", "skill_name": SRC,
                     "params": {"file_path": files["obs.csv"]}},
                    {"node_name": "读土壤", "skill_name": SRC,
                     "params": {"file_path": files["soil.csv"]}},
                    {"node_name": "时空关联", "skill_name": MERGE, "params": {
                        "input_1": {"source_node": "读气象", "source_param": "output"},
                        "input_2": {"source_node": "读土壤", "source_param": "output"},
                        "mode": "join", "join_keys": "站点ID,日期", "join_type": "inner",
                        "output_file_name": "joined.csv"}},
                    {"node_name": "落地", "skill_name": SAVE, "params": {
                        "output": {"source_node": "时空关联", "source_param": "output"},
                        "absolute_path": "/workspace/artifacts/joined.csv",
                        "overwrite": "true"}},
                ],
            },
            "产出": "joined.csv",
        },
        {
            "标题": "④ 跨域汇聚 —— 两个中心各出一份，只传中间结果",
            "请求": "把广州的气象观测和北京的土壤湿度按站点日期关联，结果存在北京",
            "看点": "两个中心各自读本地数据，广州侧算完只把中间结果传回北京，原始数据不出中心",
            "意图": {
                "goal": "跨中心关联气象与土壤观测",
                "requirements": [
                    {"key": "variables", "values": ["气温", "降水", "土壤湿度"]},
                ],
                "datasets": [
                    {"alias": "obs", "dataset_id": "ds-obs"},
                    {"alias": "soil", "dataset_id": "ds-soil"},
                ],
                "operations": [{"op": "关联", "target": "obs", "detail": "按站点与日期关联"}],
                "location_hints": [
                    {"center_id": XJ, "applies_to": "obs", "raw": "广州的气象观测"},
                    {"center_id": BJ, "applies_to": "关联", "raw": "结果存在北京"},
                ],
                "output": {"format": "csv"}, "assumptions": [], "unresolved": [],
            },
            "规划": {
                "task": {"name": "跨中心气象土壤关联", "description": "广州读气象，北京读土壤并汇聚落地"},
                "nodes": [
                    {"node_name": "读气象", "skill_name": SRC,
                     "params": {"file_path": files["obs.csv"]}, "dataCenter": XJ},
                    {"node_name": "读土壤", "skill_name": SRC,
                     "params": {"file_path": files["soil.csv"]}, "dataCenter": BJ},
                    {"node_name": "时空关联", "skill_name": MERGE, "params": {
                        "input_1": {"source_node": "读土壤", "source_param": "output"},
                        "input_2": {"source_node": "读气象", "source_param": "output"},
                        "mode": "join", "join_keys": "站点ID,日期", "join_type": "inner",
                        "output_file_name": "cross.csv"}, "dataCenter": BJ},
                    {"node_name": "落地", "skill_name": SAVE, "params": {
                        "output": {"source_node": "时空关联", "source_param": "output"},
                        "absolute_path": "/workspace/artifacts/cross.csv",
                        "overwrite": "true"}, "dataCenter": BJ},
                ],
            },
            "跨域": True,
        },
        {
            "标题": "⑤ 算子库缺能力 —— 拦下来，不硬凑",
            "请求": "把长江流域的 NDVI 从 16 天重采样成日尺度，再和气温降水关联",
            "看点": "关联能用真算子，重采样没有算子；宁可报缺口也不用语义不对的算子凑数",
            "预期拒绝": True,
            "意图": {
                "goal": "NDVI 重采样后与气象关联",
                "requirements": [{"key": "variables", "values": ["气温", "降水", "NDVI"]}],
                "datasets": [
                    {"alias": "obs", "dataset_id": "ds-obs"},
                    {"alias": "ndvi", "dataset_id": "ds-ndvi"},
                ],
                "operations": [
                    {"op": "重采样", "target": "ndvi", "detail": "16 天合成重采样为日尺度"},
                    {"op": "关联", "target": "obs", "detail": "按站点与日期关联"},
                ],
                "location_hints": [], "output": {}, "assumptions": [], "unresolved": [],
            },
            "规划": {
                "task": {"name": "NDVI 重采样后关联", "description": "缺时间重采样算子，用占位算子标出"},
                "nodes": [
                    {"node_name": "读气象", "skill_name": SRC,
                     "params": {"file_path": files["obs.csv"]}},
                    {"node_name": "读NDVI", "skill_name": SRC,
                     "params": {"file_path": files["obs.csv"]}},
                    {"node_name": "NDVI重采样", "skill_name": "missing_operator_stop", "params": {
                        "input": {"source_node": "读NDVI", "source_param": "output"},
                        "expected_skill": "temporal_resampler",
                        "capability": "把 16 天合成的 NDVI 重采样成日尺度时间序列",
                        "reason": "算子库中没有时间重采样算子"}},
                    {"node_name": "时空关联", "skill_name": MERGE, "params": {
                        "input_1": {"source_node": "读气象", "source_param": "output"},
                        "input_2": {"source_node": "NDVI重采样", "source_param": "output"},
                        "mode": "join", "join_keys": "站点ID,日期"}},
                    {"node_name": "落地", "skill_name": SAVE, "params": {
                        "output": {"source_node": "时空关联", "source_param": "output"},
                        "absolute_path": "/workspace/artifacts/x.csv", "overwrite": "true"}},
                ],
            },
        },
    ]


# ---- 跑 ---------------------------------------------------------------

def run_flow(dsl: dict, workspace: Path) -> str | None:
    runner = Runner.create().bind(RUNNER_CONTEXT_WORKSPACE_ROOT, str(workspace))
    process = runner.start(FlowBean.from_dict(convert_frontend_dag_to_piflow(dsl)).construct_flow())
    try:
        process.await_termination(timeout=60)
    except Exception as error:
        return f"{type(error).__name__}: {error}"
    return None


def count_remote(dsl: dict) -> int:
    total = 0
    for node in dsl.get("nodes") or []:
        if not str(node.get("node_id", "")).startswith(REMOTE_NODE_PREFIX):
            continue
        total += 1
        for param in node.get("input_params") or []:
            if param.get("param_name") == "subdag_definition_json":
                total += count_remote(json.loads(param["param_value"]))
    return total


def show_table(path: Path, limit: int = 5) -> None:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for index, row in enumerate(rows[:limit + 1]):
        line = "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
        print(f"      {line}")
        if index == 0:
            print(f"      {'-' * len(line)}")
    if len(rows) > limit + 1:
        print(f"      … 共 {len(rows) - 1} 行")


def main() -> int:
    config = get_cross_dc_config()
    workspace = Path(tempfile.mkdtemp(prefix="xdc-demo-"))
    files = build_workspace(workspace)
    failures = 0

    print(f"工作区: {workspace}")
    print(f"本地中心: {config.local_center_id}   已配置中心: {sorted(config.centers)}")

    for case in scenarios(files):
        print()
        print("=" * 78)
        print(case["标题"])
        print("=" * 78)
        print(f"  用户输入: {case['请求']}")
        print(f"  看点    : {case['看点']}")

        payloads = [case["意图"]]
        if "规划" in case:
            payloads.append(case["规划"])

        try:
            plan = plan_cross_dag(
                case["请求"],
                llm=ScriptedLLM(*payloads),
                plan_id=f"demo-{len(case['标题'])}",
                skill_resolver=lambda name: name,
            )
        except CrossDagError as error:
            # 规划本身不成立时链路直接中断，接口上是 HTTP 400。
            # 这不是崩溃，是把"做不到"如实说出来。
            print("\n  分支    : 规划被拒绝（接口返回 400）")
            print(f"  原因    : {error}")
            if case.get("预期拒绝"):
                print("  → 符合预期")
            else:
                failures += 1
            continue
        view = build_plan_view(plan)

        print(f"\n  分支    : {view['mode']}")
        print(f"  结论    : {view['conclusion']}")

        if view["mode"] == "direct":
            access = view["access"]
            print(f"  目标    : {access['name']}")
            print(f"  副本    : {access['replica']['replica_id']} @ "
                  f"{access['replica']['center_id']}  ->  {access['replica']['locator']}")
            print(f"  同样满足需求的其他数据集: {len(access['alternatives'])} 个")
            continue

        if view["mode"] == "unavailable":
            print(f"  缺失取值: {view['unavailable']['missing_values']}")
            print(f"  检索了  : {view['unavailable']['scanned_count']} 个数据集")
            continue

        dag = view["dag"]
        print(f"  DAG     : {len(dag['nodes'])} 节点 / {len(dag['edges'])} 连线")
        for node in dag["nodes"]:
            print(f"            {node['name']:12s} {node['skill_name'].rsplit('.', 1)[-1]:20s} "
                  f"@ {node['center_name']}")
        print(f"  跨中心传输: {dag['cross_center_transfers']} 次")

        if not view["validation"]["ok"]:
            print(f"  校验    : ✗ 不可执行")
            for error in view["validation"]["errors"]:
                print(f"            {error}")
            continue

        print(f"  校验    : ✓ 通过")

        if case.get("跨域"):
            remote = count_remote(plan.nested_dsl)
            need = dag["cross_center_transfers"]
            ok = remote == need
            print(f"  嵌套    : {len(plan.segment_graph.segments)} 个执行单元，"
                  f"生成 {remote} 个远程节点（需跨中心 {need} 次）{'✓' if ok else '✗'}")
            print(f"  说明    : 广州侧算完只把中间结果传回北京，原始数据不出中心。")
            print(f"            真执行需要三个中心都起 gRPC，这里只验证结构。")
            failures += 0 if ok else 1
            continue

        error = run_flow(plan.nested_dsl, workspace)
        if error:
            print(f"  执行    : ✗ {error}")
            failures += 1
            continue
        print(f"  执行    : ✓ 引擎跑通")
        produced = workspace / "artifacts" / case["产出"]
        if produced.exists():
            print(f"  产出    : {produced.name}")
            show_table(produced)

    print()
    print("=" * 78)
    print(f"{'全部通过' if not failures else f'{failures} 个场景未达预期'}")
    print("=" * 78)
    print(f"\n工作区保留在 {workspace}，看完可以删掉。")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
