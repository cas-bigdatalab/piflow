---
name: unique_constraint_check
description: |
  唯一性约束校验工具。检查指定字段的值是否在全表中唯一，标记重复出现的值所在行
  （保留首次出现），支持空值跳过。当用户提到唯一性检查、重复值检测、主键约束等需求时使用此skill。
name_zh: 唯一性约束校验算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: unique_fields
    type: string
    required: true
    description: 唯一性字段，逗号分隔，每个字段分别检查
  - name: allow_null
    type: string
    required: false
    description: 允许多个空值（默认开启，空值不视为重复）
  - name: qc_mark
    type: string
    required: true
    description: 质控标识
  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名
output_params:
  - name: output_path
    type: csv_file
    description: 带质控标识的输出文件
tag: 校验
---

# unique_constraint_check 唯一性约束校验Skill

## 功能概述

检查字段值是否在全表中唯一。多字段时分别独立检查（非组合唯一键），空值默认跳过不参与检测。适用于主键约束、业务唯一键（如邮箱、手机号）验证。

## 处理逻辑

1. 读取输入数据表
2. 对每个 unique_fields 中的字段分别执行 duplicated(keep='first')
3. 空值（空串/nan/None/NA/null）默认跳过
4. 重复行标记 qc_mark（首次出现保留，后续重复标记）
5. 输出每字段的重复统计和样例值

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
# 检查 email 和 phone 分别唯一
python scripts/unique_constraint_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --unique_fields "email,phone" \
    --qc_mark QC0027
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--unique_fields` | 是 | 唯一字段，逗号分隔（分别检查） |
| `--allow_null` | 否 | 允许多个空值（开启后空值不视为重复） |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名（默认 QC0000） |

## 输出示例

```
[QC FAIL] 唯一性约束未通过 (2 项):
  [email] 1 行重复，示例: ['alice@test.com']
  [phone] 1 行重复，示例: ['13800138000']
```

## 注意事项

1. 多字段是分别独立检查（如 `email,phone` 检查 email 唯一 AND phone 唯一），不是组合唯一键
2. 如有组合唯一需求（如 email+phone 同时相同），请先用 Pi 技能合并字段再检查
3. 空值默认跳过，使用 `--allow_null` 可将空值也视为可重复的值
4. keep='first' 保留首次出现，后续重复标记
