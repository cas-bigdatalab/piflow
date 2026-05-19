---
name: ray_video_deduplicator
description: |
  Ray分布式视频去重工具。使用精确匹配（MD5哈希）在文档级别删除重复视频，基于Ray分布式框架。
  当用户提到视频去重、删除重复视频、分布式去重、大规模视频去重等需求时使用此skill。
  即使用户没有明确说出"Ray"或"分布式"，只要任务涉及大规模视频去重处理，
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

  - name: video_key
    type: string
    required: false
    default: videos
    description: 视频字段的键名

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

output_params:
  - name: output
    type: jsonl_file
    description: 去重后的JSON文件
---

# Ray Video Deduplicator Ray分布式视频去重 Skill

## 功能概述

本skill基于Ray分布式框架，使用MD5哈希算法对视频文件进行精确匹配去重。
适用于大规模视频数据的并行处理场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 视频去重
- 删除重复视频
- 分布式去重
- 大规模视频去重
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
| `--backend` | 分布式后端类型 | `ray_actor` |
| `--redis_address` | Redis服务器地址 | `redis://localhost:6379` |
| `--video_key` | 视频字段的键名 | `videos` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {
    "videos": ["/path/to/video1.mp4"]
  },
  {
    "videos": ["/path/to/video2.mp4"]
  },
  {
    "videos": ["/path/to/video1_dup.mp4"]
  }
]
```

多视频格式：

```json
[
  {
    "videos": ["/path/to/video1.mp4", "/path/to/video2.mp4"]
  },
  {
    "videos": ["/path/to/video3.mp4"]
  }
]
```

## 使用方法

### 基本用法（需要先启动Ray）
```bash
python scripts/run_ray_video_deduplicator.py \
  --input ./input.json \
  --output ./output.json
```

### 使用Redis后端
```bash
python scripts/run_ray_video_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --backend redis \
  --redis_address redis://localhost:6379
```

## 输出示例

**命令行输出：**
```
[OK] Ray video deduplication completed!
   Backend: ray_actor
   Original documents: 7
   Deduplicated documents: 3
   Removed duplicates: 4
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"videos": ["/path/to/video1.mp4"]},
  {"videos": ["/path/to/video2.mp4"]},
  {"videos": ["/path/to/video3.mp4"]}
]
```

## 环境要求

**安装依赖：**
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

## 注意事项

1. **分布式环境**：使用前需要启动 Ray 或 Redis
2. **视频路径**：输入JSON中的视频路径应为绝对路径或相对于工作目录的路径
3. **支持格式**：支持 MP4、AVI、MOV 等常见视频格式
4. **哈希算法**：使用 MD5 哈希对视频二进制数据进行精确匹配
