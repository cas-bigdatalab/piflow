---
name: QC6_SingleFieldMultiThresholdCheck
description: |
  单字段多条件阈值检验工具。读取被检验表和阈值表，将指定字段的属性项值与阈值表中定义的多条件门限进行比对，
  检查是否在门限范围内，不允许超出门限值（包括上限和下限）。不满足条件的数据会标记质控标识并输出异常数据。
  当用户提到单字段阈值检验、多条件阈值检验、单字段多条件检查等需求时使用此skill。
  即使用户没有说出"单字段多条件"，只要任务涉及根据多个条件进行单字段阈值校验，就应该使用此skill。

input_params:
  - name: original_file
    type: string
    required: true
    description: 被检验数据文件路径

  - name: threshold_file
    type: string
    required: true
    description: 阈值表文件路径

  - name: origin_output
    type: string
    required: true
    description: 处理后原始数据输出路径

  - name: field_name
    type: string
    required: true
    description: 阈值检测字段名

  - name: qc_mark
    type: string
    required: true
    description: 质控标识

  - name: error_output
    type: string
    required: false
    description: 异常数据输出路径（可选）

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

  - name: id_field_name
    type: string
    required: false
    default: ID0000
    description: 唯一ID字段名

output_params:
  - name: origin_output
    type: csv_file
    description: 处理后原始数据文件，带质控标识

  - name: error_output
    type: csv_file
    description: 异常数据文件（可选），包含不满足阈值条件的记录
tag: 校验
---

# QC6_SingleFieldMultiThresholdCheck 单字段多条件阈值检验Skill

## 功能概述

本skill用于将被检验表中的指定字段的属性项值与阈值表中定义的多条件门限进行比对，检查是否在门限范围内（不允许超出门限值包括上限和下限）。不满足条件的数据会标记质控标识并输出异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 单字段阈值检验
- 多条件阈值检验
- 单字段多条件检查
- 指定字段的范围校验
- 字段多条件门限检查

## 处理逻辑

1. 读取被检验表和阈值表数据
2. 根据用户指定的检测字段，遍历阈值表的每一行条件
3. 对每一行数据检查是否满足阈值条件：
   - max开头的列：检查字段值是否大于最大值
   - min开头的列：检查字段值是否小于最小值
   - 其他列：作为匹配条件进行精确匹配
4. 如果数据不满足任何阈值条件，则标记为异常
5. 为异常数据添加质控标识
6. 输出两个文件：
   - 处理后的原始数据（带质控标识）
   - 异常数据（可选）

## 阈值表格式

阈值表可以包含以下类型的列：
- `max_xxx`：最大值条件（如max_age表示age字段的最大值）
- `min_xxx`：最小值条件（如min_age表示age字段的最小值）
- 其他列：作为匹配条件进行精确匹配

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 被检验表路径
2. 阈值表路径
3. 处理后原始数据输出路径
4. 异常数据输出路径（可选）
5. 检测字段名
6. 质控标识
7. 质控标识字段名（默认：QC0000）
8. 唯一ID字段名（默认：ID0000）

### 步骤2：执行单字段多条件阈值检验脚本

在 `scripts/` 目录下找到 `QC6_SingleFieldMultiThresholdCheck.py`，使用Python执行：

```bash
python scripts/QC6_SingleFieldMultiThresholdCheck.py \
    --original_file <被检验表> \
    --threshold_file <阈值表> \
    --origin_output <处理后数据输出> \
    --error_output <异常数据输出> \
    --field_name <检测字段> \
    --qc_mark "<质控标识>" \
    --mark_field_name <质控字段名> \
    --id_field_name <ID字段名>
```

### 步骤3：返回结果

- 如果有异常数据：显示异常数量并输出异常数据预览
- 如果无异常：告知用户校验通过

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--original_file` | 是 | 被检验数据文件路径 |
| `--threshold_file` | 是 | 阈值表文件路径 |
| `--origin_output` | 是 | 处理后原始数据输出路径 |
| `--error_output` | 否 | 异常数据输出路径（可选） |
| `--field_name` | 是 | 阈值检测字段名 |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |
| `--id_field_name` | 否 | 唯一ID字段名，默认ID0000 |

## 阈值表示例

| min_age | max_age | region |
|---------|---------|-------|
| 0      | 18      | north |
| 19     | 60      | south |
| 61     | 120     | east  |

表示：
- region=north时，age需要在0-18之间
- region=south时，age需要在19-60之间
- region=east时，age需要在61-120之间

## 输出示例

### 有异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/original.csv, shape: (1000, 18)
Successfully read file: /path/to/threshold.csv, shape: (3, 3)
########## Exception: Threshold check failed: out of range!!!
First 10 abnormal records:
...
```

### 无异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/original.csv, shape: (1000, 18)
Successfully read file: /path/to/threshold.csv, shape: (3, 3)
Successfully written file: /path/to/output.csv
```

## 注意事项

1. 阈值表支持多条件组合判断
2. max开头的列表示最大值限制
3. min开头的列表示最小值限制
4. 其他列作为精确匹配条件
5. 数据必须满足阈值表中任意一行条件，否则标记为异常
6. 输出两个文件：处理后的原始数据（标记质控结果）和异常数据（可选）
