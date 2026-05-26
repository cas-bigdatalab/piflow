---
name: docx_to_markdown
description: 将DOCX文档转换为Markdown格式
version: 1.0.0
category: document_conversion
name_zh: 将DOCX文档转换为Markdown格式算子
input_params:
  - name: input_path
    type: docx_file
    description: 输入DOCX文件路径
  - name: output_path
    type: markdown_file
    description: 输出markdown文件路径
output_params:
  - name: output_path
    type: markdown_file
    description: 输出Markdown文件(.md)
tag: 格式转换
---

# docx_to_markdown 技能

## 功能说明

该技能将DOCX文档转换为Markdown格式，支持提取文本内容、标题样式、表格等元素，适用于文档格式转换和内容迁移场景。

## 核心功能

- 提取DOCX中的文本内容
- 支持标题样式转换（Heading1-Heading6）
- 支持粗体、斜体文本样式
- 支持表格转换
- 支持列表和引用样式
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_docx_to_markdown.py --input_path <输入DOCX> --output_path <输出MD>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入DOCX文件路径 |
| output_path | string | 是 | - | 输出Markdown文件路径 |

## 示例

```bash
python scripts/run_docx_to_markdown.py --input_path document.docx --output_path document.md
```

## 支持的样式转换

| DOCX样式 | Markdown格式 |
| :--- | :--- |
| Heading1 | `# 标题` |
| Heading2 | `## 标题` |
| Heading3 | `### 标题` |
| Heading4 | `#### 标题` |
| Heading5 | `##### 标题` |
| Heading6 | `###### 标题` |
| 粗体 | `**文本**` |
| 斜体 | `_文本_` |
| 粗斜体 | `**_文本_**` |
| ListParagraph | `- 列表项` |
| Quote | `> 引用` |
| 表格 | Markdown表格格式 |

## 输出示例

```markdown
# 文档标题

## 章节标题

这是一段普通文本，包含**粗体**和_斜体_样式。

- 列表项1
- 列表项2

> 这是一段引用文本

| 列1 | 列2 | 列3 |
| --- | --- | --- |
| 数据1 | 数据2 | 数据3 |
```

## 注意事项

- 输出目录不存在时会自动创建
- 复杂的DOCX格式（如图片、复杂表格、脚注等）可能无法完全转换
- 扫描版PDF转换的DOCX无法提取文本（需先使用OCR）