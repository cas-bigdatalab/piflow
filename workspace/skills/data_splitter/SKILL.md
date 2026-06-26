---
name: data_splitter
description: 'JSONL比例切分工具。读取JSONL数据集，按给定比例拆成多个子集，支持随机切分和按字段分层切分。

  当用户明确提到按比例拆分JSONL、训练集/验证集/测试集切分、分层保持类别分布等需求时使用此skill。

  即使用户没有明确说出"切分"，只要任务是把一份JSONL按比例分成多个子集，就应该使用此skill。

  不负责按固定条数均匀分块，不负责按份数切块，也不负责处理非JSONL输入。

  '
name_zh: 数据分割算子
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: outputs
  type: string
  required: true
  description: 输出文件路径，逗号分隔
- name: ratios
  type: string
  required: true
  description: 分割比例，逗号分隔（如0.7,0.2,0.1）
- name: stratify_field
  type: string
  required: false
  default: ''
  description: 分层字段（用于分层分割）
- name: seed
  type: string
  required: false
  default: "42"
  description: 随机种子
- name: log_file
  type: string
  required: false
  default: ''
  description: 日志文件路径
output_params:
- name: outputs
  type: list
  description: 分割后的数据子集
- name: split_stats
  type: object
  description: 分割统计信息
tag: 切分与采样
---

# Data Splitter 数据分割 Skill

## 功能概述

本skill用于将JSONL数据集按比例拆分为多个子集，支持：
- **随机切分**：打乱后按比例拆分
- **分层切分**：按指定字段保持类别分布一致

## 触发条件

当用户请求以下任务时，应使用此skill：
- 按比例拆分JSONL
- 训练集/验证集/测试集拆分
- 数据集切分
- 分层切分
- JSONL样本拆分

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSONL文件路径 |
| `--outputs` | 输出文件路径，逗号分隔 |
| `--ratios` | 分割比例，逗号分隔 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stratify_field` | 分层字段 | 空 |
| `--seed` | 随机种子 | `42` |
| `--log_file` | 日志文件路径 | 空 |

## 输入文件格式

```jsonl
{"id": 1, "category": "A", "text": "样本1"}
{"id": 2, "category": "A", "text": "样本2"}
{"id": 3, "category": "B", "text": "样本3"}
{"id": 4, "category": "C", "text": "样本4"}
```

## 使用方法

### 随机切分
```bash
python scripts/run_data_splitter.py \
  --input data.jsonl \
  --outputs train.jsonl,valid.jsonl,test.jsonl \
  --ratios 0.7,0.2,0.1 \
  --seed 42
```

### 分层切分
```bash
python scripts/run_data_splitter.py \
  --input data.jsonl \
  --outputs train.jsonl,valid.jsonl,test.jsonl \
  --ratios 0.7,0.2,0.1 \
  --stratify_field category \
  --seed 42
```

## 输出示例

```text
[OK] Data splitting completed
   [train.jsonl] 7 records (70.0%)
   [valid.jsonl] 2 records (20.0%)
   [test.jsonl] 1 records (10.0%)
   Input: data.jsonl
   Total records: 10
   Split ratios: [0.7, 0.2, 0.1]
   Stratified: True
   Stratify field: category
   Random seed: 42
```

## 环境要求

```bash
python scripts/run_data_splitter.py --help
```

## 注意事项

1. `--outputs` 的数量必须与 `--ratios` 一致。
2. `--ratios` 的总和建议为 1.0。
3. 分层切分适合类别不平衡数据，但小样本类别仍可能受整数取整影响。
4. 输入必须是 JSONL，每行一个 JSON 对象。
