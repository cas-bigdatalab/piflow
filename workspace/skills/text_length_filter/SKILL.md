---
name: text_length_filter
description: |
  文本长度过滤器。过滤以保持文本总长度在特定范围内的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到文本长度过滤、文本字数筛选、按文本长度过滤、按字数过滤等需求时使用此skill。

name_zh: 文本长度过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: min_len
    type: int
    required: false
    default: 10
    description: 最小文本长度

  - name: max_len
    type: int
    required: false
    description: 最大文本长度（默认不限制）

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
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件
tag: 过滤与筛选

---

## 功能概述

该算子根据文本总长度进行过滤，保留长度在指定范围内的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_len | int | 否 | 10 | 最小文本长度 |
| max_len | int | 否 | 2147483647 | 最大文本长度 |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段需要检测长度的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_text_length_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_len 10 \
  --max_len 50
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_len`: 最小文本长度（默认10）
- `--max_len`: 最大文本长度（默认不限制）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 长度按字符数计算，不是字节数
2. 是批处理算子，可适当调整 batch_size 提高效率