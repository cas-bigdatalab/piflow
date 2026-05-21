---
name: result_storage_operator
description: 分析结果落盘算子。用户提到结果保存、导出CSV、结果存储时调用。
allowed-tools:
  - emit_operator

input_params: []

output_params:
  - name: operator_definition
    type: json_file
    description: 结果存储算子的标准JSON定义，用于作为DAG的sink节点
tag: 输出
---

# result_storage_operator

返回 `结果存储` 算子的标准 JSON 片段，用于作为 DAG 的 sink 节点。

## 语义触发提示（给模型）

- 典型语义：`结果保存`、`导出 CSV`、`结果落盘`、`输出存储`。
- 该算子通常作为最终节点，与上游分析算子自动拼接。
