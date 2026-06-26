---
name: batch_data_splitter
description: |
  批量数据均匀分片工具。读取json/jsonl/csv输入，按份数或固定条数切成多个子文件，输出一个清单JSON供下游节点消费。
  当用户提到数据分割、批量拆分、数据分片、均匀分块等需求时使用此skill。
  即使用户没有明确说出"分片"，只要任务是把整份批量数据均匀拆成多个文件，就应该使用此skill。
  不负责按字段分组导出或随机采样。

name_zh: 批量数据均匀分割算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持json/jsonl/csv）

  - name: output_dir
    type: string
    required: true
    description: 分割结果输出目录路径

  - name: num_splits
    type: string
    required: false
    default: "0"
    description: 分割份数（0表示按chunk_size分割）

  - name: chunk_size
    type: string
    required: false
    default: "1000"
    description: 每份样本数量

  - name: output_prefix
    type: string
    required: false
    default: split
    description: 输出文件名前缀

  - name: shuffle
    type: string
    required: false
    default: "False"
    description: 是否打乱顺序后分割

  - name: random_seed
    type: string
    required: false
    default: "42"
    description: 随机种子（shuffle时使用）

output_params:
  - name: output_dir
    type: file
    default: output_manifest.json
    description: 分割结果清单文件路径（JSON，含 splits_dir/output_files/total_count/actual_num_splits/samples_per_split）

tag: 切分与采样
---

# Batch Data Splitter 批量数据均匀分割 Skill

## 功能概述

本skill面向大容量批量数据集进行均等分割，可设定分割份数或单份样本容量，将整体数据集均匀划分为多组子数据集。
无差别平均分配原始样本，保持各组数据分布一致性，适配流水线分批运算、多任务并行处理、数据分库存储等业务场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 批量拆分
- 数据分片
- 均匀划分
- 按份数切块
- 按固定条数切块

## 核心参数说明

### 必需参数
- `--input`：输入文件路径
- `--output_dir`：输出清单文件路径（JSON），实际分割文件写入同名 `_splits/` 子目录

### 可选参数
- `--num_splits`：分割份数，默认 0（0 表示按 chunk_size 分割）
- `--chunk_size`：每份样本数量，默认 1000
- `--output_prefix`：输出文件名前缀，默认 `split`
- `--shuffle`：是否打乱顺序，默认 false
- `--random_seed`：随机种子，默认 42

## 输入文件格式

支持 `json`、`jsonl`、`csv`。

## 使用方法

### 按份数分割
```bash
python scripts/run_batch_data_splitter.py \
  --input corpus.csv \
  --output_dir ./splits_manifest.json \
  --num_splits 10
```

### 按每份数量分割
```bash
python scripts/run_batch_data_splitter.py \
  --input corpus.csv \
  --output_dir ./splits_manifest.json \
  --chunk_size 5000
```

### 打乱后分割
```bash
python scripts/run_batch_data_splitter.py \
  --input corpus.csv \
  --output_dir ./splits_manifest.json \
  --num_splits 5 \
  --shuffle true
```

## 输出示例

```
[OK] Batch data splitting completed!
   Input file: corpus.csv
   Total samples: 11
   Number of splits: 4
   Samples per split: [3, 3, 3, 2]
   Manifest file: ./splits_manifest.json
   Splits directory: ./splits_manifest_splits
   Output files:
     - split_001.csv (3 samples)
     - split_002.csv (3 samples)
     - split_003.csv (3 samples)
     - split_004.csv (2 samples)
```

## 环境要求

- Python 3.x
- 标准库即可运行

## 注意事项

1. 如果总数不能整除，最后一份可能样本数较少。
2. `num_splits` 优先级高于 `chunk_size`。
3. 当 `num_splits` 大于总样本数时，会自动收敛为最多生成 `total_count` 份。
4. 输出文件名格式：`{prefix}_{序号}.{扩展名}`。
5. `--output_dir` 指定的是清单 JSON 文件路径，实际分割文件写入同名 `_splits/` 子目录，是引擎下游节点可消费的单文件输出。
6. 这里只做均匀分片，不做比例拆分或分层保持。
