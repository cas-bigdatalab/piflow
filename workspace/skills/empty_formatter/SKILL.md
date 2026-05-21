---
name: empty_formatter
description: |
  空数据格式化器。用于创建空数据。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到创建空数据集、生成空数据、初始化数据集、测试用空数据等需求时使用此skill。

input_params:
  - name: output_path
    type: string
    required: true
    description: 输出JSONL文件路径

  - name: length
    type: int
    required: false
    default: 0
    description: 空数据集长度

  - name: feature_keys
    type: list
    required: false
    default: "[]"
    description: 字段名列表

output_params:
  - name: output
    type: jsonl_file
    description: 空数据集JSONL文件
tag: 格式转换
---

## 功能概述

该算子用于创建空数据集，可指定长度和字段结构。适用于初始化、测试等场景。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| output_path | string | 是 | - | 输出JSONL文件路径 |
| length | int | 否 | 0 | 空数据集长度 |
| feature_keys | list | 否 | [] | 字段名列表 |

## 输出数据格式

输出为 JSONL 格式，每行一个样本，字段值为 null。

## 使用示例

### 命令行调用

```bash
# 创建10条空数据，无字段
python scripts/run_empty_formatter.py \
  --output_path /path/to/output.jsonl \
  --length 10

# 创建5条空数据，指定字段
python scripts/run_empty_formatter.py \
  --output_path /path/to/output.jsonl \
  --length 5 \
  --feature_keys text \
  --feature_keys label
```

### 参数说明

- `--output_path`: 输出JSONL文件路径
- `--length`: 空数据集长度（默认0）
- `--feature_keys`: 字段名，可重复指定多个（默认空）

## 注意事项

1. 创建的是包含 null 值的空数据集
2. 可用于初始化测试数据集
3. 输出格式为 JSONL