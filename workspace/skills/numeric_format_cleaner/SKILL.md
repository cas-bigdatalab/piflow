---
name: numeric_format_cleaner
description: '数值格式清洗工具。读取 JSONL 结构化数据，按字段规则统一单位、数值格式、范围和空值表达，输出规整后的 JSONL 和统计文件。

  当用户提到数值格式化、单位统一、千分位、科学计数法、空值填充、数值规整等需求时使用此skill。

  即使用户没有明确说出"数值格式清洗"，只要任务涉及按字段规则整理数值表达，就应该使用此skill。

  不负责文本去重、标点清洗、字段校验或非数值内容整理。

  '
name_zh: 数值格式清洗算子
tag: 清洗
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: field_rules
  type: string
  required: true
  description: 字段清洗规则（JSON格式，见示例）
- name: conversion_rules
  type: string
  required: false
  default: ''
  description: '单位转换规则（JSON格式，如 {"kg::g": 1000}）'
- name: decimal_places
  type: string
  required: false
  default: "2"
  description: 默认小数位数
- name: fill_null
  type: string
  required: false
  default: ''
  description: 空值填充值（如"N/A"或"0"）
- name: mark_cleaned
  type: string
  required: false
  default: "True"
  description: 是否标记已清洗样本
- name: stats_output
  type: string
  required: false
  default: numeric_format_cleaner_stats.json
  description: 统计输出文件路径
output_params:
- name: output
  type: jsonl_file
  description: 清洗后的JSONL文件
- name: stats_output
  type: json_file
  description: 清洗统计文件
---

# Numeric Format Cleaner 数值格式清洗 Skill

## 功能概述

本 skill 读取 JSONL 结构化数据，按字段规则统一数值表达：单位转换、千分位格式、科学计数法、范围限制和空值填充。
适用于实验记录、环境观测、统计表等需要统一数值格式的科研数据处理场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数值格式清洗
- 单位统一
- 千分位规整
- 科学计数法输出
- 空值填充
- 按字段规则整理数值

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入 JSONL 文件路径 |
| `--output` | 输出 JSONL 文件路径 |
| `--field_rules` | 字段清洗规则 JSON |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--conversion_rules` | 单位转换规则 JSON | 空字符串 |
| `--decimal_places` | 默认小数位数 | `2` |
| `--fill_null` | 空值填充值 | 空字符串 |
| `--mark_cleaned` | 是否标记已清洗样本 | `True` |
| `--stats_output` | 统计输出文件路径 | `numeric_format_cleaner_stats.json` |

## 输入文件格式

输入必须为 JSONL，每行一个对象，字段值可以是数值、带单位字符串或空值。

```jsonl
{"distance": "12.3km", "weight": "1500g"}
{"distance": "N/A", "weight": null}
```

## 使用方法

```bash
python scripts/run_numeric_format_cleaner.py \
  --input data.jsonl \
  --output cleaned.jsonl \
  --field_rules '{"distance":{"target_unit":"m","decimal_places":2}}'
```

```bash
python scripts/run_numeric_format_cleaner.py \
  --input data.jsonl \
  --output cleaned.jsonl \
  --field_rules '{"distance":{"target_unit":"m","decimal_places":2},"weight":{"target_unit":"kg","decimal_places":3}}' \
  --conversion_rules '{"km::m":1000,"g::kg":0.001}' \
  --stats_output stats.json
```

## 处理示例

- `12.345km` → `10000.00m`
- `1500g` → `1.500kg`
- `1234567.89` → `1,234,568`
- `0.0004567` → `4.57e-04`
- `N/A` → 按 `fill_null` 填充

## 输出示例

```text
[OK] Numeric format cleaning completed
   Total samples: 10
   Samples with changes: 10
   Total field changes: 64
   Errors: 1
```

## 环境要求

- Python 3.10+
- 仅依赖标准库

## 注意事项

1. 输入必须是 JSONL，且字段规则用 JSON 字符串传入。
2. `fill_null` 只影响空值或 null-like 值，不会改动正常数值。
3. 只有字段规则命中的字段才会被处理。
4. `mark_cleaned=True` 时，会在输出中追加清洗标记字段。
