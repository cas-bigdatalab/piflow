---
name: citation_marker_remover
description: |
  文献引用标记移除工具。读取含引用标记的文本，移除数字型、作者年份型和上标型引用标记，保留正文语义并输出清理后的文本。
  当用户提到移除引用标记、清理参考文献标注、删除文献引用等需求时使用此skill。
  适用于科研论文、学术文档的文本清洗，不负责参考文献章节重写、文献内容解析或非引用括号内容的系统抽取。

name_zh: 文献引用标记移除算子
tag: 清洗
input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持txt/json/jsonl/csv等）

  - name: output
    type: string
    required: true
    description: 输出文件路径

  - name: citation_styles
    type: string
    required: false
    default: all
    description: 要移除的引用格式（all=全部, numeric=数字型[1], author_year=作者年份型(Smith,2020), superscript=上标型）

  - name: remove_inline_refs
    type: string
    required: false
    default: "True"
    description: 是否移除行内引用标记

  - name: remove_reference_section
    type: string
    required: false
    default: "False"
    description: 是否移除参考文献章节

  - name: preserve_context
    type: string
    required: false
    default: "True"
    description: 是否保留引用周围的上下文（避免产生多余空格）

  - name: text_field
    type: string
    required: false
    default: text
    description: JSON/JSONL输入时的文本字段名

output_params:
  - name: output
    type: file
    description: 清理后的文件

  - name: total_count
    type: integer
    description: 处理的样本总数

  - name: citations_removed
    type: integer
    description: 移除的引用标记数量

tag: 清洗

---

# Citation Marker Remover 文献引用标记移除 Skill

## 功能概述

本skill用于移除科研文本中的引用标记，支持多种常见的引用格式。
适用于科研论文、学术文档的文本清洗，为后续NLP处理提供干净的文本。

## 输入文件格式

支持以下文件格式：
- JSONL
- JSON
- CSV
- TXT
- Markdown

不支持的文件格式会直接报错拒绝，不会自动猜测格式；如需处理其他格式，请先转换为以上支持格式后再使用本skill。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 移除引用标记
- 清理参考文献标注
- 删除文献引用
- 清洗学术文本

## 支持的引用格式

### 1. 数字型引用 (numeric)
- `[1]`, `[2]`, `[1,2,3]`
- `[1-5]`, `[1,3-5]`
- `(1)`, `(2,3)`
- 上标数字：`¹`, `²`, `³`

### 2. 作者年份型引用 (author_year)
- `(Smith, 2020)`
- `(Smith and Jones, 2020)`
- `(Smith et al., 2020)`
- `Smith (2020)`
- `(Smith, 2020; Jones, 2021)`

### 3. 上标型引用 (superscript)
- `¹`, `²`, `³`, `⁴`, `⁵`
- `[1]` 作为上标

### 4. 其他格式
- `{1}`, `<1>`
- `[ref1]`, `[cite1]`

## 使用方法

### 基本用法 - 移除所有引用
```bash
python scripts/run_citation_marker_remover.py \
  --input paper.jsonl \
  --output cleaned.jsonl
```

### 只移除数字型引用
```bash
python scripts/run_citation_marker_remover.py \
  --input paper.jsonl \
  --output cleaned.jsonl \
  --citation_styles numeric
```

### 同时移除参考文献章节
```bash
python scripts/run_citation_marker_remover.py \
  --input paper.jsonl \
  --output cleaned.jsonl \
  --remove_reference_section true
```

### 移除多种格式
```bash
python scripts/run_citation_marker_remover.py \
  --input paper.jsonl \
  --output cleaned.jsonl \
  --citation_styles "numeric,author_year"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 输出文件路径 |
| `--citation_styles` | 否 | 引用格式：all/numeric/author_year/superscript，默认all |
| `--remove_inline_refs` | 否 | 是否移除行内引用，默认true |
| `--remove_reference_section` | 否 | 是否移除参考文献章节，默认false |
| `--preserve_context` | 否 | 是否保留上下文，默认true |
| `--text_field` | 否 | 文本字段名，默认text |

## 输出示例

### 清理前后对比
```
原文: 研究表明[1]，该方法具有较高的准确率[2,3]。Smith et al. (2020)也得出了类似结论。
清理后: 研究表明，该方法具有较高的准确率。也得出了类似结论。

原文: 根据文献(Johnson, 2019; Lee, 2020)，这一现象普遍存在。
清理后: 根据文献，这一现象普遍存在。

原文: 实验结果¹²³表明该假设成立。
清理后: 实验结果表明该假设成立。
```

### 执行结果
```
[OK] Citation marker removal completed!
   Input file: paper.jsonl
   Citation styles: all
   Total samples: 1000
   Modified samples: 850 (85.0%)
   Citations removed: 5200
   Citation types:
     - Numeric [1]: 3500
     - Author-year (Smith, 2020): 1200
     - Superscript: 500
   Output file: cleaned.jsonl
```

## 注意事项

1. 移除引用后会自动清理多余的空格和标点
2. 作者年份型引用可能误匹配普通括号内容，建议先检查结果
3. 参考文献章节识别基于关键词（"参考文献"、"References"等）
4. 上标数字可能与其他用途的上标混淆，请谨慎使用
5. 建议在移除前备份原始文件
