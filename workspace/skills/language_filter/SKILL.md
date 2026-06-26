---
name: language_filter
description: |
  语种过滤工具。对指定或全部文本列进行语言检测，可选择保留或剔除目标语种，
  输出过滤后的数据并附带 detected_lang 列。
name_zh: 语种过滤算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）
  - name: output_path
    type: string
    required: true
    description: 输出文件路径（过滤后的文件）
  - name: target_lang
    type: string
    required: true
    description: 目标语种代码（如 zh, en, fr 等）
  - name: text_columns
    type: string
    required: false
    description: 用于检测的文本列，逗号分隔；不填默认全部字符串列
  - name: mode
    type: string
    required: false
    description: keep=保留目标语种，drop=剔除目标语种，默认 keep
output_params:
  - name: output_path
    type: csv_file
    description: 语种过滤后的结构化数据文件（含 detected_lang）
tag: 清洗
---

# language_filter 语种过滤

## 功能概述
- langdetect 识别语种，写入 detected_lang 列。
- 根据模式保留或剔除目标语种样本。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--input_path` | 是 |  | 输入文件路径（支持CSV/TSV/Excel等） |
| `--output_path` | 是 |  | 输出文件路径（过滤后的文件） |
| `--target_lang` | 是 |  | 目标语种代码（如 zh, en, fr 等） |
| `--text_columns` | 否 |  | 用于检测的文本列，逗号分隔；不填默认全部字符串列 |
| `--mode` | 否 |  | keep=保留目标语种，drop=剔除目标语种，默认 keep |

## 使用方法
```bash
python scripts/language_filter.py \
  --input_path <输入文件> \
  --output_path <输出文件> \
  --target_lang zh \
  [--text_columns col1,col2] \
  [--mode keep|drop]
```

## 输出说明
- 新增列 detected_lang 标记检测结果。
- 根据 mode 输出过滤后的数据。

## 注意事项
- 依赖 langdetect，请确保已安装：`pip install langdetect`。
- 语言检测对极短文本可能不稳定，建议提供上下文较多的列或多列拼接。
