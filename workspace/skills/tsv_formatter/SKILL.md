---
name: tsv_formatter
description: |
  TSV格式化器。用于加载和格式化tsv类型的文件。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到TSV格式化、TSV数据加载、读取TSV文件、TSV转JSONL等需求时使用此skill。

name_zh: TSV格式化器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入TSV文件路径或目录

  - name: output_path
    type: string
    required: true
    description: 输出JSONL文件路径

  - name: text_keys
    type: list
    required: false
    default: ['text']
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
  - name: output_path
    type: jsonl_file
    description: 输出的JSONL格式数据集文件
tag: 格式转换

---

## 功能概述

该算子用于加载 TSV（Tab-Separated Values）格式的文件并格式化为统一的数据集格式，输出为 JSONL 格式。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入TSV文件路径或目录 |
| output_path | string | 是 | - | 输出JSONL文件路径 |
| text_keys | list | 否 | ['text'] | 文本字段名列表 |
| add_suffix | bool | 否 | False | 是否添加文件后缀信息 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入可以是：
1. 单个 TSV 文件：`/path/to/data.tsv`
2. TSV 文件目录：`/path/to/tsv_directory/`

## 输出数据格式

输出为 JSONL 格式，每行一个样本。

## 使用示例

### 命令行调用

```bash
# 加载单个TSV文件
python scripts/run_tsv_formatter.py \
  --input_path /path/to/input.tsv \
  --output_path /path/to/output.jsonl

# 指定文本字段
python scripts/run_tsv_formatter.py \
  --input_path /path/to/input.tsv \
  --output_path /path/to/output.jsonl \
  --text_keys text

# 加载目录中的所有TSV文件
python scripts/run_tsv_formatter.py \
  --input_path /path/to/tsv_directory \
  --output_path /path/to/output.jsonl \
  --add_suffix
```

### 参数说明

- `--input_path`: 输入TSV文件或目录路径
- `--output_path`: 输出JSONL文件路径
- `--text_keys`: 文本字段名，可重复指定多个（默认 ['text']）
- `--add_suffix`: 是否添加文件后缀信息
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. TSV 使用 Tab (`\t`) 作为分隔符
2. 输入文件必须是有效的 TSV 格式
3. 空值或None的文本样本会被自动过滤