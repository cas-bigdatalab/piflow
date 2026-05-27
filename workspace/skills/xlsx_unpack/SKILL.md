---
name: xlsx_unpack
description: 将XLSX文件解压为XML目录
version: 1.0.0
category: spreadsheet_processing
name_zh: 将XLSX文件解压为XML目录算子
input_params:
  - name: input_path
    type: xlsx_file
    description: 输入XLSX文件路径
  - name: output_dir
    type: directory
    description: 输出目录路径
output_params:
  - name: output_dir
    type: directory
    description: 解压后的XML目录
tag: 输入

---

# xlsx_unpack 技能

## 功能说明

该技能将XLSX文件解压为XML目录结构，方便查看和编辑XLSX内部的XML文件。XLSX本质上是一个ZIP压缩包，包含多个XML文件和资源文件。

## 核心功能

- 将XLSX文件解压为可读的XML目录
- 自动创建输出目录
- 支持.xlsx和.xlsm文件格式

## 使用方法

```bash
python scripts/run_xlsx_unpack.py --input_path <输入XLSX> --output_dir <输出目录>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入XLSX文件路径 |
| output_dir | string | 是 | - | 输出目录路径 |

## 示例

```bash
python scripts/run_xlsx_unpack.py --input_path data.xlsx --output_dir ./unpacked/
```

## 输出结构

解压后的目录结构：
```
output_dir/
├── [Content_Types].xml
├── _rels/
│   └── .rels
└── xl/
    ├── workbook.xml
    ├── worksheets/
    │   └── sheet1.xml
    └── ...
```

## 注意事项

- 输出目录不存在时会自动创建
- 解压后的XML文件可以直接编辑，之后可使用xlsx_pack重新打包