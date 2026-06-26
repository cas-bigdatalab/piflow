---
name: smart_quote_normalizer
description: |
  智能引号/排版字符规范化工具。将弯引号、长破折号、省略号等排版字符转为标准 ASCII 形式，
  适配 Word/PDF/网页文本的后处理清洗。当用户提到智能引号、弯引号转直引号、排版字符规范化、
  长破折号等需求时使用此skill。
name_zh: DC32_智能引号规范化算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径
  - name: output_path
    type: string
    required: true
    description: 输出文件路径
  - name: text_columns
    type: string
    required: false
    description: 处理的文本列，逗号分隔
output_params:
  - name: output_path
    type: csv_file
    description: 规范化后的结构化数据文件
tag: 清洗
---

# smart_quote_normalizer 智能引号规范化Skill

## 功能概述

将弯引号、长破折号、省略号等排版字符转为标准 ASCII 形式，覆盖直引号、单引号、破折号、省略号、非 ASCII 连字符、项目符号和不换行空格等常见清洗场景。

## 触发条件

- 智能引号 / 弯引号转直引号
- 排版字符规范化
- 长破折号转换
- 省略号转三个点
- Word/PDF 导出文本清洗

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 CSV/TSV/Excel 等结构化文件路径 |
| `--output_path` | 输出清洗后文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 需要处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |

## 输入文件格式

输入为结构化表格，至少包含一个文本列：

```csv
id,text
1,"He said “hello”—then paused…"
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/smart_quote_normalizer.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |

## 输出示例

```
[OK] 智能引号/排版字符规范化完成 -> output.csv
   文本列: ['text']
   映射字符数: 20 + 4 多字符
```

输入 `"Hello" — groundbreaking…` → 输出 `"Hello" -- groundbreaking...`

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. 1:1 字符映射使用 translate（高效），1:N 使用 str.replace
2. 不会破坏正常的 ASCII 直引号和连字符
3. 覆盖德语 `„`、法语 `«»`、中文弯引号等
