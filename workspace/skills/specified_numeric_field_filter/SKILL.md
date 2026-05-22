---
name: specified_numeric_field_filter
description: |
  指定数值字段过滤器。根据指定的数值字段信息进行筛选。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到数值字段过滤、字段范围筛选、数值范围过滤、元数据数值过滤、按数值过滤等需求时使用此skill。

name_zh: 指定数值字段过滤器算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入数据文件路径 (JSON/JSONL格式)

  - name: output_path
    type: string
    required: true
    description: 输出数据文件路径 (JSONL格式)

  - name: field_key
    type: string
    required: true
    description: 字段路径，用点号分隔，如 'meta.star'

  - name: min_value
    type: float
    required: false
    description: 最小值（默认不限）

  - name: max_value
    type: float
    required: false
    description: 最大值（默认不限）

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output
    type: jsonl_file
    description: 过滤后的JSONL格式数据文件，保持原始字段结构
tag: 过滤与筛选

---

## 功能概述

该算子根据指定数值字段的值进行过滤，保留数值在指定范围内的样本。支持嵌套字段。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入数据文件路径 (JSON/JSONL格式) |
| output_path | string | 是 | - | 输出数据文件路径 (JSONL格式) |
| field_key | string | 是 | - | 字段路径，用点号分隔，如 'meta.star' 或 'meta.key1.key2.count' |
| min_value | float | 否 | -2147483648 | 最小值 |
| max_value | float | 否 | 2147483647 | 最大值 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

输入文件应为 JSON 或 JSONL 格式，每行包含一个样本，样本需包含指定的数值字段：

```json
{"text": "文本内容", "meta": {"star": 50}}
```

支持嵌套字段：
```json
{"text": "文本内容", "meta": {"key1": {"key2": {"count": 34}}}}
```

## 输出数据格式

输出为 JSONL 格式，每行一个符合条件的样本，保持原始字段结构。

## 使用示例

### 命令行调用

```bash
# 根据 meta.star 字段过滤
python scripts/run_specified_numeric_field_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --field_key meta.star \
  --min_value 10 \
  --max_value 70

# 根据嵌套字段过滤
python scripts/run_specified_numeric_field_filter.py \
  --input_path /path/to/input.jsonl \
  --output_path /path/to/output.jsonl \
  --field_key meta.key1.key2.count \
  --min_value 10 \
  --max_value 70
```

### 参数说明

- `--input_path`: 输入文件路径
- `--output_path`: 输出文件路径  
- `--field_key`: 字段路径，支持嵌套（如 meta.star）
- `--min_value`: 最小值（默认不限）
- `--max_value`: 最大值（默认不限）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. `field_key` 使用点号分隔多级字段（如 `meta.key1.key2.count`）
2. 如果字段值不能转换为数字，该样本会被过滤掉
3. 这是 `NON_STATS_FILTERS`，不需要计算统计信息，处理效率较高