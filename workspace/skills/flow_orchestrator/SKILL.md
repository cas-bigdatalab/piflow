---
name: flow_orchestrator
description: 按“算法选择 -> 数据源绑定 -> 缓存执行”三阶段组装并执行 flow JSON 的编排 skill。
allowed-tools:
  - plan_analysis
  - build_flow
  - build_flow_with_selected_sources
  - build_flow_json
  - prepare_dam_analysis_session
  - execute_flow_from_temp
---

# flow_orchestrator

本 skill 只负责 JSON 组装与缓存，不做语义拆词硬编码。

## 标准流程

1. 根据用户语义选择算法 skill，得到 `selected_operators`。
2. 调用 `plan_analysis(selected_operators=...)` 获取 `required_sources`。  
   算法 stop 的完整 JSON 在内部保留，面向用户只展示名称。
3. 用户选择数据源后，调用  
   `build_flow_with_selected_sources(selected_operators, selected_dataset_stops, source_bindings)`  
   组装完整 flow JSON（算法 JSON + 数据源 JSON），并自动缓存到内部临时目录。
4. 用户说“开始执行”时，使用返回的 `run_payload`（或 `flow_session_id`）调用执行 skill。

## 数据源输入约束（强制）

- `selected_dataset_stops` 必须是完整数据源 stop JSON 数组。
- 每个数据源对象至少应包含：
  - `customizedProperties`
  - `dataSourceId`
  - `dataCenter`
  - `registerId`
  - `sourceType`
  - `webAddress`
  - `name`
  - `uuid`
  - `bundle`
  - `properties`
- 不接受仅名称字符串或不完整对象；否则编排函数会报错。

## 连边规则

- 仅采用：
  - `source_bindings` 显式绑定（name 或 dataSourceId）
  - `required_sources` 与数据源 `name` 同名精确匹配
- 不使用模糊匹配逻辑。

## 对用户输出约束

- 不向用户暴露内部临时路径（如 `/temp/dam_flow_xxx.json`）。
- 用户侧只展示 `flow_session_id` 作为会话标识。

