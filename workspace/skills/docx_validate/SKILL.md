---
name: docx_validate
description: 验证DOCX文件格式有效性
version: 1.0.0
category: document_processing
name_zh: 验证DOCX文件格式有效性算子
input_params:
  - name: input_path
    type: docx_file
    description: 输入DOCX文件路径
  - name: output_path
    type: docx_file
    description: 输出DOCX文件路径
output_params:
  - name: output_path
    type: json_file
    description: 验证结果JSON文件
tag: 校验

---

# docx_validate 技能

## 功能说明

该技能验证DOCX文件格式的有效性，检查文件是否为有效的ZIP压缩包，以及是否包含DOCX所需的必要文件。

## 核心功能

- 检查文件是否存在
- 验证是否为有效的ZIP文件
- 检查必要文件是否存在
- 检查XML文件编码
- 输出详细的验证结果

## 使用方法

```bash
python scripts/run_docx_validate.py --input_path <输入DOCX> --output_path <输出JSON>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入DOCX文件路径 |
| output_path | string | 是 | - | 输出JSON结果文件路径 |

## 示例

```bash
python scripts/run_docx_validate.py --input_path document.docx --output_path result.json
```

## 输出格式

```json
{
  "valid": true,
  "file_exists": true,
  "is_zip": true,
  "has_required_files": true,
  "required_files": [
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml"
  ],
  "missing_files": [],
  "file_size": 102400,
  "total_files": 15,
  "errors": [],
  "warnings": []
}
```

## 验证项目

| 项目 | 说明 |
| :--- | :--- |
| valid | 整体验证结果 |
| file_exists | 文件是否存在 |
| is_zip | 是否为有效ZIP文件 |
| has_required_files | 是否包含必要文件 |
| required_files | 必需文件列表 |
| missing_files | 缺失的必需文件 |
| file_size | 文件大小（字节） |
| total_files | ZIP内文件总数 |
| errors | 错误信息列表 |
| warnings | 警告信息列表 |

## 注意事项

- 输出目录不存在时会自动创建
- 返回码为0表示验证通过，非0表示验证失败