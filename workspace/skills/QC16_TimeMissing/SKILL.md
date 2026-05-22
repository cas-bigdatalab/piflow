---
name: QC16_TimeMissing
description: |
  数据时序完整性检查工具。读取时间序列数据，设定数据记录频率（如每2分钟、30分钟或60分钟），
  以此频率为基准遍历数据的时间范围，检查数据时序是否完整，发现缺失与多余数据点，最后输出为相同格式的文件。
  当用户提到时序完整性检查、时间序列缺失检查、时间点完整性、数据遗漏检验等需求时使用此skill。
  即使用户没有说出"时序完整性"，只要任务涉及检查时间序列数据是否有遗漏或多余的时间点，就应该使用此skill。

name_zh: QC16_数据时序完整性检查算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: origin_output_path
    type: string
    required: true
    description: 原始数据输出路径

  - name: error_output_path
    type: string
    required: true
    description: 异常数据输出路径（缺失/多余时间点）

  - name: data_frequency
    type: int
    required: true
    description: 数据记录频率（分钟，如30表示每30分钟）

  - name: time_field
    type: string
    required: true
    description: 时间字段名

  - name: time_format
    type: string
    required: true
    description: 时间格式（如：%Y-%m-%d %H:%M:%S）

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

output_params:
  - name: origin_output
    type: csv_file
    description: 处理后原始数据文件，带质控标识

  - name: error_output
    type: csv_file
    description: 异常数据文件，包含缺失/多余时间点记录
tag: 校验

---

# QC16_TimeMissing 数据时序完整性检查Skill

## 功能概述

本skill用于检查时间序列数据的时序完整性。具体来说：
1. 根据设定的时间频率（如每30分钟）生成预期的时间戳序列
2. 遍历数据的实际时间范围，识别缺失的时间点（数据遗漏）
3. 识别多余/不匹配的时间点（不在预期频率上的数据）
4. 标记异常数据并输出

## 触发条件

当用户请求以下任务时，应使用此skill：
- 时序完整性检查
- 时间序列缺失检查
- 时间点完整性检验
- 数据遗漏检验
- 检查时间序列是否有缺失时间点
- 检查时间序列是否有非预期时间点

## 处理逻辑

1. 读取输入的时间序列数据
2. 设定数据记录频率（如30分钟）
3. 计算数据时间范围内的预期时间点数量
4. 生成预期时间戳序列
5. 通过对比识别缺失时间点
6. 通过对比识别多余/不匹配时间点
7. 为异常数据添加质控标识
8. 输出处理后的数据文件（原始数据 + 异常数据）

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 输入文件路径
2. 原始数据输出路径
3. 异常数据输出路径
4. 数据记录频率（分钟，如30表示30分钟）
5. 时间字段名
6. 时间格式
7. 质控标识字段名（默认：QC0000）

### 步骤2：执行时序完整性检查脚本

在 `scripts/` 目录下找到 `QC16_TimeMissing.py`，使用Python执行：

```bash
python scripts/QC16_TimeMissing.py \
    --input_path <输入文件> \
    --origin_output_path <原始数据输出文件> \
    --error_output_path <异常数据输出文件> \
    --data_frequency <数据频率(分钟)> \
    --time_field <时间字段> \
    --time_format "<时间格式>" \
    --mark_field_name <质控字段名>
```

### 步骤3：返回结果

告知用户处理完成。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--origin_output_path` | 是 | 原始数据输出路径 |
| `--error_output_path` | 是 | 异常数据输出路径（缺失/多余时间点） |
| `--data_frequency` | 是 | 数据记录频率（分钟，如30表示每30分钟） |
| `--time_field` | 是 | 时间字段名 |
| `--time_format` | 是 | 时间格式（如：%Y-%m-%d %H:%M:%S） |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |

## 时间格式示例

| 格式 | 示例 |
|------|------|
| %Y-%m-%d | 2024-01-15 |
| %Y-%m-%d %H:%M:%S | 2024-01-15 14:30:00 |
| %Y/%m/%d | 2024/01/15 |

## 数据频率示例

| 频率值 | 含义 |
|--------|------|
| 2 | 每2分钟 |
| 30 | 每30分钟 |
| 60 | 每60分钟 |

## 输出示例

```
Start reading input data...
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, data shape: (100, 5)
Min timestamp in data: 2024-01-15 00:00:00
Max timestamp in data: 2024-01-15 23:30:00

--- Missing time period check report ---
Found missing time periods, total 5 time points:

--- Extra/mismatched time period check report ---
No extra or mismatched time points found with expected frequency.

Start writing original data...
Successfully wrote file: /path/to/origin_output.csv
Start writing error data...
Successfully wrote file: /path/to/error_output.csv
Processing completed!
```

## 质控标识说明

- `Missing time point` - 缺失时间点（数据遗漏）
- `Extra time point` - 多余时间点（非预期时间点）

## 注意事项

1. 时间字段必须是可解析的日期时间格式
2. 数据频率必须为正整数（分钟）
3. 异常数据会输出到单独的文件，包含时间字段和质控标识字段
4. 原始数据保持不变，仅输出异常数据明细
5. 时间格式需要与实际数据中的格式完全匹配
