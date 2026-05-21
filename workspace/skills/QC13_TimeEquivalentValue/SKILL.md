---
name: QC13_TimeEquivalentValue
description: |
  等值检验（连续数值无变化检查）工具。读取时间序列数据，检查在连续的时间段内，
  某个关键指标的数值是否长时间保持不变（久无变化检查），识别并标记异常数据，最后输出为相同格式的文件。
  当用户提到等值检验、连续无变化检查、久无变化检查、时间序列恒定值检查等需求时使用此skill。
  即使用户没有说出"等值检验"，只要任务涉及检查时间序列数据是否长时间保持不变，就应该使用此skill。

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
    description: 检验条件，格式：字段名,连续次数，多行用换行分隔

  - name: time_field
    type: string
    required: true
    description: 时间字段名（用于排序判断连续性）

  - name: time_format
    type: string
    required: true
    description: 时间格式（如：%Y-%m-%d %H:%M:%S）

  - name: qc_mark
    type: string
    required: false
    default: "等值异常"
    description: 质控标识

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

output_params:
  - name: output
    type: csv_file
    description: 等值检验后的结构化数据文件，带质控标识
tag: 校验
---

# QC13_TimeEquivalentValue 等值检验Skill

## 功能概述

本skill用于检查时间序列数据中，在连续的时间段内某个关键指标的数值是否长时间保持不变。如果数值连续多次保持不变，则标记为异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 等值检验
- 连续无变化检查
- 久无变化检查
- 时间序列恒定值检查
- 检查数据是否长时间不变
- 连续数值不变检查

## 处理逻辑

1. 读取输入的被检验数据
2. 解析等值检验条件（字段名和连续次数）
3. 按时间字段排序
4. 对每个指定字段，检查连续N个时间点数值是否相同
5. 如果连续N次数值相同，标记为异常
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
3. 等值检验条件（格式：字段名,连续次数）
4. 时间字段名
5. 时间格式
6. 质控标识（默认：等值异常）
7. 质控标识字段名（默认：QC0000）

### 步骤2：执行等值检验脚本

在 `scripts/` 目录下找到 `QC13_TimeEquivalentValue.py`，使用Python执行：

```bash
python scripts/QC13_TimeEquivalentValue.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --conditions "<检验条件>" \
    --time_field <时间字段> \
    --time_format "<时间格式>" \
    --qc_mark "<质控标识>" \
    --mark_field_name <质控字段名>
```

### 步骤3：返回结果

告知用户处理完成。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--conditions` | 是 | 检验条件，格式：字段名,连续次数（如：Do_ppm,3）多行用换行分隔 |
| `--time_field` | 是 | 时间字段名（用于排序判断连续性） |
| `--time_format` | 是 | 时间格式（如：%Y-%m-%d %H:%M:%S） |
| `--qc_mark` | 否 | 质控标识，默认"等值异常" |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |

## 检验条件格式

每行格式：`字段名,连续次数`

示例：
```
Do_ppm,3
Temp_C,3
pH,3
```

表示：
- Do_ppm字段连续3次相同则标记异常
- Temp_C字段连续3次相同则标记异常
- pH字段连续3次相同则标记异常

## 时间格式示例

| 格式 | 示例 |
|------|------|
| %Y-%m-%d | 2024-01-15 |
| %Y-%m-%d %H:%M:%S | 2024-01-15 14:30:00 |
| %Y/%m/%d | 2024/01/15 |

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Reading input data: /path/to/input.csv
Writing output data: /path/to/output.csv
Processing completed!
```

质控标识格式示例：`等值异常(Do_ppm)` 表示Do_ppm字段连续多次数值相同

## 注意事项

1. 检验条件格式：字段名,连续次数，每行一个字段
2. 连续次数N表示连续N次数值相同则标记为异常
3. 数据按时间字段排序后进行检查
4. 质控标识格式：质控标识(异常字段1,异常字段2,...)
5. 与原有质控标识用分号拼接
