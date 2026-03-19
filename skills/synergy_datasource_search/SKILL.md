---
name: synergy_datasource_search
description: 检索 Conet 协同数据源并返回标准 stop JSON 数组。用于分析流程输入数据源推荐。
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

- 该脚本是纯检索执行器，不做语义拆词和意图路由硬编码。
- 模型必须先做语义理解，再传入关键词与全称检索列表。

## 调用约束（强制）

- 对分析类请求，`required_data_source_full_names` 不能传 `None`。
- 如果已有算子选择结果（例如 `flow_orchestrator.plan_analysis.required_sources`），必须把这些名称写入 `required_data_source_full_names`。

## 图像分割场景（强制）

当用户语义为“图像分割算法分析 / 遥感图像分割 / YOLO 分割流程输入数据源推荐”时，  
`required_data_source_full_names` 至少必须包含：

1. `榆林市卫星遥感数据集图像分割文件`
2. `榆林市地理坐标信息文件`

即使关键词检索已有其它候选，也必须做这两条全称检索，并在结果中优先展示。

## 展示规则（面向用户）

- 按数据类型分组展示，不按命中方式分组。
- 推荐分组：`地形高程`、`沟道网络`、`地貌特征`、`遥感影像`、`地理坐标`、`其他候选`。
- 每条默认展示：`数据集名称`、`dataSourceId`、（可选）一句用途。
- 不展示“精确匹配/关键词候选/高置信命中”这类命中标签文案。
