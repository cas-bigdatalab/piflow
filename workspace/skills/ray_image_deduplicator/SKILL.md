---
name: ray_image_deduplicator
description: |
  Ray分布式图像去重工具。使用图像哈希精确匹配在文档级别删除重复样本，基于Ray分布式框架。
  当用户提到图像去重、删除重复图片、分布式去重、大规模图像去重等需求时使用此skill。
  即使用户没有明确说出"Ray"或"分布式"，只要任务涉及大规模图像去重处理，
  就应该使用此skill。

name_zh: Ray分布式图像去重算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: method
    type: string
    required: false
    default: phash
    description: 图像哈希方法（phash/dhash/whash/ahash）

  - name: backend
    type: string
    required: false
    default: ray_actor
    description: 分布式后端类型（ray_actor/redis）

  - name: redis_address
    type: string
    required: false
    default: "redis://localhost:6379"
    description: Redis服务器地址

  - name: image_key
    type: string
    required: false
    default: images
    description: 图像字段的键名

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

output_params:
  - name: output
    type: jsonl_file
    description: 去重后的JSON文件
tag: 去重

---

# Ray Image Deduplicator Ray分布式图像去重 Skill

## 功能概述

本skill基于Ray分布式框架，使用图像哈希算法（phash/dhash/whash/ahash）进行图像级别的精确匹配去重。
适用于大规模图像数据的并行处理场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 图像去重
- 删除重复图片
- 分布式去重
- 大规模图像去重
- Ray并行处理

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
| `--backend` | 分布式后端类型 | `ray_actor` |
| `--redis_address` | Redis服务器地址 | `redis://localhost:6379` |
| `--image_key` | 图像字段的键名 | `images` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {
    "images": ["/path/to/image1.png"]
  },
  {
    "images": ["/path/to/image2.jpg"]
  },
  {
    "images": ["/path/to/image1_dup.png"]
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

### 基本用法（需要先启动Ray）
```bash
python scripts/run_ray_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json
```

### 使用指定哈希方法
```bash
python scripts/run_ray_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --method dhash
```

### 使用Redis后端
```bash
python scripts/run_ray_image_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --backend redis \
  --redis_address redis://localhost:6379
```

## 输出示例

**命令行输出：**
```
[OK] Ray image deduplication completed!
   Method: phash
   Backend: ray_actor
   Original documents: 7
   Deduplicated documents: 3
   Removed duplicates: 4
   Input file: ./input.json
   Output file: ./output.json
```

## 环境要求

**安装依赖：**
```bash
pip install py-data-juicer ray redis imagededup
```

**启动Ray：**
```bash
ray start --head
```

## 与普通ImageDeduplicator的区别

| 特性 | ImageDeduplicator | RayImageDeduplicator |
|------|-------------------|---------------------|
| 处理方式 | 单机处理 | 分布式并行处理 |
| 适用场景 | 小规模数据 | 大规模数据 |
| 依赖 | data_juicer | data_juicer + Ray/Redis |
| 性能 | 一般 | 高 |

## 注意事项

1. **分布式环境**：使用前需要启动 Ray 或 Redis
2. **图像路径**：输入JSON中的图像路径应为绝对路径或相对于工作目录的路径
3. **哈希方法**：默认使用 phash，适合大多数场景
4. **图像格式**：支持 PNG、JPG、JPEG 等常见图像格式
