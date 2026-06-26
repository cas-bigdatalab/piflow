---
name: en_text_cleaner
description: '英文文本基础清洗工具。读取英文科研文本，展开常见缩写、修正常见拼写错误并可选规范大小写，输出整理后的 JSONL 数据。

  当用户提到英文文本清洗、英文缩写展开、英文拼写纠正、英文文本规整等需求时使用此skill。

  适合外文论文、英文实验记录的基础规整，不负责翻译、语法改写或跨语言语义修复。

  '
name_zh: 英文文本清洗优化算子
tag: 清洗
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: text_field
  type: string
  required: false
  default: text
  description: 文本字段名
- name: expand_abbreviations
  type: string
  required: false
  default: "True"
  description: 是否展开缩写
- name: fix_spelling
  type: string
  required: false
  default: "True"
  description: 是否纠正拼写
- name: normalize_case
  type: string
  required: false
  default: "False"
  description: 是否规范化大小写
- name: mark_cleaned
  type: string
  required: false
  default: "True"
  description: 是否标记已清洗样本
- name: custom_abbreviations
  type: string
  required: false
  default: ''
  description: 自定义缩写词典JSON文件路径
- name: custom_spellings
  type: string
  required: false
  default: ''
  description: 自定义拼写词典JSON文件路径
output_params:
- name: output
  type: jsonl_file
  description: 清洗后的JSONL文件
- name: total_samples
  type: integer
  description: 总样本数
- name: processed_samples
  type: integer
  description: 处理样本数
- name: abbreviations_expanded
  type: integer
  description: 缩写展开次数
- name: spelling_fixed
  type: integer
  description: 拼写纠正次数
---

# EnTextCleaner - 英文文本清洗优化算子

## 功能概述

英文文本基础清洗工具。读取英文科研文本，展开常见缩写、修正常见拼写错误并可选规范大小写，输出整理后的 JSONL 数据。
适合外文论文、英文实验记录的基础规整，不负责翻译、语法改写或跨语言语义修复。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 英文缩写展开
- 英文拼写纠正
- 英文文本规整
- 英文大小写规范化

## 核心参数说明

### 必需参数
- `--input`：输入JSONL文件路径
- `--output`：输出JSONL文件路径

### 可选参数
- `--text_field`：文本字段名，默认 `text`
- `--expand_abbreviations`：是否展开缩写，默认 `true`
- `--fix_spelling`：是否纠正拼写，默认 `true`
- `--normalize_case`：是否规范化大小写，默认 `false`
- `--mark_cleaned`：是否标记已清洗样本，默认 `true`
- `--custom_abbreviations`：自定义缩写词典JSON文件路径
- `--custom_spellings`：自定义拼写词典JSON文件路径

## 输入文件格式

- JSONL

## 使用方法

```bash
python scripts/run_en_text_cleaner.py \
  --input data.jsonl \
  --output cleaned.jsonl \
  --text_field text
```

## 输出示例

```
[OK] English text cleaning completed
   Total samples: 1000
   Samples processed: 234
   Abbreviations expanded: 156
   Spelling fixed: 89
```

## 环境要求

- Python 3.10+
- 仅依赖标准库

## 注意事项

1. 本skill只做缩写展开和拼写纠正，不负责语法修正或全句翻译。
2. 自定义词典需要符合JSON格式。
3. 修改样本会附带 `_en_cleaned` 标记和 `_en_change_details` 明细。
