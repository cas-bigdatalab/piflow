---
name: text_action_filter
description: |
  文本动作词过滤器。过滤以保留文本中包含操作的文本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到动作词过滤、动词检测、文本动作过滤、文本操作词过滤等需求时使用此skill。
---

## 功能概述

该算子使用 spaCy 模型检测文本中的动作词（动词），过滤保留动作词数量大于指定最小值的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码：'en' 或 'zh' |
| min_action_num | int | 否 | 1 | 最小动作词数量 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "Tom is playing piano."}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本。

## 使用示例

### 命令行调用

```bash
# 英语动作词过滤
python scripts/run_text_action_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --min_action_num 1

# 中文动作词过滤
python scripts/run_text_action_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --min_action_num 1
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en，仅支持 en 和 zh）
- `--min_action_num`: 最小动作词数量（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 该算子使用 spaCy 模型进行动作词检测
2. 需要安装 spacy-pkuseg（pip install spacy-pkuseg）
3. 仅支持英语(en)和中文(zh)