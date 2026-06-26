---
name: abbrev_expander
description: |
  领域缩略语展开 Skill：按内置或外部词典将独立缩略语替换为全称，可选在全称后保留原缩写。
  适用于技术文本、论文摘要和业务记录中的缩写清洗；不负责模糊缩写消歧或大小写无关替换。
name_zh: 缩略语展开
tag: 清洗
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入结构化文件路径
  - name: output_path
    type: string
    required: true
    description: 输出结构化文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔；默认全部字符串列
  - name: dict_path
    type: string
    required: false
    description: 外部缩略语词典路径，支持 json/csv/tsv
  - name: keep_abbr
    type: string
    required: false
    description: 是否在全称后保留原缩写
output_params:
  - name: output_path
    type: string
    description: 缩略语展开后的结构化文件
---

# abbrev_expander 缩略语展开 Skill

## 功能概述

本 skill 按词典将文本列中的独立缩略语替换为全称。默认内置 `AI`、`NLP`、`CPU`、`GPU`、`ML` 等通用技术缩略语；也支持通过 JSON/CSV/TSV 外部词典提供 `abbrev -> full` 映射。匹配按缩略语长度优先，并使用词边界避免替换单词内部子串。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 展开领域缩略语
- 用词典替换缩写为全称
- 在展开全称后保留原缩写
- 避免 `AIM`、`AIGC` 这类完整词被 `AI` 误替换

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 CSV/TSV/Excel 等结构化文件路径 |
| `--output_path` | 输出结构化文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |
| `--dict_path` | 外部词典路径，支持 JSON 对象或含 `abbrev,full` 列的 CSV/TSV | 内置词典 |
| `--keep_abbr` | 在全称后保留原缩写，如 `artificial intelligence (AI)` | `False` |

## 输入文件格式

```csv
id,text
1,"AI and NLP models used GPU acceleration."
2,"AIGC should remain a single token."
```

外部 CSV/TSV 词典格式：

```csv
abbrev,full
LLM,large language model
RAG,retrieval augmented generation
```

## 使用方法

### 使用内置词典展开
```bash
python scripts/abbrev_expander.py \
  --input_path input.csv \
  --output_path output.csv \
  --text_columns text
```

### 使用外部词典并保留原缩写
```bash
python scripts/abbrev_expander.py \
  --input_path input.csv \
  --output_path output.csv \
  --text_columns text \
  --dict_path custom_dict.csv \
  --keep_abbr
```

## 处理示例

| 输入文本 | 输出文本 |
|----------|----------|
| `AI and NLP models used GPU acceleration.` | `artificial intelligence and natural language processing models used graphics processing unit acceleration.` |
| `AI and NLP models used GPU acceleration.` with `--keep_abbr` | `artificial intelligence (AI) and natural language processing (NLP) models used graphics processing unit (GPU) acceleration.` |
| `AIGC should remain a single token.` | `AIGC should remain a single token.` |

## 输出示例

```csv
id,text
1,"artificial intelligence and natural language processing models used graphics processing unit acceleration."
2,"AIGC should remain a single token."
```

## 环境要求

依赖 Python、pandas，以及本仓库 DC 公用 `data_io` 读写工具。

## 注意事项

1. 默认匹配大小写敏感，`ai` 不会被内置 `AI` 规则替换。
2. 该 skill 不做上下文消歧；同一缩写多义时需通过外部词典先确定目标含义。
3. 仅匹配词边界，避免替换单词内部子串。
