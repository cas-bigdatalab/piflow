---
name: maximum_line_length_filter
description: |
  最大行长度过滤器。过滤器将最大行长度的样本保持在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到最大行长度过滤、文本行长筛选、最长行过滤、按行长度过滤等需求时使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: min_len
    type: int
    required: false
    default: 10
    description: 最小行长度（字符数）

  - name: max_len
    type: int
    required: false
    default: 2147483647
    description: 最大行长度（字符数）

  - name: batch_size
    type: int
    required: false
    default: 1
    description: 批处理大小

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output
    type: jsonl_file
    description: 过滤后的JSONL文件，包含最大行长度在指定范围内的样本
tag: 过滤与筛选
---

## 功能概述

该算子用于过滤最大行长度在指定范围内的文本样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_len | int | 否 | 10 | 最小行长度（字符数） |
| max_len | int | 否 | 2147483647 | 最大行长度（字符数） |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "第一行文本\n第二行文本\n第三行文本"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_maximum_line_length_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_len 10 \
  --max_len 20
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_len`: 最小行长度（默认10）
- `--max_len`: 最大行长度（默认不限制）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 该算子计算文本中所有行的最大长度
2. 长度按字符数计算，不是字节数
3. 处理大量数据时可适当增加 batch_size 和 num_proc 提高效率