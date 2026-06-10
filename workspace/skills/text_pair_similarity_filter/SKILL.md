---
name: text_pair_similarity_filter
description: |
  文本对相似度过滤器。过滤器将文本之间具有相似性的文本对保留在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到文本对相似度过滤、文本对过滤、双文本相似度、文本配对过滤等需求时使用此skill。

name_zh: 文本对相似度过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: text_key_second
    type: string
    required: true
    description: 第二个文本字段名

  - name: hf_clip
    type: string
    required: false
    default: openai/clip-vit-base-patch32
    description: HuggingFace上的CLIP模型

  - name: min_score
    type: float
    required: false
    default: 0.1
    description: 最小相似度分数

  - name: max_score
    type: float
    required: false
    default: 1.0
    description: 最大相似度分数

  - name: any_or_all
    type: string
    required: false
    default: any
    description: 过滤策略（any 或 all）

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

  - name: text_key
    type: string
    required: false
    default: text
    description: 要操作的文本字段名

output_params:
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件
tag: 过滤与筛选

---

## 功能概述

该算子使用CLIP模型计算两个文本之间的相似度，过滤相似度在指定范围内的文本对。支持多种过滤策略：
- `any`: 任意一个文本对符合条件即保留
- `all`: 所有文本对都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_clip | string | 否 | 'openai/clip-vit-base-patch32' | HuggingFace上的CLIP模型 |
| min_score | float | 否 | 0.1 | 最小相似度分数 |
| max_score | float | 否 | 1.0 | 最大相似度分数 |
| text_key_second | string | 是 | - | 第二个文本字段名 |
| any_or_all | string | 否 | 'any' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含两个文本字段：

```json
{"text": "a lovely cat", "target_text": "a cute cat"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
python scripts/run_text_pair_similarity_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --text_key_second target_text \
  --min_score 0.85 \
  --max_score 0.99 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_clip`: CLIP模型（默认：openai/clip-vit-base-patch32）
- `--min_score`: 最小相似度分数（默认0.1）
- `--max_score`: 最大相似度分数（默认1.0）
- `--text_key_second`: 第二个文本字段名（必填）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1
- `--text_key`: 要操作的文本字段名（默认text）

## 注意事项

1. 该算子使用CLIP模型计算文本对相似度，首次运行会下载模型
2. 必须指定 `text_key_second` 参数
3. 依赖 torch 和 transformers，请确保已安装