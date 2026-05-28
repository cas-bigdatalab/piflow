---
name: remote_formatter
description: |
  远程格式化器。用于从huggingface hub的存储库加载数据集。
  本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用以下指令进行安装：
  pip install py-data-juicer
  
  当用户提到加载HuggingFace数据集、远程数据集加载、HuggingFace Hub等需求时使用此skill。

name_zh: 远程格式化器算子
input_params:
  - name: dataset_path
    type: string
    required: true
    description: HuggingFace数据集路径（如 "rotten_tomatoes"）

  - name: output_path
    type: string
    required: true
    description: 输出JSONL文件路径

  - name: text_keys
    type: list
    required: false
    default: ['text']
    description: 文本字段名列表

  - name: split
    type: string
    required: false
    default: train
    description: 数据集划分

  - name: num_proc
    type: int
    required: false
    default: 1
    description: 并行处理的进程数

output_params:
  - name: output_path
    type: jsonl_file
    description: 输出的JSONL格式数据集文件
tag: 格式转换

---

## 功能概述

该算子用于从 HuggingFace Hub 加载数据集，支持加载公开数据集和需要认证的私有数据集。

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| dataset_path | string | 是 | - | HuggingFace数据集路径 |
| output_path | string | 是 | - | 输出JSONL文件路径 |
| text_keys | list | 否 | ['text'] | 文本字段名列表 |
| split | string | 否 | 'train' | 数据集划分 |
| num_proc | int | 否 | 1 | 并行处理的进程数 |

## 输入数据格式

`dataset_path` 支持以下格式：
- 公开数据集：`username/dataset_name`
- 本地路径或远程路径

## 输出数据格式

输出为 JSONL 格式，每行一个样本。

## 使用示例

### 命令行调用

```bash
# 加载HuggingFace公开数据集
python scripts/run_remote_formatter.py \
  --dataset_path "rotten_tomatoes" \
  --output_path /path/to/output.jsonl

# 指定文本字段
python scripts/run_remote_formatter.py \
  --dataset_path "yelp_review_full" \
  --output_path /path/to/output.jsonl \
  --text_keys text \
  --split train

# 带认证加载私有数据集
python scripts/run_remote_formatter.py \
  --dataset_path "private_user/private_dataset" \
  --output_path /path/to/output.jsonl
```

### 参数说明

- `--dataset_path`: HuggingFace数据集路径
- `--output_path`: 输出JSONL文件路径
- `--text_keys`: 文本字段名，可重复指定多个（默认 ['text']）
- `--split`: 数据集划分（默认 'train'）
- `--num_proc`: 并行进程数，默认1

## 注意事项

1. 首次运行会下载数据集，可能需要较长时间
2. 对于私有数据集，需要先登录 HuggingFace：`huggingface-cli login`
3. 支持的数据集格式由 HuggingFace datasets 库决定