---
name: text_entity_dependency_filter
description: |
  文本实体依赖过滤器。识别文本中与其他令牌独立的实体，并对其进行过滤。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到实体依赖过滤、文本实体检测、依存关系过滤、实体独立性过滤等需求时使用此skill。

name_zh: 文本实体依赖过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: lang
    type: string
    required: false
    default: en
    description: 语言代码（en 或 zh）

  - name: min_dependency_num
    type: int
    required: false
    default: 1
    description: 最小依赖边数

  - name: any_or_all
    type: string
    required: false
    default: all
    description: 过滤策略（any 或 all）

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件
tag: 过滤与筛选

---

## 功能概述

该算子使用 spaCy 模型识别文本中的实体及其依赖关系，过滤保留具有依赖关系的实体（不孤立的实体）。支持多种过滤策略：
- `any`: 任意一个实体符合条件即保留
- `all`: 所有实体都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码：'en' 或 'zh' |
| min_dependency_num | int | 否 | 1 | 最小依赖边数 |
| any_or_all | string | 否 | 'all' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "Tom is playing piano."}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
# 英语实体依赖过滤
python scripts/run_text_entity_dependency_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --any_or_all any

# 中文实体依赖过滤
python scripts/run_text_entity_dependency_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --min_dependency_num 1 \
  --any_or_all all
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en，仅支持 en 和 zh）
- `--min_dependency_num`: 最小依赖边数（默认1）
- `--any_or_all`: 过滤策略（默认 all）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 该算子使用 spaCy 模型进行实体依赖分析
2. 需要安装 spacy-pkuseg（pip install spacy-pkuseg）
3. 仅支持英语(en)和中文(zh)