---
name: time_anomaly_marker
description: |
  时序/数值异常标记工具。对指定或全部数值列进行 Z-Score 异常和差分突变检测，
  输出 anomaly_flag 与 anomaly_reasons，不删除数据，适用于时序稳态/突变异常识别。
name_zh: time_anomaly_marker_时序异常标记算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）
  - name: output_path
    type: string
    required: true
    description: 输出文件路径（标记后的文件）
  - name: numeric_columns
    type: string
    required: false
    description: 需检测的数值列，逗号分隔；不填默认所有数值列
  - name: z_threshold
    type: string
    required: false
    description: Z-Score 阈值，默认 3.0
  - name: diff_threshold
    type: string
    required: false
    description: 差分突变阈值(倍数标准差)，默认 3.0
output_params:
  - name: output_path
    type: csv_file
    description: 包含 anomaly_flag 与 anomaly_reasons 的标记后文件
tag: 清洗
---

# time_anomaly_marker 时序/数值异常标记

## 功能概述
- 基于 Z-Score 检测全局异常值。
- 基于差分标准差检测尖峰/突变。
- 输出 anomaly_flag（布尔）与 anomaly_reasons（多条原因分号分隔）。
- 不删除数据，仅标记，便于后续复核/过滤。

## 触发条件
- 时序数据需识别稳态异常或突变异常。
- 需要为后续过滤/校验提供异常标记。

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--input_path` | 是 |  | 输入文件路径（支持CSV/TSV/Excel等） |
| `--output_path` | 是 |  | 输出文件路径（标记后的文件） |
| `--numeric_columns` | 否 |  | 需检测的数值列，逗号分隔；不填默认所有数值列 |
| `--z_threshold` | 否 |  | Z-Score 阈值，默认 3.0 |
| `--diff_threshold` | 否 |  | 差分突变阈值(倍数标准差)，默认 3.0 |

## 使用方法
```bash
python scripts/time_anomaly_marker.py \
  --input_path <输入文件> \
  --output_path <输出文件> \
  [--numeric_columns col1,col2] \
  [--z_threshold 3.0] \
  [--diff_threshold 3.0]
```

## 输出说明
- 新增列：
  - anomaly_flag: 是否命中异常
  - anomaly_reasons: 命中原因列表（分号分隔）
- 输出格式与输入一致，其余列保持不变。

## 注意事项
- 默认检测所有数值列，可通过 numeric_columns 指定。
- Z-Score 与差分阈值可按噪声水平调节。
- 对全空列/全 NaN 列自动跳过。
