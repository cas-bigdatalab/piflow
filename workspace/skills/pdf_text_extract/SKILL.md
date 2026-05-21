---
name: pdf_text_extract
description: 从PDF文件中提取文本内容，保存为txt文件。当用户需要从PDF中提取文字时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入PDF文件路径

  - name: output_path
    type: string
    required: true
    description: 输出txt文件路径

  - name: pages
    type: string
    required: false
    description: 页码范围，如"1-3,5"（可选，默认全部页面）

output_params:
  - name: output
    type: text_file
    description: 提取的文本文件(.txt)
tag: 输入
---

# pdf_text_extract 技能

## 功能说明

该技能从PDF文件中提取文本内容，保存为txt文件，适用于需要从PDF中提取可编辑文本的场景。

## 核心功能

- 提取PDF中的文本内容
- 支持指定页码范围提取
- 按页码分隔输出
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_text_extract.py --input_path <输入PDF> --output_path <输出TXT> [--pages <页码范围>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出txt文件路径 |
| pages | string | 否 | 全部 | 页码范围，如"1-3,5" |

## 示例

### 示例1：提取全部页面文本

```bash
python scripts/run_pdf_text_extract.py --input_path document.pdf --output_path text.txt
```

### 示例2：提取指定页码文本

```bash
python scripts/run_pdf_text_extract.py --input_path document.pdf --output_path text.txt --pages "1-10"
```

## 输出格式

```
--- Page 1 ---
这是第一页的文本内容...

--- Page 2 ---
这是第二页的文本内容...
```

## 注意事项

- 扫描版PDF（图片格式）无法提取文本，需使用pdf_ocr技能
- 输出目录不存在时会自动创建
- 文本提取结果受PDF质量影响，部分PDF可能提取效果不佳
