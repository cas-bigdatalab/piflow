---
name: missing_value_remover
description: |
  缺失值删除工具。读取结构化表格或 JSONL 数据，删除包含缺失值的行或删除缺失比例过高的列；不负责缺失值填充。
  当用户提到删除缺失值、删除空值行、删除空值列等需求时使用此skill。
  适用于科研表格和结构化数据的缺失清理，不负责插值、补值、均值填充或其他修复操作。

name_zh: 缺失值删除算子
tag: 清洗
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel/JSON等）

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: columns
    type: string
    required: false
    description: 要处理的字段，逗号分隔，默认全部字段

  - name: strategy
    type: string
    required: false
    default: "drop"
    description: 删除策略（drop/drop_cols）

  - name: threshold
    type: string
    required: false
    default: "0.5"
    description: 删除阈值（drop_cols时，缺失比例超过此值则删除该列）

output_params:
  - name: output
    type: csv_file
    description: 删除缺失值后的数据文件
tag: 清洗

---

# Missing Value Remover 缺失值删除 Skill

## 功能概述

本skill用于删除数据中包含缺失值的行或列：
- **drop**：删除包含任何缺失值的行
- **drop_cols**：删除缺失比例超过阈值的列

## 输入文件格式

支持以下结构化文件格式：
- CSV
- TSV
- Excel（.xlsx / .xls）
- JSON
- JSONL

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为以上支持格式后再使用本skill。

## 使用方法

### 删除含缺失值的行
```bash
python scripts/run_missing_value_remover.py \
  --input data.csv \
  --output cleaned.csv \
  --strategy drop
```

### 删除缺失严重的列
```bash
python scripts/run_missing_value_remover.py \
  --input data.csv \
  --output cleaned.csv \
  --strategy drop_cols \
  --threshold 0.5
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--columns` | 否 | 处理字段，逗号分隔 |
| `--strategy` | 否 | 删除策略，默认"drop" |
| `--threshold` | 否 | 删除阈值，默认0.5 |

## 环境要求

```bash
pip install pandas numpy openpyxl
```
