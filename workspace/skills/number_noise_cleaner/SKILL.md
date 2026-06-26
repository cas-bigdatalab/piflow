---
name: number_noise_cleaner
description: '无用数字字符清理工具。读取结构化文本数据，对指定或全部文本字段移除无语义的独立数字字符，输出清理后的结构化文件。

  当用户提到无用数字字符清理、数字噪声删除、文本中的杂散数字清理等需求时使用此skill。

  即使用户没有明确说出"number_noise_cleaner"，只要任务涉及从文本中删除无业务意义的数字字符，就应该使用此skill。

  不负责数值规整、字段校验或通用正则替换。

  '
name_zh: 无用数字字符清理算子
tag: 清洗
input_params:
- name: input_path
  type: string
  required: true
  description: 输入文件路径（支持CSV/TSV/Excel等data_io支持的格式）
- name: output_path
  type: string
  required: true
  description: 输出文件路径（清理后的文件）
- name: text_columns
  type: string
  required: false
  description: 需清洗的文本列，逗号分隔；不填则默认所有字符串列
- name: preserve_years
  type: string
  required: false
  default: "True"
  description: 是否保留年份
- name: year_min
  type: string
  required: false
  default: "1900"
  description: 年份保留下限
- name: year_max
  type: string
  required: false
  default: "2099"
  description: 年份保留上限
- name: preserve_identifiers
  type: string
  required: false
  default: "True"
  description: 是否保留编号/版本号等标识
- name: identifier_markers
  type: string
  required: false
  default: ID,No.,No,编号,样本,批次,版本,实验,试验
  description: 编号上下文标记，逗号分隔
- name: preserve_measurements
  type: string
  required: false
  default: "True"
  description: 是否保留实验数值/单位数值
- name: measurement_units
  type: string
  required: false
  default: '%,mg,g,kg,ug,μg,mL,ml,L,℃,°C,mol,mm,cm,m,h,s,min'
  description: 实验数值单位，逗号分隔
output_params:
- name: output_path
  type: csv_file
  description: 无用数字字符清理后的结构化数据文件
---

# number_noise_cleaner 无用数字字符清理

## 功能概述

本skill用于对文本进行无用数字字符清理，读取结构化数据文件并移除无语义的独立数字 token。
- 保留 1900-2099 范围内的年份
- 保留编号、版本号、样本号等业务标识中的数字
- 保留实验数值、小数、分数、百分比和带单位数值

## 触发条件

当用户请求以下任务时，应使用此skill：
- 无用数字字符清理
- 数字噪声删除
- 文本中的杂散数字清理
- 删除无业务意义的数字

## 核心参数说明

### 必需参数
- `--input_path`：输入文件路径
- `--output_path`：输出文件路径

### 可选参数
- `--text_columns`：需清洗的文本列，逗号分隔；不填则默认处理所有字符串列
- `--preserve_years`：是否保留年份，默认 `true`
- `--year_min`：年份保留下限，默认 `1900`
- `--year_max`：年份保留上限，默认 `2099`
- `--preserve_identifiers`：是否保留编号/版本号等标识，默认 `true`
- `--identifier_markers`：编号上下文标记，逗号分隔
- `--preserve_measurements`：是否保留实验数值/单位数值，默认 `true`
- `--measurement_units`：实验数值单位，逗号分隔

## 输入文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/number_noise_cleaner.py \
  --input_path <输入文件> \
  --output_path <输出文件> \
  --text_columns text \
  --preserve_years true \
  --year_min 1900 \
  --year_max 2099 \
  --preserve_identifiers true \
  --preserve_measurements true
```

## 输出示例

```text
[OK] 无用数字字符清理完成 -> output.csv
   处理列: ['text']
   行数: 10
```

## 注意事项

1. 仅移除文本中的无语义数字 token，不修改数值型列。
2. 默认保留年份、标识符和实验数值，避免误伤科研文本中的有效信息。
3. 该skill不负责数值规整、字段校验或通用正则替换。
4. 使用项目内 `data_io` 读写结构化数据。
