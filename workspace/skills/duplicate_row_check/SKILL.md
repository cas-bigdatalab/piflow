---
name: duplicate_row_check
description: '结构化表格重复行检测工具。仅检查CSV/TSV/Excel等表格型数据中的完全重复记录或指定列子集重复，

  标记后续重复行并保留首次出现；不处理文本片段清理、文档去重或其他字段质控。

  '
name_zh: 重复行检测算子
input_params:
- name: input_path
  type: string
  required: true
  description: 输入文件路径
- name: output_path
  type: string
  required: true
  description: 输出文件路径
- name: dup_columns
  type: string
  required: false
  description: 检测列，逗号分隔；不指定则全列比较
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

# Duplicate Row Check 重复行检测 Skill

## 功能概述

检测表格型结构化数据中的精确重复行。可指定列子集比较（如仅按 name+email 检测），首次出现的行标记为空（通过），后续重复行标记为质控标识。与去重类技能不同，duplicate_row_check 负责行级校验而不是删除重复行。

## 触发条件

当用户提到以下任务时，应使用此 skill：
- 重复行检测
- 完全重复记录检查
- 指定列重复校验
- 行级重复质控

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入文件路径 |
| `--output_path` | 输出文件路径 |
| `--qc_mark` | 质控标识 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--dup_columns` | 检测列，逗号分隔；不指定则全列比较 | 全列比较 |
| `--mark_field_name` | 质控标识字段名 | `QC0000` |

## 输入文件格式

- CSV、TSV、Excel、SPSS 等结构化表格文件

## 使用方法

```bash
python scripts/duplicate_row_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --dup_columns "name,email" \
    --qc_mark QC0020
```

## 输出示例

```
[QC FAIL] 发现 1 行重复 (检测列: ['name'])
[OK] 结果已写入 -> output.csv
```

## 注意事项

1. 不指定 dup_columns 时全列比较（包含所有字段）
2. keep='first' 保留首次出现，后续重复标记
3. 与去重类技能不同，duplicate_row_check 不删除重复行，仅标记
