---
name: data_split_by_field
description: '按字段拆分数据工具。根据指定字段的值将结构化表格拆分为多个文件，每个唯一值对应一个输出文件。

  当用户提到数据拆分、按字段分组导出、分类导出、数据分片、按某列值分割文件等需求时使用此skill。

  即使用户没有明确说出"拆分"，只要任务涉及将结构化表格按某字段值分成多个文件，就应该使用此skill。

  不负责字段聚合统计、行级过滤或跨表关联合并。

  '
name_zh: 按字段拆分数据算子
input_params:
- name: input
  type: string
  required: true
  description: 输入CSV、TSV、Excel或SPSS文件路径
- name: output_dir
  type: string
  required: true
  description: 输出目录路径
- name: split_field
  type: string
  required: true
  description: 用于拆分的字段名
- name: output_prefix
  type: string
  required: false
  default: split
  description: 输出文件名前缀
- name: output_format
  type: string
  required: false
  default: csv
  description: 输出文件格式（csv/tsv/xlsx/parquet）
- name: use_dask
  type: string
  required: false
  default: "False"
  description: 是否使用Dask处理大数据
- name: blocksize
  type: string
  required: false
  default: 64MB
  description: Dask分块大小
output_params:
- name: output_dir
  type: directory
  description: 包含拆分后文件的目录
tag: 切分与采样
---

# Data Split By Field 按字段拆分数据 Skill

## 功能概述

本skill用于根据指定字段的值将结构化表格拆分为多个文件。每个唯一的字段值会生成一个独立的输出文件，
文件名包含字段值以便识别。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 按字段拆分数据
- 分组导出
- 分类导出
- 数据分片
- 按某列值分割文件

## 核心参数说明

### 必需参数
- `--input`：输入文件路径
- `--output_dir`：输出目录路径
- `--split_field`：用于拆分的字段名

### 可选参数
- `--output_prefix`：输出文件名前缀，默认 `split`
- `--output_format`：输出文件格式，默认 `csv`
- `--use_dask`：是否使用Dask处理大数据，默认 `False`
- `--blocksize`：Dask分块大小，默认 `64MB`

## 输入文件格式

输入文件可以是 CSV、TSV、Excel 或 SPSS 文件，且必须包含 `split_field` 对应的列。

## 使用方法
```bash
python scripts/run_data_split_by_field.py --input data.csv --output_dir ./output --split_field category
```

## 输出示例
```text
[OK] Data split completed!
   Engine: pandas
   Input file: data.csv
   Split field: category
   Total rows: 1000
   Unique values: 5
   Output files:
     - ./output/split_cat1.csv (200 rows)
     - ./output/split_cat2.csv (300 rows)
```

## 环境要求
- Python 3.10+
- pandas
- openpyxl、xlrd、pyreadstat 等按输入格式需要安装
- 可选：dask

## 注意事项
1. 拆分字段必须存在于数据中
2. 输出文件名格式为：`{prefix}_{field_value}.{format}`
3. 字段值中的特殊字符会被替换为下划线
4. 输出目录不存在时会自动创建
