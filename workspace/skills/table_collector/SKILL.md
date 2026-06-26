---
name: table_collector
description: |
  表格文件采集工具。读取单个表格文件或目录中的 csv、tsv、xlsx、xls 文件，执行行记录采集，输出统一结构化表格记录文件。
  当用户提到表格采集、读取科研数据表、汇总 CSV/TSV/Excel 表格、把本地表格文件转成结构化记录等需求时使用此 skill。
  即使用户没有明确说出"表格采集"，只要任务涉及把本地结构化表格文件内容收集成统一记录，就应该使用此 skill。
  不负责表格清洗、空行删除、字段去空格、格式校验、字段过滤或格式转换。
name_zh: 表格类数据采集接入算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入表格文件或目录路径

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: encoding
    type: string
    required: false
    default: auto
    description: CSV/TSV 文件编码，默认 auto 自动检测

  - name: recursive
    type: string
    required: false
    default: "False"
    description: 是否递归采集子目录中的表格文件

  - name: add_metadata
    type: string
    required: false
    default: "True"
    description: 是否为每行记录添加来源文件元信息

  - name: output_format
    type: string
    required: false
    default: jsonl
    description: 输出格式，支持 jsonl/json/csv/auto
output_params:
  - name: output
    type: jsonl_file
    description: 采集后的结构化表格记录文件
tag: 采集
---

# Table Collector 表格采集 Skill

## 功能概述

本 skill 用于读取单个结构化表格文件或目录中的表格文件，将每一行采集为统一结构化记录，并输出为 JSONL、JSON 或 CSV。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 表格文件采集
- 读取科研数据表
- 汇总 CSV、TSV、Excel 表格内容
- 将本地表格文件转为结构化记录
- 为后续清洗、校验、入库准备统一表格输入

不适用于 PDF 表格抽取、图片表格识别、表格清洗、空行删除、字段去空格、格式结构校验、字段过滤或格式转换；这些任务需要使用对应的文档、图像、清洗、校验、筛选或转换 skill。

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入表格文件或目录路径 |
| `--output` | 输出文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--encoding` | CSV/TSV 文件编码，`auto` 会按常见编码尝试读取 | `auto` |
| `--recursive` | 是否递归采集子目录中的表格文件 | `False` |
| `--add_metadata` | 是否为每行记录添加 `_meta` 来源文件元信息 | `True` |
| `--output_format` | 输出格式，支持 `jsonl`、`json`、`csv`、`auto` | `jsonl` |

## 输入文件格式

输入可以是单个受支持表格文件，也可以是包含受支持表格文件的目录。目录模式只采集 `.csv`、`.tsv`、`.xlsx`、`.xls`，其它扩展名会跳过。

```text
input_dir/
  station_observations.csv
  station_observations.tsv
  nested/station_observations.xlsx
  skip.txt
```

## 使用方法

### 递归采集目录并输出 JSONL
```bash
python scripts/run_table_collector.py \
  --input ./input_dir \
  --output ./table_collector_output.jsonl \
  --encoding auto \
  --recursive true \
  --add_metadata true \
  --output_format jsonl
```

### 采集单个表格文件并输出 JSON
```bash
python scripts/run_table_collector.py \
  --input ./station_observations.csv \
  --output ./table_collector_output.json \
  --output_format json
```

## 处理示例

| 输入文件 | 参数效果 | 预期结果 |
|----------|----------|----------|
| `station_observations.csv` | 支持的 `.csv` 文件 | 每个数据行采集为一条记录 |
| `station_observations.tsv` | 支持的 `.tsv` 文件 | 每个数据行采集为一条记录 |
| `nested/station_observations.xlsx` | `--recursive true` | 每个数据行采集为一条记录 |
| `skip.txt` | 非支持扩展名 | 不进入采集列表 |

## 输出示例

```json
{"sample_id": "QYZ-001", "domain": "forest", "value": "12.4", "_meta": {"source_file": "station_observations.csv", "filename": "station_observations.csv", "row_count": 12, "collected_at": "2026-06-12 10:00:00"}}
```

## 环境要求

使用仓库内 Python 环境运行；Windows bash 下建议加 `PYTHONIOENCODING=utf-8` 避免中文控制台编码问题。Excel 读取需要运行环境已安装 `openpyxl`。

## 注意事项

1. `--recursive false` 时只扫描输入目录第一层文件。
2. `--add_metadata false` 时输出记录只包含原始表格字段。
3. 输出文件扩展名不会自动决定格式，除非 `--output_format auto`。
