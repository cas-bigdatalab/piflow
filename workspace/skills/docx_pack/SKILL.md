---
name: docx_pack
description: 将解压的XML目录重新打包为DOCX文件
version: 1.0.0
category: document_processing
name_zh: 将解压的XML目录重新打包为DOCX文件算子
input_params:
  - name: input_dir
    type: directory
    description: 解压的XML目录路径
  - name: output_path
    type: docx_file
    description: 输出DOCX文件路径
  - name: original
    type: docx_file
    description: 原始DOCX文件路径（可选）
  - name: validate
    type: boolean
    description: 是否启用自动修复
    default: true
output_params:
  - name: output_path
    type: docx_file
    description: 打包后的DOCX文件
tag: 输入

---

# docx_pack 技能

## 功能说明

该技能将解压的XML目录重新打包为DOCX文件，与docx_unpack技能配合使用，实现DOCX文件的编辑和重建。

## 核心功能

- 将XML目录打包为标准DOCX文件
- 自动修复常见问题（durableId溢出、空格保留等）
- 自动创建输出目录
- 支持UTF-8编码

## 使用方法

```bash
python scripts/run_docx_pack.py --input_dir <XML目录> --output_path <输出DOCX> [--validate]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_dir | string | 是 | - | 解压的XML目录路径 |
| output_path | string | 是 | - | 输出DOCX文件路径 |
| original | string | 否 | - | 原始DOCX文件路径（用于参考） |
| validate | bool | 否 | true | 是否启用自动修复 |

## 示例

```bash
python scripts/run_docx_pack.py --input_dir ./unpacked/ --output_path modified.docx
```

## 自动修复功能

当启用validate时，会自动修复以下问题：
- durableId值超过0x7FFFFFFF的问题
- w:t元素前后空格丢失问题（添加xml:space="preserve"）

## 注意事项

- 输入目录必须包含有效的DOCX XML结构
- 输出目录不存在时会自动创建
- 打包后的DOCX文件应能被Word等软件正常打开