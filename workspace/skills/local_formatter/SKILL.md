---
name: local_formatter
description: |
  本地格式化器。类用于从本地文件或本地目录加载数据集。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到加载本地数据集、读取本地文件、格式化本地数据、数据集加载等需求时使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 数据集文件或目录路径

  - name: output_path
    type: string
    required: true
    description: 输出JSONL文件路径

  - name: suffixes
    type: list
    required: false
    description: 指定后缀列表，如 ['.json', '.csv']

  - name: text_keys
    type: list
    required: false
    default: "['text']"
    description: 文本字段名列表

  - name: add_suffix
    type: bool
    required: false
    default: false
    description: 是否添加文件后缀信息

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output
    type: jsonl_file
    description: 格式化后的JSONL数据集文件
---

## 功能概述

该算子用于从本地文件或本地目录加载数据集，支持多种数据格式（JSON、CSV等），并格式化为统一的数据集格式。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 数据集文件或目录路径 |
| output_path | string | 是 | - | 输出JSONL文件路径 |
| suffixes | list | 否 | None | 指定后缀列表，如 ['.json', '.csv'] |
| text_keys | list | 否 | ['text'] | 文本字段名列表 |
| add_suffix | bool | 否 | False | 是否添加文件后缀信息 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入可以是：
1. 单个数据文件：`/path/to/data.json`
2. 数据文件目录：`/path/to/data_directory/`

支持的文件格式由 suffixes 参数指定，默认为自动识别。

## 输出数据格式

输出为 JSONL 格式，每行一个样本。

## 使用示例

### 命令行调用

```bash
# 加载本地JSON文件
python scripts/run_local_formatter.py \
  --input_path /path/to/input.json \
  --output_path /path/to/output.jsonl

# 加载目录中指定后缀的文件
python scripts/run_local_formatter.py \
  --input_path /path/to/data_directory \
  --output_path /path/to/output.jsonl \
  --suffixes .json \
  --suffixes .csv \
  --text_keys text

# 添加文件后缀信息
python scripts/run_local_formatter.py \
  --input_path /path/to/data_directory \
  --output_path /path/to/output.jsonl \
  --add_suffix
```

### 参数说明

- `--input_path`: 输入数据集文件或目录路径
- `--output_path`: 输出JSONL文件路径
- `--suffixes`: 目标后缀，可重复指定多个
- `--text_keys`: 文本字段名，可重复指定多个（默认 ['text']）
- `--add_suffix`: 是否添加文件后缀信息
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 支持多种本地文件格式（json, csv 等）
2. 空值或 None 的文本样本会被自动过滤
3. 相对路径会根据输入数据集目录自动转换为绝对路径