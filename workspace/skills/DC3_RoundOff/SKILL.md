---
name: DC3_RoundOff
description: |
  四舍五入数据处理工具。读取结构化数据文件和标准配置文件，根据配置对数字型字段进行四舍五入处理，
  然后输出为相同格式的文件。当用户提到四舍五入、数字取整、保留小数位、数据舍入等需求时使用此skill。
  即使用户没有明确说出"四舍五入"，只要任务涉及根据配置文件对数据进行舍入处理，就应该使用此skill。
---

# DC3_RoundOff 四舍五入处理Skill

## 功能概述

本skill用于读取结构化数据文件和标准配置文件，根据配置对数字型字段进行四舍五入处理，然后输出为相同格式的文件。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 四舍五入处理
- 数字取整
- 保留小数位
- 数据舍入
- 根据配置进行数值精度处理

## 输入文件说明

### 原始数据文件 (origin_path)
需要处理的原始数据文件，支持CSV、TSV、Excel、SPSS等格式。

### 标准配置文件 (standard_path)
配置文件，用于指定哪些字段需要四舍五入以及保留几位小数。配置文件应包含以下列：
- `流水线`：流水线名称（可选，用于筛选配置）
- `表名`：文件名称（可选，用于筛选配置）
- `字段类型`：字段类型（如"数字型"）
- `字段代码`：字段名称
- `小数位`：保留的小数位数

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径

向用户确认：
1. 原始数据文件路径（需要处理的文件）
2. 标准配置文件路径（包含字段配置）
3. 输出文件路径（处理后的文件）
4. 可选：流水线名称、文件名称（用于筛选配置）

### 步骤2：执行四舍五入处理脚本

在 `scripts/` 目录下找到 `DC3_RoundOff.py`，使用Python执行：

```bash
python scripts/DC3_RoundOff.py --origin_path <原始数据文件> --standard_path <标准配置文件> --output_path <输出文件> [--flow_name <流水线名>] [--file_name <文件名>]
```

### 步骤3：返回结果

脚本执行完成后，告知用户四舍五入处理已完成。

## 输出示例

```
[OK] Using encoding GB2312 successfully read CSV file
Successfully read file: /path/to/origin.csv, shape: (1000, 18)
Successfully read file: /path/to/standard.csv, shape: (50, 5)
Successfully written file: /path/to/output.csv
Round off completed, result saved to: /path/to/output.csv
```

## 注意事项

1. 需要提供原始数据文件和标准配置文件两个输入
2. 输出文件格式会自动保持与原始输入文件一致
3. 仅处理标准配置中指定的数字型字段
4. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_rounded` 后缀
