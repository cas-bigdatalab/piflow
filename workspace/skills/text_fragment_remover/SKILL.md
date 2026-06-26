---
name: text_fragment_remover
description: |
  指定文本片段删除工具。读取结构化数据中的文本字段，删除用户显式给出的固定片段并保留其他字段不变。
  当用户提到删除固定词、固定占位符、固定水印短语、固定噪声片段等需求时使用此skill。
  即使用户没有明确说出 skill 名，只要任务是按明确片段从文本字段中移除内容，就应该使用此skill。
  不负责按类别自动识别 HTML、URL、emoji、数字、标点、控制字符等内容，这些应交给专用清洗 skill。

name_zh: 文本片段删除算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/JSON/JSONL）

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: text_field
    type: string
    required: true
    description: 文本字段名

  - name: remove_texts
    type: string
    required: true
    description: 要删除的文本片段，支持用 || 或换行分隔多个片段

output_params:
  - name: output
    type: csv_file
    description: 处理后的数据文件
tag: 清洗
---

# Text Fragment Remover 文本片段删除 Skill

## 功能概述

本skill用于删除文本字段中的用户指定片段：
- 删除固定词或固定短语
- 删除固定占位符或水印
- 删除固定噪声标记
- 保留未命中的其他文本内容

## 触发条件

当用户明确要求删除某些固定文本片段，而不是按类别自动识别 HTML、URL、emoji、数字或标点时，使用此skill。

## 核心参数说明

### 必需参数

- `--input`：输入文件路径
- `--output`：输出文件路径
- `--text_field`：要处理的文本字段
- `--remove_texts`：要删除的文本片段，多个片段可用 `||` 或换行分隔

### 可选参数

无。

## 输入文件格式

支持以下结构化文件格式：
- CSV
- TSV
- JSON
- JSONL

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为以上支持格式后再使用本skill。

不支持的文件格式会直接报错拒绝，不会自动猜测格式。

## 使用方法

```bash
python scripts/run_text_fragment_remover.py \
  --input data.csv \
  --output cleaned.csv \
  --text_field text \
  --remove_texts "[DRAFT]||REMOVE_ME"
```

## 输出示例

输入文本：`[DRAFT] This is REMOVE_ME sample.`

输出文本：` This is  sample.`

## 环境要求

```bash
pip install pandas
```

## 注意事项

- 只按字面量删除，不做正则匹配。
- 不会自动识别 HTML、URL、emoji、数字或标点。
- 未命中的文本会原样保留。
