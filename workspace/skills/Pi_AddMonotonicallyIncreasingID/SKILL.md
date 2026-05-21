---
name: Pi_AddMonotonicallyIncreasingID
description: |
  添加单调递增ID工具。读取结构化数据文件，检查是否存在指定的ID字段（默认为ID0000），
  如果不存在则添加从1开始的单调递增ID字段，并将其放在第一列，最后输出为相同格式的文件。
  当用户提到添加ID、添加自增ID、添加序号、添加行号等需求时使用此skill。
  即使用户没有明确说出"添加ID"，只要任务涉及给数据添加自增ID，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel等）

  - name: output_path
    type: string
    required: true
    description: 输出文件路径（处理后的文件）

  - name: id_field_name
    type: string
    required: false
    default: ID0000
    description: ID字段名

output_params:
  - name: output
    type: csv_file
    description: 添加了单调递增ID的结构化数据文件
tag: 增强
---

# Pi_AddMonotonicallyIncreasingID 添加单调递增ID Skill

## 功能概述

本skill用于读取结构化数据文件，检查是否存在指定的ID字段。如果该字段不存在，则添加从1开始的单调递增ID字段，并将其放在第一列，然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 添加ID
- 添加自增ID
- 添加序号
- 添加行号
- 添加递增ID
- 补全ID字段

## 处理逻辑

1. 读取输入的结构化数据文件
2. 检查指定的ID字段是否存在（默认字段名：ID0000）
3. 如果字段不存在：
   - 添加从1开始的单调递增ID
   - 将ID字段放到第一列位置
4. 如果字段已存在，则不添加（保持原样）
5. 输出处理后的数据文件

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 输入文件路径（需要添加ID的文件）
2. 输出文件路径（处理后的文件）
3. 可选：ID字段名（默认：ID0000）

### 步骤2：执行添加单调递增ID脚本

在 `scripts/` 目录下找到 `Pi_AddMonotonicallyIncreasingID.py`，使用Python执行：

```bash
python scripts/Pi_AddMonotonicallyIncreasingID.py --input_path <输入文件> --output_path <输出文件> [--id_field_name <字段名>]
```

### 步骤3：返回结果

告知用户处理结果：
- 如果字段已存在：告知用户ID字段已存在，无需添加
- 如果字段不存在：告知用户已添加ID字段及ID范围

## 输出示例

### ID字段不存在，已添加
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 18)
Successfully written file: /path/to/output.csv
Processing completed! Result saved to: /path/to/output.csv
Field 'ID0000' was added with IDs from 1 to 1000.
```

### ID字段已存在
```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/input.csv, shape: (1000, 19)
Successfully written file: /path/to/output.csv
Processing completed! Result saved to: /path/to/output.csv
Field 'ID0000' already exists.
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 默认字段名为ID0000，可通过 `--id_field_name` 参数自定义
4. ID从1开始递增
5. 新增的ID字段会放在第一列位置
6. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_with_id` 后缀
