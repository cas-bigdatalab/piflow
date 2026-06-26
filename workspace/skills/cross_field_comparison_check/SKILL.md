---
name: cross_field_comparison_check
description: |
  跨字段比较校验工具。读取结构化数据文件（CSV、TSV、Excel等），检查两个字段之间的逻辑约束关系
  是否满足（如 start < end、min ≤ max、price >= cost），支持六种比较运算符，多约束可组合使用。
  当用户提到跨字段校验、字段间比较、逻辑约束检查、大小关系验证等需求时使用此skill。
  即使用户没有明确说出"跨字段"，只要任务涉及验证两个字段值之间的逻辑关系，就应该使用此skill。

name_zh: cross_field_comparison_check_跨字段比较校验算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持CSV/TSV/Excel/SPSS等）

  - name: output_path
    type: string
    required: true
    description: 输出文件路径（带质控标识的结果文件）

  - name: constraints
    type: string
    required: true
    description: 约束表达式，| 分隔。格式：左字段,运算符,右字段。如 start,<,end|min,<=,max

  - name: qc_mark
    type: string
    required: true
    description: 质控标识（如QC标识）

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

# cross_field_comparison_check 跨字段比较校验Skill

## 功能概述

本skill用于逐行验证两个字段值之间的逻辑关系是否成立。典型应用场景：

- 时间区间校验：`start_time < end_time`
- 数值范围校验：`min_value <= max_value`
- 价格逻辑校验：`cost < price`
- 库存校验：`sold <= total`

### 支持运算符

| 运算符 | 含义 | 示例 |
|------|------|------|
| `<` | 小于 | `start,<,end` |
| `<=` | 小于等于 | `min,<=,max` |
| `>` | 大于 | `end,>,start` |
| `>=` | 大于等于 | `current,>=,baseline` |
| `==` | 等于 | `computed,==,expected` |
| `!=` | 不等于 | `status,!=,deleted` |

### 约束格式

- 每个约束：`左字段,运算符,右字段`
- 多个约束用 `|` 分隔
- 约束之间为 AND 关系（任一违反即标记）
- 示例：`start,<,end|min,<=,max` 表示同时满足 start<end 且 min≤max

## 触发条件

当用户请求以下任务时，应使用此skill：
- 跨字段比较校验
- 字段间逻辑约束检查
- 大小关系验证
- 字段值一致性比对
- 数据逻辑规则检查

## 处理逻辑

1. 读取输入数据表
2. 解析 constraints 字符串，拆分出每个约束（按 `|` 分割）
3. 对每行数据：
   a. 提取左右字段的值并转为数值（numeric）
   b. 按指定运算符比较
   c. 违反任一约束 → 标记 `qc_mark`
4. 非数值数据（如字符串）转为 NaN 后跳过该约束的比较
5. 输出标记结果和统计摘要

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
3. 约束表达式（格式：左字段,运算符,右字段|...）
4. 质控标识

### 步骤2：执行跨字段比较校验脚本

在 `scripts/` 目录下找到 `cross_field_comparison_check.py`，使用Python执行：

单约束（时间区间）：

```bash
python scripts/cross_field_comparison_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --constraints "start_time,<,end_time" \
    --qc_mark QCFLAG
```

多约束（范围+价格）：

```bash
python scripts/cross_field_comparison_check.py \
    --input_path data.csv \
    --output_path checked.csv \
    --constraints "start,<,end|min,<=,max|cost,<=,price" \
    --qc_mark QCFLAG
```

### 步骤3：返回结果

脚本执行完成后，告知用户：
- 每条约束的违反行数
- 示例违反数据
- 总标记行数

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径（支持CSV/TSV/Excel/SPSS） |
| `--output_path` | 是 | 输出文件路径 |
| `--constraints` | 是 | 约束表达式，`|` 分隔。格式：`左字段,运算符,右字段` |
| `--qc_mark` | 是 | 质控标识（如QC标识） |
| `--mark_field_name` | 否 | 质控标识字段名（默认QC0000） |

## 输出示例

### 发现问题

```
[OK] Using encoding UTF-8 successfully read CSV file
Successfully read file: /path/to/data.csv, shape: (500, 8)
Constraints: start < end | min <= max
[QC FAIL] 跨字段比较校验未通过 (2 项问题):
  [start < end] 3 行违反 (示例: 行42 start=100 > end=80)
  [min <= max] 5 行违反 (示例: 行126 min=50 > max=30)
已标记 8 行
Successfully written file: /path/to/checked.csv
```

### 通过

```
[OK] Using encoding UTF-8 successfully read CSV file
Successfully read file: /path/to/data.csv, shape: (300, 6)
Constraints: start < end | cost <= price
[QC PASS] 跨字段比较校验通过
Successfully written file: /path/to/checked.csv
```

## 注意事项

1. 输入输出路径需要用户提供
2. 输出文件格式会自动保持与输入文件一致
3. 约束分隔符规则：
   - 约束内部用半角逗号 `,` 分隔（左字段,运算符,右字段）
   - 约束之间用竖线 `|` 分隔
4. 数值类型：字段值强制转为 numeric，非数值按 NaN 处理并跳过该行
5. 约束之间为 AND 关系：每条约束独立判断，任一违反即标记该行
6. 被比较的两个字段名在表中必须存在，否则报错退出
7. 如果用户没有指定输出路径，可以建议使用原文件名加上 `_checked` 后缀
