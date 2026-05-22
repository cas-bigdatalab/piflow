---
name: QC8_DataTypeCheck
description: |
  数据类型检查工具。读取被检验表，检查指定数值型字段的数据类型是否正确（是否能转换为数值型），
  并标记不合格的数据点，最后输出为相同格式的文件。
  当用户提到数据类型检查、数值类型校验、字段类型检查、数据格式校验等需求时使用此skill。
  即使用户没有说出"数据类型检查"，只要任务涉及检查数据字段类型是否正确，就应该使用此skill。

name_zh: QC8_数据类型检查算子
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
    required: true
    description: 质控标识

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

output_params:
  - name: output
    type: csv_file
    description: 数据类型检查后的结构化数据文件，带质控标识
tag: 校验

---

# QC8_DataTypeCheck 数据类型检查Skill

## 功能概述

本skill用于检查指定数值型字段的数据类型是否正确（是否能转换为数值型），将无法转换为数值型的数据标记为不合格，并输出处理后的数据文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数据类型检查
- 数值类型校验
- 字段类型检查
- 数据格式校验
- 检查字段是否为数值型
- 验证数据类型

## 处理逻辑

1. 读取输入的被检验数据
2. 解析需要检查的字段列表（逗号分隔）
3. 对每个指定字段进行检查：
   - 如果字段值可以转换为数值型，则为正常
   - 如果字段值无法转换为数值型（如包含字母、特殊字符等），则标记为异常
   - 空值（NA/NaN）不判定为错误
4. 为异常数据添加质控标识（格式：QC8(字段1,字段2,...)）
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
4. 质控标识（如：QC8）
5. 质控标识字段名（默认：QC0000）

### 步骤2：执行数据类型检查脚本

在 `scripts/` 目录下找到 `QC8_DataTypeCheck.py`，使用Python执行：

```bash
python scripts/QC8_DataTypeCheck.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --check_fields_name "<检查字段>" \
    --qc_mark "<质控标识>" \
    --mark_field_name <质控字段名>
```

### 步骤3：返回结果

告知用户处理完成，异常数据已标记质控标识。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--check_fields_name` | 是 | 检查字段名，逗号分隔（如：field1,field2） |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Reading input data: /path/to/input.csv
Starting data type check, check fields: fa0116,fa0118
Writing output data: /path/to/output.csv
Processing completed!
```

质控标识格式示例：`QC8(fa0116)` 表示fa0116字段存在非数值型数据

## 注意事项

1. 检查字段名用逗号分隔，可以同时检查多个字段
2. 空值（NA/NaN）不会被标记为错误
3. 质控标识格式：质控标识(异常字段1,异常字段2,...)
4. 多个异常字段用逗号分隔
5. 与原有质控标识用分号拼接
