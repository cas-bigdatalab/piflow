---
name: tab_space_normalizer
description: 'Tab/空格规范化工具。读取结构化数据文件，执行制表符展开、行尾空格清理与可选公共缩进去除，输出空白已统一的结构化数据文件。

  当用户提到Tab转空格、制表符转空格、缩进规范化、行尾空格清除、公共缩进去除等需求时使用此skill。

  即使用户没有明确说出"tab_space_normalizer"，只要任务涉及文本中的Tab/空格归一，就应该使用此skill。

  不负责文本内容改写、拼写纠错、重复标点合并或其他非空白字符清理。

  '
name_zh: tab_space_normalizer_空白规范化算子
tag: 清洗
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
- name: tab_width
  type: string
  required: false
  default: "4"
  description: Tab替换为空格的数量
- name: strip_trailing
  type: string
  required: false
  default: "True"
  description: 去除行尾多余空格（默认开启）
- name: dedent
  type: string
  required: false
  default: "False"
  description: 去除公共前导空格
output_params:
- name: output_path
  type: csv_file
  description: 规范化后的结构化数据文件
---

# tab_space_normalizer Tab空格规范化Skill

## 功能概述

三步处理：(1) Tab → 空格转换（可配置宽度）；(2) 去除行尾多余空格；(3) 可选 de-indent（去除所有行的公共前导空格）。适用于代码、日志、表格文本的空白规范化。

## 触发条件

- Tab 转空格 / 制表符转空格
- 缩进规范化 / 行尾空格清除
- 公共缩进去除 / de-indent
- 空白字符统一

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 CSV/TSV/Excel 等结构化文件路径 |
| `--output_path` | 输出清洗后文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 需要处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |
| `--tab_width` | Tab 展开为空格的数量 | 4 |
| `--strip_trailing` | 是否去除行尾空格 | true |
| `--dedent` | 去除公共前导缩进 | false |

## 输入文件格式

输入为结构化表格，文本列中可包含 Tab、行尾空格和公共缩进：

```csv
id,text
1,"tab\tinside"
2,"trail  "
3,"    indented"
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/tab_space_normalizer.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--tab_width 2] \
    [--strip_trailing true] \
    [--dedent]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--tab_width` | 否 | Tab 展开宽度 |
| `--strip_trailing` | 否 | 是否去除行尾空格 |
| `--dedent` | 否 | 去除公共前导缩进 |

## 输出示例

```
[OK] Tab/空格规范化完成 -> output.csv
   列: ['text'], tab_width=4, strip_trailing=True, dedent=False
```

输入 `tab\tinside` → 输出 `tab    inside`

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. 使用 Python 标准 `str.expandtabs(tab_width)` 进行 Tab 展开
2. de-indent 使用 `textwrap.dedent`，只去除所有行共同的前导空格
3. 处理顺序：Tab 展开 → 行尾空格 → de-indent
