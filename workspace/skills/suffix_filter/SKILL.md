---
name: suffix_filter
description: |
  后缀过滤器。过滤器以保留具有指定后缀的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到后缀过滤、文件类型过滤、按文件后缀筛选等需求时使用此skill。

name_zh: 后缀过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: suffixes
    type: list
    required: false
    default: []
    description: 目标后缀列表，如 ['.txt', '.pdf']

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件，保持原始字段结构
tag: 过滤与筛选

---

## 功能概述

该算子根据样本的 `suffix` 字段值进行过滤，保留后缀在目标列表中的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| suffixes | list | 否 | [] | 目标后缀列表，如 ['.txt', '.pdf'] |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `suffix` 字段：

```json
{"text": "文本内容", "suffix": ".txt"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，保持原始字段结构。

## 使用示例

### 命令行调用

```bash
# 过滤保留 .txt 和 .pdf 后缀的样本
python scripts/run_suffix_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --suffixes .txt \
  --suffixes .pdf

# 不指定后缀则保留所有样本
python scripts/run_suffix_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--suffixes`: 目标后缀，可重复指定多个（默认为空，保留所有）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. `suffix` 字段用于标识文件类型/后缀
2. 这是 `NON_STATS_FILTERS`，不需要计算统计信息，处理效率较高
3. 如果不指定 suffixes，则保留所有样本