---
name: ray_document_deduplicator
description: |
  Ray分布式文档去重工具。使用精确匹配（MD5哈希）在文档级别删除重复的样本，基于Ray分布式框架。
  当用户提到文档去重、删除重复文档、样本去重、分布式去重、大规模数据去重等需求时使用此skill。
  即使用户没有明确说出"Ray"或"分布式"，只要任务涉及大规模文档去重处理，
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

  - name: lowercase
    type: bool
    required: false
    default: false
    description: 是否将文本转为小写进行比对

  - name: ignore_non_character
    type: bool
    required: false
    default: false
    description: 是否忽略非字母字符（空格、数字、标点）

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

# Ray Document Deduplicator Ray分布式文档去重 Skill

## 功能概述

本skill基于Ray分布式框架，使用MD5哈希算法进行文档级别的精确匹配去重。
适用于大规模数据集的并行处理场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 文档去重
- 删除重复文档
- 样本去重
- 分布式去重
- 大规模数据去重
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
| `--lowercase` | 是否将文本转为小写进行比对 | `False` |
| `--ignore_non_character` | 是否忽略非字母字符（空格、数字、标点） | `False` |
| `--backend` | 分布式后端类型 | `ray_actor` |
| `--redis_address` | Redis服务器地址 | `redis://localhost:6379` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
{
  "data": [
    {"text": "文档内容1"},
    {"text": "文档内容2"},
    {"text": "文档内容1"}
  ]
}
```

或直接使用文档列表：

```json
[
  {"text": "文档内容1"},
  {"text": "文档内容2"},
  {"text": "文档内容1"}
]
```

## 使用方法

### 基本用法
```bash
python scripts/run_ray_document_deduplicator.py \
  --input ./input.json \
  --output ./output.json
```

### 使用Redis后端
```bash
python scripts/run_ray_document_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --backend redis \
  --redis_address redis://localhost:6379
```

### 忽略大小写去重
```bash
python scripts/run_ray_document_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --lowercase True
```

## 输出示例

**命令行输出：**
```
[OK] Ray document deduplication completed!
   Backend: ray_actor
   Original documents: 5
   Deduplicated documents: 4
   Removed duplicates: 1
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"text": "文档内容1"},
  {"text": "文档内容2"},
  {"text": "文档内容3"},
  {"text": "文档内容4"}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer 和 Ray，请在调用前安装好python环境并安装依赖：
```bash
pip install py-data-juicer ray redis
```

**启动Ray：**
```bash
ray start --head
```

**或启动Redis：**
```bash
redis-server
```

## 与普通DocumentDeduplicator的区别

| 特性 | DocumentDeduplicator | RayDocumentDeduplicator |
|------|---------------------|------------------------|
| 处理方式 | 单机处理 | 分布式并行处理 |
| 适用场景 | 小规模数据 | 大规模数据 |
| 依赖 | 仅data_juicer | data_juicer + Ray/Redis |
| 性能 | 一般 | 高 |

## 注意事项

1. **分布式环境**：使用前需要启动 Ray 或 Redis
2. **后端选择**：小规模数据用 `ray_actor`，超大规模用 `redis`
3. **输入格式**：输入JSON需要包含 `data` 字段或直接是文档列表
4. **处理逻辑**：保留首次出现的文档，删除后续重复项
