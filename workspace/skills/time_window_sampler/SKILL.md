---
name: time_window_sampler
description: '时间窗口采样算子。读取JSONL时间序列记录，按指定时间窗口分组后在每个窗口内均匀抽取样本。

  当用户提到按天抽样、按小时抽样、周期性抽样、时间窗口采样等需求时使用此skill。

  即使用户没有明确说出"时间窗口采样"，只要任务涉及按时间粒度分组后抽样，就应该使用此skill。

  不负责时间字段清洗、时间聚合统计或异常检测。

  '
name_zh: 时间窗口采样算子
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: time_field
  type: string
  required: true
  description: 时间字段名
- name: window_size
  type: string
  required: true
  description: 窗口大小（如1d, 2h, 1m, 1w）
- name: time_format
  type: string
  required: false
  description: 时间格式字符串
- name: sample_per_window
  type: string
  required: false
  default: "1"
  description: 每个窗口采样数量
- name: log_file
  type: string
  required: false
  description: 日志文件路径
output_params:
- name: output
  type: jsonl_file
  description: 时间窗口采样后的数据
tag: 切分与采样
---

# TimeWindowSampler - 时间窗口采样算子

## 功能概述

按照时间窗口对数据进行采样，每个窗口内均匀抽取指定数量的样本。支持按天、小时、月、周等时间粒度，适用于时间序列数据的周期性抽样。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 按天抽样
- 按小时抽样
- 周期性抽样
- 时间窗口采样
- 按时间粒度分组后抽样

## 核心参数说明

### 必需参数
- `--input`：输入JSONL文件路径
- `--output`：输出JSONL文件路径
- `--time_field`：时间字段名
- `--window_size`：窗口大小（如 `1d`、`2h`、`1m`、`1w`）

### 可选参数
- `--time_format`：时间格式字符串
- `--sample_per_window`：每个窗口采样数量，默认 `1`
- `--log_file`：日志文件路径

## 输入文件格式

输入文件必须是JSONL，每行一个JSON对象，且至少包含时间字段。时间字段应能被脚本识别为日期时间字符串。

## 使用方法

```bash
python scripts/run_time_window_sampler.py --input data.jsonl --output sampled.jsonl --time_field event_time --window_size 1d --sample_per_window 2
```

## 输出示例

```jsonl
{"id": 1, "event_time": "2025-06-01 00:15:00", "_time_window": "2025-06-01", "_window_sample_index": 0}
{"id": 7, "event_time": "2025-06-01 06:15:00", "_time_window": "2025-06-01", "_window_sample_index": 1}
```

## 环境要求

- Python 3.10+
- 标准库 `datetime`

## 注意事项

- 无法解析时间字段的记录会被跳过
- `_time_window` 标记窗口起点标签
- `_window_sample_index` 标记窗口内抽样顺序
