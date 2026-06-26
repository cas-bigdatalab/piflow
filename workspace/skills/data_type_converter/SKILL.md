---
name: data_type_converter
description: |
  数据类型转换工具。转换数据字段的类型，支持数值、字符串、日期等类型互转。
  当用户提到类型转换、数据格式转换、字段类型修改等需求时使用此skill。
  即使用户没有明确说出"类型转换"，只要任务涉及改变字段的数据类型，就应该使用此skill。

name_zh: 数据类型转换算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel/JSON等）

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: conversions
    type: string
    required: true
    description: 转换规则，格式：字段名:目标类型，多个用逗号分隔

  - name: date_format
    type: string
    required: false
    default: "%Y-%m-%d"
    description: 日期格式（用于日期类型转换）

  - name: errors
    type: string
    required: false
    default: "coerce"
    description: 错误处理方式（raise/coerce/ignore）

output_params:
  - name: output
    type: csv_file
    description: 转换后的数据文件
tag: 格式转换

---

# Data Type Converter 数据类型转换 Skill

## 功能概述

本skill用于转换数据字段的类型，支持：
- **数值转换**：int, float
- **字符串转换**：str
- **日期转换**：datetime
- **布尔转换**：bool
- **分类转换**：category

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数据类型转换
- 字段格式转换
- 日期格式化
- 数值格式化

## 支持的目标类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `int` | 整数 | "123" → 123 |
| `float` | 浮点数 | "123.45" → 123.45 |
| `str` | 字符串 | 123 → "123" |
| `datetime` | 日期时间 | "2024-01-01" → datetime |
| `bool` | 布尔值 | "true" → True |
| `category` | 分类类型 | 优化内存 |

## 使用方法

### 基本类型转换
```bash
python scripts/run_data_type_converter.py \
  --input data.csv \
  --output converted.csv \
  --conversions "age:int,score:float,name:str"
```

### 日期类型转换
```bash
python scripts/run_data_type_converter.py \
  --input data.csv \
  --output converted.csv \
  --conversions "date:datetime" \
  --date_format "%Y-%m-%d"
```

### 多字段转换
```bash
python scripts/run_data_type_converter.py \
  --input data.csv \
  --output converted.csv \
  --conversions "id:int,amount:float,date:datetime,category:category"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--conversions` | 是 | 转换规则 |
| `--date_format` | 否 | 日期格式，默认"%Y-%m-%d" |
| `--errors` | 否 | 错误处理，默认"coerce" |

## 错误处理方式

| 方式 | 说明 |
|------|------|
| `raise` | 遇到错误时抛出异常 |
| `coerce` | 转换失败设为NaN |
| `ignore` | 保留原值 |

## 输出示例

```
[OK] Data type conversion completed!
   Input file: data.csv
   Output file: converted.csv
   Conversions:
     - age: object → int64
     - score: object → float64
     - date: object → datetime64[ns]
   Total rows: 1000
   Conversion errors: 5
```

## 环境要求

```bash
pip install pandas numpy openpyxl
```
