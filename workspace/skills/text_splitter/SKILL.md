---
name: text_splitter
description: '长文本规则切分工具。将超长文本按照段落、句子、固定字符长度、非空行或科研论文章节标题进行自动切分，生成粒度均匀的短文本片段。

  当用户提到文本切分、长文本拆分、按段落分割、按句子分割、文本分块、论文章节切分等需求时使用此skill。

  适用于科研论文、实验综述、长篇文稿等资料的粒度拆分需求。

  不负责采样、清洗、格式转换或PDF解析。

  '
name_zh: 长文本规则切分算子
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持txt/md/json/jsonl等文本文件）
- name: output
  type: string
  required: true
  description: 输出文件路径
- name: split_mode
  type: string
  required: false
  default: paragraph
  description: 切分模式（paragraph=按段落, sentence=按句子, length=按字符长度, line=按非空行, section=按科研论文章节标题）
- name: max_length
  type: string
  required: false
  default: "1000"
  description: 切分模式为length时的最大字符数
- name: overlap
  type: string
  required: false
  default: "0"
  description: 切分片段之间的重叠字符数（仅length模式有效）
- name: min_length
  type: string
  required: false
  default: "10"
  description: 最小片段长度，低于此长度的片段将被合并或丢弃
- name: separator
  type: string
  required: false
  default: auto
  description: 自定义分隔符（auto=自动检测，或指定如"\n\n"、"。"等）
- name: output_format
  type: string
  required: false
  default: jsonl
  description: 输出格式（jsonl=每行一个JSON对象, txt=纯文本分隔, json=JSON数组）
- name: keep_metadata
  type: string
  required: false
  default: "True"
  description: 是否保留元信息（片段序号、原始位置等）
- name: text_field
  type: string
  required: false
  default: text
  description: JSON/JSONL输入时的文本字段名
- name: language
  type: string
  required: false
  default: auto
  description: 论文章节切分时的论文语言（auto/zh/en/mixed）
- name: custom_sections
  type: string
  required: false
  default: ''
  description: 论文章节切分时的自定义章节标题，逗号分隔
- name: include_default
  type: string
  required: false
  default: "True"
  description: 论文章节切分时是否包含默认章节关键词
- name: keep_title
  type: string
  required: false
  default: "True"
  description: 论文章节切分时是否在章节内容中保留标题
- name: min_section_length
  type: string
  required: false
  default: "50"
  description: 论文章节切分时最小章节长度，低于此长度的章节将被合并
output_params:
- name: output
  type: file
  description: 切分后的文本文件
- name: split_count
  type: integer
  description: 切分后的片段数量
tag: 切分与采样
---

# Text Splitter 长文本规则切分 Skill

## 功能概述

本skill用于将超长文本按照指定规则进行切分，生成粒度均匀的短文本片段。支持段落、句子、固定长度、非空行以及科研论文章节标题切分，适配科研论文、实验综述、长篇文稿等资料的粒度拆分需求。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 长文本切分/拆分
- 按段落分割文本
- 按句子分割文本
- 文本分块/分片
- 论文章节切分/按摘要引言方法结论分割
- 将长文档拆成短片段

## 核心参数说明

### 必需参数
- `--input`：输入文件路径
- `--output`：输出文件路径

### 可选参数
- `--split_mode`：paragraph / sentence / length / line / section
- `--max_length`：length 模式最大字符数
- `--overlap`：length 模式重叠字符数
- `--min_length`：最小片段长度
- `--separator`：自定义分隔符
- `--output_format`：jsonl / txt / json
- `--keep_metadata`：是否保留元信息
- `--text_field`：JSON/JSONL 输入时的文本字段名
- `--language`：section 模式下论文语言
- `--custom_sections`：自定义章节标题
- `--include_default`：是否包含默认章节关键词
- `--keep_title`：section 模式下是否保留标题
- `--min_section_length`：section 模式下最小章节长度

## 输入文件格式

- 纯文本 (.txt, .md)
- JSON (.json) - 读取指定字段或数组中的文本字段
- JSONL (.jsonl) - 逐行处理

## 切分模式说明

### 1. 段落模式 (paragraph)
按空行分割文本，适合结构清晰的文档。

### 2. 句子模式 (sentence)
按句号、问号、感叹号等句末标点分割，适合需要句子级粒度的场景。

### 3. 长度模式 (length)
按固定字符长度切分，可设置重叠区域，适合需要均匀分块的场景。

### 4. 行模式 (line)
按非空行切分，每个非空行作为一个片段。

### 5. 章节模式 (section)
按科研论文章节标题切分，识别摘要、引言、方法、结果、结论、参考文献、附录等标题及其编号变体。

## 使用方法

### 按段落切分
```bash
python scripts/run_text_splitter.py \
  --input long_document.txt \
  --output chunks.jsonl \
  --split_mode paragraph
```

### 按句子切分
```bash
python scripts/run_text_splitter.py \
  --input article.txt \
  --output sentences.jsonl \
  --split_mode sentence
```

### 按固定长度切分（带重叠）
```bash
python scripts/run_text_splitter.py \
  --input paper.txt \
  --output chunks.jsonl \
  --split_mode length \
  --max_length 500 \
  --overlap 50
```

### 按科研论文章节切分
```bash
python scripts/run_text_splitter.py \
  --input paper.txt \
  --output sections.jsonl \
  --split_mode section \
  --language auto
```

## 输出示例

### JSONL 格式输出
```json
{"chunk_id": 0, "text": "摘要\n本文研究了...", "section_name": "摘要", "start_pos": 0, "end_pos": 12, "source": "paper.txt"}
{"chunk_id": 1, "text": "引言\n随着科技发展...", "section_name": "引言", "start_pos": 13, "end_pos": 28, "source": "paper.txt"}
```

### 执行结果
```text
[OK] Text split completed!
   Input file: paper.txt
   Split mode: section
   Language: zh
   Split count: 8
   Output file: sections.jsonl
   Average chunk length: 390 chars
```

## 注意事项

1. 句子模式同时支持中文（。！？）和英文（.!?）句末标点
2. 长度模式切分时会尽量在词边界处断开，避免截断词语
3. 过短的片段（低于min_length）会被合并到相邻片段
4. JSONL 输入默认处理每行的 "text" 字段，可通过 text_field 指定其他字段
5. 章节模式识别基于行首匹配，支持带序号格式（如 "1. 引言"、"第一章 引言"）
6. PDF 文件需要先转换为文本再处理
