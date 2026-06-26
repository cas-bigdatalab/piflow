---
name: referential_integrity_check
description: '引用完整性校验工具。读取子表及参考表，检查外键值是否存在于参考键集合中，标记孤立记录行并输出结果文件。

  当用户提到外键检查、引用完整性、孤立记录、父子表引用等需求时使用此skill。

  即使用户没有明确说出“引用完整性”，只要任务涉及检查字段值是否能在参考表中找到，就应该使用此skill。

  不负责重复行、空值、列存在性、字段格式等其他校验任务。

  '
name_zh: 引用完整性校验算子
input_params:
- name: input_path
  type: string
  required: true
  description: 子表文件路径
- name: output_path
  type: string
  required: true
  description: 输出文件路径
- name: check_field
  type: string
  required: true
  description: 子表检查字段
- name: reference_path
  type: string
  required: false
  description: 外部参考表路径；不指定则使用同表中的 reference_column
- name: reference_column
  type: string
  required: true
  description: 参考列名
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

# Referential Integrity Check 引用完整性校验 Skill

## 功能概述

外键约束检查。两类模式：(1) 同表引用 — check_field 的值必须在同表的 reference_column 中存在；(2) 跨表引用 — check_field 的值必须在外部 reference_path 文件的 reference_column 中存在。标记在参考集中找不到匹配值的孤立行。

## 触发条件

当用户提到以下任务时，应使用此 skill：
- 外键检查
- 引用完整性
- 孤立记录
- 父子表引用

## 使用方法

```bash
python scripts/referential_integrity_check.py --input_path <输入文件> --output_path <输出文件> --check_field <检查字段> --reference_path <参考表文件> --reference_column <参考列> --qc_mark <质控标识> --mark_field_name <标识字段名>
```

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入文件路径 |
| `--output_path` | 输出文件路径 |
| `--check_field` | 检查字段（外键） |
| `--reference_column` | 参考列（主键） |
| `--qc_mark` | 质控标识 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--reference_path` | 外部参考表（不指定则同表） | 同表 |
| `--mark_field_name` | 质控标识字段名 | `QC0000` |

## 注意事项

1. 空值不标记为孤立值（仅标记有值但不在参考集中的行）
2. 参考值取自 reference_column 的去重集合
3. 列不存在时直接报错退出
