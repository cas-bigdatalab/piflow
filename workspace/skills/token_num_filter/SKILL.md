---
name: token_num_filter
description: |
  Token数量过滤器。筛选器将总令牌数的样本保留在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到token数量过滤、文本token数筛选、按token数过滤、文本分词过滤等需求时使用此skill。

name_zh: Token数量过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: hf_tokenizer
    type: string
    required: false
    default: EleutherAI/pythia-6.9b-deduped
    description: HuggingFace tokenizer 模型

  - name: min_num
    type: int
    required: false
    default: 10
    description: 最小 token 数量

  - name: max_num
    type: int
    required: false
    description: 最大 token 数量（默认不限制）

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数
  - name: text_key
    type: string
    required: false
    default: text
    description: 要操作的文本字段名


output_params:
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件
tag: 过滤与筛选

---

## 功能概述

该算子使用 HuggingFace tokenizer 计算文本的 token 数量，过滤保留 token 数在指定范围内的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| hf_tokenizer | string | 否 | 'EleutherAI/pythia-6.9b-deduped' | HuggingFace tokenizer 模型 |
| min_num | int | 否 | 10 | 最小 token 数量 |
| max_num | int | 否 | 2147483647 | 最大 token 数量 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |
| text_key | string | 否 | text | 要操作的文本字段名 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text_key` 指定的字段（默认 `text`）：

```json
{"<text_key>": "这是一段需要计算token数的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
python scripts/run_token_num_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_num 10 \
  --max_num 20
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--hf_tokenizer`: HuggingFace tokenizer 模型
- `--min_num`: 最小 token 数量（默认10）
- `--max_num`: 最大 token 数量（默认不限制）
- `--num_proc`: 并行进程数，默认1
- `--text_key`: 要操作的文本字段名（默认text）

## 注意事项

1. 该算子使用 HuggingFace tokenizer 计算 token 数量
2. 不同 tokenizer 对同一文本可能产生不同的 token 数
3. 处理大量数据时可适当增加 num_proc 提高效率