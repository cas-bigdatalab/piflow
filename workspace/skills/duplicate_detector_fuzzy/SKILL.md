---
name: duplicate_detector_fuzzy
description: '模糊去重工具。使用标准库相似度匹配检测并处理数据集中的近似重复记录，可发现非完全一致但高度相似的记录。

  当用户提到模糊去重、近似重复检测、相似度去重、文本去重等需求时使用此skill。

  '
name_zh: 模糊去重算子
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
  description: 用于比对相似度的文本字段
- name: similarity_threshold
  type: string
  required: false
  default: "0.9"
  description: 相似度阈值（0-1），默认0.9
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

# Duplicate Detector Fuzzy 模糊去重 Skill

## 功能概述

本skill使用标准库相似度算法检测数据集中的近似重复记录。

与精确去重不同，模糊去重可以发现内容高度相似但不完全相同的记录，如：
- 拼写略微不同的姓名
- 格式稍有差异的地址
- 包含少量错别字的文本

## 保留策略

| 策略 | 说明 |
|------|------|
| `first` | 保留第一条记录 |
| `last` | 保留最后一条记录 |
| `none` | 删除所有重复记录 |
| `mark` | 标记重复但不删除 |

## 使用方法

```bash
python scripts/run_duplicate_detector_fuzzy.py \
  --input data.csv \
  --output deduped.csv \
  --subset "name" \
  --similarity_threshold 0.9
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--subset` | 是 | 比对相似度的文本字段 |
| `--similarity_threshold` | 否 | 相似度阈值(0-1)，默认0.9 |
| `--keep` | 否 | 保留策略，默认"first" |

## 环境要求

```bash
pip install pandas openpyxl
```
