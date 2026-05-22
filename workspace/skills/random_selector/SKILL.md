---
name: random_selector
description: 从CSV数据集中随机抽取样本。支持按比例（0-1）或固定数量抽取，当两者同时提供时取较小值。
allowed-tools:
  - process

name_zh: 从CSV数据集中随机抽取样本算子
input_params:
  - name: input_file
    type: string
    required: true
    description: 输入CSV文件路径

  - name: output_file
    type: string
    required: true
    description: 输出CSV文件路径

  - name: select_ratio
    type: float
    required: false
    description: 抽取比例（0-1），与select_num同时提供时取较小值

  - name: select_num
    type: int
    required: false
    description: 抽取数量，与select_ratio同时提供时取较小值

  - name: seed
    type: int
    required: false
    description: 随机种子

output_params:
  - name: output_file
    type: csv_file
    description: 随机采样后的CSV文件
tag: 过滤与筛选

---

# random_selector

## Overview
该技能通过 `random_selector.py` 执行 CSV 数据随机采样。

## Instructions
### 1. 检查文件
确保 `input_file` 存在。

### 2. 构建命令
根据需求组合参数，**仅提供用户明确指定的参数**。若参数为可选（None），则不要在 shell 命令中包含该 flag。

### 3. 执行采样
`使用以下模板执行：`
```bash
python scripts/random_selector.py \
  --input_file "{input_file}" \
  --output_file "{output_file}" \
  { "--select_ratio " + str(select_ratio) if select_ratio else "" } \
  { "--select_num " + str(select_num) if select_num else "" } \
  { "--seed " + str(seed) if seed else "" }