---
name: QC14_TimePeakValue
description: |
  尖峰检验（连续剧烈变化检测）工具。读取时间序列数据，识别在连续N次的相邻读数之间的差值（变化量）的绝对值都高于预设阈值的异常数据，最后输出为相同格式的文件。
  当用户提到尖峰检验、连续剧烈变化检测、峰值检测、时间序列突变检查等需求时使用此skill。
  即使用户没有说出"尖峰检验"，只要任务涉及检查时间序列数据的剧烈变化，就应该使用此skill。

name_zh: QC14_尖峰检验（连续剧烈变化检测）算子
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
    description: 检验条件，格式：字段名,峰值阈值,连续次数，多行用换行分隔

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
    default: "尖值异常"
    description: 质控标识

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名

output_params:
  - name: output
    type: csv_file
    description: 尖峰检验后的结构化数据文件，带质控标识
tag: 校验

---

# QC14_TimePeakValue 尖峰检验Skill

## 功能概述

本skill用于检查时间序列数据中，连续N次的相邻读数之间的差值（变化量）的绝对值是否都高于预设的阈值。如果连续多次变化都超过阈值，则标记为异常数据。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 尖峰检验
- 连续剧烈变化检测
- 峰值检测
- 时间序列突变检查
- 检查数据变化是否剧烈
- 连续变化异常检测

## 处理逻辑

1. 读取输入的被检验数据
2. 解析尖峰检验条件（字段名、峰值阈值、连续次数）
3. 按时间字段排序
4. 对每个指定字段，计算连续N-1次相邻读数的差值绝对值
5. 如果连续N-1次差值的绝对值都高于阈值，标记为异常
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
3. 尖峰检验条件（格式：字段名,峰值阈值,连续次数）
4. 时间字段名
5. 时间格式
6. 质控标识（默认：尖值异常）
7. 质控标识字段名（默认：QC0000）

### 步骤2：执行尖峰检验脚本

在 `scripts/` 目录下找到 `QC14_TimePeakValue.py`，使用Python执行：

```bash
python scripts/QC14_TimePeakValue.py \
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
| `--conditions` | 是 | 检验条件，格式：字段名,峰值阈值,连续次数（如：Do_ppm,1,3）多行用换行分隔 |
| `--time_field` | 是 | 时间字段名（用于排序判断连续性） |
| `--time_format` | 是 | 时间格式（如：%Y-%m-%d %H:%M:%S） |
| `--qc_mark` | 否 | 质控标识，默认"尖值异常" |
| `--mark_field_name` | 否 | 质控标识字段名，默认QC0000 |

## 检验条件格式

每行格式：`字段名,峰值阈值,连续次数`

示例：
```
Do_ppm,1,3
Temp_C,2,4
pH,4,5
```

表示：
- Do_ppm字段连续3次变化量绝对值>=1则标记异常
- Temp_C字段连续4次变化量绝对值>=2则标记异常
- pH字段连续5次变化量绝对值>=4则标记异常

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
Starting peak value check...
Writing output data: /path/to/output.csv
Peak value check completed!
```

质控标识格式示例：`尖值异常(Do_ppm)` 表示Do_ppm字段存在连续剧烈变化

## 注意事项

1. 检验条件格式：字段名,峰值阈值,连续次数，每行一个字段
2. 峰值阈值：连续变化量的绝对值需要达到的最小值
3. 连续次数：需要连续多少次变化都超过阈值才标记为异常
4. 数据按时间字段排序后进行检查
5. 质控标识格式：质控标识(异常字段1,异常字段2,...)
6. 与原有质控标识用分号拼接
