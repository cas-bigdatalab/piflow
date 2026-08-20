"""意图识别与全局 DAG 规划 —— 流水线里仅有的两次 LLM 调用。"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from .registry_stub import DatasetRecord, DatasourceRegistry, get_registry
from .schema import (
    DATASET_URI_PREFIX,
    CrossDagError,
    IntentDataset,
    IntentSpec,
    LocationHint,
    ReplicaCandidate,
    RequirementFacet,
)

log = logging.getLogger("flow.cross_dag.intent")

SYSTEM_SKILL_CATALOG: list[dict[str, Any]] = [
    {
        "skill_name": "piflow_engine.cn.piflow.engine.local.source_file_stop.SourceFileStop",
        "描述": "文件输入算子。读取工作区内的一个文件作为数据源。",
        "输入参数": {"file_path": "文件路径"},
        "输出参数": ["output"],
        "可接上游的参数": [],
        "可接上游数": 0,
    },
    {
        "skill_name": "piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop",
        "描述": "文件输出算子。把上游产物保存到指定路径，作为 DAG 终点。",
        "输入参数": {"output": "上游产物引用", "absolute_path": "保存路径", "overwrite": "true/false"},
        "输出参数": ["output"],
        "可接上游的参数": ["output"],
        "可接上游数": 1,
    },
    {
        "skill_name": "piflow_engine.cn.piflow.engine.local.corpus_dataset_source_stop.CorpusDatasetSourceStop",
        "描述": (
            "语料数据集输入算子。按 dataset_id 从语料寻址系统取数：查数据集详情拿 cstr，"
            "再取下载地址并下载到本地。没有上游，只能作为 DAG 的起点。"
            "读取已注册的语料数据集时用它，不要用文件输入算子。"
        ),
        "输入参数": {"dataset_id": "数据集 ID，写成 dataset://<dataset_id>，系统会替换"},
        "输出参数": ["output"],
        "可接上游的参数": [],
        "可接上游数": 0,
    },
    {
        "skill_name": "piflow_engine.cn.piflow.engine.local.table_merge_stop.TableMergeStop",
        "描述": (
            "多路表格汇聚算子。把 2~8 路上游的 CSV/TSV 合成一张表。"
            "mode=concat 纵向拼接（行堆叠，列名取并集，缺列留空）；"
            "mode=join 横向关联（按 join_keys 逐路关联，以 input_1 为基准）。"
            "需要把多个数据集合到一起时用它。"
        ),
        "输入参数": {
            "input_1": "第 1 路上游产物引用（必填）",
            "input_2": "第 2 路上游产物引用（必填）",
            "input_3": "第 3 路上游产物引用",
            "input_4": "第 4 路上游产物引用",
            "input_5": "第 5 路上游产物引用",
            "input_6": "第 6 路上游产物引用",
            "input_7": "第 7 路上游产物引用",
            "input_8": "第 8 路上游产物引用",
            "mode": "concat 或 join，默认 concat",
            "join_keys": "mode=join 时必填，关联键列名，逗号分隔，如 站点ID,日期",
            "join_type": "inner/left/outer，默认 inner",
            "output_file_name": "输出文件名，默认 merged.csv",
            "delimiter": "分隔符，默认英文逗号",
            "encoding": "编码，默认 utf-8",
            "source_column": "concat 时额外记录每行来自哪个端口的列名，留空则不记录",
        },
        "输出参数": ["output"],
        "可接上游的参数": [f"input_{i}" for i in range(1, 9)],
        "可接上游数": 8,
    },
    {
        "skill_name": "piflow_engine.cn.piflow.engine.local.tar_archive_merge_stop.TarArchiveMergeStop",
        "描述": (
            "多路 tar 归档汇聚算子。把 2~8 个语料数据集下载得到的 tar 包合成一个 tar，"
            "不解包、不改变成员内容。用户要求打包、归档或合并多个 tar 时使用。"
        ),
        "输入参数": {
            **{f"data{i}": f"第 {i} 路上游 tar 产物引用" for i in range(1, 9)},
            "output_file_name": "输出归档文件名，默认 result.tar",
        },
        "输出参数": ["output"],
        "可接上游的参数": [f"data{i}" for i in range(1, 9)],
        "可接上游数": 8,
    },
]


def build_dataset_catalog(registry: DatasourceRegistry | None = None) -> list[dict[str, Any]]:
    resolved = registry or get_registry()
    catalog: list[dict[str, Any]] = []
    for item in resolved.list_datasets():
        entry: dict[str, Any] = {
            "dataset_id": item.dataset_id,
            "名称": item.name,
            "描述": item.description,
            "locator": item.locator,
            "标签": list(item.tags),
            "读取契约": {
                "skill_name": item.source_skill,
                "param_name": item.source_param,
                "param_value": f"{DATASET_URI_PREFIX}{item.dataset_id}",
                "output_param": item.source_output_param,
            },
        }
        if item.facets:
            entry["维度"] = {k: list(v) for k, v in item.facets.items()}
        catalog.append(entry)
    return catalog


def build_facet_catalog(
    registry: DatasourceRegistry | None = None,
    config: Any = None,
) -> list[dict[str, Any]]:
    """可用的需求维度清单。

    维度键取自注册方在数据集上声明的元数据，label / mode 取自 config；
    平台不预设任何维度，换学科只要注册方换元数据、config 换声明。
    """
    from .config import get_cross_dc_config

    resolved_registry = registry or get_registry()
    resolved_config = config or get_cross_dc_config()

    values_of: dict[str, list[str]] = {}
    for item in resolved_registry.list_datasets():
        for key, values in (item.facets or {}).items():
            bucket = values_of.setdefault(str(key), [])
            for value in values:
                text = str(value).strip()
                if text and text not in bucket:
                    bucket.append(text)

    for key in resolved_config.requirement_facets:
        values_of.setdefault(str(key), [])

    catalog: list[dict[str, Any]] = []
    for key in sorted(values_of):
        catalog.append(
            {
                "key": key,
                "名称": resolved_config.facet_label(key),
                "是否可由多个数据集分摊覆盖": (
                    "是" if resolved_config.facet_mode(key) == "cover_all" else "否"
                ),
                "已有取值": values_of[key][:40],
            }
        )
    return catalog


def build_skill_catalog(
    extra_skills: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """可用算子清单。"""
    catalog = list(SYSTEM_SKILL_CATALOG)
    if extra_skills:
        catalog.extend(extra_skills)
        return catalog

    try:
        from runtime.dag_manager import list_dag_skills

        response = list_dag_skills(page=1, page_size=500) or {}
    except Exception:
        log.warning("dag_skills 不可用，算子清单仅含系统算子", exc_info=True)
        return catalog

    for skill in response.get("data") or []:
        name = getattr(skill, "skill_name", None) or getattr(skill, "name", None)
        if not name:
            continue

        entry: dict[str, Any] = {
            "skill_name": str(name),
            "描述": str(getattr(skill, "description", "") or ""),
        }
        inputs = _param_names(getattr(skill, "input_params", None))
        outputs = _param_names(getattr(skill, "output_params", None))
        if inputs:
            entry["输入参数"] = inputs
        if outputs:
            entry["输出参数"] = outputs

        spec = _skill_param_spec(skill)
        if spec is not None and spec.upstream_params is not None:
            entry["可接上游的参数"] = sorted(spec.upstream_params)
            entry["可接上游数"] = len(spec.upstream_params)
        catalog.append(entry)

    return catalog


def _skill_param_spec(skill: Any) -> Any:
    """取算子的参数契约，端口信息以 skill.json 为准。"""
    from .planner_bridge import _spec_from_params, _spec_from_skill_json

    skill_path = getattr(skill, "skill_path", None)
    if skill_path:
        try:
            from infra.config_loader import resolve_workspace_root

            spec = _spec_from_skill_json(resolve_workspace_root() / skill_path / "skill.json")
            if spec is not None:
                return spec
        except Exception:
            pass
    return _spec_from_params(getattr(skill, "input_params", None))


def _param_names(raw: Any) -> list[str]:
    """从 DagSkill 的 input_params/output_params 里取参数名。"""
    if isinstance(raw, dict):
        raw = raw.get("params")
    if not isinstance(raw, list):
        return []

    names: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            name = item.get("name") or item.get("param_name")
            if not name:
                continue
            if item.get("required"):
                names.append(f"{name}(必填)")
            else:
                names.append(str(name))
        elif isinstance(item, str):
            names.append(item)
    return names


def recognize_intent(
    user_request: str,
    *,
    llm: Any = None,
    registry: DatasourceRegistry | None = None,
    config: Any = None,
) -> IntentSpec:
    if not user_request.strip():
        raise CrossDagError("用户请求为空")

    from agents.cross_dag.prompt import build_intent_prompt
    from .config import get_cross_dc_config

    resolved_registry = registry or get_registry()
    catalog = build_dataset_catalog(resolved_registry)
    resolved_config = config or get_cross_dc_config()
    center_catalog = _center_catalog(resolved_config)
    facet_catalog = build_facet_catalog(resolved_registry, resolved_config)
    model = llm or _default_llm()

    raw = _invoke_json(
        model,
        system_prompt=build_intent_prompt(
            catalog, center_catalog, resolved_config.location_term, facet_catalog
        ),
        user_prompt=user_request,
        what="意图识别",
    )

    intent = IntentSpec(
        goal=str(raw.get("goal") or user_request),
        user_request=user_request,
        operations=list(raw.get("operations") or []),
        output=dict(raw.get("output") or {}),
        assumptions=[str(x) for x in raw.get("assumptions") or []],
        unresolved=[str(x) for x in raw.get("unresolved") or []],
    )

    for item in raw.get("requirements") or []:
        if not isinstance(item, dict):
            continue
        facet = RequirementFacet.from_json(item)
        if not facet.key or not facet.values:
            continue
        facet.label = facet.label or resolved_config.facet_label(facet.key)
        facet.mode = resolved_config.facet_mode(facet.key)
        intent.requirements.append(facet)

    known_centers = set(resolved_config.centers)
    for item in raw.get("location_hints") or []:
        if not isinstance(item, dict):
            continue
        center_id = str(item.get("center_id", "") or "").strip()
        if not center_id:
            continue
        if center_id not in known_centers:
            intent.unresolved.append(f"模型指定了未注册的中心 {center_id}，已忽略")
            continue
        intent.location_hints.append(LocationHint.from_json(item))

    mentioned = _mentioned_locations(user_request, resolved_config)
    if mentioned and not intent.location_hints:
        term = resolved_config.location_term
        intent.unresolved.append(
            f"用户请求里提到了{term} {mentioned}，但意图识别未产出 location_hints；"
            f"跨{term}要求可能被忽略，请检查规划结果是否退化成单一{term}"
        )

    for item in raw.get("datasets") or []:
        dataset_id = str(item.get("dataset_id") or "").strip()
        if not dataset_id:
            continue
        record = resolved_registry.get_dataset(dataset_id)
        if record is None:
            intent.unresolved.append(f"模型选择了未注册的数据集 {dataset_id}，已忽略")
            continue
        intent.datasets.append(_to_intent_dataset(item, record))

    if not intent.datasets and not intent.unresolved:
        intent.unresolved.append("未能从候选数据集中匹配到满足需求的数据")

    return intent


def plan_global_dag(
    intent: IntentSpec,
    *,
    llm: Any = None,
    skill_catalog: list[dict[str, Any]] | None = None,
    config: Any = None,
) -> dict[str, Any]:
    if not intent.datasets:
        raise CrossDagError(
            "意图中没有可用数据集，无法规划 DAG。未解决问题: "
            + ("；".join(intent.unresolved) or "无")
        )

    from agents.cross_dag.prompt import build_planning_prompt
    from .config import get_cross_dc_config

    model = llm or _default_llm()
    resolved_config = config or get_cross_dc_config()
    center_catalog = _center_catalog(resolved_config)
    dataset_catalog = [
        {
            "alias": item.alias,
            "dataset_id": item.dataset_id,
            "名称": item.name,
            "引用方式": f"{DATASET_URI_PREFIX}{item.dataset_id}",
            "读取算子": item.source_skill,
            "读取参数": item.source_param,
            "输出参数": item.source_output_param,
            "副本数": len(item.replicas),
        }
        for item in intent.datasets
    ]

    resolved_catalog = skill_catalog or build_skill_catalog()

    planning_json = _invoke_json(
        model,
        system_prompt=build_planning_prompt(
            dataset_catalog,
            resolved_catalog,
            center_catalog,
            resolved_config.location_term,
            sorted(resolved_config.placeholder_skills),
        ),
        user_prompt=json.dumps(
            {
                "用户原始请求": intent.user_request or intent.goal,
                "执行位置要求": [h.to_json() for h in intent.location_hints],
                "意图": intent.to_json(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        what="DAG 规划",
    )

    if not planning_json.get("nodes"):
        raise CrossDagError("规划结果中没有 nodes")
    return planning_json


def _center_catalog(config: Any) -> list[dict[str, Any]]:
    """喂给模型的执行位置清单。带上别名，模型才能把用户的叫法对应到 ID。"""
    catalog: list[dict[str, Any]] = []
    for center in config.centers.values():
        entry: dict[str, Any] = {"center_id": center.center_id, "名称": center.center_name}
        if center.aliases:
            entry["别名"] = list(center.aliases)
        catalog.append(entry)
    return catalog


def _mentioned_locations(user_request: str, config: Any) -> list[str]:
    """请求里提到了哪些执行位置。"""
    text = user_request.lower()
    hit: list[str] = []
    for center in config.centers.values():
        for term in center.mention_terms():
            if term.lower() in text:
                hit.append(center.center_id)
                break
    return hit


def _to_intent_dataset(raw: dict[str, Any], record: DatasetRecord) -> IntentDataset:
    alias = str(raw.get("alias") or "").strip() or record.dataset_id
    return IntentDataset(
        alias=alias,
        dataset_id=record.dataset_id,
        source_id=record.source_id,
        center_id=record.center_id,
        locator=record.locator,
        name=record.name,
        replicas=[ReplicaCandidate.from_json(r.to_json()) for r in record.replicas],
        facets={str(k): [str(x) for x in v] for k, v in (record.facets or {}).items()},
        source_skill=record.source_skill,
        source_param=record.source_param,
        source_output_param=record.source_output_param,
    )


def _default_llm() -> Any:
    from agents.cross_dag.factory import CrossDagLLMFactory

    return CrossDagLLMFactory.create_llm()


LAST_CALL_STATS: dict[str, dict[str, Any]] = {}


def _invoke_json(
    llm: Any,
    *,
    system_prompt: str,
    user_prompt: str,
    what: str,
) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    text, stats = _call(llm, messages, what)

    try:
        return _extract_json_object(text)
    except ValueError as exc:
        parse_error = str(exc)
    log.warning("%s 首次输出非法 JSON，重试一次: %s", what, parse_error)

    repair = [
        *messages,
        {"role": "assistant", "content": text},
        {
            "role": "user",
            "content": (
                f"上面的输出不是合法 JSON，解析报错：{parse_error}\n"
                "请只重新输出修正后的完整 JSON 对象，不要解释、不要 markdown 代码块。"
            ),
        },
    ]
    retry_text, retry_stats = _call(llm, repair, what)
    stats["重试"] = retry_stats
    LAST_CALL_STATS[what] = stats

    try:
        return _extract_json_object(retry_text)
    except ValueError as retry_exc:
        raise CrossDagError(
            f"{what}两次均未返回合法 JSON: {retry_exc}\n原始输出:\n{retry_text[:2000]}"
        ) from retry_exc


def _call(llm: Any, messages: list[dict[str, str]], what: str) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    response = llm.invoke(messages)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    content = getattr(response, "content", response)
    text = content if isinstance(content, str) else _join_content(content)

    stats: dict[str, Any] = {
        "耗时_ms": elapsed_ms,
        "提示词字符数": sum(len(m.get("content", "")) for m in messages),
        "输出字符数": len(text),
    }
    stats.update(_usage_of(response))
    LAST_CALL_STATS[what] = stats
    log.info("llm call what=%s stats=%s", what, stats)
    return text, stats


def _usage_of(response: Any) -> dict[str, Any]:
    """把 token 用量抽出来，重点是 reasoning_tokens ——"""
    out: dict[str, Any] = {}
    meta = getattr(response, "response_metadata", None) or {}
    usage = meta.get("token_usage") or getattr(response, "usage_metadata", None) or {}
    if not isinstance(usage, dict):
        return out

    for src, dst in (
        ("prompt_tokens", "输入tokens"),
        ("input_tokens", "输入tokens"),
        ("completion_tokens", "输出tokens"),
        ("output_tokens", "输出tokens"),
        ("total_tokens", "总tokens"),
    ):
        if usage.get(src) is not None:
            out[dst] = usage[src]

    details = usage.get("completion_tokens_details") or usage.get("output_token_details") or {}
    if isinstance(details, dict) and details.get("reasoning_tokens") is not None:
        out["思考tokens"] = details["reasoning_tokens"]
        out["思考模式"] = "开启（这是慢的主因）" if details["reasoning_tokens"] else "已关闭"
    return out


def _join_content(content: Any) -> str:
    if isinstance(content, list):
        parts = []
        for chunk in content:
            if isinstance(chunk, dict):
                parts.append(str(chunk.get("text", "")))
            else:
                parts.append(str(chunk))
        return "".join(parts)
    return str(content)


def _extract_json_object(text: str) -> dict[str, Any]:
    """容忍模型套 markdown 代码块或前后加话。"""
    stripped = text.strip()

    fenced = re.search(r"```(?:json)?\s*(.+?)\s*```", stripped, re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("输出中找不到 JSON 对象")
        parsed = json.loads(stripped[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("输出的顶层不是 JSON 对象")
    return parsed
