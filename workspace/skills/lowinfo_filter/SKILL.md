---
name: lowinfo_filter
description: |
  低信息量过滤工具。读取结构化数据文件，对指定文本列同时校验字符总数与行数是否落在阈值区间内，输出过滤后的合规行。
  当用户提到低信息量过滤、字符数筛选、短文本过滤、超长文本过滤、行数过滤、信息量阈值等需求时使用此skill。
  即使用户没有明确说出"低信息量"，只要任务涉及同时按字符数和行数两个维度过滤文本行，就应该使用此skill。
  不负责按单词数过滤（用words_num_filter）、按token数过滤（用token_num_filter）、按最长单行长度过滤（用maximum_line_length_filter）或按平均行长度过滤（用average_line_length_filter）。与这些skill的关键区别在于：本skill同时校验字符总数与行数两个维度，且原生支持CSV/TSV/Excel多列输入、不依赖data_juicer。
name_zh: 低信息量过滤算子
tag: 清洗
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）
  - name: output_path
    type: string
    required: true
    description: 输出文件路径（过滤后的文件）
  - name: text_columns
    type: string
    required: false
    description: 需检测的文本列，逗号分隔；不填默认全部字符串列
  - name: min_chars
    type: string
    required: false
    description: 最小字符数，默认 10
  - name: max_chars
    type: string
    required: false
    description: 最大字符数（0 表示不限），默认 2000
  - name: min_lines
    type: string
    required: false
    description: 最小行数，默认 1
  - name: max_lines
    type: string
    required: false
    description: 最大行数（0 表示不限），默认 200
output_params:
  - name: output_path
    type: csv_file
    description: 过滤后的结构化数据文件
tag: 清洗
---

# lowinfo_filter 低信息量过滤

## 功能概述
- 按字符数/行数上下限过滤低/高信息样本。
- 支持多列检测，默认所有字符串列。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--input_path` | 是 |  | 输入文件路径（支持CSV/TSV/Excel等） |
| `--output_path` | 是 |  | 输出文件路径（过滤后的文件） |
| `--text_columns` | 否 |  | 需检测的文本列，逗号分隔；不填默认全部字符串列 |
| `--min_chars` | 否 |  | 最小字符数，默认 10 |
| `--max_chars` | 否 |  | 最大字符数（0 表示不限），默认 2000 |
| `--min_lines` | 否 |  | 最小行数，默认 1 |
| `--max_lines` | 否 |  | 最大行数（0 表示不限），默认 200 |

## 使用方法
```bash
python scripts/lowinfo_filter.py \
  --input_path <输入文件> \
  --output_path <输出文件> \
  [--text_columns col1,col2] \
  [--min_chars 10] [--max_chars 2000] \
  [--min_lines 1] [--max_lines 200]
```

## 输出说明
- 仅保留满足阈值的行；过滤掉的行不输出。
- 控制台提示输出行数与原始行数。

## 注意事项
- 合理设置 min/max，避免过度过滤。
- 若需保留原因，可调整脚本保留 filter_reason 列（当前实现剔除）。
