---
name: word_repetition_filter
description: |
  单词重复比例过滤器。过滤器将单词级n-gram重复比率的样本保持在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到单词重复过滤、文本重复比例过滤、n-gram重复过滤、清理重复内容等需求时使用此skill。
---

## 功能概述

该算子计算单词级 n-gram 重复比率，过滤保留重复比率在指定范围内的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码 |
| tokenization | bool | 否 | False | 是否使用分词模型 |
| rep_len | int | 否 | 10 | n-gram 重复长度 |
| min_ratio | float | 否 | 0.0 | 最小重复比率 |
| max_ratio | float | 否 | 0.5 | 最大重复比率 |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段需要检测重复比例的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
# 英语单词重复过滤
python scripts/run_word_repetition_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --rep_len 3 \
  --min_ratio 0.0 \
  --max_ratio 0.2

# 中文单词重复过滤
python scripts/run_word_repetition_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --tokenization \
  --rep_len 3 \
  --min_ratio 0.0 \
  --max_ratio 0.2
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en）
- `--tokenization`: 是否使用分词模型
- `--rep_len`: n-gram 重复长度（默认10）
- `--min_ratio`: 最小重复比率（默认0.0）
- `--max_ratio`: 最大重复比率（默认0.5）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 是批处理算子，可适当调整 batch_size 提高效率
2. 中文处理建议开启 `tokenization`