---
name: random_sampler
description: 'JSONL 随机采样工具。读取 JSONL 数据集，按抽样数量或抽样比例无放回抽取样本，输出保留原字段结构的采样结果。

  当用户提到随机采样、按数量抽样、按比例抽样、JSONL 抽样筛查等需求时使用此skill。

  即使用户没有明确说出"random_sampler"，只要任务涉及对 JSONL 记录做无放回随机抽取，就应该使用此skill。

  不负责分层采样、领域均衡采样、表格采样或其他格式转换。

  '
name_zh: 随机采样算子
input_params:
- name: input
  type: string
  required: true
  description: 输入 JSONL 文件路径
- name: output
  type: string
  required: true
  description: 输出 JSONL 文件路径
- name: method
  type: string
  required: true
  description: 采样方式：count/ratio
- name: count
  type: string
  required: false
  default: "0"
  description: 采样数量（method=count时使用）
- name: ratio
  type: string
  required: false
  default: "0"
  description: 采样比例0-1（method=ratio时使用）
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
  type: list
  description: 采样后的数据列表
- name: sample_count
  type: integer
  description: 采样数量
tag: 切分与采样
---

# Random Sampler 随机采样 Skill

## 功能概述

本 skill 面向 JSONL 数据集进行无放回随机采样，可按数量或按比例抽取样本，并支持随机种子保证结果可复现。
采样过程中保留原始 JSON 对象结构，不改动字段内容，适用于大批量语料抽样筛查、小样本人工核验、流程调试等场景。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 随机采样
- 按数量抽样
- 按比例抽样
- JSONL 抽样筛查

## 核心参数说明

### 必需参数

- `--input`：输入 JSONL 文件路径
- `--output`：输出 JSONL 文件路径
- `--method`：采样方式，支持 `count` 或 `ratio`

### 可选参数

- `--count`：采样数量，`method=count` 时使用
- `--ratio`：采样比例 0-1，`method=ratio` 时使用
- `--seed`：随机种子，默认 `42`
- `--log_file`：日志文件路径

## 输入文件格式

输入文件必须为 JSONL，每一行是一条独立 JSON 记录。

示例：
```jsonl
{"id": 1, "text": "sample a"}
{"id": 2, "text": "sample b"}
{"id": 3, "text": "sample c"}
```

## 使用方法

### 按数量采样
```bash
python scripts/run_random_sampler.py \
  --input data.jsonl \
  --output sampled.jsonl \
  --method count \
  --count 100 \
  --seed 42
```

### 按比例采样
```bash
python scripts/run_random_sampler.py \
  --input data.jsonl \
  --output sampled.jsonl \
  --method ratio \
  --ratio 0.1 \
  --seed 42
```

## 输出示例

```text
[OK] Random sampling completed
   Input: data.jsonl
   Output: sampled.jsonl
   Total records: 12
   Sampled records: 5
   Sampling rate: 41.67%
   Random seed: 42
```

## 环境要求

- Python 3.x
- 输入文件为有效 JSONL

## 注意事项

1. 采样是无放回的，每条记录最多被选中一次
2. 设置相同的种子可以得到相同的采样结果
3. 如果 `count` 或 `ratio` 超过总数，则返回全部数据
