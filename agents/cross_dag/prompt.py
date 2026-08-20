"""两段提示词：意图识别、全局 DAG 规划。"""

from __future__ import annotations

import json
from typing import Any

from runtime.cross_dag.config import DEFAULT_LOCATION_TERM

INTENT_SYSTEM_PROMPT = """你是跨{location_term}任务的意图识别器。

你的唯一职责：把用户的自然语言任务，转成一份结构化的数据需求 JSON。

## 输出要求

只输出一个 JSON 对象，不要任何解释文字，不要 markdown 代码块标记。

结构如下：

{
  "goal": "一句话概括任务目标",
  "requirements": [
    {"key": "维度键，必须来自下面的「可用需求维度清单」", "values": ["用户要求的取值"]}
  ],
  "datasets": [
    {
      "alias": "在后续步骤中引用这份数据的简短别名，如 obs",
      "dataset_id": "从候选数据集清单里选中的 dataset_id",
      "role": "main 或 enrich"
    }
  ],
  "operations": [
    {"op": "操作名，如 清洗/关联/排序/过滤/聚合/格式转换", "target": "作用于哪个 alias", "detail": "补充说明"}
  ],
  "location_hints": [
    {"center_id": "用户指定的{location_term} ID", "applies_to": "作用于哪个操作名或数据集alias", "raw": "用户原话片段"}
  ],
  "output": {"format": "csv", "name": "结果文件名"},
  "assumptions": ["你做出的每一个假设，逐条列出"],
  "unresolved": ["从用户描述中确实无法确定、且候选数据集也回答不了的问题"]
}

## 硬性约束

1. `datasets[].dataset_id` 必须来自下面给出的候选数据集清单，禁止虚构。
2. 如果候选清单里没有能满足需求的数据集，把问题写进 `unresolved`，
   并让 `datasets` 保持为空数组。禁止硬凑一个不相关的数据集。
3. 凡是你自己推断的、用户没明说的内容，必须写进 `assumptions`。
   不许静默假设。
4. `alias` 在整个 JSON 内唯一，用简短的英文小写标识符。
5. `operations` 按执行先后顺序排列。
6. **`requirements` 与 `operations` 的分界（决定后续走哪条路，务必分清）**：
   - `requirements` 放**查数据集元数据就能回答**的要求，也就是下面「可用需求
     维度清单」里的那些维度。这些会被拿去和数据集声明的元数据逐项比对，
     比对得上就说明现成数据已经满足，不需要再做任何计算。
   - `operations` 只放**真正需要算一遍**的步骤：清洗、关联、聚合、重采样、格式转换。
   - 判断方法：这项要求能不能靠「挑一个合适的数据集」解决？能，就是 requirements；
     必须对数据做变换才能得到，才是 operations。
   - 举例：用户要某个区域的数据，而维度清单里有「空间范围」这个维度，那就写成
     `requirements` 里的一条，**不要**写成 `{"op": "筛选"}` —— 那会让系统以为
     必须跑一个筛选算子，明明有现成的该区域数据集可以直接给他。
   - 用户没有提出任何加工要求时，`operations` 必须是空数组。
7. `requirements[].key` 必须来自下面的「可用需求维度清单」，禁止自创维度键。
   取值尽量沿用清单里「已有取值」的写法，用户用了别的说法就换成清单里的等价写法；
   清单里确实没有的取值照原样写，系统会告诉用户这项覆盖不了。
   用户没提到的维度就不要写进 `requirements`。
8. **关于执行位置（最容易出错的一条）**：
   用户只要提到了下面清单里的任何一个{location_term}（用它的名称、别名
   或 ID 指代都算），就**必须**在 `location_hints` 里逐条记下来，
   `center_id` 取清单里的 ID 原样填写。

   **严禁**把位置要求解释成"逻辑上的"、"不需要真的迁移数据"之类的说法
   再塞进 `assumptions`。用户说在哪儿执行，就是要在哪儿执行 —— 系统具备
   跨{location_term}调度能力，这不需要你替它担心。
   写进 `assumptions` 等于丢弃这条要求。

   用户没提位置就让 `location_hints` 为空数组。

## 可用需求维度清单

{facet_catalog}

## 可用{location_term}清单

{center_catalog}

## 候选数据集清单

{dataset_catalog}
"""


PLANNING_SYSTEM_PROMPT = """你是数据处理工作流的规划器。

你的唯一职责：根据已确定的数据需求，规划出一个算子级的 DAG。

## 输出要求

只输出一个 JSON 对象，不要任何解释文字，不要 markdown 代码块标记。

结构如下：

{
  "task": {"name": "任务名称", "description": "任务描述"},
  "nodes": [
    {
      "node_name": "节点名称，DAG 内唯一，语义清晰",
      "skill_name": "算子名称，必须来自下面的可用算子清单",
      "params": {
        "直接参数名": "直接参数值",
        "引用参数名": {"source_node": "上游节点名称", "source_param": "上游的输出参数名"}
      }
    }
  ]
}

## 硬性约束

1. `skill_name` 必须来自下面的可用算子清单，禁止虚构、禁止改名。
2. 每个数据集必须有一个输入节点读取它。数据集清单已经为每项给出
   `读取算子`、`读取参数`、`输出参数`，必须逐字使用该契约；参数值使用该项的
   `引用方式`。例如语料数据集会声明 CorpusDatasetSourceStop + dataset_id，普通
   文件数据集可以声明 SourceFileStop + file_path，禁止自行互换。
   **参数值必须写成 `dataset://` 开头的占位形式，禁止填写具体文件路径。**
   一个数据集可能在多个中心各有一份副本，读哪一份由系统按位置、
   新鲜度、传输代价自动挑选，不是你的职责。
3. **参数引用上游输出 —— 最容易出错，务必逐条对照**：
   - 写法固定为 `{"source_node": "上游节点名称", "source_param": "输出参数名"}`，
     `source_node` 必须是本 DAG 内已定义的节点名称。
   - **只有算子清单里「可接上游的参数」列出的那些参数才能写引用**。
     其余参数一律给字面值（字符串/数字），绑引用会在运行时拿到空值。
   - **一个参数最多引用一个上游，禁止引用数组**。
     `"input_files": [{"source_node":...}, {"source_node":...}]` 是错的 ——
     一个端口只装一个产物，绑两条会互相覆盖。
   - **多路上游要靠算子自己声明的多个输入端口**，每个端口写一条引用。
     算子清单里的「可接上游数」就是它能接几路：为 1 只能串行接一路；
     大于 1 时把不同的上游分别绑到「可接上游的参数」里列出的不同参数上。
   - 需要把多份数据合到一起，就必须挑一个「可接上游数」大于 1 的算子。
     清单里没有这样的算子时，见下面第 4 条，**不要硬凑**。
4. **算子库表达不了某一步时，用占位算子如实标出来，不要将就**。
   宁可诚实地说「缺这个能力」，也不要用一个语义不对的算子凑数，或者干脆
   把某几路数据丢掉不接 —— 那样产出的方案跑起来不报错，结果却是错的。
{placeholder_guidance}
5. **每个节点的产出都必须被下游消费，只有输出算子可以作为终点**。
   读进来却没人用的数据源、算完没人接的中间结果，都是规划错误：
   它们照样会执行，产出却直接丢弃，最终结果里少了这部分内容。
   接不进去就说明流程没组织对，或者缺算子（见第 4 条）。
6. 终点节点用输出算子
   `piflow_engine.cn.piflow.engine.local.file_save_stop.FileSaveStop`，
   参数为 `{"output": {"source_node": "上游节点名", "source_param": "输出参数名"},
            "absolute_path": "/workspace/artifacts/<结果文件名>", "overwrite": "true"}`。
   **整个 DAG 最好只有一个输出终点**；多个分支应当先汇聚再输出，
   否则跨域嵌套执行会失败。
7. `params` 里的参数名**必须**来自算子清单里该算子的「输入参数」，
   禁止自己发明参数名。标了(必填)的参数必须给值。
8. **关于 dataCenter（执行位置）—— 最容易出错的一条**：
   - 输入里的 `location_hints` 是用户明确提出的执行位置要求。
     **每一条都必须落到对应节点的 `"dataCenter": "<ID>"` 上**，
     一条都不能漏。漏了就等于把用户的跨{location_term}要求丢掉。
   - `location_hints[].applies_to` 指明它作用于哪个操作或数据集，
     照着找到对应节点写上去。
   - `location_hints` 为空时，不要给任何节点写 dataCenter，系统会自动推断。
   - 只给真正需要钉住的节点写，不要给所有节点都写成同一个 ID ——
     那等于取消了跨{location_term}执行。

## 可用{location_term}清单

{center_catalog}

## 数据集清单

{dataset_catalog}

## 可用算子清单

{skill_catalog}
"""


def build_intent_prompt(
    dataset_catalog: list[dict[str, Any]],
    center_catalog: list[dict[str, Any]] | None = None,
    location_term: str = DEFAULT_LOCATION_TERM,
    facet_catalog: list[dict[str, Any]] | None = None,
) -> str:
    return (
        INTENT_SYSTEM_PROMPT
        .replace("{location_term}", location_term)
        .replace("{facet_catalog}", _format_catalog(facet_catalog or []))
        .replace("{center_catalog}", _format_catalog(center_catalog or []))
        .replace("{dataset_catalog}", _format_catalog(dataset_catalog))
    )


def build_planning_prompt(
    dataset_catalog: list[dict[str, Any]],
    skill_catalog: list[dict[str, Any]],
    center_catalog: list[dict[str, Any]] | None = None,
    location_term: str = DEFAULT_LOCATION_TERM,
    placeholder_skills: list[str] | None = None,
) -> str:
    return (
        PLANNING_SYSTEM_PROMPT
        .replace("{location_term}", location_term)
        .replace("{placeholder_guidance}", _placeholder_guidance(placeholder_skills))
        .replace("{dataset_catalog}", _format_catalog(dataset_catalog))
        .replace("{skill_catalog}", _format_catalog(skill_catalog))
        .replace("{center_catalog}", _format_catalog(center_catalog or []))
    )


def _placeholder_guidance(placeholder_skills: list[str] | None) -> str:
    """占位算子的用法说明。没配置占位算子的部署就退化成「写进描述里」。"""
    names = [str(x).strip() for x in (placeholder_skills or []) if str(x).strip()]
    if not names:
        return (
            "   当前部署没有配置占位算子，请在 `task.description` 里写清楚缺的是"
            "什么能力，并且**不要**把相关数据源放进 DAG。"
        )
    listed = "、".join(f"`{n}`" for n in names)
    return (
        f"   本部署提供了占位算子 {listed}。遇到算子库表达不了的步骤时用它，"
        "并在参数里写清楚缺的是什么：期望的算子名、需要它做什么、为什么现有算子"
        "不行。系统会在提交前拦下这样的方案，并把你写的说明转达给用户，所以请"
        "写得具体、可执行 —— 这是让算子库缺口被看见的正规途径。"
    )


def _format_catalog(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "（无）"
    return "\n".join(
        f"- {json.dumps(entry, ensure_ascii=False)}" for entry in entries
    )
