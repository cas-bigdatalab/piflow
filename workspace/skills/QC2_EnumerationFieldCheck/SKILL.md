---
name: QC2_EnumerationFieldCheck
description: |
  公共基础项枚举校验工具。读取被检验表和标准词典文件，将被检验表中的属性项值与标准词典进行比对，
  检查是否超出词典规定的固有词表枚举值范围，超出范围的记录会标记质控标识并输出异常数据。
  当用户提到枚举校验、枚举值检查、属性项校验、词表校验等需求时使用此skill。
  即使用户没有明确说出"枚举校验"，只要任务涉及将被检验数据与标准词典进行比对，就应该使用此skill。

input_params:
  - name: origin_file_path
    type: string
    required: true
    description: 被检验数据文件路径

  - name: standard_file_path
    type: string
    required: true
    description: 标准词典文件路径

  - name: error_output_path
    type: string
    required: true
    description: 异常数据输出路径

  - name: origin_output_path
    type: string
    required: true
    description: 处理后原始数据输出路径

  - name: comparison_field
    type: string
    required: true
    description: 对比字段，格式：原字段1,原字段2:标准字段1,标准字段2

  - name: qc_mark
    type: string
    required: true
    description: 质控标识（如QC2_ERROR）

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
  - name: error_output
    type: csv_file
    description: 异常数据文件，包含不在标准词典范围内的记录

  - name: origin_output
    type: csv_file
    description: 处理后原始数据文件，带质控标识
tag: 校验
---

# QC2_EnumerationFieldCheck 枚举校验Skill

## 功能概述

本skill用于将被检验表中的属性项值与相应标准词典进行比对，检查是否超出词典规定的固有词表枚举值范围。如果超出范围，会标记质控标识并输出异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 枚举校验
- 枚举值检查
- 属性项校验
- 词表校验
- 检查数据是否在标准词典范围内
- 数据枚举值验证

## 处理逻辑

1. 读取被检验表和标准词典文件
2. 根据指定的对比字段进行匹配（支持多字段）
3. 找出不在标准词典范围内的异常数据
4. 为异常数据添加质控标识
5. 输出两个文件：
   - 异常数据文件
   - 处理后的原始数据文件（带质控标识）

## 输入文件说明

### 被检验表 (origin_file_path)
需要校验的数据文件，支持CSV、TSV、Excel、SPSS等格式。

### 标准词典表 (standard_file_path)
标准词典文件，包含正确的枚举值列表。

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 被检验表路径
2. 标准词典文件路径
3. 异常数据输出路径
4. 处理后原始数据输出路径
5. 对比字段（格式：原始字段:标准字段，如：sscode,ssname:sscode,ssname）
6. 质控标识（如：QC2_ERROR）
7. 质控标识字段名（默认：QC0000）
8. 唯一ID字段名（默认：ID0000）

### 步骤2：执行枚举校验脚本

在 `scripts/` 目录下找到 `QC2_EnumerationFieldCheck.py`，使用Python执行：

```bash
python scripts/QC2_EnumerationFieldCheck.py \
    --origin_file_path <被检验表> \
    --standard_file_path <标准词典> \
    --error_output_path <异常数据输出> \
    --origin_output_path <处理后数据输出> \
    --comparison_field "<对比字段>" \
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
| `--origin_file_path` | 是 | 被检验数据文件路径 |
| `--standard_file_path` | 是 | 标准词典文件路径 |
| `--error_output_path` | 是 | 异常数据输出路径 |
| `--origin_output_path` | 是 | 处理后原始数据输出路径 |
| `--comparison_field` | 是 | 对比字段，格式：原字段1,原字段2:标准字段1,标准字段2 |
| `--qc_mark` | 是 | 质控标识（如QC2_ERROR） |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |
| `--id_field_name` | 否 | 唯一ID字段名，默认ID0000 |

## 输出示例

### 有异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/origin.csv, shape: (1000, 18)
Successfully read file: /path/to/standard.csv, shape: (50, 2)
########## Exception: Enumeration value out of range!!!
Abnormal data (first 10 rows):
...
Enumeration check completed, output files generated!
```

### 无异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/origin.csv, shape: (1000, 18)
Successfully read file: /path/to/standard.csv, shape: (50, 2)
Enumeration check completed, output files generated!
```

## 注意事项

1. 对比字段格式必须正确，使用冒号分隔原字段和标准字段
2. 输出两个文件：异常数据和处理后的原始数据
3. 异常数据的质控标识字段会被标记为用户指定的质控标识
4. 处理后的原始数据会保留原始质控标识并追加新的标识
