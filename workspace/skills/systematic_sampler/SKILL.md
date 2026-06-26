---
name: systematic_sampler
description: '系统采样算子。按照固定间隔从数据中进行系统采样，适用于时间序列数据或需要均匀分布样本的场景。

  当用户提到系统采样、等距抽样、按间隔取样、均匀抽样等需求时使用此skill。

  即使用户没有明确说出"系统采样"，只要任务涉及从有序数据中按固定步长抽取样本，就应该使用此skill。

  不负责分层采样或随机采样。

  '
name_zh: 系统采样算子
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: method
  type: string
  required: true
  description: 采样方式：interval/count
- name: interval
  type: string
  required: false
  default: "0"
  description: 采样间隔（method=interval时）
- name: count
  type: string
  required: false
  default: "0"
  description: 目标采样数量（method=count时）
- name: start_offset
  type: string
  required: false
  default: "0"
  description: 起始偏移量
- name: log_file
  type: string
  required: false
  description: 日志文件路径
output_params:
- name: output
  type: list
  description: 系统采样后的数据
- name: sample_count
  type: integer
  description: 采样数量
tag: 切分与采样
---

# SystematicSampler - 系统采样算子

## 功能概述
按照固定间隔从数据中进行系统采样，适用于时间序列数据或需要均匀分布样本的场景。支持指定间隔或根据目标数量自动计算间隔。

## 触发条件

当用户提到以下任务时，应使用此skill：
- 系统采样
- 等距抽样
- 按间隔取样
- 均匀抽样

## 核心参数说明

### 必需参数
- `--input`：输入JSONL文件路径
- `--output`：输出JSONL文件路径
- `--method`：采样方式，`interval` 或 `count`

### 可选参数
- `--interval`：采样间隔，`method=interval` 时使用
- `--count`：目标采样数量，`method=count` 时使用
- `--start_offset`：起始偏移量，默认 `0`
- `--log_file`：日志文件路径

## 输入文件格式

支持 JSONL，每行一个 JSON 对象。

## 使用方法

### 按间隔采样
```bash
python scripts/run_systematic_sampler.py \
  --input data.jsonl \
  --output sampled.jsonl \
  --method interval \
  --interval 10 \
  --start_offset 0
```

### 按目标数量采样
```bash
python scripts/run_systematic_sampler.py \
  --input data.jsonl \
  --output sampled.jsonl \
  --method count \
  --count 1000 \
  --start_offset 5
```

## 输出示例

```
[OK] Systematic sampling completed
   Input: data.jsonl
   Output: sampled.jsonl
   Total records: 12
   Sampling interval: 3
   Start offset: 1
   Sampled records: 4
   Sampling rate: 33.33%
```

## 环境要求

- Python 3.x
- 标准库即可运行

## 注意事项

1. 输入必须是 JSONL 格式。
2. `method=count` 会基于目标数量估算间隔，并在需要时截断到目标数量。
3. `start_offset` 不能大于数据长度。
4. 输出记录会追加 `_sample_index` 和 `_sample_interval` 标记。
