---
name: image_face_ratio_filter
description: |
  图像人脸面积比例过滤器。过滤以保持面面积比在特定范围内的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到过滤图片、人脸占比、面部面积比例、图片人脸区域筛选、按人脸占比过滤等需求时使用此skill。
---

## 功能概述

该算子用于过滤人脸面积占比在指定范围内的图像样本。计算图像中最大人脸区域与图像总面积的比值，支持多种过滤策略：
- `any`: 任意一张图像符合条件即保留
- `all`: 所有图像都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_ratio | float | 否 | 0.0 | 最小人脸面积比例 |
| max_ratio | float | 否 | 0.4 | 最大人脸面积比例 |
| any_or_all | string | 否 | 'any' | 过滤策略：'any' 或 'all' |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `images` 字段：

```json
{"images": ["/path/to/image1.jpg", "/path/to/image2.jpg"]}
```

也支持空图片列表：
```json
{"text": "some text", "images": []}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
python scripts/run_image_face_ratio_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_ratio 0.4 \
  --max_ratio 1.0 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_ratio`: 最小人脸面积比例（默认0.0）
- `--max_ratio`: 最大人脸面积比例（默认0.4）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 依赖 opencv-python 进行人脸检测，请确保已安装
3. 处理大量数据时可适当增加 num_proc 提高效率