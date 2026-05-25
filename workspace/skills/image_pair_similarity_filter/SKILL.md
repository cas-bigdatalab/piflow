---
name: image_pair_similarity_filter
description: |
  图像对相似度过滤器。过滤器将图像之间具有相似性的图像对保持在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到图像相似度检测、图像对过滤、双图相似度、图片相似度筛选、图像pair过滤等需求时使用此skill。

name_zh: 图像对相似度过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

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
    description: 过滤策略（any/all）

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL文件，包含图像对相似度在指定范围内的样本
tag: 过滤与筛选

---

## 功能概述

该算子用于计算两个图像之间的相似度（使用CLIP模型），过滤掉相似度不在指定范围内的图像对。支持多种过滤策略：
- `any`: 任意一个图像对符合条件即保留
- `all`: 所有图像对都符合条件才保留

注意：每个样本必须包含且仅包含2个图像。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_clip | string | 否 | 'openai/clip-vit-base-patch32' | HuggingFace上的CLIP模型 |
| min_score | float | 否 | 0.1 | 最小相似度分数 |
| max_score | float | 否 | 1.0 | 最大相似度分数 |
| any_or_all | string | 否 | 'any' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 和 `images` 字段，其中 images 必须是恰好2个图像路径：

```json
{"text": "image pair 1", "images": ["/path/to/image1.jpg", "/path/to/image2.jpg"]}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，包含 text 和 images 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_image_pair_similarity_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_score 0.85 \
  --max_score 1.0 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_clip`: CLIP模型（默认：openai/clip-vit-base-patch32）
- `--min_score`: 最小相似度（默认0.1）
- `--max_score`: 最大相似度（默认1.0）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中每个样本必须恰好包含2个图像路径
2. 该算子使用CLIP模型计算图像相似度，首次运行会下载模型
3. 依赖 torch 和 transformers，请确保已安装
4. 处理大量数据时可适当增加 num_proc 提高效率