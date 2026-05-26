---
name: xlsx_validate
description: 验证XLSX文件格式有效性
version: 1.0.0
category: spreadsheet_processing
name_zh: 验证XLSX文件格式有效性算子
input_params:
  - name: input_path
    type: xlsx_file
    description: 输入XLSX文件路径
  - name: output_path
    type: xlsx_file
    description: 输出XLSX文件路径
output_params:
  - name: output_path
    type: json_file
    description: 验证结果JSON文件
tag: 校验

---

# xlsx_validate 技能

## 功能说明

该技能验证XLSX文件格式的有效性，检查文件是否为有效的ZIP压缩包，以及是否包含XLSX所需的必要文件。

## 核心功能

- 检查文件是否存在
- 验证是否为有效的ZIP文件
- 检查必要文件是否存在
- 输出详细的验证结果

## 使用方法

```bash
python scripts/run_xlsx_validate.py --input_path <输入XLSX> --output_path <输出JSON>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入XLSX文件路径 |
| output_path | string | 是 | - | 输出JSON结果文件路径 |

## 示例

```bash
python scripts/run_xlsx_validate.py --input_path data.xlsx --output_path result.json
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
    "xl/workbook.xml",
    "xl/worksheets/sheet1.xml"
  ],
  "missing_files": [],
  "file_size": 102400,
  "total_files": 15,
  "errors": [],
  "warnings": []
}
```

## 注意事项

- 输出目录不存在时会自动创建
- 返回码为0表示验证通过，非0表示验证失败