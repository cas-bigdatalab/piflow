---
name: numeric_distribution_check
description: |
  字段分布校验工具。读取结构化数据文件（CSV、TSV、Excel等），按模式检查数值字段统计特征或分类字段频率分布是否合理。
  数值模式用于检查均值、标准差、中位数、分位数等统计量；分类模式用于检查类别数上限和单类占比是否异常。
  当用户提到分布校验、统计特征验证、类别频率检查、类别倾斜检测等需求时使用此skill。
  即使用户没有明确说出"分布校验"，只要任务涉及验证字段整体分布是否偏移或失衡，就应该使用此skill。
name_zh: 字段分布校验算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel/SPSS等）

  - name: output_path
    type: string
    required: true
    description: 输出文件路径（带质控标识的结果文件）

  - name: mode
    type: string
    required: false
    default: numeric
    description: 校验模式：numeric（数值分布）或 categorical（分类频率）

  - name: value_field
    type: string
    required: false
    description: 数值模式下要统计的数值字段名

  - name: stat_constraints
    type: string
    required: false
    description: 数值模式下的统计约束，格式：统计量,min,max；如 mean,0,100 或 std,0,50，支持 mean/median/std/min/max/p25/p75

  - name: category_field
    type: string
    required: false
    description: 分类模式下要检查的分类字段名

  - name: max_categories
    type: string
    required: false
    description: 分类模式下允许的最大类别数（超过则标记）

  - name: max_single_ratio
    type: string
    required: false
    description: 分类模式下单类最大占比 0~1（超过则标记该类别所有行）

  - name: qc_mark
    type: string
    required: true
    description: 质控标识（如QC0029）

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

# numeric_distribution_check 字段分布校验Skill

## 功能概述

本skill用于在**表级别**检查字段的整体分布是否合理，包含两种模式：

### 数值模式（numeric）
- 计算数值字段的统计特征
- 支持均值、标准差、中位数、最小值、最大值、25%分位数、75%分位数
- 任一统计量超出约束范围时，整表标记为不通过

### 分类模式（categorical）
- 统计分类字段的类别数和类别占比
- 检查类别数是否超过 `max_categories`
- 检查单类占比是否超过 `max_single_ratio`
- 类别数超限时整表标记；单类占比超限时仅标记该类别对应的行

## 触发条件

当用户请求以下任务时，应使用此skill：
- 分布校验
- 统计特征验证
- 均值/标准差检查
- 数值分布偏移检测
- 类别频率检查
- 分类分布检查
- 类别倾斜检测
- 数据平衡性分析

## 处理逻辑

1. 读取输入数据表
2. 根据 `mode` 选择校验路径：
   - `numeric`：提取 `value_field` 的有效数值，计算统计量并与 `stat_constraints` 比较
   - `categorical`：统计 `category_field` 的类别频次和占比，检查 `max_categories` 与 `max_single_ratio`
3. 若任一约束超限，则在 `mark_field_name` 列标记 `qc_mark`
4. 输出统计摘要和校验结果

## 支持的文件格式

- CSV (.csv)
- TSV (.tsv)
- Excel (.xls, .xlsx)
- SPSS (.sav)

## 使用方法

### 步骤1：获取用户输入输出路径及参数

向用户确认：
1. 输入文件路径（需要校验的文件）
2. 输出文件路径（校验结果文件）
3. 校验模式（numeric 或 categorical）
4. 数值字段名与统计约束，或分类字段名与类别阈值
5. 质控标识

### 步骤2：执行字段分布校验脚本

在 `scripts/` 目录下找到 `numeric_distribution_check.py`，使用Python执行：

数值模式：

```bash
python scripts/numeric_distribution_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --mode numeric \
    --value_field "score" \
    --stat_constraints "mean,40,60 std,0,20" \
    --qc_mark QC0029
```

分类模式：

```bash
python scripts/numeric_distribution_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --mode categorical \
    --category_field "category" \
    --max_categories 20 \
    --max_single_ratio 0.5 \
    --qc_mark QC0029
```

### 步骤3：返回结果

脚本执行完成后，告知用户：
- 实际统计值或类别分布概况
- 哪些约束超出范围
- 是否整表标记，或仅标记单类倾斜行

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径（支持CSV/TSV/Excel/SPSS） |
| `--output_path` | 是 | 输出文件路径 |
| `--mode` | 否 | 校验模式：`numeric`（默认）或 `categorical` |
| `--value_field` | 数值模式必需 | 要统计的数值字段名 |
| `--stat_constraints` | 数值模式必需 | 统计约束，格式：`统计量,min,max`，多组用空格或分号分隔 |
| `--category_field` | 分类模式必需 | 要检查的分类字段名 |
| `--max_categories` | 分类模式可选 | 最大允许类别数（超过则全部标记） |
| `--max_single_ratio` | 分类模式可选 | 单类最大占比 0~1（超过则标记倾斜类别所有行） |
| `--qc_mark` | 是 | 质控标识（如QC0029） |
| `--mark_field_name` | 否 | 质控标识字段名（默认QC0000） |

## 输出示例

### 数值模式：分布偏移

```
[OK] Using encoding UTF-8 successfully read CSV file
Successfully read file: /path/to/data.csv, shape: (1000, 5)
  [mean] 期望 [40, 60], 实际 72.3000 ✗ 超限
  [std] 期望 [0, 20], 实际 15.8000 ✓
[QC FAIL] 数值分布校验未通过 (1 项):
  [mean] 期望 [40, 60], 实际 72.3000 ✗ 超限
Successfully written file: /path/to/checked.csv
```

### 数值模式：通过

```
[OK] Using encoding UTF-8 successfully read CSV file
Successfully read file: /path/to/data.csv, shape: (500, 4)
  [mean] 期望 [40, 60], 实际 52.1000 ✓
  [std] 期望 [0, 20], 实际 12.3000 ✓
[QC PASS] 数值分布校验通过
Successfully written file: /path/to/checked.csv
```

### 分类模式：未通过

```
[OK] Using encoding UTF-8 successfully read CSV file
Successfully read file: /path/to/data.csv, shape: (500, 8)
[INFO] 总行数: 500, 类别数: 35
  dominant                                 362 (72.4%)
  ... 还有 34 个类别
[QC FAIL] 分类频率校验未通过 (2 项):
  [类别数] 实际 35 > 最大 20
  [倾斜] 类别 'dominant' 占比 72.4% > 60%
Successfully written file: /path/to/checked.csv
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 本skill为**表级别**校验：数值模式不通过时整表标记；分类模式中类别数超限时整表标记，单类倾斜时只标记该类别对应行
4. 数值模式约束表达式格式：`统计量,min,max`，多组用空格或分号分隔
5. 非数值数据自动转为 NaN 后从统计中排除
6. 分类模式会忽略空值和空字符串
7. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_checked` 后缀
8. 与逐行离群点检测、枚举词典合规校验等 skill 的职责不同，本 skill 只负责字段分布合理性检查
