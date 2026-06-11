---
name: source_stop
description: DAG 输入源算子。用于声明工作流的输入文件，并为下游算子提供数据源引用。该算子没有上游输入，必须作为 DAG 的起始节点使用。
name_zh: 输入源算子
input_params:
  - name: file_path
    type: string
    required: true
    description: 输入文件路径
output_params:
  - name: output
    type: string
    description: 提供给下游算子引用的数据源输出占位
tag: 输入
node_category: system
---

# source_stop

用于作为 DAG 的起始节点，声明一个输入文件，并向下游节点暴露 `output` 输出槽位供引用。

