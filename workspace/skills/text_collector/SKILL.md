---
name: text_collector
description: |
  纯文本文件采集工具。读取单个文本文件或目录中的 txt、md、rst、log、text 文件，执行文件正文采集，输出结构化文本记录文件。
  当用户提到文本文件采集、读取纯文本语料、汇总 Markdown/RST/日志文本、把本地文本文件转成结构化记录等需求时使用此 skill。
  即使用户没有明确说出"文本采集"，只要任务涉及把本地纯文本文件内容收集成统一记录，就应该使用此 skill。
  不负责文档解析、图片解析、表格读取、文本清洗或质量过滤。
name_zh: 文本类数据采集接入算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件或目录路径

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: encoding
    type: string
    required: false
    default: auto
    description: 文件编码，默认auto自动检测

  - name: recursive
    type: string
    required: false
    default: "False"
    description: 是否递归处理子目录

  - name: add_metadata
    type: string
    required: false
    default: "True"
    description: 是否添加文件元信息

  - name: output_format
    type: string
    required: false
    default: jsonl
    description: 输出格式，支持jsonl/json/csv/auto
output_params:
  - name: output
    type: jsonl_file
    description: 采集后的结构化文本记录文件
tag: 采集
---

# Text Collector 文本采集 Skill

## 功能概述

本skill用于读取单个纯文本文件或目录中的纯文本文件，将文件正文采集为统一结构化文本记录，并输出为 JSONL、JSON 或 CSV。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 文本文件采集
- 读取纯文本语料
- 汇总 txt、md、rst、log 或 text 文件内容
- 将本地文本文件转为结构化记录
- 为后续清洗、校验、入库准备统一文本输入

不适用于 PDF、Word、图片、Excel、网页结构解析、文本清洗或质量过滤；这些任务需要使用对应的文档、图片、表格、清洗或过滤 skill。

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入文件或目录路径 |
| `--output` | 输出文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--encoding` | 文件编码，`auto` 会按常见编码尝试读取 | `auto` |
| `--recursive` | 是否递归扫描子目录 | `False` |
| `--add_metadata` | 是否输出 `_meta` 文件元信息 | `True` |
| `--output_format` | 输出格式，支持 `jsonl`、`json`、`csv`、`auto` | `jsonl` |

## 输入文件格式

输入可以是单个受支持文本文件，也可以是包含受支持文本文件的目录。目录模式只采集 `.txt`、`.md`、`.rst`、`.log`、`.text`，其它扩展名会跳过。

```text
input_dir/
  note.txt
  report.md
  method.rst
  readme.text
  logs/collector.log
  nested/field_notes.txt
  skip.exe
```

## 使用方法

### 递归采集目录并输出 JSONL
```bash
python scripts/run_text_collector.py \
  --input ./input_dir \
  --output ./text_collector_output.jsonl \
  --encoding auto \
  --recursive true \
  --add_metadata true \
  --output_format jsonl
```

### 采集单个文本文件并输出 JSON
```bash
python scripts/run_text_collector.py \
  --input ./note.txt \
  --output ./text_collector_output.json \
  --output_format json
```

## 处理示例

| 输入文件 | 参数效果 | 预期结果 |
|----------|----------|----------|
| `note.txt` | 支持的 `.txt` 文件 | 采集为一条记录 |
| `nested/field_notes.txt` | `--recursive true` | 采集为一条记录 |
| `skip.exe` | 非支持扩展名 | 不进入采集列表 |
| `readme.text` | 支持的 `.text` 文件 | 采集为一条记录 |

## 输出示例

```json
{"text": "QYZ station daily note...", "_meta": {"source_file": "note.txt", "filename": "note.txt", "file_size": 734, "collected_at": "2026-06-11 16:39:55", "encoding": "utf-8"}}
```

## 环境要求

使用仓库内 Python 环境运行；Windows bash 下建议加 `PYTHONIOENCODING=utf-8` 避免中文控制台编码问题。脚本仅使用 Python 标准库。

## 注意事项

1. `--recursive false` 时只扫描输入目录第一层文件。
2. `--add_metadata false` 时输出记录只包含 `text` 字段。
3. 输出文件扩展名不会自动决定格式，除非 `--output_format auto`。
