---
name: v1_FormatConsistency
description: |
  格式一致性校验工具。读取被检验表和标准化数据模式表，比对两者的表头结构（字段名、字段数量）是否一致，
  校验通过后输出数据文件。当用户提到格式一致性校验、表头校验、数据结构比对、字段一致性检查等需求时使用此skill。
  即使用户没有明确说出"格式一致性"，只要任务涉及比对数据表结构与标准模式结构，就应该使用此skill。

name_zh: v1_格式一致性校验算子
input_params:
  - name: original_path
    type: string
    required: true
    description: 被检验表文件路径（需要校验的文件）

  - name: standard_path
    type: string
    required: true
    description: 标准化数据模式表路径（包含正确字段结构）

  - name: output_path
    type: string
    required: true
    description: 校验通过后输出文件路径

output_params:
  - name: output_path
    type: csv_file
    description: 格式一致性校验通过后的结构化数据文件
tag: 校验

---

# v1_FormatConsistency 格式一致性校验Skill

## 功能概述

本skill用于将被检验表的数据表结构与标准化数据模式结构进行比对校验，确保表头（字段名、字段数量）完全一致，校验通过后输出数据文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 格式一致性校验
- 表头校验
- 数据结构比对
- 字段一致性检查
- 校验数据表与标准模式是否一致

## 校验规则

1. **字段数量**：被检验表与标准表的字段数量必须一致
2. **字段名称**：字段名称必须完全匹配（区分大小写）
3. **字段顺序**：字段顺序必须与标准表一致

如果校验失败，脚本会抛出异常并显示具体的不匹配字段信息。

## 输入文件说明

### 被检验表 (original_path)
需要校验的数据文件，支持CSV、TSV、Excel、SPSS等格式。

### 标准模式表 (standard_path)
标准化的数据模式表，包含正确的字段结构（字段名、字段顺序）。

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 被检验表路径（需要校验的文件）
2. 标准模式表路径（包含正确字段结构）
3. 输出文件路径（校验通过后的数据）

### 步骤2：执行格式一致性校验脚本

在 `scripts/` 目录下找到 `v1_FormatConsistency.py`，使用Python执行：

```bash
python scripts/v1_FormatConsistency.py --original_path <被检验表> --standard_path <标准模式表> --output_path <输出文件>
```

### 步骤3：返回结果

- 校验通过：告知用户校验成功，输出文件已生成
- 校验失败：显示具体的不匹配字段信息

## 输出示例

### 校验通过
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/original.csv, shape: (1000, 18)
Successfully read file: /path/to/standard.csv, shape: (50, 18)
Successfully written file: /path/to/output.csv
Format consistency check passed! Data output to: /path/to/output.csv
```

### 校验失败（字段数量不一致）
```
########## Exception: 一致性检查异常：输入的数据表结构与标准化数据模式结构的字段数目不一致！！！
```

### 校验失败（字段名称不匹配）
```
########## Exception: 输入的数据表结构与标准化数据模式结构，以下字段未对应：
字段A:字段X
字段B:字段Y
########## Exception: 一致性检查异常：输入的数据表结构与标准化数据模式结构不一致！！！
```

## 注意事项

1. 需要提供被检验表和标准模式表两个输入文件
2. 输出文件格式会自动保持与被检验表一致
3. 校验失败时脚本会抛出异常，不会生成输出文件
4. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_validated` 后缀
