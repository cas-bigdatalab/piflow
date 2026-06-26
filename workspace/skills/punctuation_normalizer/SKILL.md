---
name: punctuation_normalizer
description: |
  文本标点规范化工具。只处理标点本身：合并重复标点、统一中英文标点与引号样式、规范省略号和标点周围空格。
  当用户提到标点规范化、标点清理、合并重复标点、全半角转换等需求时使用此skill。
  适用于科研文本中标点混乱、重复符号过多的场景，不负责 HTML、表情、数字或拼写清理。
name_zh: 文本标点规范化算子
tag: 清洗
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径，支持 txt/json/jsonl/csv

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: merge_repeated
    type: string
    required: false
    default: "True"
    description: 是否合并重复标点

  - name: max_repeat
    type: string
    required: false
    default: "1"
    description: 允许的最大重复次数

  - name: normalize_width
    type: string
    required: false
    default: auto
    description: 全半角规范化模式（auto、full、half、none）

  - name: normalize_quotes
    type: string
    required: false
    default: "True"
    description: 是否规范化引号

  - name: quote_style
    type: string
    required: false
    default: chinese
    description: 引号风格（chinese 或 english）

  - name: normalize_ellipsis
    type: string
    required: false
    default: "True"
    description: 是否规范化省略号

  - name: remove_space_around_punct
    type: string
    required: false
    default: "True"
    description: 是否移除标点周围的多余空格

  - name: text_field
    type: string
    required: false
    default: text
    description: JSON/JSONL 输入时的文本字段名

output_params:
  - name: output
    type: file
    description: 规范化后的文件

  - name: total_count
    type: integer
    description: 处理的样本总数

  - name: modified_count
    type: integer
    description: 被修改的样本数

tag: 清洗
---

# Punctuation Normalizer 文本标点规范化 Skill

## 功能概述

文本标点规范化工具，读取结构化或半结构化文本文件，合并重复标点、统一标点与引号样式、清理标点周围空格并保留省略号。
适用于科研文本中标点混乱、连续符号过多、引号样式不统一的标点规整场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 标点规范化
- 标点清理
- 合并重复标点
- 统一中英文标点
- 引号或省略号规整

## 核心参数说明

### 必需参数
- `--input`：输入文件路径。
- `--output`：输出文件路径。

### 可选参数
- `--merge_repeated`：是否合并重复标点，默认 `true`。
- `--max_repeat`：允许的最大重复次数，默认 `1`。
- `--normalize_width`：全半角规范化模式，默认 `auto`。
- `--normalize_quotes`：是否规范化引号，默认 `true`。
- `--quote_style`：引号风格，默认 `chinese`。
- `--normalize_ellipsis`：是否规范化省略号，默认 `true`。
- `--remove_space_around_punct`：是否移除标点周围的多余空格，默认 `true`。
- `--text_field`：JSON/JSONL 输入时的文本字段名，默认 `text`。

## 输入文件格式

- `csv`：处理文本列并保持表头与其他列不变。
- `json` / `jsonl`：处理指定文本字段。
- `txt` / `md`：按单文本内容处理。

## 使用方法

```bash
python scripts/run_punctuation_normalizer.py --input input.csv --output output.csv
```

```bash
python scripts/run_punctuation_normalizer.py --input input.jsonl --output output.jsonl --quote_style english
```

## 处理示例

- `Wait!!! Really???` → `Wait! Really?`
- `中文！！！真的吗？？？？好的。。` → `中文!真的吗?好的……`
- `“Smart quotes” and ‘single quotes’` → `“Smart quotes” and ‘single quotes’`
- `Ellipsis......` → `Ellipsis……`
- `Extra   spaces before   text` → `Extra spaces before text`

## 输出示例

```text
[OK] Punctuation normalization completed!
   Total samples: 10
   Modified samples: 6 (60.0%)
   Unchanged samples: 4 (40.0%)
   Modifications:
     - Merged repeated punctuation: 3
     - Normalized width: 2
     - Normalized quotes: 0
     - Normalized ellipsis: 2
     - Removed extra spaces: 1
```

## 环境要求

- Python 3.10+
- 仅依赖标准库

## 注意事项

1. `auto` 模式按中英文字符比例选择半角归一策略。
2. 省略号统一保留为 `……`。
3. 不处理 HTML、表情、数字或拼写问题。
4. 输出会保留原始行列结构和未修改字段。
