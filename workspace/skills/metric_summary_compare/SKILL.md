---
name: metric_summary_compare
name_zh: 双数据集数值摘要对比
description: |
  双数据集数值摘要对比算子。只接受两路 numeric_metric_topn_summary 产生的
  metric_summary_v1 CSV；校验指标和单位一致后，计算两组均值的差值与比值并输出最终 CSV。
  本算子不读取原始数据、不筛选记录、不重新聚合。input_1 和 input_2 必须各绑定一个不同
  数据分支，output 只连接 FileSaveStop。用户要求两份数据各自筛选统计后再进行差值、比值或
  性能对比时使用本算子。difference_order 优先使用 input_1-input_2 或 input_2-input_1；
  同时兼容 <dataset_label>_minus_<dataset_label>，执行时会根据两路摘要的 dataset_name
  解析方向，并统一输出为标准端口表达式。
input_params:
  - name: input_1
    role: input_data
    type: csv_file
    required: true
    description: 第一份 metric_summary_v1
  - name: input_2
    role: input_data
    type: csv_file
    required: true
    description: 第二份 metric_summary_v1
  - name: difference_order
    role: data
    type: string
    required: false
    default: input_2-input_1
    description: 优先填写 input_2-input_1 或 input_1-input_2；也可填写 <dataset_label>_minus_<dataset_label>
  - name: output_file_name
    role: data
    type: string
    required: false
    default: metric_summary_comparison.csv
    description: 结果文件名元数据
output_params:
  - name: output
    role: output_data
    type: csv_file
    description: 最终跨数据集对比 CSV
tag: 数据统计
disciplinary_field: 基础
publisher: PRIVATE
---

# 双数据集数值摘要对比

该算子是跨数据集计算节点，只比较两个标准摘要，不承担任何上游的数据发现、字段识别、
Top-N 或统计职责。结果包含两组 count/mean/min/max，以及按 `difference_order` 计算的均值差值和比值。

```bash
python {script_path} --input_1 "{input_1}" --input_2 "{input_2}" --output "{output}" --difference_order "{difference_order}" --output_file_name "{output_file_name}"
```

约束：

- `input_1`、`input_2` 必须分别来自两个 `numeric_metric_topn_summary` 节点。
- 两个摘要的 `metric_key` 和 `unit` 必须相同。
- `difference_order` 优先使用标准端口表达式；语义表达式中的名称必须能唯一匹配两路摘要的 `dataset_name`。
- 例如 `input_1.dataset_name=supercapacitor`、`input_2.dataset_name=catalyst` 时，
  `supercap_minus_catalyst` 会被规范化为 `input_1-input_2`。
- 分母均值为零时明确报错，不输出无意义比值。
- 输出已经是最终对比结果，只连接结果保存节点。
