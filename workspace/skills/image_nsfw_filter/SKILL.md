---
name: image_nsfw_filter
description: |
  图像NSFW内容检测过滤器。过滤器保留图像具有低nsfw分数的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到图片安全检测、NSFW过滤、不良内容过滤、图片审核、图像内容过滤等需求时使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: hf_nsfw_model
    type: string
    required: false
    default: Falconsai/nsfw_image_detection
    description: HuggingFace上的NSFW检测模型

  - name: max_score
    type: float
    required: false
    default: 0.5
    description: 最大NSFW分数阈值（0-1之间，低于此值保留）

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
    description: 过滤后的JSONL文件，包含NSFW分数低于阈值的样本
tag: 过滤与筛选
---

## 功能概述

该算子用于检测图像的NSFW（Not Safe For Work 不适宜在工作场所观看的内容）分数，过滤掉高分值的图像。支持多种过滤策略：
- `any`: 任意一张图像符合条件即保留
- `all`: 所有图像都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_nsfw_model | string | 否 | 'Falconsai/nsfw_image_detection' | HuggingFace上的NSFW检测模型 |
| max_score | float | 否 | 0.5 | 最大NSFW分数阈值（0-1之间，低于此值保留） |
| any_or_all | string | 否 | 'any' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `images` 字段：

```json
{"images": ["/path/to/image1.jpg", "/path/to/image2.jpg"]}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
python scripts/run_image_nsfw_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --max_score 0.0005 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_nsfw_model`: NSFW检测模型（默认：Falconsai/nsfw_image_detection）
- `--max_score`: 最大NSFW分数阈值（默认0.5，值越低越严格）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 该算子需要加载HuggingFace模型，首次运行会下载模型，可能需要较长时间
3. 依赖 torch，请确保已安装
4. 处理大量数据时可适当增加 num_proc 提高效率