---
name: duplicate_detector_exact
description: '精确去重工具。使用pandas精确匹配检测并处理数据集中的完全重复记录，速度快、无额外依赖。

  当用户提到精确去重、完全重复检测、数据去重等需求时使用此skill。

  '
name_zh: 精确去重算子
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持CSV/TSV/Excel/JSON等）
- name: output
  type: string
  required: true
  description: 输出文件路径
- name: subset
  type: string
  required: false
  description: 用于判断重复的字段列表，逗号分隔，默认全部字段
- name: keep
  type: string
  required: false
  default: first
  description: 保留策略（first/last/none/mark）
output_params:
- name: output
  type: csv_file
  description: 去重后的数据文件
tag: 去重
---

# Duplicate Detector Exact 精确去重 Skill

## 功能概述

本skill用于检测和处理数据集中的完全重复记录，基于pandas的精确匹配：
- **全字段匹配**：所有列完全相同的记录
- **指定字段匹配**：只比较指定的字段

## 保留策略

| 策略 | 说明 |
|------|------|
| `first` | 保留第一条重复记录 |
| `last` | 保留最后一条重复记录 |
| `none` | 删除所有重复记录 |
| `mark` | 标记重复但不删除（添加is_duplicate列） |

## 使用方法

### 全字段去重
```bash
python scripts/run_duplicate_detector_exact.py \
  --input data.csv \
  --output deduped.csv
```

### 按指定字段去重
```bash
python scripts/run_duplicate_detector_exact.py \
  --input data.csv \
  --output deduped.csv \
  --subset "name,phone"
```

### 标记重复
```bash
python scripts/run_duplicate_detector_exact.py \
  --input data.csv \
  --output marked.csv \
  --keep mark
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--subset` | 否 | 判断重复的字段，逗号分隔 |
| `--keep` | 否 | 保留策略，默认"first" |

## 环境要求

```bash
pip install pandas openpyxl
```
