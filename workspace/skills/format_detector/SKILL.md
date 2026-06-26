---
name: format_detector
description: |
  接入资源格式识别工具。读取单个文件或目录中的接入资源，识别文本、表格、文档、图像、HTML、数据或未知类型，输出带推荐处理路由的格式识别结果文件。
  当用户提到格式识别、资源类型预判、采集入口分流、为文本/表格/文档/图像/HTML 选择后续处理路径等需求时使用此 skill。
  即使用户没有明确说出"格式识别"，只要任务涉及在采集入口判断文件类型并分配推荐处理路由，就应该使用此 skill。
  不负责读取正文内容、提取图像元信息、表格采集、文档解析、格式转换或实际执行后续处理。
name_zh: 采集基础格式识别算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件或目录路径

  - name: output
    type: string
    required: true
    description: 输出文件路径（格式识别结果）

  - name: recursive
    type: string
    required: false
    default: "False"
    description: 是否递归扫描子目录

  - name: output_format
    type: string
    required: false
    default: jsonl
    description: 输出格式，支持 jsonl/json/csv/auto
output_params:
  - name: output
    type: jsonl_file
    description: 格式识别结果文件
tag: 采集
---

# Format Detector 格式识别 Skill

## 功能概述

本 skill 用于在采集入口扫描文件资源，按扩展名和轻量内容特征识别资源基础类型，并输出推荐后续处理路由。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 识别文件格式
- 判断资源是文本、表格、文档、图像、HTML 还是数据文件
- 为采集入口资源分配后续处理路由
- 对混合目录做格式预识别
- 降低异构资源进入流水线后的适配冲突

不适用于正文采集、图像元信息提取、表格读取、文档解析、格式转换或实际执行后续处理；这些任务需要使用对应的采集、解析或转换 skill。

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入文件或目录路径 |
| `--output` | 输出文件路径（格式识别结果） |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--recursive` | 是否递归扫描子目录 | `False` |
| `--output_format` | 输出格式，支持 `jsonl`、`json`、`csv`、`auto` | `jsonl` |

## 输入文件格式

输入可以是单个文件，也可以是包含多类文件的目录。目录模式会扫描所有普通文件并输出格式识别记录。

```text
input_dir/
  notes.txt
  station_table.csv
  report.pdf
  image.png
  payload.json
  nested/raw.bin
```

## 使用方法

### 递归识别目录并输出 JSONL
```bash
python scripts/run_format_detector.py \
  --input ./input_dir \
  --output ./format_detector_output.jsonl \
  --recursive true \
  --output_format jsonl
```

### 识别单个文件并输出 JSON
```bash
python scripts/run_format_detector.py \
  --input ./notes.txt \
  --output ./format_detector_output.json \
  --output_format json
```

## 处理示例

| 输入文件 | 识别类型 | 推荐路由 |
|----------|----------|----------|
| `notes.txt` | `text` | `text_collector` |
| `station_table.csv` | `table` | `table_collector` |
| `report.pdf` | `document` | `pdf_collector` |
| `image.png` | `image` | `image_collector` |
| `payload.json` | `data` | `content_parser` |
| `page.html` | `html` | `content_parser` |
| `raw.bin` | `unknown` | `manual_review` |

## 输出示例

```json
{"file_path": "notes.txt", "filename": "notes.txt", "extension": ".txt", "category": "text", "content_format": "plain_text", "recommended_route": "text_collector", "file_size": 128, "detected_at": "2026-06-12 14:00:00"}
```

## 环境要求

使用仓库内 Python 环境运行；Windows bash 下建议加 `PYTHONIOENCODING=utf-8` 避免中文控制台编码问题。脚本仅使用 Python 标准库。

## 注意事项

1. 本 skill 只做格式识别和推荐路由，不读取完整正文或执行后续处理。
2. `--recursive false` 时只扫描输入目录第一层文件。
3. `file_path` 输出为相对输入根目录路径，不能包含本地绝对路径。
4. 未识别扩展名会归类为 `unknown`，推荐路由为 `manual_review`。
