---
name: hydro_susceptibility_operator
description: 山洪/水文敏感度计算算子。用户提到山洪敏感度、易发性评估、水文风险分析时优先调用。
allowed-tools:
  - emit_operator

input_params: []

output_params:
  - name: operator_definition
    type: json_file
    description: 水文敏感度算子的标准JSON片段，包含算子配置和数据源依赖
tag: 其他
---

# hydro_susceptibility_operator

返回 `hydro_susceptibility` 算子的标准 JSON 片段。

## 语义触发提示（给模型）

- 典型语义：`山洪敏感度`、`易发性评估`、`水文风险`、`灾害敏感度栅格`。
- 常见上游数据源全称：
  - `地貌信息熵`
  - `2019年中国榆林市沟道信息`
  - `2019年中国榆林市30m数字高程数据集`

模型命中该算子后，应在数据源推荐阶段走 `synergy_datasource_search.process`，并同时使用关键词检索与全称检索。
