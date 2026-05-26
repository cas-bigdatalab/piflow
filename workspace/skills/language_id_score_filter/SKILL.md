---
name: language_id_score_filter
description: |
  语言识别分数过滤器。过滤器以保留置信度得分大于特定最小值的特定语言的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到语言识别过滤、语言检测、文本语言筛选、按语言过滤等需求时使用此skill。

name_zh: 语言识别分数过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径（JSON/JSONL格式）

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径（JSONL格式）

  - name: lang
    type: string
    required: false
    default: ""
    description: 指定语言代码，可重复指定多个（为空则保留所有语言）

  - name: min_score
    type: float
    required: false
    default: 0.8
    description: 最小语言识别置信度分数

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output_path
    type: jsonl_file
    description: 过滤后的JSONL文件，包含指定语言且置信度达标的样本
tag: 过滤与筛选

---

## 功能概述

该算子使用 FastText 模型识别文本语言，过滤保留指定语言的样本，且置信度分数需大于最小阈值。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string/list | 否 | '' | 指定语言，可为单个语言字符串如 'en'，或列表如 ['en', 'zh']，为空则保留所有语言 |
| min_score | float | 否 | 0.8 | 最小语言识别置信度分数 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段中文文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
# 过滤英语文本
python scripts/run_language_id_score_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --min_score 0.8

# 过滤多种语言
python scripts/run_language_id_score_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --lang zh \
  --min_score 0.8
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 指定语言代码，可重复指定多个语言（默认为空，保留所有语言）
- `--min_score`: 最小置信度分数（默认0.8）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 该算子使用 FastText 模型进行语言识别
2. 支持的语言代码如：'en'(英语), 'zh'(中文), 'ja'(日语), 'ko'(韩语) 等
3. 当 lang 为空时，只根据 min_score 进行过滤
4. 处理大量数据时可适当增加 num_proc 提高效率