---
name: emoji_marker_remover
description: |
  文本表情标识移除工具。读取文本或文本字段，移除 Unicode 表情符号、装饰标识和杂项图标，并将清理后的内容写入结果文件。
  当用户提到表情符号清理、emoji 移除、装饰图标剔除、网络科研文本净化等需求时使用此 skill。
  即使用户未明确提及“表情标识移除”，只要任务涉及从文本中删除无业务价值的可见表情或装饰图标，就应使用此 skill。
  适用于网络来源、转载整合和科普类科研文本的批量净化场景。
name_zh: 文本表情标识移除算子
tag: 数据清洗
publisher: COMMUNITY
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文本或数据文件路径，支持 txt、md、csv、tsv、json、jsonl
  - name: output_path
    type: string
    required: true
    description: 清理结果文件路径
  - name: text_columns
    type: string
    required: false
    default: ""
    description: CSV 或 TSV 中待处理的文本列，逗号分隔；不填时处理全部列
  - name: text_field
    type: string
    required: false
    default: text
    description: JSON 或 JSONL 中待处理的文本字段名
output_params:
  - name: output_path
    type: file
    description: 移除表情标识后的结果文件
---

# 文本表情标识移除 Skill

## 功能概述

读取文本文件或包含文本字段的数据文件，识别并删除 Unicode 表情符号、装饰性标识和杂项图标。清理时保留普通文字、数字、标点、换行及原有数据结构，并将结果写入指定输出文件。

## 触发条件

- 表情符号清理或 emoji 移除
- 装饰标识、趣味图标或小众图标剔除
- 网络转载文本、科研资讯或科普资料净化
- 清除文本中的非业务可见图标

## 处理逻辑

1. 识别默认以 emoji 展示的 Unicode 字符、旗帜、肤色修饰、键帽和 ZWJ 组合，并删除以 emoji 变体选择符呈现的装饰符号。
2. 对可作为数学、单位或科研符号使用的字符，仅在其明确采用 emoji 展示序列时删除，避免误删普通文本形态的科研符号。
3. 从指定文本内容中删除匹配序列，不改写其余文字、标点和换行。
4. 对 CSV/TSV 文件处理指定列或全部列；对 JSON/JSONL 文件处理指定字段；对 TXT/MD 文件处理全文。
5. 按输入文件格式写出同格式结果文件。

## 使用方法

```bash
python scripts/run_emoji_marker_remover.py \
  --input_path {input_path} \
  --output_path {output_path} \
  --text_columns {text_columns} \
  --text_field {text_field}
```

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `--input_path` | 是 | - | 输入文本或数据文件路径，支持 TXT、MD、CSV、TSV、JSON、JSONL。 |
| `--output_path` | 是 | - | 清理结果文件路径，扩展名应与输入格式一致。 |
| `--text_columns` | 否 | 空 | CSV/TSV 中待处理的文本列，逗号分隔；不填时处理全部列。 |
| `--text_field` | 否 | `text` | JSON/JSONL 中待处理的文本字段名。 |

## 输入文件说明

- TXT/MD：处理整个文件内容。
- CSV/TSV：保留表头和其他字段，只清理选定文本列或全部列。
- JSON：支持顶层对象、对象列表或字符串；对象中的 `text_field` 指定字段会被清理。
- JSONL：逐行读取 JSON 对象，并清理 `text_field` 指定字段。

## 注意事项

1. 本算子只删除表情序列、装饰标识和杂项图标，不进行样本过滤、标点规范化或一般不可见字符清理。
2. 可能用于数学、单位或技术表达的符号在普通文本形态下保留；使用 emoji 变体选择符的展示形态会被删除。
3. 输出目录会在不存在时自动创建。
4. JSON/JSONL 输入中不存在指定文本字段的记录会保持不变。
