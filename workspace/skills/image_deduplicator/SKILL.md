---
name: image_deduplicator
description: |
  图像去重工具。使用图像哈希精确匹配在文档级别删除包含重复图像的样本。
  当用户提到图像去重、删除重复图片、图片去重、清理重复图像等需求时使用此skill。
  即使用户没有明确说出"图像去重"，只要任务涉及从包含图像的数据中删除重复图片，
  就应该使用此skill。
---

# Image Deduplicator 图像去重 Skill

## 功能概述

本skill使用图像哈希算法（phash/dhash/whash/ahash）进行图像级别的精确匹配去重。
通过计算每个图像的哈希值，识别并删除包含相同图像的重复文档样本。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 图像去重
- 删除重复图片
- 图片去重
- 清理重复图像
- 文档图像去重

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--method` | 图像哈希方法 | `phash` |
| `--consider_text` | 是否同时考虑文本哈希 | `False` |
| `--image_key` | 图像字段的键名 | `images` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {
    "images": ["/path/to/image1.png", "/path/to/image2.jpg"]
  },
  {
    "images": ["/path/to/image3.jpg"]
  }
]
```

带文本的格式：

```json
[
  {
    "images": ["/path/to/image1.png"],
    "text": "这是一段描述文字"
  },
  {
    "images": ["/path/to/image2.png"],
    "text": "另一段描述文字"
  }
]
```

## 哈希方法说明

| 方法 | 说明 |
|------|------|
| `phash` | 感知哈希，速度快，准确性高（默认） |
| `dhash` | 差值哈希 |
| `whash` | 小波哈希 |
| `ahash` | 平均哈希，最快但最粗糙 |

## 使用方法

### 基本用法
```bash
python scripts/run_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json
```

### 使用指定哈希方法
```bash
python scripts/run_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --method dhash
```

### 同时考虑文本去重
```bash
python scripts/run_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --consider_text True
```

## 输出示例

**命令行输出：**
```
[OK] Image deduplication completed!
   Method: phash
   Consider text: False
   Original documents: 7
   Deduplicated documents: 3
   Removed duplicates: 4
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"images": ["/path/to/image1.png"]},
  {"images": ["/path/to/image2.jpg"]},
  {"images": ["/path/to/image3.jpg"]}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer，可用以下指令进行安装：
```bash
pip install py-data-juicer
```

**额外依赖：**
```bash
pip install imagededup
```

## 注意事项

1. **图像路径**：输入JSON中的图像路径应为绝对路径或相对于工作目录的路径
2. **哈希方法**：默认使用 phash，适合大多数场景
3. **consider_text**：设为 True 时，图像和文本都相同才算重复
4. **图像格式**：支持 PNG、JPG、JPEG 等常见图像格式
