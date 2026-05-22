---
name: mixture_formatter
description: |
  混合格式化器。该类通过从每个数据集中随机选择样本并合并它们来混合多个数据集，然后将合并的数据集导出为新的混合数据集。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到混合数据集、合并多个数据集、数据集混合、数据融合等需求时使用此skill。

name_zh: 混合格式化器算子
input_params:
  - name: dataset_path
    type: string
    required: true
    description: 数据集路径，支持带权重格式（如 "0.7 path1 0.3 path2"）

  - name: output_path
    type: string
    required: true
    description: 输出JSONL文件路径

  - name: suffixes
    type: list
    required: false
    description: 指定后缀列表

  - name: text_keys
    type: list
    required: false
    default: "['text']"
    description: 文本字段名列表

  - name: add_suffix
    type: bool
    required: false
    default: false
    description: 是否添加文件后缀信息

  - name: max_samples
    type: int
    required: false
    description: 混合数据集最大样本数

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output
    type: jsonl_file
    description: 混合后的JSONL数据集文件
tag: 格式转换

---

## 功能概述

该算子用于混合多个数据集，通过从每个数据集中按权重随机选择样本并合并，生成新的混合数据集。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| dataset_path | string | 是 | - | 数据集路径，支持带权重格式 |
| output_path | string | 是 | - | 输出JSONL文件路径 |
| suffixes | list | 否 | None | 指定后缀列表 |
| text_keys | list | 否 | ['text'] | 文本字段名列表 |
| add_suffix | bool | 否 | False | 是否添加文件后缀信息 |
| max_samples | int | 否 | None | 混合数据集最大样本数 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

`dataset_path` 支持以下格式：
- 单个文件：`/path/to/data.jsonl`
- 单个目录：`/path/to/data_directory`
- 带权重格式：`<权重1> 路径1 <权重2> 路径2 ...`

例如：`/path/to/dataset1.jsonl 0.5 /path/to/dataset2.jsonl 0.5`

## 输出数据格式

输出为 JSONL 格式，每行一个样本。

## 使用示例

### 命令行调用

```bash
# 混合两个数据集，等权重
python scripts/run_mixture_formatter.py \
  --dataset_path "/path/to/dataset1.jsonl /path/to/dataset2.jsonl" \
  --output_path /path/to/output.jsonl

# 带权重的混合
python scripts/run_mixture_formatter.py \
  --dataset_path "0.7 /path/to/dataset1.jsonl 0.3 /path/to/dataset2.jsonl" \
  --output_path /path/to/output.jsonl

# 限制最大样本数
python scripts/run_mixture_formatter.py \
  --dataset_path "/path/to/dataset1.jsonl /path/to/dataset2.jsonl" \
  --output_path /path/to/output.jsonl \
  --max_samples 10000
```

### 参数说明

- `--dataset_path`: 数据集路径，支持空格分隔的多个路径和权重
- `--output_path`: 输出JSONL文件路径
- `--suffixes`: 目标后缀
- `--text_keys`: 文本字段名
- `--add_suffix`: 是否添加文件后缀
- `--max_samples`: 最大样本数
- `--num_proc`: 并行进程数

## 注意事项

1. 权重格式：`<权重> 路径`，权重可选，不指定时默认为1.0
2. 样本按权重比例分配，总和可能不等于 max_samples
3. 每个数据集的样本是随机选择的