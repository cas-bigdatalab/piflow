---
name: QC4_AssociationRuleCheck
description: |
  数值关联规则校验工具。读取被检验表，根据用户自定义的条件表达式（类似Hive SQL规则）进行数据校验，
  具有关联关系的数据项需满足特定约束条件。不满足条件的数据会标记质控标识并输出异常数据。
  当用户提到关联规则校验、数据约束校验、自定义规则校验、条件表达式校验等需求时使用此skill。
  即使用户没有说出"关联规则"，只要任务涉及根据自定义条件表达式进行数据校验，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: origin_output_path
    type: string
    required: true
    description: 处理后原始数据输出路径

  - name: expression
    type: string
    required: true
    description: 条件表达式（pandas eval语法）

  - name: filter_type
    type: string
    required: true
    description: yes=满足表达式为正确数据，not=满足表达式为异常数据

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
    description: 异常数据文件（可选），包含不满足约束条件的记录
---

# QC4_AssociationRuleCheck 关联规则校验Skill

## 功能概述

本skill用于根据用户自定义的条件表达式（类似Hive SQL/HiveQL规则）对数据进行校验，具有关联关系的数据项需满足特定约束条件。不满足条件的数据会标记质控标识并输出异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 关联规则校验
- 数据约束校验
- 自定义规则校验
- 条件表达式校验
- 数据逻辑校验
- 根据表达式检查数据

## 处理逻辑

1. 读取输入的被检验数据
2. 解析并执行用户自定义的条件表达式（pandas eval语法）
3. 根据filter_type参数判断：
   - `not`：满足表达式的是异常数据
   - `yes`：满足表达式的是正确数据（取反）
4. 为异常数据添加质控标识
5. 输出两个文件：
   - 处理后的原始数据（带质控标识）
   - 异常数据（可选）

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 输入文件路径
2. 处理后原始数据输出路径
3. 异常数据输出路径（可选）
4. 条件表达式（pandas eval语法）
5. 过滤类型（yes/not）
6. 质控标识
7. 质控标识字段名（默认：QC0000）
8. 唯一ID字段名（默认：ID0000）

### 步骤2：执行关联规则校验脚本

在 `scripts/` 目录下找到 `QC4_AssociationRuleCheck.py`，使用Python执行：

```bash
python scripts/QC4_AssociationRuleCheck.py \
    --input_path <输入文件> \
    --origin_output_path <处理后数据输出> \
    --error_output_path <异常数据输出> \
    --expression "<条件表达式>" \
    --filter_type <yes|not> \
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
| `--origin_output_path` | 是 | 处理后原始数据输出路径 |
| `--error_output_path` | 否 | 异常数据输出路径（可选） |
| `--expression` | 是 | 条件表达式（pandas eval语法） |
| `--filter_type` | 是 | yes：满足表达式的是正确数据；not：满足表达式的是异常数据 |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |
| `--id_field_name` | 否 | 唯一ID字段名，默认ID0000 |

## 表达式语法说明

支持以下pandas eval语法：
1. 关系运算：`==`, `!=`, `<`, `<=`, `>`, `>=`, `isna`, `notna`, `str.contains`
2. 逻辑运算：`&`, `|`, `~`
3. 数值运算：`round`, `abs`, `sin`, `cos`
4. 字符串函数：`str.len`, `str.lower`, `str.upper`, `str.strip`
5. 数学运算：`+`, `-`, `*`, `/`, `%`
6. 类型转换：`astype`，例：`age.astype('float')`

## 输出示例

### 有异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Reading input data: /path/to/input.csv
Starting numeric association rule check...
Writing processed data: /path/to/output.csv
==================================================
Found 25 abnormal records, first 10 preview:
...
==================================================
```

### 无异常数据
```
[OK] Using encoding GB2312 successfully read CSV file
Reading input data: /path/to/input.csv
Starting numeric association rule check...
Writing processed data: /path/to/output.csv
No abnormal data found
```

## 注意事项

1. 条件表达式使用pandas eval语法，需符合pandas规范
2. filter_type参数决定表达式的含义：
   - `not`：满足表达式 = 异常数据
   - `yes`：满足表达式 = 正确数据（取反后才是异常数据）
3. 输出两个文件：处理后的原始数据（标记质控结果）和异常数据（可选）
