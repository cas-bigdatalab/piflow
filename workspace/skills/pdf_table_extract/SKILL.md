---
name: pdf_table_extract
description: 从PDF文件中提取表格数据，输出为JSON格式。当用户需要从PDF中提取表格时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

name_zh: 从PDF文件中提取表格数据，输出为JSON格式算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入PDF文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

  - name: pages
    type: string
    required: false
    description: 页码范围，如"1-3,5"（可选，默认全部页面）

output_params:
  - name: output_path
    type: json_file
    description: 提取的表格JSON文件
tag: 输入

---

# pdf_table_extract 技能

## 功能说明

该技能从PDF文件中提取表格数据，输出为JSON格式，适用于需要从PDF报告中提取结构化表格数据的场景。

## 核心功能

- 自动检测并提取PDF中的表格
- 支持指定页码范围提取
- 输出结构化JSON格式（包含表头和数据行）
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_table_extract.py --input_path <输入PDF> --output_path <输出JSON> [--pages <页码范围>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |
| pages | string | 否 | 全部 | 页码范围，如"1-3,5" |

## 示例

### 示例1：提取全部页面的表格

```bash
python scripts/run_pdf_table_extract.py --input_path report.pdf --output_path tables.json
```

### 示例2：提取指定页码的表格

```bash
python scripts/run_pdf_table_extract.py --input_path report.pdf --output_path tables.json --pages "3-5"
```

## 输出格式

```json
[
  {
    "page": 3,
    "headers": ["姓名", "部门", "职位"],
    "rows": [
      {"姓名": "张三", "部门": "技术部", "职位": "工程师"},
      {"姓名": "李四", "部门": "市场部", "职位": "经理"}
    ]
  }
]
```

## 注意事项

- 需要安装pdfplumber库
- 复杂表格可能提取不准确
- 输出目录不存在时会自动创建
