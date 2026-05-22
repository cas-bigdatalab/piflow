---
name: gully_slop_operator
description: 沟道坡度特征计算算子。用户提到沟道坡度、DEM地形坡度预处理、沟道地形分析时优先调用。
allowed-tools:
  - emit_operator

name_zh: 沟道坡度特征计算算子
input_params: []

output_params:
  - name: operator_definition
    type: json_file
    description: 沟道坡度算子的标准JSON片段，包含算子配置和数据源依赖
tag: 其他

---

# gully_slop_operator

返回 `gully_slop` 算子的标准 JSON 片段。

## 语义触发提示（给模型）

- 典型语义：`沟道坡度`、`坡度特征`、`DEM 预处理`、`沟道地形`。
- 常见上游数据源全称：
  - `2019年中国榆林市沟道信息`
  - `2019年中国榆林市30m数字高程数据集`

模型命中该算子后，应在数据源推荐阶段走 `synergy_datasource_search.process`，并同时使用关键词检索与全称检索。
