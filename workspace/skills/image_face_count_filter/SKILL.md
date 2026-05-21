---
name: image_face_count_filter
description: |
  图像人脸数量过滤器。过滤以保持样本的面数在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到过滤图片、识别人脸、人脸数量检测、图片人脸筛选、按人脸数量过滤等需求时使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: min_face_count
    type: int
    required: false
    default: 1
    description: 最少人脸数量

  - name: max_face_count
    type: int
    required: false
    default: 1
    description: 最多人脸数量

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
    description: 过滤后的JSONL文件，包含人脸数量在指定范围内的样本
tag: 过滤与筛选
---

## 功能概述

该算子用于过滤包含指定人脸数量范围的图像样本。支持多种过滤策略：
- `any`: 任意一张图像符合条件即保留
- `all`: 所有图像都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_face_count | int | 否 | 1 | 最少人脸数量 |
| max_face_count | int | 否 | 1 | 最多人脸数量 |
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
python scripts/run_image_face_count_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_face_count 1 \
  --max_face_count 3 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_face_count`: 最小人脸数（默认1）
- `--max_face_count`: 最大人脸数（默认1）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 依赖 opencv-python 进行人脸检测，请确保已安装
3. 处理大量数据时可适当增加 num_proc 提高效率