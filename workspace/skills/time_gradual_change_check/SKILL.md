---
name: time_gradual_change_check
description: |
  时序平缓性检测工具。检测时序数据是否符合渐变规律，包括突变跳点检测（相邻点变化超阈值）
  和方向振荡检测（窗口内反复升降），对应功能说明(八)模块中的平缓性检测维度。
  当用户提到时序平缓性、渐变规律、突变跳点、方向振荡等需求时使用此skill。
name_zh: 时间平缓性检测算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: check_field
    type: string
    required: true
    description: 检测字段名
  - name: time_field
    type: string
    required: true
    description: 时间字段名
  - name: time_format
    type: string
    required: true
    description: 时间格式（如 %Y-%m-%d %H:%M:%S）
  - name: jump_threshold
    type: string
    required: false
    description: 突变跳点阈值
  - name: window_size
    type: string
    required: false
    default: "5"
    description: 振荡检测窗口大小
  - name: oscillation_limit
    type: string
    required: false
    default: "2"
    description: 窗口内允许的最大反转次数
  - name: qc_mark
    type: string
    required: true
    description: 质控标识
  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质控标识字段名
output_params:
  - name: output_path
    type: csv_file
    description: 带质控标识的输出文件
tag: 校验
---

# time_gradual_change_check 时序平缓性检测Skill

## 功能概述

与 QC13（恒定值检测）互补的平缓性检测。两项检查：(1) 突变跳点——相邻时间点的变化幅度超过 jump_threshold；(2) 方向振荡——滑动窗口内数值升降反转次数超过 oscillation_limit。

## 处理逻辑

1. 读取输入数据表，按时间字段排序
2. 计算相邻点的一阶差分
3. 突变跳点：标记 |Δ| > jump_threshold 的点及前一个点
4. 方向振荡：滑动窗口内统计符号变化次数，超限则标记整个窗口
5. 输出带质控标识的结果文件

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/time_gradual_change_check.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --check_field temperature \
    --time_field timestamp \
    --time_format "%Y-%m-%d %H:%M:%S" \
    --jump_threshold 10.0 \
    --qc_mark QC0017 \
    --mark_field_name QC0000
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--check_field` | 是 | 检测字段 |
| `--time_field` | 是 | 时间字段 |
| `--time_format` | 是 | 时间格式 |
| `--jump_threshold` | 否 | 突变阈值（不设则不检测跳点） |
| `--window_size` | 否 | 振荡窗口（默认5） |
| `--oscillation_limit` | 否 | 窗口最大反转次数（默认2） |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名 |

## 输出示例

```
[QC FAIL] 时序平缓性检测未通过 (2 项问题):
  [突变跳点] 1 处相邻变化超过阈值 20.0
  [方向振荡] 存在振荡异常（5 点窗口内反转超过 1 次），共标记 6 个数据点
[OK] 结果已写入 -> output.csv
```

## 注意事项

1. 数据按时间字段排序后再检测
2. jump_threshold 不设则不检测跳点（只检测振荡）
3. 与 QC10_TimeConsistency（变化率）互补：QC17 侧重于变化幅度的平滑性而非速度
