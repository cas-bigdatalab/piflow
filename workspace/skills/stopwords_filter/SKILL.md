---
name: stopwords_filter
description: |
  停用词过滤器。过滤以保持停止词比率大于特定最小值的样本。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到停用词过滤、停用词比例过滤、文本质量过滤、停用词占比检测等需求时使用此skill。

name_zh: 停用词过滤器算子
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
    description: 语言代码（支持 en, zh, all 等）

  - name: tokenization
    type: bool
    required: false
    default: false
    description: 是否使用模型进行分词（中文建议开启）

  - name: min_ratio
    type: float
    required: false
    default: 0.3
    description: 最小停用词比例

  - name: use_words_aug
    type: bool
    required: false
    default: false
    description: 是否使用词语增强（中文建议开启）

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

该算子根据停用词在文本中的比例进行过滤，保留停用词比例大于指定最小值的样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| lang | string | 否 | 'en' | 语言代码，影响停用词表和分词方式 |
| tokenization | bool | 否 | False | 是否使用模型进行分词（中文建议开启） |
| min_ratio | float | 否 | 0.3 | 最小停用词比例 |
| use_words_aug | bool | 否 | False | 是否使用词语增强（中文建议开启） |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段需要检测停用词比例的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
# 英语停用词过滤
python scripts/run_stopwords_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang en \
  --min_ratio 0.3

# 中文停用词过滤（建议开启 tokenization 和 use_words_aug）
python scripts/run_stopwords_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --lang zh \
  --tokenization \
  --use_words_aug \
  --min_ratio 0.2
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--lang`: 语言代码（默认 en，支持 en, zh, all 等）
- `--tokenization`: 是否使用分词模型（中文建议开启）
- `--min_ratio`: 最小停用词比例（默认0.3）
- `--use_words_aug`: 是否使用词语增强（中文建议开启）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 停用词比例 = 停用词数量 / 总词数
2. 中文处理建议开启 `tokenization` 和 `use_words_aug`
3. 处理大量数据时可适当增加 num_proc 提高效率