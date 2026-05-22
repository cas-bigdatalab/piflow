---
name: image_size_filter
description: |
  图像文件大小过滤器。保留图像大小 (以字节/KB/MB/... 为单位) 在特定范围内的数据样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到图像文件大小过滤、图片大小筛选、图像尺寸KB/MB过滤、按文件大小过滤等需求时使用此skill。

name_zh: 图像文件大小过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: min_size
    type: string
    required: false
    default: "0"
    description: 最小文件大小，支持120kb、1MB、1GB等格式

  - name: max_size
    type: string
    required: false
    default: 1TB
    description: 最大文件大小，支持180KB、1MB等格式

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
    description: 过滤后的JSONL文件，包含文件大小在指定范围内的样本
tag: 过滤与筛选

---

## 功能概述

该算子用于过滤图像文件大小在指定范围内的样本。注意这里是文件大小（字节数），不是图像分辨率。支持多种过滤策略：
- `any`: 任意一张图像符合条件即保留
- `all`: 所有图像都符合条件才保留

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_size | string | 否 | '0' | 最小文件大小，支持 120kb, 1MB, 1GB 等格式 |
| max_size | string | 否 | '1TB' | 最大文件大小，支持 180KB, 1MB 等格式 |
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
python scripts/run_image_size_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_size 120kb \
  --max_size 180KB \
  --any_or_all any
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_size`: 最小文件大小，支持 kb, KB, mb, MB, gb, GB 等单位（默认0，无限制）
- `--max_size`: 最大文件大小（默认1TB，无限制）
- `--any_or_all`: 过滤策略，默认any
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 输入文件中的图像路径应为有效且可访问的文件路径
2. 该算子直接读取文件大小，不加载图像到内存，效率较高
3. 支持的大小单位：Bytes, KB/KiB, MB/MiB, GB/GiB, TB/TiB（不区分大小写）