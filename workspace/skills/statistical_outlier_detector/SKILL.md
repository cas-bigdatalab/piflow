---
name: statistical_outlier_detector
description: '统计与机器学习异常值检测工具。读取结构化表格数据，使用 IQR、Z-score、IsolationForest 或分组标准差一致性方法识别异常值，输出带异常标记、删除异常行或裁剪异常值后的结果文件。

  当用户提到异常值检测、离群值识别、IQR、Z-score、IsolationForest、按实验组/分类组检查数值一致性等需求时使用此skill。

  即使用户没有明确说出“statistical_outlier_detector”，只要任务涉及结构化数值字段异常识别或分组均值标准差一致性检查，就应该使用此skill。

  不负责字段固定阈值上下限校验、枚举值校验、时间序列缺失/频率校验或格式转换。

  '
name_zh: 统计与机器学习异常值检测工具
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持CSV/TSV/Excel/JSON/JSONL）
- name: output
  type: string
  required: true
  description: 输出文件路径
- name: columns
  type: string
  required: false
  default: ''
  description: 要检测的数值字段，逗号分隔；留空时使用所有数值字段
- name: method
  type: string
  required: false
  default: iqr
  description: 检测方法（iqr/zscore/isolation_forest/group_zscore）
- name: threshold
  type: string
  required: false
  default: "1.5"
  description: 阈值（IQR倍数或Z-score标准差倍数）
- name: contamination
  type: string
  required: false
  default: "0.05"
  description: IsolationForest异常比例
- name: group_columns
  type: string
  required: false
  default: ''
  description: 分组字段，group_zscore方法必填，多个字段用逗号分隔
- name: action
  type: string
  required: false
  default: mark
  description: 处理方式（mark/remove/clip）
output_params:
- name: output
  type: csv_file
  description: 处理后的数据文件
tag: 校验
---

# Statistical Outlier Detector 统计与机器学习异常值检测 Skill

## 功能概述

本skill用于结构化表格数据的离群值检验，支持统计阈值、机器学习和分组一致性三类方法。
它既能识别全局分布中的异常值，也能识别按分组字段计算后的组内偏离点。
它适合实验对比数据、分类统计数据、传感器数值表等需要数值一致性检查的场景。
它不负责固定业务上下限校验、枚举词典校验或时间序列完整性校验。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 异常值检测 / 离群值检测
- IQR / Z-score / 四分位距 / 标准差阈值识别
- Isolation Forest / 孤立森林异常识别
- 按实验组、分类组、批次组检查数值一致性
- 组内均值偏离超过标准差倍数的异常标记

## 核心参数说明

### 必需参数

- `--input`：输入文件路径
- `--output`：输出文件路径

### 可选参数

- `--columns`：要检测的数值字段，逗号分隔；留空时自动使用所有数值字段
- `--method`：检测方法，默认 `iqr`
- `--threshold`：IQR倍数或标准差倍数，默认 `1.5`
- `--contamination`：IsolationForest异常比例，默认 `0.05`
- `--group_columns`：分组字段，`group_zscore` 方法必填
- `--action`：处理方式，默认 `mark`

## 输入文件格式

支持 CSV、TSV、Excel（`.xls` / `.xlsx`）、JSON、JSONL。
`columns` 中指定的字段会先转换为数值列后再进行检测；无法转换为数值的值会被视为缺失。
`group_columns` 仅在分组一致性模式下使用，分组字段本身不参与数值检测。

## 使用方法

### IQR方法检测
```bash
python scripts/run_statistical_outlier_detector.py \
  --input data.csv \
  --output result.csv \
  --columns "value,score" \
  --method iqr \
  --threshold 1.5 \
  --action mark
```

### Z-score方法检测
```bash
python scripts/run_statistical_outlier_detector.py \
  --input data.csv \
  --output result.csv \
  --columns "value" \
  --method zscore \
  --threshold 3.0 \
  --action remove
```

### IsolationForest方法检测
```bash
python scripts/run_statistical_outlier_detector.py \
  --input data.csv \
  --output result.csv \
  --columns "value,score" \
  --method isolation_forest \
  --contamination 0.1 \
  --action mark
```

### 分组一致性检测
```bash
python scripts/run_statistical_outlier_detector.py \
  --input data.csv \
  --output result.csv \
  --columns "value" \
  --group_columns "experiment,treatment" \
  --method group_zscore \
  --threshold 2.0 \
  --action mark
```

## 输出示例

```
[OK] Outlier detection completed!
   Input file: data.csv
   Output file: result.csv
   Columns: value, score
   Method: group_zscore
   Threshold: 2.0
   Group columns: experiment, treatment
   Action: mark
   Total rows: 1000
   Total outlier rows: 62
```

## 环境要求

```bash
pip install pandas scipy scikit-learn
```

## 注意事项

1. `iqr`、`zscore`、`group_zscore` 支持 `mark`、`remove`、`clip`，`isolation_forest` 仅支持 `mark` 和 `remove`。
2. `group_zscore` 需要提供 `group_columns`，否则无法计算组内均值和标准差。
3. `columns` 为空时会自动选择所有数值列，但仍会忽略无法转为数值的字段。
4. `mark` 模式会新增 `is_outlier` 和字段级异常标记列；`remove` 模式会删除异常行；`clip` 模式会截断异常数值。
5. 这是统一的离群检验 skill，不再拆分为独立的机器学习异常行检测 skill。
