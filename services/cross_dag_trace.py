"""全过程可观测：跑一遍真实链路，把每个环节的输入输出都记下来。"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from runtime.cross_dag.config import get_cross_dc_config
from runtime.cross_dag.engine import plan_cross_dag
from runtime.cross_dag.registry_stub import get_registry
from runtime.cross_dag.schema import CrossDagError

log = logging.getLogger("flow.cross_dag.trace")

STAGE_META: dict[str, dict[str, Any]] = {
    "intent": {
        "seq": 1,
        "title": "意图识别",
        "uses_llm": True,
        "描述": "自然语言 -> 结构化数据需求。模型只选 dataset_id，位置信息由注册表补全。",
        "看什么": [
            "datasets[].center_id 和 replicas 必须非空 —— 证明是从注册表查的，不是模型编的",
            "assumptions 是模型显式声明的假设，不该有静默猜测",
            "unresolved 里如果有『未注册的数据集』，说明模型产生了幻觉但被拦住了",
        ],
    },
    "satisfaction": {
        "seq": 2,
        "title": "需求满足分析",
        "uses_llm": False,
        "描述": "拿需求维度逐项去比对候选数据集的元数据，算出覆盖矩阵，"
                "决定走「直接获取」还是「智能组装」。确定性，不调模型。",
        "看什么": [
            "mode 就是分支结论：direct 表示有现成数据集能整个满足需求，不用生成 DAG",
            "coverages 是覆盖矩阵：每个数据集在每个维度上覆盖了哪些取值、缺哪些",
            "notes 里如果有『没有声明元数据』，说明注册方元数据不全，"
            "本可以直接获取的需求会被保守地退化成组装",
            "notes 里如果有『在所有候选数据集里都找不到』，说明平台确实没有这份数据",
        ],
    },
    "unavailable": {
        "seq": 3,
        "title": "无可用数据",
        "uses_llm": False,
        "描述": "检索完发现平台里没有能满足需求的数据。这是一个正常结论，不是失败："
                "直接给结果，不再花一次模型调用去规划一个注定跑不通的 DAG。",
        "看什么": [
            "missing_values 是缺的具体取值，可以直接展示给用户",
            "scanned_count 说明检索了多少个数据集才得出这个结论",
            "warnings 里带着意图识别阶段模型写的 unresolved，是更细的解释",
        ],
    },
    "access": {
        "seq": 4,
        "title": "数据访问路由",
        "uses_llm": False,
        "描述": "直接获取分支的终点：确定目标数据集，挑一个可用副本，给出访问路径。不生成 DAG。",
        "看什么": [
            "replica_decision 是完整的挑选证据：打分表 + 淘汰理由",
            "alternatives 是同样完整匹配的其他数据集，供用户切换",
            "用户点名了位置时，副本会优先取那个位置的",
        ],
    },
    "planning": {
        "seq": 5,
        "title": "全局 DAG 规划",
        "uses_llm": True,
        "描述": "数据需求 -> 算子级 DAG。注意这一层没有 edges，依赖藏在 params 的引用里。",
        "看什么": [
            "source 节点的 file_path 应该是 dataset://<id> 占位，不能是具体路径",
            "params 里 {source_node, source_param} 就是依赖关系",
            "只能有一个终点节点，否则下游会报错",
            "skill_name 必须来自算子清单，不能虚构",
        ],
    },
    "expand": {
        "seq": 6,
        "title": "展开为逻辑 DAG",
        "uses_llm": False,
        "描述": "补 node_id、把 params 引用物化成 bindings、回填生产者的 out_params。"
                "现有链路里这一步由外部 MCP 完成，仓库内没有，所以自带了一份。",
        "看什么": [
            "bindings 数量应等于 params 里引用的数量",
            "引用型入参 value_mode=reference（不进 properties），直接值 value_mode=manual",
            "source_node_ids / sink_node_ids 是后面分段的依据",
            "errors 非空说明规划本身有问题：产出被丢弃的悬空分支、"
            "算子库表达不了而用了占位算子 —— 这两类都会让方案不可执行",
            "warnings 里「意图认下了却没进 DAG」要当回事：规划器绕过去了，"
            "相关参数很可能是模型编的字面量",
        ],
    },
    "bind": {
        "seq": 7,
        "title": "位置绑定 + 副本挑选",
        "uses_llm": False,
        "描述": "决定每个节点在哪个中心执行。数据源节点先挑副本，再跟随副本所在中心。",
        "看什么": [
            "replica_decisions 是多副本路由的完整证据：打分表 + 淘汰理由",
            "chosen.locator 会被回写到节点的 file_path —— 不同副本路径不同，漏了会读错文件",
            "reasons 里每个节点都有人话解释：显式标注 / 副本挑选 / 继承上游 / 默认中心",
            "preferred_center_id 是一步前瞻的结果：下游钉死在哪，就优先选哪的副本",
        ],
    },
    "segment": {
        "seq": 8,
        "title": "分层分段",
        "uses_llm": False,
        "描述": "level(n) = max(level(上游) + 跨中心?1:0)，段 = (中心, level)；"
                "不能按中心朴素分组，A->B->A 会成环。分层之后再把同中心的段"
                "在不成环的前提下合回一个执行单元，避免给同机器的边套远程调用。",
        "看什么": [
            "同一个中心通常只剩一个执行单元；还留着多个，说明本地边与绕远端的路径并存，"
            "合并会成环，这时由 nester 就地内联兜底",
            "cross_edges 里中心相同的边不会变成远程节点，只有跨中心的才会",
            "终点单元必须唯一，它就是最外层，且必须是本地中心",
        ],
    },
    "nest": {
        "seq": 9,
        "title": "递归嵌套构造",
        "uses_llm": False,
        "描述": "从最下游段往上游递归。嵌套方向与数据流相反 —— 最外层是最下游的中心。",
        "看什么": [
            "depth = 嵌套层数",
            "nest_count 里若有段 > 1，说明菱形依赖导致该段会被重复执行",
            "远程节点数应当等于真正需要跨中心传输的次数；多出来就是划分有问题",
            "每个 __remote__ 节点的 subdag_definition_json 里装着完整的上游子 DAG",
            "每个子 DAG 末尾都有 __export__ 节点（FileSaveStop），否则远端查不到产物",
        ],
    },
    "validate": {
        "seq": 10,
        "title": "编译期校验",
        "uses_llm": False,
        "描述": "宁可提交前报错，也不要让坏 DAG 跑到一半失败 —— 跨域场景排查成本是十倍。",
        "看什么": [
            "errors 非空则拒绝执行",
            "warnings 常见的是菱形重复执行，属于嵌套模型的固有限制",
        ],
    },
}

_ORDER = [
    "intent",
    "satisfaction",
    "unavailable",
    "access",
    "planning",
    "expand",
    "bind",
    "segment",
    "nest",
    "validate",
]


def trace_cross_dag_plan(*, user_request: str, user_id: str) -> dict[str, Any]:
    """跑一遍完整真实链路，返回逐环节的输入输出。"""
    run_id = f"xdc-trace-{uuid.uuid4().hex[:8]}"
    # 这个端点是给人看的排障视图，不是前端契约。前端读 /xdc/plan 或
    # /xdc/plan/stream 的 done 事件 —— 那两个只给渲染需要的字段。
    config = get_cross_dc_config()
    registry = get_registry()

    started: dict[str, float] = {}
    records: dict[str, dict[str, Any]] = {}
    order_seen: list[str] = []

    def on_stage(stage: str, payload: dict[str, Any]) -> None:
        now = time.perf_counter()
        if payload.get("status") == "started":
            started[stage] = now
            if stage not in order_seen:
                order_seen.append(stage)
            return
        record = dict(payload)
        record.pop("status", None)
        record["elapsed_ms"] = round((now - started.get(stage, now)) * 1000, 1)
        records[stage] = record

    from runtime.cross_dag.intent import LAST_CALL_STATS

    LAST_CALL_STATS.clear()

    t0 = time.perf_counter()
    error: str | None = None
    plan = None
    try:
        plan = plan_cross_dag(user_request, plan_id=run_id, on_stage=on_stage)
    except CrossDagError as exc:
        error = str(exc)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    total_ms = round((time.perf_counter() - t0) * 1000, 1)

    failed_at = next((s for s in _ORDER if s in order_seen and s not in records), None)

    stages = [
        _build_stage(name, records[name], user_request, registry)
        for name in _ORDER
        if name in records
    ]

    if failed_at:
        failed_stage = _build_stage(failed_at, {}, user_request, registry)
        failed_stage["failed"] = True
        failed_stage["error"] = error
        insert_at = _ORDER.index(failed_at)
        stages.insert(min(insert_at, len(stages)), failed_stage)

    # 分支不同，出现的阶段也不同，静态 seq 会跳号。按实际顺序重排一遍。
    for index, stage in enumerate(stages, start=1):
        stage["seq"] = index

    result: dict[str, Any] = {
        "用途": "排障用：逐环节输入输出。前端请改用 POST /xdc/plan 或 /xdc/plan/stream",
        "run_id": run_id,
        "user_request": user_request,
        "total_elapsed_ms": total_ms,
        # 数真实发生的模型调用，不是数「这个阶段用不用模型」——
        # 阶段失败时后者会虚高（阶段进了列表，调用其实没成功）。
        "llm_calls": len(LAST_CALL_STATS),
        "stage_count": len(stages),
        "ok": error is None,
        "环境": {
            "local_center_id": config.local_center_id,
            "centers": sorted(config.centers),
            "replica_weights": config.replica_weights or "（默认值）",
            "数据源": "注册桩（stub）",
            "大模型": "真实调用",
        },
        "stages": stages,
    }

    if error:
        result["error"] = error
        result["failed_at"] = failed_at
        result["提示"] = f"链路在【{STAGE_META.get(failed_at, {}).get('title', failed_at)}】环节失败"
        log.warning("cross dag trace failed run_id=%s stage=%s err=%s", run_id, failed_at, error)
        return result

    assert plan is not None
    result["final"] = _final_block(plan)
    log.info("cross dag traced run_id=%s stages=%s ms=%s", run_id, len(stages), total_ms)
    return result


def _final_block(plan: Any) -> dict[str, Any]:
    """收尾块按分支给内容。

    直接获取分支没有 DAG，此前照样报「节点数 0 / 分段数 0 / 涉及中心 []」和一个
    空的 nested_dsl —— 一次成功的直接获取看起来像什么都没干成。
    """
    from runtime.cross_dag.schema import MODE_COMPOSITION, MODE_DIRECT

    block: dict[str, Any] = {
        "plan_id": plan.plan_id,
        "mode": plan.mode,
        "结论": plan.satisfaction.reason if plan.satisfaction else "",
        "validation": plan.validation.to_json(),
    }

    if plan.mode == MODE_COMPOSITION:
        block["summary"] = {
            "节点数": len(plan.logical_dag.nodes),
            "分段数": len(plan.segment_graph.segments),
            "跨段边数": len(plan.segment_graph.cross_edges),
            "涉及中心": sorted({s.center_id for s in plan.segment_graph.segments.values()}),
        }
        # nested_dsl 不在这里重复：nest 阶段的 output 里已经有完整一份，
        # 两处一模一样只会让人以为是两个东西
        block["可执行"] = plan.validation.ok
        block["下一步"] = f"POST /xdc/execute  body: {{\"plan_id\": \"{plan.plan_id}\"}}"
    elif plan.mode == MODE_DIRECT:
        access = plan.direct_access
        chosen = access.replica_decision.chosen if access and access.replica_decision else None
        block["summary"] = {
            "目标数据集": access.name if access else "",
            "副本": chosen.replica_id if chosen else "",
            "所在中心": chosen.center_id if chosen else "",
            "访问路径": chosen.locator if chosen else "",
            "同样满足需求的其他数据集": len(access.alternatives) if access else 0,
        }
        block["可执行"] = plan.validation.ok
        block["下一步"] = f"POST /xdc/execute  body: {{\"plan_id\": \"{plan.plan_id}\"}}（直接返回访问路由，不提交 DAG）"
    else:
        report = plan.satisfaction
        block["summary"] = {
            "检索数据集数": report.scanned_count if report else 0,
            "缺失的需求取值": report.missing_values if report else [],
        }
        block["可执行"] = False
        block["下一步"] = "平台没有这部分数据，无需执行；可换个说法或补充数据源后重试"
    return block


def _build_stage(
    name: str,
    record: dict[str, Any],
    user_request: str,
    registry: Any,
) -> dict[str, Any]:
    meta = STAGE_META.get(name, {})
    elapsed = record.pop("elapsed_ms", 0.0)

    stage: dict[str, Any] = {
        "seq": meta.get("seq", 0),
        "stage": name,
        "title": meta.get("title", name),
        "uses_llm": bool(meta.get("uses_llm")),
        "elapsed_ms": elapsed,
        "描述": meta.get("描述", ""),
        "看什么": meta.get("看什么", []),
        "input": _describe_input(name, record, user_request, registry),
        "output": record,
    }

    llm_key = {"intent": "意图识别", "planning": "DAG 规划"}.get(name)
    if llm_key:
        from runtime.cross_dag.intent import LAST_CALL_STATS

        stats = LAST_CALL_STATS.get(llm_key)
        if stats:
            stage["llm开销"] = dict(stats)

    return stage


def _describe_input(
    name: str,
    record: dict[str, Any],
    user_request: str,
    registry: Any,
) -> Any:
    """每个环节的输入是上一环节的输出，这里只标注来源，避免响应体翻倍。"""
    if name == "intent":
        return {
            "用户请求": user_request,
            "候选数据集": [
                {"dataset_id": d.dataset_id, "名称": d.name, "副本数": len(d.replicas)}
                for d in registry.list_datasets()
            ],
        }
    if name == "satisfaction":
        return "上一环节的 IntentSpec（requirements + datasets）+ 数据集的维度元数据"
    if name == "unavailable":
        return "满足分析的覆盖结论 + 意图识别里模型写下的 unresolved"
    if name == "access":
        return "满足分析给出的完整匹配数据集 + 各副本状态与资源指标"
    if name == "planning":
        return "上一环节的 IntentSpec + 可用算子清单"
    if name == "expand":
        return "上一环节的规划态 DAG JSON"
    if name == "bind":
        return "逻辑 DAG + IntentSpec 里的副本清单 + config/cross_dc.yaml 的权重"
    if name == "segment":
        return "逻辑 DAG + 每个节点的中心归属"
    if name == "nest":
        return "逻辑 DAG + 段图 + 各中心的 grpc_endpoint"
    if name == "validate":
        return "段图 + 嵌套 DSL"
    return None
