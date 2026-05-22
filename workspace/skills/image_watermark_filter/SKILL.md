---
name: image_watermark_filter
description: |
  图像水印过滤器。过滤器以保持其图像没有水印的样本具有高概率。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到图像水印检测、图片无水印过滤、水印去除、检测图片水印等需求时使用此skill。

name_zh: 图像水印过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: hf_watermark_model
    type: string
    required: false
    default: amrul-hzz/watermark_detector
    description: HuggingFace上的水印检测模型

  - name: prob_threshold
    type: float
    required: false
    default: 0.8
    description: 水印概率阈值（0-1之间，低于此值保留）

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
    description: 过滤后的JSONL文件，包含无水印或水印概率低于阈值的样本
tag: 过滤与筛选

---

## 功能概述

该算子使用水印检测模型判断图像是否包含水印，过滤掉水印概率超过阈值的图像，保留无水印的样本。支持多种过滤策略：
- `any`: 任意一张图像符合条件即保留
- `all`: 所有图像都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_watermark_model | string | 否 | 'amrul-hzz/watermark_detector' | HuggingFace上的水印检测模型 |
| prob_threshold | float | 否 | 0.8 | 水印概率阈值（0-1之间，低于此值保留） |
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
python scripts/run_image_watermark_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --prob_threshold 0.8 \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_watermark_model`: 水印检测模型（默认：amrul-hzz/watermark_detector）
- `--prob_threshold`: 水印概率阈值（默认0.8，值越低越严格）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 该算子需要加载HuggingFace水印检测模型，首次运行会下载模型
3. 依赖 torch，请确保已安装
4. 处理大量数据时可适当增加 num_proc 提高效率