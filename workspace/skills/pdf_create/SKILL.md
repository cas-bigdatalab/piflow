---
name: pdf_create
description: |
  从零创建PDF文件工具。使用reportlab库生成专业PDF文档，支持自定义页面大小、标题、作者、
  以及通过JSON配置内容结构（标题、段落、表格等）。当用户需要生成PDF报告、文档时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

name_zh: 从零创建PDF文件算子
input_params:
  - name: output_path
    type: string
    required: true
    description: 输出PDF文件路径

  - name: title
    type: string
    required: false
    description: 文档标题

  - name: pagesize
    type: string
    required: false
    default: letter
    description: 页面大小（letter/a4）

  - name: author
    type: string
    required: false
    description: 作者名称

  - name: content
    type: string
    required: false
    description: 内容JSON字符串，定义文档结构

output_params:
  - name: output
    type: csv_file
    description: 生成的PDF文件
tag: 输入

---

# pdf_create 技能

## 功能说明

该技能使用 reportlab 库从零创建专业的 PDF 文档，支持自定义页面大小、标题、作者信息，以及通过 JSON 配置灵活定义文档内容结构，包括标题、段落、表格等元素。

## 核心功能

- 支持自定义页面大小（letter/a4）
- 支持设置文档标题和作者信息
- 通过 JSON 配置灵活定义文档内容结构
- 支持多种内容元素：标题、段落、表格、分页符等

## 内容结构配置

content 参数支持以下类型的元素：

| 类型 | 说明 | 必填字段 | 可选字段 |
| :--- | :--- | :--- | :--- |
| title | 文档主标题 | text | - |
| heading1 | 一级标题 | text | - |
| heading2 | 二级标题 | text | - |
| paragraph | 段落文本 | text | - |
| spacer | 空白间隔 | - | height |
| page_break | 分页符 | - | - |
| table | 表格 | data | style |

## 使用方法

```bash
python scripts/run_pdf_create.py --output_path <输出路径> [选项]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| output_path | string | 是 | - | 输出PDF文件路径 |
| title | string | 否 | - | 文档标题 |
| pagesize | string | 否 | letter | 页面大小（letter/a4） |
| author | string | 否 | - | 作者名称 |
| content | string | 否 | - | 内容JSON字符串或JSON文件路径 |

## 示例

### 示例1：创建简单PDF

```bash
python scripts/run_pdf_create.py --output_path ./output.pdf --title "我的报告" --author "张三"
```

### 示例2：通过JSON配置内容

```bash
python scripts/run_pdf_create.py --output_path ./report.pdf --content '[
    {"type": "title", "text": "年度报告"},
    {"type": "paragraph", "text": "这是一份使用pdf_create技能生成的专业报告。"},
    {"type": "heading1", "text": "一、项目概述"},
    {"type": "paragraph", "text": "本项目旨在展示PDF创建功能的强大能力。"},
    {"type": "table", "data": [["姓名", "部门", "职位"], ["张三", "技术部", "工程师"], ["李四", "市场部", "经理"]]}
]'
```

### 示例3：从文件读取内容配置

```bash
python scripts/run_pdf_create.py --output_path ./report.pdf --content ./content.json
```

## 注意事项

- content 参数可以是 JSON 字符串，也可以是 JSON 文件路径
- 表格样式支持自定义颜色、边框等属性
- 输出目录不存在时会自动创建
