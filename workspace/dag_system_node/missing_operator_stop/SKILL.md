---
name: missing_operator_stop
description: 用于 Workflow Planning 阶段的占位算子。当前 Skill 库不存在满足用户需求的业务 Skill 时，使用本算子保持 DAG 数据流完整，等待后续生成真实 Skill 后替换。
name_zh: DAG占位算子
input_params:
  - name: input
    type: string
    required: true
    description: 引用上游节点输出
  - name: expected_skill
    type: string
    required: false
    description: 需要补齐的算子名称
  - name: capability
    type: string
    required: true
    description: 需要补齐的算子能力描述
  - name: reason
    type: string
    required: false
    description: 需要补齐的算子无法满足用户需求的原因描述
output_params:
  - name: output
    type: string
    description: 供下游节点引用的输出占位参数
tag: 占位
node_category: system
---

# missing_operator_stop

用于作为 DAG 的占位节点，当用户需要的流程中，存在系统不具备的算子能力时，声明本占位算子，承接上游输出作为本占位节点输入，并向下游节点暴露 `output` 输出槽位供引用，保证DAG结构完整。
