---
name: words_num_filter
description: |
  单词数量过滤器。过滤器，以保持总字数在特定范围内的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到单词数量过滤、文本字数筛选、按单词数过滤、按字数过滤等需求时使用此skill。

name_zh: 单词数量过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: lang
    type: string
    required: false
    default: en
    description: 语言代码

  - name: tokenization
    type: bool
    required: false
    default: false
    description: 是否使用分词模型

  - name: min_num
    type: int
    required: false
    default: 10
    description: 最小单词数量

  - name: max_num
    type: int
    required: false
    description: 最大单词数量（默认不限制）

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
    description: 过滤后的JSONL格式数据文件
tag: 过滤与筛选

---

## 功能概述

该算子根据文本的单词数量进行过滤，保留单词数在指定范围内的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码 |
| tokenization | bool | 否 | False | 是否使用分词模型 |
| min_num | int | 否 | 10 | 最小单词数量 |
| max_num | int | 否 | 2147483647 | 最大单词数量 |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段需要计算单词数的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
# 英语单词数量过滤
python scripts/run_words_num_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_num 5 \
  --max_num 15

# 中文单词数量过滤
python scripts/run_words_num_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --tokenization \
  --min_num 10 \
  --max_num 25
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en）
- `--tokenization`: 是否使用分词模型
- `--min_num`: 最小单词数量（默认10）
- `--max_num`: 最大单词数量（默认不限制）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 是批处理算子，可适当调整 batch_size 提高效率
2. 中文处理建议开启 `tokenization`