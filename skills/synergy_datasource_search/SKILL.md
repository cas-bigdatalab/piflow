---
name: synergy_datasource_search
description: 检索 Conet 协同数据源并返回标准 stop JSON。仅用于分析流程输入数据源推荐，不用于普通数据集检索。
allowed-tools:
  - process
---

# synergy_datasource_search

调用 `synergy_datasource_search.process(...)` 返回：
1. `analysis_name`
2. `required_data_source_keywords`
3. `required_data_source_full_names`
4. `dataset_stops`
5. `missing_required_full_names`
6. `exact_full_name_matched_dataset_stops`
7. `keyword_related_dataset_stops`

## 关键原则

- 该脚本是检索执行器，不做语义路由决策。
- 语义理解应由模型完成，再传入检索参数。

## 路由规则（强制）

- `routing_intent` 必传，且由模型根据用户语义决定。
- 当请求是分析流程输入推荐时：`routing_intent="analysis"`。
- 当请求是普通找数据/下载数据时：应改走 `sciencedb_search.process`，不要调用本 skill。
- 若误传 `routing_intent="generic_search"` 给本 skill，脚本会直接返回路由建议并跳过协同检索。

## 调用约束（分析场景）

- 分析类请求里，`required_data_source_full_names` 不应为 `None`。
- 若已有 `flow_orchestrator.plan_analysis.required_sources`，应原样传入 `required_data_source_full_names`。

## 展示规则（面向用户）

- 按数据类别分组展示，不按命中方式分组。
- 推荐分组：`地形高程`、`沟道网络`、`地貌特征`、`遥感影像`、`地理坐标`、`气象水文`、`其他`。
- 每条默认展示：`数据集名称`、`dataSourceId`、（可选）一句用途。
- 不展示“完全匹配/关键词匹配/精确匹配/候选命中”等命中标签文案。

