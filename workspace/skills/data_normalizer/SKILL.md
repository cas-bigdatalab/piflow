---
name: data_normalizer
description: '数值标准化工具。读取JSONL数据，按指定字段执行Z-score或Min-Max标准化，并保留原始值与变更标记。

  当用户提到数值标准化、归一化、字段规整、范围映射等需求时使用此skill。

  即使用户没有明确说出"data_normalizer"，只要任务涉及对某个数值字段做标准化处理，就应该使用此skill。

  不负责四舍五入/小数位统一（见DC3_RoundOff）、文本清洗、类别编码或多字段联合统计分析。

  '
name_zh: 数据标准化算子
input_params:
- name: input
  type: string
  required: true
  description: 输入JSONL文件路径
- name: output
  type: string
  required: true
  description: 输出JSONL文件路径
- name: field
  type: string
  required: true
  description: 要标准化的字段名
- name: method
  type: string
  required: true
  description: 标准化方法：z_score/min_max
- name: new_min
  type: string
  required: false
  default: "0"
  description: min_max的目标最小值
- name: new_max
  type: string
  required: false
  default: "1"
  description: min_max的目标最大值
- name: log_file
  type: string
  required: false
  description: 日志文件路径
output_params:
- name: output
  type: jsonl_file
  description: 标准化后的JSONL文件
- name: log_file
  type: json_file
  description: 可选日志文件
tag: 标准化
---

# data_normalizer 数据标准化 Skill

## 功能概述

本 skill 对 JSONL 中的单一数值字段进行标准化处理，支持 Z-score 标准化和 Min-Max 归一化两种方式。
它会在保留原始值的同时写回标准化结果，并为每条命中的记录补充变更标记。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 数值标准化
- 归一化
- 字段规整
- 范围映射
- Z-score 变换

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSONL文件路径 |
| `--output` | 输出JSONL文件路径 |
| `--field` | 要标准化的字段名 |
| `--method` | 标准化方法 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--new_min` | Min-Max 目标最小值 | `0` |
| `--new_max` | Min-Max 目标最大值 | `1` |
| `--log_file` | 日志文件路径 | - |

## 输入文件格式

```jsonl
{"id": 1, "score": 87.65}
{"id": 2, "score": 120}
{"id": 3, "score": -5}
```

输入必须是 JSONL，每行是一条 JSON 记录。
目标字段应为可转成数值的字段；无法转换的值会被跳过。

## 使用方法

### Z-score 标准化
```bash
python scripts/run_data_normalizer.py \
  --input ./input.jsonl \
  --output ./output.jsonl \
  --field score \
  --method z_score
```

### Min-Max 归一化到 [0, 100]
```bash
python scripts/run_data_normalizer.py \
  --input ./input.jsonl \
  --output ./output.jsonl \
  --field score \
  --method min_max \
  --new_min 0 \
  --new_max 100
```

## 输出示例

每条被处理记录会增加以下字段：
- `_{field}_normalized`: true
- `_{field}_original`: 原始值

示例输出：
```jsonl
{"id": 1, "score": 0.44, "_score_normalized": true, "_score_original": 87.65}
```

## 环境要求

- Python 3.x
- 只依赖标准库

## 注意事项

1. 只处理可转为数值的字段值。
2. `z_score` 会按当前样本整体均值和标准差计算。
3. `min_max` 在所有值相等时会统一映射为 `new_min`。
4. 小数位统一 / 四舍五入需求请使用 DC3_RoundOff。

