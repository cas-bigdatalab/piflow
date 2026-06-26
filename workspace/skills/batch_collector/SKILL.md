---
name: batch_collector
description: |
  批量文件清单采集器。扫描一个或多个本地文件/目录，或从任务列表加载路径，
  按支持的扩展名生成文件元信息清单，供后续文本、表格、文档、图像等采集流程继续处理。
  当用户需要批量盘点待采集文件、生成本地文件 manifest、统计输入文件类型或为后续采集算子准备文件清单时使用此 skill。
name_zh: 批量文件清单采集器
input_params:
  - name: input
    type: string
    required: false
    description: 输入文件或目录路径列表，与 task_list 二选一

  - name: task_list
    type: string
    required: false
    description: 任务列表文件路径，支持 json 或 txt，与 input 二选一

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: recursive
    type: string
    required: false
    default: "False"

  - name: file_types
    type: string
    required: false
    description: 指定允许采集的扩展名，如 txt csv pdf；不填时使用脚本默认支持类型

  - name: batch_size
    type: string
    required: false
    default: "0"
    description: 进度报告间隔，0 表示不按批次报告

  - name: output_format
    type: string
    required: false
    default: jsonl
    description: 输出格式：jsonl、json、csv 或 auto
output_params:
  - name: output
    type: jsonl_file
    description: 文件元信息清单，每条记录包含 file_path、filename、extension、file_size、collected_at、task_index、total_tasks

  - name: total_files
    type: integer
    description: 采集到的文件总数

  - name: type_counts
    type: object
    description: 按扩展名统计的文件数量分布
tag: 采集
---

# Batch Collector 批量文件清单采集器

## 功能概述

本 skill 用于批量扫描本地文件或目录，生成“待采集文件清单”。它不会读取、清洗或解析文件正文，只记录文件路径、文件名、扩展名、大小、采集时间和任务序号等基础元信息。

它适合放在采集流程入口，用来把一批本地资源整理成统一 manifest，再交给 text_collector、table_collector、image_collector 等后续算子继续处理。

## 触发条件

当用户提出以下需求时，应使用本 skill：

- 批量盘点本地待采集文件
- 扫描一个或多个输入目录并生成文件清单
- 统计输入文件的扩展名分布
- 为后续采集/解析/校验流程准备 manifest
- 从任务列表批量加载待处理路径

## 不处理什么

- 不读取文件正文
- 不清洗文本内容
- 不解析 CSV、JSON、PDF、DOCX 等内部结构
- 不判断文件内容质量
- 不执行真实下载、爬取或远程采集

## 核心参数说明

### 必需参数

| 参数 | 说明 |
|------|------|
| `--output` | 输出文件路径 |

### 输入参数

| 参数 | 说明 |
|------|------|
| `--input` | 一个或多个文件/目录路径，与 `--task_list` 二选一 |
| `--task_list` | 任务列表文件，支持 json 或 txt，与 `--input` 二选一 |

### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--recursive` | `false` | 是否递归扫描子目录 |
| `--file_types` | 脚本默认支持类型 | 指定允许采集的扩展名，如 `txt csv pdf` |
| `--batch_size` | `0` | 进度报告间隔，0 表示不按批次报告 |
| `--output_format` | `jsonl` | 输出格式：`jsonl`、`json`、`csv` 或 `auto` |

## 输入文件格式

### 目录输入

```text
input_dir/
  alpha.txt
  beta.csv
  config.json
  nested/
    deep.md
  skip.exe
```

### 文本任务列表

```text
workspace/data/a.txt
workspace/data/b.csv
workspace/data/docs
```

### JSON任务列表

```json
[
  "workspace/data/a.txt",
  "workspace/data/b.csv",
  "workspace/data/docs"
]
```

## 输出格式

默认输出 JSONL，每行代表一个被采集到的文件：

```json
{"file_path": "workspace/data/a.txt", "filename": "a.txt", "extension": ".txt", "file_size": 123, "collected_at": "2026-06-10 10:00:00", "task_index": 1, "total_tasks": 2}
```

字段含义：

| 字段 | 说明 |
|------|------|
| `file_path` | 相对输入根目录的文件路径 |
| `filename` | 文件名 |
| `extension` | 扩展名 |
| `file_size` | 文件字节数 |
| `collected_at` | 清单生成时间 |
| `task_index` | 当前文件序号 |
| `total_tasks` | 本次输出文件总数 |

## 使用方法

### 扫描单个目录

```bash
python scripts/run_batch_collector.py \
  --input ./data \
  --output ./batch_result.jsonl \
  --recursive true
```

### 扫描多个路径

```bash
python scripts/run_batch_collector.py \
  --input ./papers ./tables ./images \
  --output ./batch_result.jsonl \
  --recursive true
```

### 只采集指定扩展名

```bash
python scripts/run_batch_collector.py \
  --input ./data \
  --output ./result.jsonl \
  --file_types txt csv pdf
```

### 从任务列表加载路径

```bash
python scripts/run_batch_collector.py \
  --task_list ./tasks.txt \
  --output ./batch_result.jsonl
```

## 输出示例

**命令行输出：**

```text
[OK] Batch collection completed!
   Input paths: 1
   Total files collected: 5
   File type distribution:
     - .csv: 1
     - .json: 1
     - .md: 1
     - .txt: 2
   Output: ./batch_result.jsonl
```

**JSONL输出：**

```jsonl
{"file_path": ".../alpha.txt", "filename": "alpha.txt", "extension": ".txt", "file_size": 20, "collected_at": "2026-06-10 10:00:00", "task_index": 1, "total_tasks": 5}
{"file_path": ".../beta.csv", "filename": "beta.csv", "extension": ".csv", "file_size": 24, "collected_at": "2026-06-10 10:00:00", "task_index": 2, "total_tasks": 5}
```

## 环境要求

本 skill 使用 Python 标准库实现，无需额外安装第三方依赖。请使用项目虚拟环境运行：

```bash
.\.venv\Scripts\python.exe scripts/run_batch_collector.py --help
```

## 注意事项

1. `--input` 和 `--task_list` 至少提供一个。
2. `--recursive true` 才会扫描子目录。
3. `--file_types` 只控制扩展名筛选，不检查文件内容是否真实符合该格式。
4. 输出清单中的 `file_path` 是后续算子可继续读取的文件路径。
5. 如果需要正文抽取、表格解析、图像检查或内容校验，应交给后续专用 skill。
