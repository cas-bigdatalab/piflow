---
name: image_aspect_ratio_filter
description: |
  图像长宽比过滤器。过滤图像长宽比不在指定范围内的样本。
  当用户提到图像长宽比、图片比例过滤、图像尺寸筛选、图像宽高比等需求时使用此skill。
  即使用户没有明确说出"长宽比"，只要任务涉及根据图像宽高比来筛选数据，
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

  - name: min_ratio
    type: float
    required: false
    default: 0.333
    description: 最小长宽比

  - name: max_ratio
    type: float
    required: false
    default: 3.0
    description: 最大长宽比

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
    description: 过滤后的JSON文件，包含长宽比在指定范围内的图像样本
tag: 过滤与筛选
---

# Image Aspect Ratio Filter 图像长宽比过滤 Skill

## 功能概述

本skill根据图像的长宽比（宽/高）进行过滤，只保留长宽比在指定范围内的图像。
常用于筛选特定比例的图像，如正方形、横屏、竖屏等。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 图像长宽比过滤
- 图片比例筛选
- 图像尺寸过滤
- 图像宽高比筛选
- 筛选正方形图像
- 筛选横屏/竖屏图像

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--min_ratio` | 最小长宽比 | `0.333` |
| `--max_ratio` | 最大长宽比 | `3.0` |
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

## 长宽比说明

- **长宽比 = 宽 / 高**
- 1.0 = 正方形
- < 1.0 = 竖屏图像
- > 1.0 = 横屏图像

## 使用方法

### 默认参数过滤（长宽比0.333-3.0）
```bash
python scripts/run_image_aspect_ratio_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 筛选正方形图像（长宽比接近1.0）
```bash
python scripts/run_image_aspect_ratio_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_ratio 0.9 \
  --max_ratio 1.1
```

### 筛选横屏图像
```bash
python scripts/run_image_aspect_ratio_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_ratio 1.0
```

### 筛选竖屏图像
```bash
python scripts/run_image_aspect_ratio_filter.py \
  --input ./input.json \
  --output ./output.json \
  --max_ratio 1.0
```

## 过滤策略说明

| 策略 | 说明 |
|------|------|
| `any` | 任一图像满足条件即保留（默认） |
| `all` | 所有图像都满足条件才保留 |

## 输出示例

**命令行输出：**
```
[OK] Image aspect ratio filtering completed!
   Min ratio: 0.333
   Max ratio: 3.0
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

## 注意事项

1. **图像路径**：输入JSON中的图像路径应为绝对路径或相对于工作目录的路径
2. **长宽比计算**：`宽 / 高`，1.0 表示正方形
3. **支持格式**：支持 PNG、JPG、JPEG 等常见图像格式
4. **适用场景**：筛选特定比例的图像、过滤极端比例图像
