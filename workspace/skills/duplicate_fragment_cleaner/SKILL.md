---
name: duplicate_fragment_cleaner
description: '文本内部重复片段模糊清理工具。读取 JSONL 文本数据，按文本字段删除近似重复的段落、句子或连续片段，保留首次出现内容并输出清理后的样本。

  当用户提到清理重复片段、删除重复段落、去掉近似重复内容等需求时使用此 skill。

  即使用户没有明确说出 "duplicate_fragment_cleaner"，只要任务涉及同一文本内部的重复片段清理，就应该使用此 skill。

  不负责跨记录去重、摘要改写或语义重写。

  '
name_zh: 重复文本片段模糊清理算子
tag: 清洗
input_params:
- name: input
  type: string
  required: true
  description: 输入 JSONL 文件路径
- name: output
  type: string
  required: true
  description: 输出 JSONL 文件路径
- name: text_field
  type: string
  required: false
  default: text
  description: 文本字段名
- name: min_fragment_length
  type: string
  required: false
  default: "30"
  description: 候选重复片段的最小字符长度
- name: max_fragment_length
  type: string
  required: false
  default: "500"
  description: 候选重复片段的最大字符长度
- name: similarity_threshold
  type: string
  required: false
  default: "0.88"
  description: 判定为近似重复的相似度阈值
- name: keep_first
  type: string
  required: false
  default: "True"
  description: 保留第一次出现的重复片段
- name: mark_cleaned
  type: string
  required: false
  default: "True"
  description: 是否标记已清洗样本
- name: log_file
  type: string
  required: false
  description: 删除片段日志文件路径
output_params:
- name: output
  type: jsonl_file
  description: 清理后的 JSONL 文件
- name: total_samples
  type: integer
  description: 总样本数
- name: cleaned_samples
  type: integer
  description: 清洗样本数
- name: fragments_removed
  type: integer
  description: 删除片段总数
- name: unique_fragments
  type: integer
  description: 唯一片段数
---

# Duplicate Fragment Cleaner 文本内部重复片段模糊清理 Skill

## 功能概述

本 skill 用于清理单条文本内部的近似重复内容：
- 删除重复段落、重复句子或连续重复片段
- 保留首次出现内容
- 支持按相似度阈值识别轻微改写、标点差异、空白差异造成的重复

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 清理重复片段
- 删除重复段落
- 去掉近似重复内容
- 文本内部重复清理

## 核心参数说明

### 必需参数
- `--input`：输入 JSONL 文件路径
- `--output`：输出 JSONL 文件路径

### 可选参数
- `--text_field`：文本字段名，默认 `text`
- `--min_fragment_length`：候选重复片段最小字符长度，默认 `30`
- `--max_fragment_length`：候选重复片段最大字符长度，默认 `500`
- `--similarity_threshold`：近似重复判定阈值，默认 `0.88`
- `--keep_first`：保留第一次出现的重复片段，默认 `true`
- `--mark_cleaned`：是否标记已清洗样本，默认 `true`
- `--log_file`：删除片段日志文件路径

## 输入文件格式

支持以下结构化文件格式：
- JSONL

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为 JSONL 后再使用本 skill。

## 使用方法

```bash
python scripts/run_duplicate_fragment_cleaner.py \
  --input data.jsonl \
  --output cleaned.jsonl \
  --text_field text \
  --min_fragment_length 30 \
  --max_fragment_length 500 \
  --similarity_threshold 0.88 \
  --keep_first true \
  --mark_cleaned true \
  --log_file removed_fragments.json
```

## 输出示例

```text
[OK] Duplicate fragment fuzzy cleaning completed
   Input: data.jsonl
   Output: cleaned.jsonl
   Total samples: 8
   Samples cleaned: 3
   Fragments removed: 4
   Unique fragments: 3
```

## 注意事项

1. 仅处理单条文本内部重复片段，不做跨记录去重。
2. 模糊匹配会受阈值影响，建议先用较高阈值验证。
3. 输出会保留原始记录的其他字段。
4. `min_fragment_length` 用于避免误删过短短语。
