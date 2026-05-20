---
name: DC2_SpaceCleaning
description: |
  字符串空格清理工具。读取结构化数据文件（CSV、TSV、Excel等），检查所有字符串类型（object）字段，
  删除字段值前后多余的空格，然后输出为相同格式的文件。当用户提到空格清理、去除空格、trim、清理字符串空格等需求时使用此skill。
  即使用户没有明确说出"空格清理"，只要任务涉及读取结构化文件并删除字符串字段的前后空格，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）

  - name: output_path
    type: string
    required: true
    description: 输出文件路径（清理后的文件）

output_params:
  - name: output
    type: csv_file
    description: 清理空格后的结构化数据文件
---

# DC2_SpaceCleaning 空格清理Skill

## 功能概述

本skill用于读取结构化数据文件，检查所有字符串类型（object类型）字段，删除字段值前后多余的空格，然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 空格清理
- 去除空格
- trim字符串
- 清理字符串前后空格
- 删除字符串字段的空格
- 净化数据中的空格

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 输入文件路径（需要清理的文件）
2. 输出文件路径（清理后的文件）

### 步骤2：执行空格清理脚本

在 `scripts/` 目录下找到 `DC2_SpaceCleaning.py`，使用Python执行：

```bash
python scripts/DC2_SpaceCleaning.py --input_path <输入文件路径> --output_path <输出文件路径>
```

### 步骤3：返回结果

脚本执行完成后，告知用户清理结果已保存至指定路径。

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
Space cleaning completed, saved to: /path/to/output.csv
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 仅处理字符串类型（object类型）的字段
4. 使用 `str.strip()` 方法去除前后空格
5. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_cleaned` 后缀
