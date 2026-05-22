---
name: docx_text_extract
description: 从DOCX文件中提取文本内容
version: 1.0.0
category: document_processing
name_zh: 从DOCX文件中提取文本内容算子
input_params:
  - name: input_path
    type: docx_file
    description: 输入DOCX文件路径
output_params:
  - name: output
    type: text_file
    description: 提取的文本文件(.txt)
tag: 输入

---

# docx_text_extract 技能

## 功能说明

该技能从DOCX文件中提取纯文本内容，保存为txt文件，适用于需要提取文档文本进行分析或处理的场景。

## 核心功能

- 提取DOCX中的文本内容
- 保持段落结构
- 支持UTF-8编码
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_docx_text_extract.py --input_path <输入DOCX> --output_path <输出TXT>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入DOCX文件路径 |
| output_path | string | 是 | - | 输出TXT文件路径 |

## 示例

```bash
python scripts/run_docx_text_extract.py --input_path document.docx --output_path text.txt
```

## 注意事项

- 输出目录不存在时会自动创建
- 提取的文本会保持段落分隔
- 不支持提取图片中的文字（如需请使用OCR工具）
- 如果DOCX文件损坏或不是标准格式，可能提取失败