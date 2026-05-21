---
name: QC7_BatchInputThresholdCheck
description: |
  批量阈值检验-输入框工具。读取被检验表，将数据列的值与输入阈值条件中定义的上下限进行比对，
  识别并标记超出允许范围（包括上限和下限）或为空值的数据点，最后输出为相同格式的文件。
  当用户提到批量阈值检验、输入框阈值检验、多字段阈值检查、范围校验等需求时使用此skill。
  即使用户没有明确说出"批量阈值输入框"，只要任务涉及根据输入的阈值条件进行批量范围校验，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: output_path
    type: string
    required: true
    description: 输出文件路径

  - name: conditions
    type: string
    required: true
    description: 阈值条件，格式：字段名,最大值,最小值，多行用换行分隔

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
    description: 批量阈值检验后的结构化数据文件，带质控标识
tag: 校验
---

# QC7_BatchInputThresholdCheck 批量阈值检验(输入框) Skill

## 功能概述

本skill用于将数据表中的字段值与用户输入的阈值条件（上下限）进行批量比对，识别并标记超出允许范围（包括上限和下限）或为空值的数据点。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 批量阈值检验
- 输入框阈值检验
- 多字段阈值检查
- 范围校验
- 检查数值是否在输入的阈值范围内
- 批量输入范围检查

## 处理逻辑

1. 解析用户输入的阈值条件（格式：字段名,最大值,最小值）
2. 读取被检验数据
3. 遍历阈值映射表，检查每个字段：
   - 如果字段值为空，标记为异常
   - 如果字段值超出最大值或小于最小值，标记为异常
4. 为异常数据添加质控标识（格式：QC7(异常字段1,异常字段2,...)）
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
3. 阈值检验条件（格式：字段名,最大值,最小值，多行用换行分隔）
4. 质控标识（如：QC7）
5. 质控标识字段名（默认：QC0000）

### 步骤2：执行批量阈值检验脚本

在 `scripts/` 目录下找到 `QC7_BatchInputThresholdCheck.py`，使用Python执行：

```bash
python scripts/QC7_BatchInputThresholdCheck.py \
    --input-path <输入文件> \
    --output-path <输出文件> \
    --conditions "<阈值条件>" \
    --qc-mark "<质控标识>" \
    --mark-field-name <质控字段名>
```

### 步骤3：返回结果

告知用户处理完成，异常数据已标记质控标识。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input-path` | 是 | 输入文件路径 |
| `--output-path` | 是 | 输出文件路径 |
| `--conditions` | 是 | 阈值条件，格式：字段名,最大值,最小值，多行用换行分隔 |
| `--qc-mark` | 是 | 质控标识 |
| `--mark-field-name` | 否 | 质控标识字段名，默认QC0000 |

## 阈值条件格式

每行格式：`字段名,最大值,最小值`

示例：
```
Temp,36,-5
pH,14,0
age,120,0
```

表示：
- Temp字段值需要在-5到36之间
- pH字段值需要在0到14之间
- age字段值需要在0到120之间

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
```

质控标识格式示例：`QC7(Temp,pH)` 表示Temp和pH字段超出阈值范围

## 注意事项

1. 阈值条件格式：字段名,最大值,最小值，每行一个字段
2. 超出阈值范围或为空的值都会被标记
3. 质控标识格式：质控标识(异常字段1,异常字段2,...)
4. 多个异常字段用逗号分隔
5. 与原有质控标识用分号拼接
