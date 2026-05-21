---
name: xlsx_pack
description: 将解压的XML目录重新打包为XLSX文件
version: 1.0.0
category: spreadsheet_processing
input_params:
  - name: input_dir
    type: directory
    description: 解压的XML目录路径
  - name: output_path
    type: xlsx_file
    description: 输出XLSX文件路径
output_params:
  - name: output
    type: xlsx_file
    description: 打包后的XLSX文件
tag: 输入
---

# xlsx_pack 技能

## 功能说明

该技能将解压的XML目录重新打包为XLSX文件，与xlsx_unpack技能配合使用，实现XLSX文件的编辑和重建。

## 核心功能

- 将XML目录打包为标准XLSX文件
- 自动创建输出目录
- 支持UTF-8编码

## 使用方法

```bash
python scripts/run_xlsx_pack.py --input_dir <XML目录> --output_path <输出XLSX>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_dir | string | 是 | - | 解压的XML目录路径 |
| output_path | string | 是 | - | 输出XLSX文件路径 |

## 示例

```bash
python scripts/run_xlsx_pack.py --input_dir ./unpacked/ --output_path modified.xlsx
```

## 注意事项

- 输入目录必须包含有效的XLSX XML结构
- 输出目录不存在时会自动创建
- 打包后的XLSX文件应能被Excel等软件正常打开