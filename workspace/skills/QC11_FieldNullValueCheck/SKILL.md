---
name: QC11_FieldNullValueCheck
description: |
  字段空值检查工具。读取被检验表，检查指定字段是否存在空值（NULL/NA），
  识别并标记存在空值的数据点，最后输出为相同格式的文件。
  当用户提到空值检查、字段空值校验、缺失值检查、NULL值检查等需求时使用此skill。
  即使用户没有说出"空值检查"，只要任务涉及检查数据字段是否为空，就应该使用此skill。

name_zh: QC11_字段空值检查算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: output_path
    type: string
    required: true
    description: 输出文件路径

  - name: check_fields_name
    type: string
    required: true
    description: 检查字段名，逗号分隔（如：field1,field2）

  - name: qc_mark
    type: string
    required: false
    default: "缺测检查"
    description: 质控标识

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
  - name: output
    type: csv_file
    description: 空值检查后的结构化数据文件，带质控标识
tag: 校验

---

# QC11_FieldNullValueCheck 字段空值检查Skill

## 功能概述

本skill用于检查指定字段是否存在空值（NULL/NA），识别并标记存在空值的数据点。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 空值检查
- 字段空值校验
- 缺失值检查
- NULL值检查
- 检查字段是否有空值
- 数据完整性检查

## 处理逻辑

1. 读取输入的被检验数据
2. 解析需要检查的字段列表（逗号分隔）
3. 检查指定字段是否存在空值
4. 为存在空值的记录添加质控标识
5. 输出处理后的数据文件

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
3. 检查字段名（逗号分隔）
4. 质控标识
5. 质控标识字段名（默认：QC0000）
6. 唯一ID字段名（默认：ID0000）

### 步骤2：执行字段空值检查脚本

在 `scripts/` 目录下找到 `QC11_FieldNullValueCheck.py`，使用Python执行：

```bash
python scripts/QC11_FieldNullValueCheck.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --check_fields_name "<检查字段>" \
    --qc_mark "<质控标识>" \
    --mark_field_name <质控字段名> \
    --id_field_name <ID字段名>
```

### 步骤3：返回结果

告知用户处理完成，显示处理数据条数和异常数据条数。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--check_fields_name` | 是 | 检查字段名，逗号分隔（如：field1,field2） |
| `--qc_mark` | 否 | 质控标识，默认"缺测检查" |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |
| `--id_field_name` | 否 | 唯一ID字段名，默认ID0000 |

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Null value check completed! Processed 1000 records, abnormal records: 25, output to: /path/to/output.csv
Script executed successfully!
```

## 注意事项

1. 检查字段名用逗号分隔，可以同时检查多个字段
2. 任意指定字段为空则标记为异常
3. 质控标识会追加到原有的质控标识字段中，用分号分隔
