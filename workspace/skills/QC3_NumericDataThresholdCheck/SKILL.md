---
name: "QC3_NumericDataThresholdCheck"
description: "数值数据阈值检验工具。读取结构化数据文件（CSV、TSV、Excel等），检查数值字段是否在指定的门限范围内，不允许超出门限值之外，最后输出为同格式的文件。当用户需要对数据进行阈值检验、数值范围检查、数据质量控制等操作时使用此skill。"

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径

  - name: origin_output_path
    type: string
    required: true
    description: 输出文件路径（与输入文件格式相同）

  - name: field_name
    type: string
    required: true
    description: 要检查的字段名

  - name: max_value
    type: float
    required: true
    description: 最大值

  - name: min_value
    type: float
    required: true
    description: 最小值

  - name: qc_mark
    type: string
    required: true
    description: QC标记

  - name: error_output_path
    type: string
    required: false
    description: 错误数据输出文件路径

  - name: additional_condition
    type: string
    required: false
    description: 额外条件

  - name: mark_field_name
    type: string
    required: false
    default: QC0000
    description: 标记字段名

  - name: id_field_name
    type: string
    required: false
    default: ID0000
    description: ID字段名

output_params:
  - name: origin_output
    type: csv_file
    description: 阈值检验后的结构化数据文件，带质控标记

  - name: error_output
    type: csv_file
    description: 错误数据文件（可选），包含超出阈值范围的记录
---

# QC3_NumericDataThresholdCheck

## 功能说明

该skill提供数值数据阈值检验的能力，具体包括：

1. **读取结构化文件**：支持 CSV、TSV、Excel 等多种格式的结构化数据文件
2. **数值阈值检验**：将被检验表中的属性项值与门限比对，检查是否在门限范围
3. **输出结果**：将检验后的数据输出为同格式的文件

## 核心功能

### 1. 数值数据阈值检验

通过执行 `QC3_NumericDataThresholdCheck.py` 脚本，读取输入文件，检查数值字段是否在指定的阈值范围内，并输出处理后的文件。

**调用方式**：
```bash
python scripts/QC3_NumericDataThresholdCheck.py --input_path <输入文件路径> --origin_output_path <输出文件路径> --field_name <字段名> --max_value <最大值> --min_value <最小值> --qc_mark <QC标记>
```

**参数说明**：
- `--input_path`：必填，输入文件路径（支持 CSV、TSV、Excel 等格式）
- `--origin_output_path`：必填，输出文件路径（与输入文件格式相同）
- `--error_output_path`：可选，错误数据输出文件路径
- `--field_name`：必填，要检查的字段名
- `--max_value`：必填，最大值
- `--min_value`：必填，最小值
- `--additional_condition`：可选，额外条件
- `--qc_mark`：必填，QC标记
- `--mark_field_name`：可选，标记字段名
- `--id_field_name`：可选，ID字段名

**使用示例**：
```bash
# 检查 DBH 字段在 0-100 之间
python scripts/QC3_NumericDataThresholdCheck.py --input_path data.csv --origin_output_path output.csv --field_name DBH --max_value 100 --min_value 0 --qc_mark "DBH阈值检验"
```

## 脚本说明

### QC3_NumericDataThresholdCheck.py
- **功能**：数值数据阈值检验的核心逻辑
- **调用接口**：通过命令行参数接收输入输出路径和阈值配置
- **特性**：
  - 支持多种结构化文件格式
  - 灵活的阈值配置
  - 保留原始数据格式
  - 详细的检验结果输出

### data_io.py
- **功能**：结构化文件读写工具
- **支持格式**：CSV、TSV、Excel、SPSS
- **特性**：
  - 自动检测文件编码
  - 多编码重试机制
  - 智能处理不同文件格式

## 注意事项

1. 确保输入文件存在且格式正确
2. 阈值配置格式必须为 `字段名:最小值-最大值`，多个字段用逗号分隔
3. 输出路径需要有写入权限
4. 脚本在用户本地执行，依赖 Python 环境
5. 支持 Windows 和 Linux 系统

## 依赖

- Python 3.x
- pandas 库
- chardet 库（用于自动检测文件编码）
- openpyxl 库（用于 Excel 文件处理）
- xlrd 库（用于旧版 Excel 文件处理）
- pyreadstat 库（用于 SPSS 文件处理）