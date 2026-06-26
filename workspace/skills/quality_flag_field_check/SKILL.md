---
name: quality_flag_field_check
description: |
  质量标识字段检测工具。检查数据表是否配置质量标识字段，验证标识字段的存在性、值规范性
  （是否为预定义合法值）、非空完整性，标记不合格数据。
  当用户提到质量标识检查、QC字段检测、标识字段合规等需求时使用此skill。
name_zh: 质量标识字段检测算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: flag_field_name
    type: string
    required: true
    description: 质量标识字段名
  - name: valid_values
    type: string
    required: false
    description: 合法值，逗号分隔（如 PASS,FAIL,WARN）
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

# quality_flag_field_check 质量标识字段检测Skill

## 功能概述

对应功能说明(二)模块中的标识符检测需求。三步检查：(1) 字段存在性——指定质量标识列是否存在；(2) 空值检测——标识字段是否为空；(3) 值规范性——标识值是否在预定义合法值列表中。

## 处理逻辑

1. 读取输入数据表
2. 检查 flag_field_name 是否存在于表列中
3. 若存在：检查空值、检查值是否在 valid_values 中
4. 若不存在：全部行标记为问题
5. 输出带质控标识的结果文件

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/quality_flag_field_check.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    --flag_field_name "qc_flag" \
    --valid_values "PASS,FAIL,WARN" \
    --qc_mark QC0009
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--flag_field_name` | 是 | 质量标识字段名 |
| `--valid_values` | 否 | 合法值（逗号分隔），不填则只检查存在性和非空 |
| `--qc_mark` | 是 | 质控标识 |
| `--mark_field_name` | 否 | 质控标识字段名（默认QC0000） |

## 输出示例

```
[QC FAIL] 质量标识字段校验未通过 (2 项问题):
  [空值] 字段 'quality_flag' 有 1 行空值
  [非法值] 字段 'quality_flag' 有 1 行不在合法值 ['PASS', 'FAIL', 'WARN'] 中，示例: ['UNKNOWN']
[OK] 结果已写入 -> output.csv
```

## 注意事项

1. 若未指定 valid_values，只检查字段存在性和非空，不检查值的具体内容
2. 空值（NA/NaN/None）单独统计为 [空值] 类别
3. 字段缺失时所有行标记为不合格
