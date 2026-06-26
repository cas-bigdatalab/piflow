---
name: content_parser
description: |
  内容解析预处理工具。读取采集后的 JSONL、JSON 或 TXT 文本记录，执行轻量内容解析，输出带标题、段落结构和内容类型的统一解析记录文件。
  当用户提到接入内容解析、采集后预处理、提取标题和段落、识别 plain/markdown/html 内容结构等需求时使用此 skill。
  即使用户没有明确说出"内容解析"，只要任务涉及把已采集文本内容解析成统一结构，就应该使用此 skill。
  不负责文件采集、表格抽取、内容清洗、质量校验、过滤筛选或格式转换。
name_zh: 接入内容解析预处理算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径，支持 jsonl/json/txt

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: parse_mode
    type: string
    required: false
    default: auto
    description: 解析模式，支持 auto/plain/markdown/html

  - name: extract_title
    type: string
    required: false
    default: "True"
    description: 是否提取标题

  - name: extract_paragraphs
    type: string
    required: false
    default: "True"
    description: 是否提取段落列表

  - name: output_format
    type: string
    required: false
    default: jsonl
    description: 输出格式，支持 jsonl/json/auto
output_params:
  - name: output
    type: jsonl_file
    description: 解析后的结构化内容记录文件
tag: 采集
---

# Content Parser 内容解析预处理 Skill

## 功能概述

本 skill 用于读取采集后的文本记录，对 `text` 字段做轻量内容解析，识别 plain、markdown、html 内容类型，并输出标题、段落结构、字符数、词数等解析结果。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 接入内容解析
- 采集后预处理
- 提取文本标题和段落结构
- 识别 plain、markdown、html 内容类型
- 将已采集文本内容转为统一解析记录

不适用于文件采集、表格抽取、内容清洗、质量校验、过滤筛选或格式转换；这些任务需要使用对应的采集、清洗、校验、过滤或转换 skill。

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入文件路径，支持 jsonl/json/txt |
| `--output` | 输出文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--parse_mode` | 解析模式，支持 `auto`、`plain`、`markdown`、`html` | `auto` |
| `--extract_title` | 是否提取标题 | `True` |
| `--extract_paragraphs` | 是否提取段落列表 | `True` |
| `--output_format` | 输出格式，支持 `jsonl`、`json`、`auto` | `jsonl` |

## 输入文件格式

输入可以是 JSONL、JSON 或 TXT 文件。JSONL/JSON 中每条记录应包含 `text` 字段；TXT 文件会整体作为一条文本记录处理。

```json
{"text": "# Research Note\n\nFirst paragraph..."}
{"text": "<html><title>Report</title><p>HTML paragraph.</p></html>"}
```

## 使用方法

### 自动识别内容类型并输出 JSONL
```bash
python scripts/run_content_parser.py \
  --input ./content_records.jsonl \
  --output ./content_parser_output.jsonl \
  --parse_mode auto \
  --extract_title true \
  --extract_paragraphs true \
  --output_format jsonl
```

### 按纯文本模式解析 TXT 文件
```bash
python scripts/run_content_parser.py \
  --input ./note.txt \
  --output ./content_parser_output.json \
  --parse_mode plain \
  --output_format json
```

## 处理示例

| 输入内容 | 参数效果 | 预期结果 |
|----------|----------|----------|
| Markdown 标题和段落 | `--parse_mode auto` | `content_type=markdown`，提取标题和段落 |
| HTML title 和 p 标签 | `--parse_mode auto` | `content_type=html`，提取标题和段落 |
| 普通文本 | `--parse_mode auto` | `content_type=plain`，首个非空行作为标题 |
| 空 `text` 字段 | 任意模式 | 输出 `_parsed.error`，不崩溃 |

## 输出示例

```json
{"_parsed": {"raw_text": "# Research Note...", "content_type": "markdown", "title": "Research Note", "paragraphs": ["Research Note", "First paragraph..."], "paragraph_count": 2, "char_count": 42, "word_count": 5, "parsed_at": "2026-06-12 14:00:00"}, "text": "# Research Note..."}
```

## 环境要求

使用仓库内 Python 环境运行；Windows bash 下建议加 `PYTHONIOENCODING=utf-8` 避免中文控制台编码问题。HTML 解析优先使用 `beautifulsoup4`，缺少依赖时脚本会退回正则清理。

## 注意事项

1. `parse_mode=auto` 会根据内容特征识别 `plain`、`markdown` 或 `html`。
2. 输入 JSONL/JSON 记录中缺少 `text` 或 `text` 为空时，输出 `_parsed.error`。
3. 本 skill 只做轻量解析，不做清洗、过滤或质量判定。
