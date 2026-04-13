---
name: special_characters_filter
description: |
  特殊字符过滤器。过滤器将具有特殊字符比率的样品保持在特定范围内。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到特殊字符过滤、特殊字符比例过滤、文本特殊字符检测、清理乱码文本等需求时使用此skill。
---

## 功能概述

该算子用于过滤特殊字符比例在指定范围内的文本样本。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| min_ratio | float | 否 | 0.0 | 最小特殊字符比例 |
| max_ratio | float | 否 | 0.25 | 最大特殊字符比例 |
| batch_size | int | 否 | 1 | 批处理大小 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含 `text` 字段：

```json
{"text": "这是一段包含特殊字符的文本内容"}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，仅包含 text 字段。

## 使用示例

### 命令行调用

```bash
python scripts/run_special_characters_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --min_ratio 0.0 \
  --max_ratio 0.25
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--min_ratio`: 最小特殊字符比例（默认0.0）
- `--max_ratio`: 最大特殊字符比例（默认0.25）
- `--batch_size`: 批处理大小（默认1）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 特殊字符包括：，。、„""«»１」「《》´∶：？！"（）"；–—．～'…━〈〉【】％► 等
2. 比例计算方式：特殊字符数 / 总字符数
3. 处理大量数据时可适当增加 batch_size 和 num_proc 提高效率