---
name: fullwidth_halfwidth_normalizer
description: |
  全角/半角字符规范化工具。读取结构化数据文件，将文本中的全角ASCII字符（字母、数字、标点）转换为半角形式，
  并可按需执行指定 Unicode 正规化。适用于中日韩混排科研文本的统一预处理，不负责空白行删除、拼写纠错或重复标点合并。
  当用户提到全角转半角、半角规范化、全半角统一、全角字母数字转换等需求时使用此skill。
name_zh: fullwidth_halfwidth_normalizer_全角半角规范化算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔；默认全部字符串列
  - name: norm_form
    type: string
    required: false
    description: Unicode正规化形式：NFC/NFD/NFKC/NFKD；默认不执行
  - name: keep_newlines
    type: string
    required: false
    description: 保留换行符（默认折叠为空格）
output_params:
  - name: output_path
    type: csv_file
    description: 全角转半角后的结构化数据文件
tag: 清洗
---

# fullwidth_halfwidth_normalizer 全角半角规范化Skill

## 功能概述

将文本中的全角 ASCII 字符（U+FF01-U+FF5E、U+3000）转换为半角形式，并支持可选的 Unicode 正规化处理。覆盖字母、数字、标点符号的全半角统一，中文专属标点（。、【】、《》等）不受影响。

## 触发条件

- 全角转半角
- 半角规范化
- 全半角统一
- 全角字母/数字/标点转换
- Unicode 正规化
- 中日韩混排文本清洗

## 输入文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 输入文件路径（需要处理的文件）
2. 输出文件路径（处理后的文件）
3. 可选：指定处理的文本列
4. 可选：Unicode正规化形式

### 步骤2：执行全角半角规范化脚本

在 `scripts/` 目录下找到 `fullwidth_halfwidth_normalizer.py`，使用Python执行：

基本用法：
```bash
python scripts/fullwidth_halfwidth_normalizer.py \
    --input_path <输入文件> \
    --output_path <输出文件>
```

带可选参数：
```bash
python scripts/fullwidth_halfwidth_normalizer.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --text_columns col1,col2 \
    --norm_form NFKC \
    --keep_newlines
```

### 步骤3：返回结果

脚本执行完成后，告知用户全角字符转换数量和输出文件路径。

## 核心参数说明

### 必需参数

| 参数 | 说明 |
|------|------|
| `--input_path` | 输入结构化文件路径 |
| `--output_path` | 输出规范化后文件路径 |

### 可选参数

`--text_columns` 指定规范化列，其他参数控制转换方向和字符范围。

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列，逗号分隔 |
| `--norm_form` | 否 | NFC/NFD/NFKC/NFKD |
| `--keep_newlines` | 否 | 保留换行符 |

## 输出示例

```
[OK] 全角/半角规范化完成 -> output.csv
   文本列: ['text']
   norm_form=无, keep_newlines=False
```

输入 `２０２４年，ＡＩ技术` → 输出 `2024年,AI技术`

## 环境要求

使用项目 Python 环境运行，依赖 pandas 和共享 `data_io` 读写工具。

## 注意事项

1. 仅转换 U+FF01-U+FF5E 范围内的全角 ASCII 字符和 U+3000 全角空格
2. 中文专属标点（。、【】、《》、——等）不受影响
3. NFKC 正规化会一并处理全角字符和其他兼容字符
4. 默认折叠换行为空格，使用 `--keep_newlines` 可保留
