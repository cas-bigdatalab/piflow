---
name: QC12_ConstantFieldCheck
description: |
  特定字段恒定下的其他字段不一致检查工具。读取被检验表，当某些字段（恒定字段）的值相同时，
  检查其他指定字段（差异字段）是否存在多个不同的值，如果存在则标记为异常数据，最后输出为相同格式的文件。
  当用户提到恒定字段检查、字段一致性检查、分组内差异检查等需求时使用此skill。
  即使用户没有说出"恒定字段"，只要任务涉及检查分组内字段是否存在不一致，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: output_path
    type: string
    required: true
    description: 输出文件路径

  - name: constantFieldsNames
    type: string
    required: true
    description: 恒定字段，逗号分隔（如：field1,field2）

  - name: diffFieldsNames
    type: string
    required: true
    description: 差异字段，逗号分隔（如：field3,field4）

  - name: QcMark
    type: string
    required: true
    description: 质控标识

  - name: markFieldName
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

  - name: idFieldName
    type: string
    required: false
    default: ID0000
    description: 唯一ID字段名

output_params:
  - name: output
    type: csv_file
    description: 恒定字段一致性检查后的结构化数据文件，带质控标识
---

# QC12_ConstantFieldCheck 恒定字段一致性检查Skill

## 功能概述

本skill用于检查当特定字段（恒定字段）的值相同时，其他指定字段（差异字段）是否存在多个不同的值。如果存在不一致，则标记为异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 恒定字段检查
- 字段一致性检查
- 分组内差异检查
- 检查分组内字段是否一致
- 检查相同条件下的字段是否相同

## 处理逻辑

1. 读取输入的被检验数据
2. 解析恒定字段列表和差异字段列表
3. 按恒定字段进行分组
4. 检查每个分组内差异字段的唯一值数量
5. 如果差异字段存在多个不同值，标记该分组的所有数据为异常
6. 为异常数据添加质控标识
7. 输出处理后的数据文件

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 输入文件路径
2. 输出文件路径
3. 恒定字段名（逗号分隔，按这些字段进行分组）
4. 差异字段名（逗号分隔，检查这些字段是否存在不一致）
5. 质控标识
6. 质控标识字段名（默认：QC0000）
7. 唯一ID字段名（默认：ID0000）

### 步骤2：执行恒定字段一致性检查脚本

在 `scripts/` 目录下找到 `QC12_ConstantFieldCheck.py`，使用Python执行：

```bash
python scripts/QC12_ConstantFieldCheck.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --constantFieldsNames "<恒定字段>" \
    --diffFieldsNames "<差异字段>" \
    --QcMark "<质控标识>" \
    --markFieldName <质控字段名> \
    --idFieldName <ID字段名>
```

### 步骤3：返回结果

告知用户处理完成。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--constantFieldsNames` | 是 | 恒定字段，逗号分隔（如：field1,field2） |
| `--diffFieldsNames` | 是 | 差异字段，逗号分隔（如：field3,field4） |
| `--QcMark` | 是 | 质控标识 |
| `--markFieldName` | 否 | 质控标识字段名，默认QC0000 |
| `--idFieldName` | 否 | 唯一ID字段名，默认ID0000 |

## 使用示例

假设有以下数据：

| ID | region | type | value |
|----|-------|------|-------|
| 1  | A     | 1    | 100   |
| 2  | A     | 1    | 200   |
| 3  | B     | 2    | 150   |

如果设置：
- 恒定字段：region
- 差异字段：value

则检查结果：region=A的分组中，value有100和200两个不同值，存在不一致，标记为异常。

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Processing completed! Output saved to: /path/to/output.csv
```

## 注意事项

1. 恒定字段用于数据分组，相同值的记录被分为一组
2. 检查差异字段在同一分组内是否存在多个不同的值
3. 如果分组内差异字段存在多个不同值，该分组的所有记录都会被标记为异常
4. 质控标识会追加到原有的质控标识字段中，用分号分隔
