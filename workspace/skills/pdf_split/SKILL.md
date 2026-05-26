---
name: pdf_split
description: 将PDF按指定页码范围拆分为独立的PDF文件。当用户需要拆分PDF文档时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

name_zh: 将PDF按指定页码范围拆分为独立的PDF文件算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入PDF文件路径

  - name: output_path
    type: string
    required: true
    description: 输出PDF文件路径（多页时自动添加_pageN后缀）

  - name: pages
    type: string
    required: false
    description: 页码范围，如"1-3,5"（可选，默认全部页拆为单页）

output_params:
  - name: output_path
    type: pdf_file
    description: 拆分后的PDF文件
tag: 输入

---

# pdf_split 技能

## 功能说明

该技能将PDF按指定页码范围拆分为独立的PDF文件，适用于需要提取特定页面或拆分大型PDF的场景。

## 核心功能

- 支持按页码范围拆分
- 单页提取输出单个文件
- 多页拆分自动添加页码后缀
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_split.py --input_path <输入PDF> --output_path <输出PDF> [--pages <页码范围>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出PDF文件路径（多页时自动添加_pageN后缀） |
| pages | string | 否 | 全部 | 页码范围，如"1-3,5"（默认全部页拆为单页） |

## 示例

### 示例1：拆分全部页面为单页

```bash
python scripts/run_pdf_split.py --input_path input.pdf --output_path split/page
```

### 示例2：提取单页

```bash
python scripts/run_pdf_split.py --input_path input.pdf --output_path page5.pdf --pages "5"
```

### 示例3：提取指定页码范围

```bash
python scripts/run_pdf_split.py --input_path input.pdf --output_path split/page --pages "1-3,5"
```

## 注意事项

- 不指定pages参数时，将所有页面拆分为单独的PDF文件
- 单页提取时输出文件名为指定路径
- 多页拆分时自动添加_pageN后缀（N为页码）
- 输出目录不存在时会自动创建
