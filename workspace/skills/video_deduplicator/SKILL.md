---
name: video_deduplicator
description: |
  视频去重工具。使用精确匹配（MD5哈希）在文档级别删除重复视频样本。
  当用户提到视频去重、删除重复视频、清理重复视频等需求时使用此skill。
  即使用户没有明确说出"视频去重"，只要任务涉及从包含视频的数据中删除重复视频，
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

  - name: consider_text
    type: bool
    required: false
    default: false
    description: 是否同时考虑文本哈希进行去重

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
tag: 去重
---

# Video Deduplicator 视频去重 Skill

## 功能概述

本skill使用MD5哈希算法对视频文件进行精确匹配去重。
通过计算每个视频的哈希值，识别并删除包含相同视频的重复文档样本。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 视频去重
- 删除重复视频
- 清理重复视频
- 文档视频去重

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--consider_text` | 是否同时考虑文本哈希进行去重 | `False` |
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

带文本的格式：

```json
[
  {
    "videos": ["/path/to/video1.mp4"],
    "text": "视频1的描述文字"
  },
  {
    "videos": ["/path/to/video2.mp4"],
    "text": "视频2的描述文字"
  }
]
```

## 使用方法

### 基本用法
```bash
python scripts/run_video_deduplicator.py \
  --input ./input.json \
  --output ./output.json
```

### 同时考虑文本去重
```bash
python scripts/run_video_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --consider_text True
```

## 输出示例

**命令行输出：**
```
[OK] Video deduplication completed!
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
  {"videos": ["/path/to/video1.mp4"]},
  {"videos": ["/path/to/video2.mp4"]},
  {"videos": ["/path/to/video3.mp4"]}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer：
```bash
pip install py-data-juicer
```

## 与 RayVideoDeduplicator 的区别

| 特性 | VideoDeduplicator | RayVideoDeduplicator |
|------|-------------------|---------------------|
| 处理方式 | 单机处理 | 分布式并行处理 |
| 适用场景 | 小规模数据 | 大规模数据 |
| 依赖 | data_juicer | data_juicer + Ray/Redis |

## 注意事项

1. **视频路径**：输入JSON中的视频路径应为绝对路径或相对于工作目录的路径
2. **哈希算法**：使用 MD5 哈希对视频二进制数据进行精确匹配
3. **consider_text**：设为 True 时，视频和文本都相同才算重复
4. **支持格式**：支持 MP4、AVI、MOV 等常见视频格式
