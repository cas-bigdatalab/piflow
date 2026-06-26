---
name: spelling_variant_normalizer
description: |
  拼写变体标准化工具。统一英美拼写差异（colour→color、analyse→analyze 等），内置 153 词条
  （含屈折形式 covered/covering 等），支持自定义词典扩展。当用户提到英美拼写统一、拼写变体、
  British/American spelling 等需求时使用此skill。
name_zh: spelling_variant_normalizer拼写变体标准化算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔
  - name: direction
    type: string
    required: false
    default: british_to_american
    description: 转换方向：british_to_american 或 american_to_british
  - name: custom_dict
    type: string
    required: false
    description: 自定义词典文件（JSON/CSV/TSV）
output_params:
  - name: output_path
    type: csv_file
    description: 拼写规范化后的结构化数据文件
tag: 清洗
---

# spelling_variant_normalizer 拼写变体标准化Skill

## 功能概述

统一英美拼写差异，内置 153 词条覆盖 8 大类：(1) -our→-or；(2) -re→-er；(3) -ise→-ize；(4) -yse→-yze；(5) -ce→-se；(6) -ogue→-og；(7) 双写 L→单 L；(8) -ae/-oe→-e 及杂项。自动保持原文大小写。

## 触发条件

- 英美拼写统一 / 拼写变体标准化
- British to American / American to British
- 多来源英语语料规整
- 拼写一致性处理

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/spelling_variant_normalizer.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--direction american_to_british] \
    [--custom_dict my_dict.json]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--direction` | 否 | british_to_american（默认）或反向 |
| `--custom_dict` | 否 | JSON/CSV/TSV 自定义词典 |

## 输出示例

```
[OK] 拼写变体规范化完成 -> output.csv
   文本列: ['text']
   方向: british_to_american, 词条数: 153
```

`colour centre analysed` → `color center analyzed`

## 注意事项

1. 使用 `\b` 单词边界匹配，不会误伤包含拼写变体的长单词
2. 自动保持全大写（COLOUR→COLOR）和首字母大写
3. 词典通过 JSON/CSV/TSV 扩展，前两列为 英→美 映射
