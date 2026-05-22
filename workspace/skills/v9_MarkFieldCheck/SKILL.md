---
name: v9_MarkFieldCheck
description: |
  标识符字段检查工具。读取结构化数据文件，检查是否存在指定的质量标识符字段（默认为QC0000），
  如果不存在则添加该字段，最后输出为相同格式的文件。当用户提到标识符字段检查、添加质量标识符、QC字段检查等需求时使用此skill。
  即使用户没有明确说出"标识符字段"，只要任务涉及检查或添加质量标识符字段，就应该使用此skill。

name_zh: v9_标识符字段检查算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: output_path
    type: string
    required: true
    description: 输出文件路径

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 质量标识符字段名

output_params:
  - name: output
    type: csv_file
    description: 处理后结构化数据文件，包含质量标识符字段
tag: 校验

---

# v9_MarkFieldCheck 标识符字段检查Skill

## 功能概述

本skill用于读取结构化数据文件，检查是否存在指定的质量标识符字段。如果该字段不存在，则自动添加该字段（值为空），然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 标识符字段检查
- 添加质量标识符
- QC字段检查
- 检查是否有标识符字段
- 补全标识符字段

## 处理逻辑

1. 读取输入的结构化数据文件
2. 检查指定的质量标识符字段是否存在（默认字段名：QC0000）
3. 如果字段不存在，添加该字段（值为空/NA）
4. 输出处理后的数据文件

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 输入文件路径（需要检查的文件）
2. 输出文件路径（处理后的文件）
3. 可选：质量标识符字段名（默认：QC0000）

### 步骤2：执行标识符字段检查脚本

在 `scripts/` 目录下找到 `v9_MarkFieldCheck.py`，使用Python执行：

```bash
python scripts/v9_MarkFieldCheck.py --input_path <输入文件> --output_path <输出文件> [--mark_field_name <字段名>]
```

### 步骤3：返回结果

告知用户处理结果：
- 如果字段已存在：告知用户字段已存在，无需添加
- 如果字段不存在：告知用户已添加新字段

## 输出示例

### 字段已存在
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 19)
Successfully written file: /path/to/output.csv
Processing completed! Output file saved to: /path/to/output.csv
Field 'QC0000' already exists.
```

### 字段不存在，已添加
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
Processing completed! Output file saved to: /path/to/output.csv
Field 'QC0000' was added.
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 默认字段名为QC0000，可通过 `--mark_field_name` 参数自定义
4. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_marked` 后缀
