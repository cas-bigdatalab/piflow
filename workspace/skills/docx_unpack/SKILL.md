---
name: docx_unpack
description: 将DOCX文件解压为XML目录
version: 1.0.0
category: document_processing
input_params:
  - name: input_path
    type: docx_file
    description: 输入DOCX文件路径
  - name: output_dir
    type: directory
    description: 输出目录路径
  - name: merge_runs
    type: boolean
    description: 是否合并相邻的文本运行
    default: true
output_params:
  - name: output
    type: directory
    description: 解压后的XML目录
tag: 输入
---

# docx_unpack 技能

## 功能说明

该技能将DOCX文件解压为XML目录结构，方便查看和编辑DOCX内部的XML文件。DOCX本质上是一个ZIP压缩包，包含多个XML文件和资源文件。

## 核心功能

- 将DOCX文件解压为可读的XML目录
- 支持合并相邻相同格式的文本运行（优化XML结构）
- 自动处理智能引号等特殊字符
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_docx_unpack.py --input_path <输入DOCX> --output_dir <输出目录> [--merge_runs]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入DOCX文件路径 |
| output_dir | string | 是 | - | 输出目录路径 |
| merge_runs | bool | 否 | true | 是否合并相邻的文本运行 |

## 示例

```bash
python scripts/run_docx_unpack.py --input_path document.docx --output_dir ./unpacked/
```

## 输出结构

解压后的目录结构：
```
output_dir/
├── [Content_Types].xml
├── _rels/
│   └── .rels
└── word/
    ├── document.xml
    ├── styles.xml
    ├── settings.xml
    └── ...
```

## 注意事项

- 输出目录不存在时会自动创建
- 合并运行功能可以减少XML文件中的冗余标签
- 解压后的XML文件可以直接编辑，之后可使用docx_pack重新打包