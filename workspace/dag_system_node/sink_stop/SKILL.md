---
name: sink_stop
description: DAG 输出终止算子。用于接收上游算子的输出，并将结果保存到指定路径。该算子没有下游输出，必须作为 DAG 的终止节点使用。
name_zh: 输出终止算子
input_params:
  - name: input
    type: string
    required: true
    description: 上游算子的输出引用
  - name: path
    type: string
    required: true
    description: 文件保存路径
  - name: overwrite
    type: bool
    required: false
    default: false
    description: 是否允许覆盖已有文件
output_params: []
tag: 输出
node_category: system
---

# sink_stop

用于作为 DAG 的终止节点，接收上游输出并将结果写入目标路径，不再向下游提供输出。

