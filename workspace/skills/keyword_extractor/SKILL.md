---
name: keyword_extractor
description: '关键词提取标注工具。读取包含文本字段的表格或JSONL语料，为每条记录提取核心关键词并写入新增关键词字段。

  当用户提到关键词提取、关键词抽取、文本关键词、标签提取等需求时使用此skill。

  即使用户没有明确说出"keyword_extractor"，只要任务涉及从文本内容中提取重要词汇或短语作为标签，就应该使用此skill。

  不负责按预置领域关键词库做相关性筛选、文本清洗、分词结果展开或章节切分。

  '
name_zh: 关键词提取算子
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持CSV/TSV/JSON等）
- name: output
  type: string
  required: true
  description: 输出文件路径
- name: text_field
  type: string
  required: true
  description: 文本字段名
- name: label_field
  type: string
  required: false
  default: keywords
  description: 输出关键词字段名
- name: topk
  type: string
  required: false
  default: "5"
  description: 提取关键词数量
output_params:
- name: output
  type: csv_file
  description: 关键词提取后的数据文件
tag: 增强
---

# Keyword Extractor 关键词提取 Skill

## 功能概述

本skill用于读取包含文本字段的 CSV、TSV、JSON 或 JSONL 数据，为每条记录新增一个关键词字段，字段值为JSON数组字符串。
支持jieba关键词抽取；未安装jieba时退回到简单词频统计。
不负责按预置领域关键词库做相关性筛选、文本清洗、分词结果展开或章节切分。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 关键词提取/关键词抽取
- 文本关键词/标签提取
- 内容关键词分析

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- JSON (.json)
- JSONL (.jsonl)

## 使用方法

```bash
python scripts/run_keyword_extractor.py \
  --input {input} \
  --output {output} \
  --text_field {text_field} \
  --label_field {label_field} \
  --topk {topk}
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--text_field` | 是 | 文本字段名 |
| `--label_field` | 否 | 输出关键词字段名，默认"keywords" |
| `--topk` | 否 | 提取关键词数量，默认5 |

## 输出示例

```csv
id,title,keywords
1,厦门海域养殖贝类体内重金属的初步研究,"[""厦门海域"", ""养殖"", ""贝类"", ""重金属""]"
```

## 环境要求

```bash
pip install jieba
```
