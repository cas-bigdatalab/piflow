---
name: stratified_sampler
description: '结构化数据分层采样工具。读取 JSONL、JSON、CSV、TSV、XLSX、XLS 等结构化数据，按指定字段分层后无放回抽取样本，输出保留原字段结构的采样结果。

  当用户提到分层采样、类别平衡采样、按标签抽样、训练集分层划分等需求时使用此skill。

  即使用户没有明确说出"stratified_sampler"，只要任务涉及按字段分层并进行代表性抽样，就应该使用此skill。

  不负责随机采样、领域均衡采样、批量切分、时间窗口抽样或格式转换。

  '
name_zh: 分层采样算子
input_params:
- name: input
  type: string
  required: true
  description: 输入结构化数据文件路径
- name: output
  type: string
  required: true
  description: 输出结构化数据文件路径
- name: strata_field
  type: string
  required: true
  description: 分层字段（如 category, label 等）
- name: sample_size
  type: string
  required: false
  description: 总采样数量（与 sample_ratio、sample_num 三选一）
- name: sample_ratio
  type: string
  required: false
  description: 每层采样比例（与 sample_size、sample_num 三选一）
- name: sample_num
  type: string
  required: false
  description: 每层固定采样数量（与 sample_size、sample_ratio 三选一）
- name: min_samples
  type: string
  required: false
  default: "0"
  description: 每层最小采样数量，仅用于 sample_size 和 sample_ratio 模式
- name: seed
  type: string
  required: false
  default: "42"
  description: 随机种子
- name: log_file
  type: string
  required: false
  description: 日志文件路径
output_params:
- name: output
  type: file
  description: 分层采样后的结果文件
- name: strata_stats
  type: object
  description: 各层采样统计
tag: 切分与采样
---

# Stratified Sampler 分层采样 Skill

## 功能概述

本 skill 面向结构化数据进行分层抽样，可按指定字段拆分样本分布后再进行无放回采样，尽量保持各层比例与总体一致。
采样过程中保留原始字段结构，适用于训练集划分、类别平衡验证、代表性样本抽样等场景。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 分层采样
- 类别平衡采样
- 按标签抽样
- 训练集分层划分

## 核心参数说明

### 必需参数

- `--input`：输入结构化数据文件路径
- `--output`：输出结构化数据文件路径
- `--strata_field`：分层字段名

### 可选参数

- `--sample_size`：总采样数量
- `--sample_ratio`：每层采样比例
- `--sample_num`：每层固定采样数量
- `--min_samples`：每层最小采样数量，默认 `0`
- `--seed`：随机种子，默认 `42`
- `--log_file`：日志文件路径

## 输入文件格式

输入文件可以是 JSONL、JSON、CSV、TSV、XLSX、XLS 等结构化数据文件。至少需要包含一个可用于分层的字段。

示例：
```jsonl
{"id": 1, "category": "A", "text": "A-1"}
{"id": 2, "category": "A", "text": "A-2"}
{"id": 3, "category": "B", "text": "B-1"}
```

## 使用方法

### 按总量分层采样
```bash
python scripts/run_stratified_sampler.py \
  --input data.jsonl \
  --output sampled.jsonl \
  --strata_field category \
  --sample_size 1000 \
  --seed 42
```

### 按比例分层采样
```bash
python scripts/run_stratified_sampler.py \
  --input data.csv \
  --output sampled.csv \
  --strata_field category \
  --sample_ratio 0.1 \
  --min_samples 1 \
  --seed 42
```

### 按每层固定数量采样
```bash
python scripts/run_stratified_sampler.py \
  --input data.xlsx \
  --output sampled.xlsx \
  --strata_field label \
  --sample_num 20 \
  --seed 42
```

## 输出示例

```text
[OK] Stratified sampling completed
   Input: data.csv
   Output: sampled.csv
   Total records: 12
   Strata field: category
   Sampled records: 6
   Strata distribution:
      A: 2/4 (50.0%)
      B: 1/3 (33.3%)
      C: 2/4 (50.0%)
      D: 1/1 (100.0%)
```

## 环境要求

- Python 3.x
- pandas
- 读取 Excel 文件时需要对应引擎依赖

## 注意事项

1. 采样是无放回的，每条记录最多被选中一次
2. 设置相同的种子可以得到相同的采样结果
3. `sample_size`、`sample_ratio`、`sample_num` 三者只能选择一个
4. `min_samples` 只用于 `sample_size` 和 `sample_ratio` 模式
5. 如果某层比例分配后采样数为 0，但该层存在样本且总采样数大于 0，脚本会保底抽取 1 条
6. 如果 `sample_size` 大于可用总量，结果会尽量返回全部数据
