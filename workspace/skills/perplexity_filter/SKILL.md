---
name: perplexity_filter
description: |
  困惑度过滤器。过滤以保留困惑度分数小于特定最大值的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到困惑度过滤、文本困惑度检测、语言模型分数过滤、文本质量过滤等需求时使用此skill。
---

## 功能概述

该算子使用语言模型（KenLM）计算文本的困惑度分数，过滤保留困惑度在指定范围内的样本。低困惑度表示文本流畅自然。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码（影响分词和语言模型） |
| max_ppl | float | 否 | 1500 | 最大困惑度阈值（低于此值保留） |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段需要检测困惑度的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
# 英语文本困惑度过滤
python scripts/run_perplexity_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --max_ppl 900

# 中文文本困惑度过滤
python scripts/run_perplexity_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --max_ppl 1500
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en，支持 en, zh 等）
- `--max_ppl`: 最大困惑度阈值（默认1500）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 该算子使用 sentencepiece 进行分词，kenlm 计算困惑度
2. 低困惑度表示文本流畅自然，高困惑度可能表示文本混乱或随机
3. 支持的语言包括：en, zh 等
4. 处理大量数据时可适当增加 batch_size 和 num_proc 提高效率