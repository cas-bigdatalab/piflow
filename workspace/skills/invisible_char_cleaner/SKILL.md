---
name: invisible_char_cleaner
description: |
  不可见字符清洗工具。移除零宽空格、BOM、软连字符、双向文本控制符、C0控制字符等 63 个码点
  的不可见/干扰字符。当用户提到不可见字符、零宽空格、BOM 清除、控制字符清洗等需求时使用此skill。
name_zh: 不可见字符清洗算子
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
  - name: keep_format
    type: string
    required: false
    description: 保留零宽连接符/非连接符（ZWJ/ZWNJ），用于阿拉伯文/梵文排版
output_params:
  - name: output_path
    type: csv_file
    description: 清洗后的结构化数据文件
tag: 清洗
---

# invisible_char_cleaner 不可见字符清洗Skill

## 功能概述

移除 63 个不可见/干扰码点，分 6 大类：(1) BOM（U+FEFF）；(2) 零宽空格/词连接符；(3) 双向文本标记（LRM/RLM/嵌入/隔离）；(4) 软连字符；(5) C0 控制字符（保留 \t \n \r）；(6) 其他（韩文填充符、蒙古文分隔符、行/段分隔符等）。

## 触发条件

- 不可见字符清洗 / 零宽空格清除
- BOM 清除
- 控制字符清洗
- 文本底层字符清理
- 多来源数据预处理

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
| `--keep_format` | 保留 ZWJ/ZWNJ 等格式控制字符 | `False` |

## 输入文件格式

输入为结构化表格，文本列可包含 BOM、零宽字符、软连字符、双向控制符等不可见字符：

```csv
id,text
1,"word​break and soft­hyphen"
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/invisible_char_cleaner.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--keep_format]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--keep_format` | 否 | 保留 ZWJ/ZWNJ（阿拉伯文等需要） |

## 输出示例

```
[OK] 不可见字符清洗完成 -> output.csv
   文本列: ['text']
   清理码点数: 63 （含ZWJ/ZWNJ）
```

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. ZWJ（‍）和 ZWNJ（‌）默认删除，阿拉伯文/梵文场景使用 `--keep_format`
2. C0 控制字符保留 \t（制表符）、\n（换行）、\r（回车）
3. 使用 translate 高速删除，不修改其他字符
