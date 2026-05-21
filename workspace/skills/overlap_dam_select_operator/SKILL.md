---
name: overlap_dam_select_operator
description: 淤地坝候选叠加筛选算子。用户提到淤地坝识别、坝体候选筛选、叠加过滤时优先调用。
allowed-tools:
  - emit_operator

input_params: []

output_params:
  - name: operator_definition
    type: json_file
    description: 淤地坝候选叠加筛选算子的标准JSON片段，包含算子配置和数据源依赖
tag: 其他
---

# overlap_dam_select_operator

返回 `overlap_dam_select` 算子的标准 JSON 片段。

## 语义触发提示（给模型）

- 典型语义：`淤地坝分析`、`坝体识别`、`候选叠加筛选`、`结果过滤`。
- 常见上游算法依赖：
  - `geotrans_main`
  - `hydro_susceptibility`
- 常见上游数据源全称（用于检索）：
  - `2019年中国榆林市30m数字高程数据集`
  - `2019年中国榆林市沟道信息`
  - `地貌信息熵`
  - `榆林市卫星遥感数据集图像分割文件`
  - `榆林市地理坐标信息文件`

模型命中该算子后，应在数据源推荐阶段走 `synergy_datasource_search.process`，并同时使用关键词检索与全称检索。
