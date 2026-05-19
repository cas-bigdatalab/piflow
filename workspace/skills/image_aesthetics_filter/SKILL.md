---
name: image_aesthetics_filter
description: |
  图像美学过滤器。过滤美学评分不在指定范围内的图像样本。
  当用户提到图像美学、图像质量过滤、图片评分筛选、图像质量评估、过滤低质量图像等需求时使用此skill。
  即使用户没有明确说出"美学评分"，只要任务涉及根据图像美学质量来筛选数据，
  就应该使用此skill。

input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: hf_scorer_model
    type: string
    required: false
    default: shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE
    description: 美学评分模型

  - name: min_score
    type: float
    required: false
    default: 0.5
    description: 最小美学评分

  - name: max_score
    type: float
    required: false
    default: 1.0
    description: 最大美学评分

  - name: any_or_all
    type: string
    required: false
    default: any
    description: 多图像过滤策略（any/all）

  - name: image_key
    type: string
    required: false
    default: images
    description: 图像字段的键名

output_params:
  - name: output
    type: json_file
    description: 过滤后的JSON文件，包含美学评分在指定范围内的图像样本
---

# Image Aesthetics Filter 图像美学过滤 Skill

## 功能概述

本skill使用预训练的美学评分模型对图像进行质量评估，只保留美学评分在指定范围内的样本。
基于 LAION-Aesthetics Predictor 模型，常用于筛选高质量图像。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 图像美学过滤
- 图像质量过滤
- 图片评分筛选
- 图像质量评估
- 过滤低质量图像
- 高质量图像筛选

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--hf_scorer_model` | 美学评分模型 | `shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE` |
| `--min_score` | 最小美学评分 | `0.5` |
| `--max_score` | 最大美学评分 | `1.0` |
| `--any_or_all` | 多图像过滤策略 | `any` |
| `--image_key` | 图像字段的键名 | `images` |

## 输入文件格式

```json
[
  {"images": ["/path/to/image1.jpg"]},
  {"images": ["/path/to/image2.jpg"]},
  {"images": ["/path/to/image3.png"]}
]
```

多图像格式：

```json
[
  {"images": ["/path/to/image1.jpg", "/path/to/image2.jpg"]},
  {"images": ["/path/to/image3.png"]}
]
```

## 使用方法

### 默认参数过滤（评分0.5-1.0）
```bash
python scripts/run_image_aesthetics_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 自定义评分范围
```bash
python scripts/run_image_aesthetics_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_score 0.6 \
  --max_score 1.0
```

### 多图像策略：所有图像都满足条件才保留
```bash
python scripts/run_image_aesthetics_filter.py \
  --input ./input.json \
  --output ./output.json \
  --any_or_all all
```

## 过滤策略说明

| 策略 | 说明 |
|------|------|
| `any` | 任一图像满足条件即保留（默认） |
| `all` | 所有图像都满足条件才保留 |

## 输出示例

**命令行输出：**
```
[OK] Image aesthetics filtering completed!
   Scorer model: shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE
   Min score: 0.5
   Max score: 1.0
   Strategy: any
   Original documents: 3
   Filtered documents: 2
   Removed documents: 1
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"images": ["/path/to/image1.jpg"]},
  {"images": ["/path/to/image2.jpg"]}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer：
```bash
pip install py-data-juicer
```

**额外依赖：**
```bash
pip install torch torchvision
```

**硬件要求：**
建议使用 GPU 加速以提高处理速度。

## 注意事项

1. **图像路径**：输入JSON中的图像路径应为绝对路径或相对于工作目录的路径
2. **评分范围**：美学评分范围为 0-1（默认模型已归一化）
3. **多图像处理**：支持多图像样本，使用 `any_or_all` 参数控制过滤策略
4. **适用场景**：图像质量评估、高质量图像筛选、低质量图像过滤
