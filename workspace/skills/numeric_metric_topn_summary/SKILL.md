---
name: numeric_metric_topn_summary
name_zh: 单数据集数值指标Top-N统计
description: |
  单数据集数值指标 Top-N 统计算子。输入必须直接来自一个数据集读取节点；算子在
  tar、zip、目录或普通文件中自动发现 CSV、TSV、XLSX、JSON、JSONL 表格，按逻辑指标名
  识别字段、解析并统一单位、过滤无效值、排序取 Top-N，最后一次性输出 count、mean、min、max。
  比表面积任务的 metric 必须填写 specific_surface_area，target_unit 填写 m2/g。
  本算子的 output 是 metric_summary_v1 统计摘要，不是明细表；同一数据分支只能使用一次，
  禁止在其后再次连接过滤、排序或统计算子。需要跨数据集计算时，把两路 output 分别绑定到
  metric_summary_compare 的 input_1 和 input_2。
input_params:
  - name: input
    role: input_data
    type: file_artifact
    required: true
    description: 单个数据集读取节点输出的数据包或结构化数据文件
  - name: dataset_label
    role: data
    type: string
    required: true
    description: 意图中已选数据集的真实名称
  - name: metric
    role: data
    type: string
    required: true
    description: 逻辑指标名；比表面积填写 specific_surface_area
  - name: order
    role: data
    type: string
    required: false
    default: desc
    description: asc 或 desc
  - name: top_n
    role: data
    type: int
    required: false
    default: 30
    description: 排序后参与统计的记录数，不足时使用全部有效记录
  - name: target_unit
    role: data
    type: string
    required: true
    description: 目标单位；比表面积填写 m2/g
output_params:
  - name: output
    role: output_data
    type: csv_file
    description: metric_summary_v1 标准统计摘要
tag: 数据统计
disciplinary_field: 基础
publisher: PRIVATE
---

# 单数据集数值指标 Top-N 统计

执行顺序固定为：发现候选表 → 识别逻辑字段 → 解析并统一单位 → 过滤无效值 → 排序 →
Top-N → count/mean/min/max。若归档同时包含同一数据的多种表示，选择有效指标记录最多的表；
数量相同时按 CSV、XLSX、TSV、JSONL、JSON 的顺序选择，避免重复统计。

```bash
python {script_path} --input "{input}" --output "{output}" --dataset_label "{dataset_label}" --metric "{metric}" --order "{order}" --top_n "{top_n}" --target_unit "{target_unit}"
```

约束：

- 本算子只处理一路数据集输入。
- 输出已经是统计摘要，不能再次使用本算子或其他明细筛选/排序算子处理。
- 找不到指标字段时明确报 `METRIC_FIELD_NOT_FOUND`，不会返回伪造的空摘要。
- 有效记录不足 `top_n` 时使用全部有效记录。

