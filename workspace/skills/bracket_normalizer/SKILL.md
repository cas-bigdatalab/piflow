---
name: bracket_normalizer
description: |
  括号类型统一工具。读取结构化数据文件，执行中文/全角括号到 ASCII 半角括号的映射，输出括号已统一的结构化数据文件。
  当用户提到括号统一、全角括号转半角、中文括号转换、括号规范化等需求时使用此skill。
  即使用户没有明确说出"bracket_normalizer"，只要任务涉及括号类符号统一，就应该使用此skill。
  不负责全角字母数字转换、Unicode正规化或其他通用全半角处理。
name_zh: bracket_normalizer_括号类型统一算子
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

# bracket_normalizer 括号类型统一Skill

## 功能概述

将中文/全角括号统一为 ASCII 半角括号：`【】〔〕［］→[]`，`「」『』→""`，`《》〈〉→<>`，`（）｟｠→()`，`｛｝→{}`。

## 触发条件

- 括号统一 / 全角括号转半角
- 中文括号转换
- 括号规范化
- 括号类符号统一

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

输入为结构化表格，文本列可包含中文/全角括号：

```csv
id,text
1,"【标题】「引用」《书名》（说明）"
```

## 支持的文件格式

- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

## 使用方法

```bash
python scripts/bracket_normalizer.py \
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
[OK] 括号类型统一完成 -> output.csv
   列: ['text'], 映射: 20 对
```

输入 `【重要】「日本語」《タイトル》` → 输出 `[重要]"日本語"<タイトル>`

## 环境要求

使用仓库内 Python 环境运行，无额外第三方依赖；读取/写入复用共享 `data_io`。

## 注意事项

1. 使用 translate 高速 1:1 映射
2. 左右括号独立映射，保持配对逻辑
3. 中文语境下 `「」→""` 可能改变语义，请确认业务场景
