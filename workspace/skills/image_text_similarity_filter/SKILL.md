---
name: image_text_similarity_filter
description: |
  图像文本相似度过滤器。过滤器将图像和文本之间的相似性保持在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到图像文本相似度过滤、图片文字相似度、文图相似度检测、图文相关性过滤等需求时使用此skill。

name_zh: 图像文本相似度过滤器算子
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

  - name: horizontal_flip
    type: bool
    required: false
    default: false
    description: 是否水平翻转图像

  - name: vertical_flip
    type: bool
    required: false
    default: false
    description: 是否垂直翻转图像

  - name: reduce_mode
    type: string
    required: false
    default: avg
    description: 多图聚合模式（avg/max/min）

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
  - name: output
    type: jsonl_file
    description: 过滤后的JSONL文件，包含图像文本相似度在指定范围内的样本
tag: 过滤与筛选

---

## 功能概述

该算子使用CLIP模型计算图像与文本之间的相似度，过滤相似度在指定范围内的样本。支持多种过滤策略：
- `any`: 任意一个相似度符合条件即保留
- `all`: 所有相似度都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_clip | string | 否 | 'openai/clip-vit-base-patch32' | HuggingFace上的CLIP模型 |
| min_score | float | 否 | 0.1 | 最小相似度分数 |
| max_score | float | 否 | 1.0 | 最大相似度分数 |
| horizontal_flip | bool | 否 | False | 是否水平翻转图像 |
| vertical_flip | bool | 否 | False | 是否垂直翻转图像 |
| reduce_mode | string | 否 | 'avg' | 多图聚合模式：avg/max/min |
| any_or_all | string | 否 | 'any' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 和 `images` 字段：

```json
{"text": "<image>a photo of a cat", "images": ["/path/to/cat.jpg"]}
```

注意：文本中需要使用 `<image>` 标记表示图像位置，如有多张图像可用 `<eos>` 分隔。

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，包含 text 和 images 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_image_text_similarity_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_score 0.2 \
  --max_score 0.9 \
  --reduce_mode avg \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_clip`: CLIP模型（默认：openai/clip-vit-base-patch32）
- `--min_score`: 最小相似度分数（默认0.1）
- `--max_score`: 最大相似度分数（默认1.0）
- `--horizontal_flip`: 是否水平翻转图像
- `--vertical_flip`: 是否垂直翻转图像
- `--reduce_mode`: 多图聚合模式，默认avg
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 该算子使用CLIP模型计算图像文本相似度，首次运行会下载模型
3. 依赖 torch 和 transformers，请确保已安装
4. 处理大量数据时可适当增加 num_proc 提高效率