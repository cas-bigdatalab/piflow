---
name: DC1_Blank_Line_Clean
description: |
  空行清洗工具。读取结构化数据文件（CSV、TSV、Excel等），删除所有列为空的行（空行），
  然后输出为相同格式的文件。当用户提到空行清洗、清理空行、删除空行、处理空白行、净化数据文件等需求时使用此skill。
  即使用户没有明确说出"空行清洗"，只要任务涉及读取结构化文件并删除空行，就应该使用此skill。

input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）

  - name: output
    type: string
    required: true
    description: 输出文件路径（清洗后的文件）

output_params:
  - name: output
    type: csv_file
    description: 清洗空行后的结构化数据文件
---

# DC1_Blank_Line_Clean 空行清洗Skill

## 功能概述

本skill用于读取结构化数据文件，删除其中所有列为空的行（空行），然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 空行清洗
- 删除空行
- 清理空白行
- 净化数据文件
- 读取结构化文件并删除空行
- 对CSV/Excel/TSV等文件进行空行处理

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 输入文件路径（需要清洗的文件）
2. 输出文件路径（清洗后的文件）

### 步骤2：执行空行清洗脚本

在 `scripts/` 目录下找到 `DC1_Blank_Line_Clean.py`，使用Python执行：

```bash
python scripts/DC1_Blank_Line_Clean.py --input <输入文件路径> --output <输出文件路径>
```

### 步骤3：返回结果

脚本执行完成后，告知用户：
- 清洗前行数
- 清洗后行数
- 删除的空行数量
- 输出文件路径

## 输出示例

```
✅ 空行清洗完成！
   输入文件：/path/to/input.csv
   输出文件：/path/to/output.csv
   清洗前行数：100 | 清洗后行数：95
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 空行定义：所有列都为空的行
4. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_cleaned` 后缀
