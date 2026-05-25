---
name: Pi_DataSorting
description: |
  数据排序工具。读取结构化数据文件，根据指定字段进行升序或降序排序，最后输出为相同格式的文件。
  当用户提到数据排序、升序排列、降序排列、按某字段排序等需求时使用此skill。
  即使用户没有明确说出"排序"，只要任务涉及对数据进行排序，就应该使用此skill。

name_zh: Pi_数据排序算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）

  - name: output_path
    type: string
    required: true
    description: 输出文件路径（排序后的文件）

  - name: id_field_name
    type: string
    required: true
    description: 排序字段名，支持多字段用逗号分隔

  - name: sort_order
    type: string
    required: false
    default: asc
    description: 排序方式（asc升序/desc降序）

output_params:
  - name: output_path
    type: csv_file
    description: 排序后的结构化数据文件
tag: 增强

---

# Pi_DataSorting 数据排序Skill

## 功能概述

本skill用于读取结构化数据文件，根据用户指定的字段进行升序或降序排序，然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 数据排序
- 升序排列
- 降序排列
- 按某字段排序
- 排序数据
- 重新排列数据顺序

## 处理逻辑

1. 读取输入的结构化数据文件
2. 解析排序字段（支持多字段，用逗号分隔）
3. 根据指定的排序方式（asc/desc）进行排序
4. 输出排序后的数据文件

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及排序参数

向用户确认：
1. 输入文件路径（需要排序的文件）
2. 输出文件路径（排序后的文件）
3. 排序字段名（必填，支持多字段用逗号分隔，如：ID0000,NAME）
4. 排序方式（可选，默认asc升序，可选desc降序）

### 步骤2：执行数据排序脚本

在 `scripts/` 目录下找到 `Pi_DataSorting.py`，使用Python执行：

```bash
python scripts/Pi_DataSorting.py --input_path <输入文件> --output_path <输出文件> --id_field_name <排序字段> [--sort_order asc|desc]
```

### 步骤3：返回结果

告知用户排序结果。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--id_field_name` | 是 | 排序字段名，支持多字段用逗号分隔 |
| `--sort_order` | 否 | 排序方式，asc升序（默认）或desc降序 |

## 输出示例

### 升序排序
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
Data sorting completed! Output to: /path/to/output.csv
```

### 降序排序
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
Data sorting completed! Output to: /path/to/output.csv
```

### 多字段排序
```
python Pi_DataSorting.py --input_path input.csv --output_path output.csv --id_field_name "ID0000,NAME" --sort_order asc
```

## 注意事项

1. 排序字段必须存在于数据中
2. 支持多字段排序，用逗号分隔
3. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_sorted` 后缀
