---
name: QC5_BatchThresholdCheck
description: |
  批量阈值检验工具。读取被检验表和阈值表，将数据列的值与阈值表中定义的上下限进行比对，
  识别并标记超出允许范围（包括上限和下限）或为空值的数据点，最后输出为相同格式的文件。
  当用户提到批量阈值检验、阈值表校验、多字段阈值检查、范围校验等需求时使用此skill。
  即使用户没有明确说出"批量阈值"，只要任务涉及根据阈值表进行多字段范围校验，就应该使用此skill。

name_zh: QC5_批量阈值检验算子
input_params:
  - name: original_data_path
    type: string
    required: true
    description: 被检验数据文件路径

  - name: threshold_data_path
    type: string
    required: true
    description: 阈值表文件路径（包含field、max_value、min_value三列）

  - name: output_path
    type: string
    required: true
    description: 处理后数据输出路径

  - name: qc_mark
    type: string
    required: true
    description: 质控标识（如QC5）

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

output_params:
  - name: output_path
    type: csv_file
    description: 批量阈值检验后的结构化数据文件，带质控标识
tag: 校验

---

# QC5_BatchThresholdCheck 批量阈值检验Skill

## 功能概述

本skill用于将数据表中的字段值与阈值表中定义的上下限进行批量比对，识别并标记超出允许范围（包括上限和下限）或为空值的数据点。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 批量阈值检验
- 阈值表校验
- 多字段阈值检查
- 范围校验
- 检查数值是否在阈值范围内
- 批量范围检查

## 处理逻辑

1. 读取被检验表和阈值表数据
2. 从阈值表构建阈值映射表（字段名 -> 最大值, 最小值）
3. 遍历数据表的每一行，检查每个阈值字段：
   - 如果字段值为空，标记为异常
   - 如果字段值超出最大值或小于最小值，标记为异常
4. 为异常数据添加质控标识（格式：QC5(异常字段1,异常字段2,...)）
5. 输出处理后的数据文件

## 阈值表格式

阈值表必须包含以下三列：
- `field`：字段名
- `max_value`：最大值
- `min_value`：最小值

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
3. 输出文件路径
4. 质控标识（如：QC5）
5. 质控标识字段名（默认：QC0000）

### 步骤2：执行批量阈值检验脚本

在 `scripts/` 目录下找到 `QC5_BatchThresholdCheck.py`，使用Python执行：

```bash
python scripts/QC5_BatchThresholdCheck.py \
    --original_data_path <被检验表> \
    --threshold_data_path <阈值表> \
    --output_path <输出文件> \
    --qc_mark "<质控标识>" \
    --mark_field_name <质控字段名>
```

### 步骤3：返回结果

告知用户处理完成，异常数据已标记质控标识。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--original_data_path` | 是 | 被检验数据文件路径 |
| `--threshold_data_path` | 是 | 阈值表文件路径 |
| `--output_path` | 是 | 处理后数据输出路径 |
| `--qc_mark` | 是 | 质控标识（如QC5） |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |

## 阈值表示例

| field | max_value | min_value |
|-------|-----------|-----------|
| age   | 120       | 0         |
| height| 300       | 0         |
| weight| 500       | 1         |

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/original.csv, shape: (1000, 18)
Successfully read file: /path/to/threshold.csv, shape: (5, 3)
Successfully written file: /path/to/output.csv
Processing completed! Output saved to: /path/to/output.csv
```

质控标识格式示例：`QC5(age,height)` 表示age和height字段超出阈值范围

## 注意事项

1. 阈值表必须包含field、max_value、min_value三列
2. 超出阈值范围或为空的值都会被标记
3. 质控标识格式：质控标识(异常字段1,异常字段2,...)
4. 多个异常字段用逗号分隔
5. 与原有质控标识用分号拼接
