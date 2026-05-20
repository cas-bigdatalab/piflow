---
name: QC10_TimeConsistency
description: |
  时间一致性检查工具。读取被检验表，按时间序列检查数据的时间一致性，
  判断相邻时间点的数据变化是否在合理范围内，识别并标记异常数据，最后输出为相同格式的文件。
  当用户提到时间一致性检查、时间序列校验、数据变化检查、时序一致性等需求时使用此skill。
  即使用户没有说出"时间一致性"，只要任务涉及检查数据的时间序列一致性，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: origin_output_path
    type: string
    required: true
    description: 处理后数据输出路径

  - name: field_name
    type: string
    required: true
    description: 一致性检查字段名

  - name: range_of_change
    type: float
    required: true
    description: 年变化量（允许的变化阈值）

  - name: change_type
    type: string
    required: true
    description: 变化类型（正值/负值/绝对值）

  - name: qc_mark
    type: string
    required: true
    description: 质控标识

  - name: error_output_path
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
    description: 异常数据文件（可选），包含时间一致性检查不通过的记录
---

# QC10_TimeConsistency 时间一致性检查Skill

## 功能概述

本skill用于检查数据的时间一致性，按时间序列（年份）排序，对比相邻时间点的数据变化是否在合理范围内。如果数据变化超出允许的变化范围，则标记为异常。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 时间一致性检查
- 时间序列校验
- 数据变化检查
- 时序一致性检验
- 检查数据变化是否合理

## 处理逻辑

1. 读取输入的被检验数据
2. 按分组字段（sss000, sscode, fa0110, fa0112）和时间字段（yyyy00）排序
3. 关联相邻时间点的记录，计算差值
4. 根据变化类型（正值/负值/绝对值）判断是否超出允许范围
5. 为异常数据添加质控标识
6. 输出两个文件：
   - 处理后的原始数据（带质控标识）
   - 异常数据（可选）

## 分组字段

默认分组字段（用于区分不同数据组）：
- sss000
- sscode
- fa0110
- fa0112
- yyyy00（时间排序字段）

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 输入文件路径
2. 处理后数据输出路径
3. 异常数据输出路径（可选）
4. 一致性检查字段名
5. 年变化量
6. 变化类型（正值/负值/绝对值）
7. 质控标识
8. 质控标识字段名（默认：QC0000）
9. 唯一ID字段名（默认：ID0000）

### 步骤2：执行时间一致性检查脚本

在 `scripts/` 目录下找到 `QC10_TimeConsistency.py`，使用Python执行：

```bash
python scripts/QC10_TimeConsistency.py \
    --input_path <输入文件> \
    --origin_output_path <处理后数据输出> \
    --error_output_path <异常数据输出> \
    --field_name <检查字段> \
    --range_of_change <年变化量> \
    --change_type <正值|负值|绝对值> \
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
| `--input_path` | 是 | 输入文件路径 |
| `--origin_output_path` | 是 | 处理后数据输出路径 |
| `--error_output_path` | 否 | 异常数据输出路径（可选） |
| `--field_name` | 是 | 一致性检查字段名 |
| `--range_of_change` | 是 | 年变化量（允许的变化阈值） |
| `--change_type` | 是 | 变化类型：正值/负值/绝对值 |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |
| `--id_field_name` | 否 | 唯一ID字段名，默认ID0000 |

## 变化类型说明

- **正值**：检查数据增加量是否超出允许范围
- **负值**：检查数据减少量是否超出允许范围
- **绝对值**：检查数据变化的绝对值是否超出允许范围

## 输出示例

### 有异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
########## Exception: Time consistency check failed!!!
Abnormal data count: 25
First 10 abnormal records:
...
```

### 无异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully written file: /path/to/output.csv
Time consistency check passed!
```

## 注意事项

1. 数据需要包含必要的分组字段：sss000, sscode, fa0110, fa0112, yyyy00
2. 年变化量是指允许的年度变化阈值
3. 变化类型决定判断异常的条件
4. 输出两个文件：处理后的原始数据（标记质控结果）和异常数据（可选）
