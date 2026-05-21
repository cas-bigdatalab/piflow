---
name: pdf_metadata_extract
description: 提取PDF文件的元数据（标题、作者、主题、页数等），输出为JSON格式。当用户需要查看PDF文档信息时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入PDF文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

output_params:
  - name: output
    type: json_file
    description: PDF元数据JSON文件
tag: 输入
---

# pdf_metadata_extract 技能

## 功能说明

该技能提取PDF文件的元数据（标题、作者、主题、页数等），输出为JSON格式，便于查看和处理PDF文档信息。

## 核心功能

- 提取PDF基本信息（文件名、大小、页数）
- 提取文档元数据（标题、作者、主题、创建者等）
- 提取日期信息（创建日期、修改日期）
- 检测PDF是否加密

## 使用方法

```bash
python scripts/run_pdf_metadata_extract.py --input_path <输入PDF> --output_path <输出JSON>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |

## 示例

```bash
python scripts/run_pdf_metadata_extract.py --input_path document.pdf --output_path metadata.json
```

## 输出格式

```json
{
  "file_name": "document.pdf",
  "file_size": 1024000,
  "pages": 20,
  "pdf_version": "PDF-1.7",
  "title": "Document Title",
  "author": "John Doe",
  "subject": "Document Subject",
  "creator": "Microsoft Word",
  "producer": "Microsoft Word 2016",
  "creation_date": "2024-01-15 10:30:00",
  "modification_date": "2024-01-15 14:20:00",
  "is_encrypted": false
}
```

## 注意事项

- 输出目录不存在时会自动创建
- 部分PDF可能没有完整的元数据，缺失字段会显示为null
