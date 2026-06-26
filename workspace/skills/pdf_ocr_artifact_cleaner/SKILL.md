---
name: pdf_ocr_artifact_cleaner
description: |
  PDF/OCR伪影清洗工具。修复从学术论文PDF提取文本时的常见问题：断行连字符拼接（dehyphenation）、
  页码去除、Unicode连字归一化（ﬁ→fi）、页眉页脚去除。
  当用户提到PDF文本清洗、OCR伪影处理、断行修复、连字符拼接等需求时使用此skill。
name_zh: pdf_ocr_artifact_cleaner_PDF/OCR伪影清洗算子
tag: 清洗
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
  - name: no_dehyphenate
    type: string
    required: false
    default: "False"
    description: 是否关闭断行连字符修复
  - name: no_strip_page_numbers
    type: string
    required: false
    default: "False"
    description: 是否关闭页码去除
  - name: no_normalize_ligatures
    type: string
    required: false
    default: "False"
    description: 是否关闭Unicode连字归一化
  - name: header_pattern
    type: string
    required: false
    description: 页眉正则
  - name: footer_pattern
    type: string
    required: false
    description: 页脚正则
output_params:
  - name: output_path
    type: csv_file
    description: 清洗后的结构化数据文件
tag: 清洗
---

# pdf_ocr_artifact_cleaner PDF/OCR伪影清洗Skill

## 功能概述

修复从 PDF/OCR 提取文本时的三大类常见伪影：(1) 断行连字符拼接 `analy-\nsis→analysis`；(2) 独立页码行去除；(3) Unicode 连字归一化 `ﬁ→fi`。同时支持通过正则表达式去除页眉页脚。

## 触发条件

- PDF 文本清洗
- OCR 伪影处理
- 断行连字符修复
- 页码去除
- 连字归一化
- 学术论文文本提取后处理

## 支持的文件格式

支持以下结构化文件格式：
- CSV (.csv) / TSV (.tsv) / Excel (.xls, .xlsx) / SPSS (.sav)

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为以上支持格式后再使用本skill。

## 使用方法

```bash
python scripts/pdf_ocr_artifact_cleaner.py \
    --input_path <输入文件> \
    --output_path <输出文件> \
    [--text_columns col1,col2] \
    [--no_dehyphenate] \
    [--header_pattern "Chapter \d+\."]
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 输入文件路径 |
| `--output_path` | 是 | 输出文件路径 |
| `--text_columns` | 否 | 处理的文本列 |
| `--no_dehyphenate` | 否 | 关闭断行连字符拼接 |
| `--no_strip_page_numbers` | 否 | 关闭页码去除 |
| `--no_normalize_ligatures` | 否 | 关闭连字归一化 |
| `--header_pattern` | 否 | 匹配页眉的正则 |
| `--footer_pattern` | 否 | 匹配页脚的正则 |

## 输出示例

```
[OK] PDF/OCR伪影清洗完成 -> output.csv
   文本列: ['text']
   启用: ['dehyphenate', 'strip_page_numbers', 'normalize_ligatures']
```

输入 `exper-\nimental` → 输出 `experimental`

## 注意事项

1. 断行连字符只修复行尾带 `-` 后紧跟换行的情况，不破坏 `state-of-the-art` 等有意的连字符
2. 页码支持阿拉伯数字（42）和罗马数字（xiv）
3. 连字归一化处理：ﬁ→fi、ﬂ→fl、ﬀ→ff、ﬃ→ffi、ﬄ→ffl
