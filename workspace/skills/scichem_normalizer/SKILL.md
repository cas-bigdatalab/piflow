---
name: scichem_normalizer
description: |
  科学公式/化学式规整 Skill：统一文本列中的数学符号、Unicode 上下标、化学反应箭头、全角 ASCII 和多余空格。
  适用于实验记录、论文摘录、化学反应式和科学公式文本；不负责公式语义解析、单位换算或化学配平。
name_zh: 科学公式化学式规整
tag: 清洗
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入结构化文件路径
  - name: output_path
    type: string
    required: true
    description: 输出结构化文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔；默认全部字符串列
output_params:
  - name: output_path
    type: string
    description: 科学/化学符号规整后的结构化文件
---

# SciChem Normalizer 科学公式化学式规整 Skill

## 功能概述

本 skill 对结构化数据中的科学公式和化学式文本做轻量规整：将特殊加减乘除、全角 ASCII、括号和等号转换为标准 ASCII；将 Unicode 上标/下标转为 `^`/`_` 标记；将反应箭头统一为 `->` 或 `<->`；折叠多余空格。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 科学公式符号规整
- 化学式上下标清洗
- 反应箭头统一
- 实验记录中的公式文本标准化

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 CSV/TSV/Excel 等结构化文件路径 |
| `--output_path` | 输出结构化文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |

## 输入文件格式

```tsv
id	text
1	The reaction H₂ + O₂ → H₂O releases energy.
2	Concentration was 5 × 10⁻³ mol/L.
```

## 使用方法

```bash
python scripts/scichem_normalizer.py \
  --input_path input.tsv \
  --output_path output.csv \
  --text_columns text
```

## 处理示例

| 输入文本 | 输出文本 |
|----------|----------|
| `H₂ + O₂ → H₂O` | `H_2 + O_2 -> H_2O` |
| `5 × 10⁻³ mol/L` | `5 * 10^-3 mol/L` |
| `Already ASCII formula H2O` | `Already ASCII formula H2O` |

## 输出示例

```csv
id,text
1,H_2 + O_2 -> H_2O
2,5 * 10^-3 mol/L
```

## 环境要求

依赖 Python、pandas，以及本仓库 DC 公用 `data_io` 读写工具。

## 注意事项

1. 该 skill 做符号级规整，不做化学方程式配平或科学公式语义解析。
2. Unicode 上下标会转换为 `^`/`_` 文本标记，需确保后续流程接受这种表示。
3. 单位换算、科学计数法数值换算不属于本 skill。
