---
name: pdf_rotate
description: 旋转PDF页面方向。支持顺时针90度、180度、270度旋转。当用户需要旋转PDF页面方向时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入PDF文件路径

  - name: output_path
    type: string
    required: true
    description: 输出PDF文件路径

  - name: angle
    type: int
    required: false
    default: 90
    description: 旋转角度（90/180/270，顺时针）

  - name: pages
    type: string
    required: false
    description: 页码范围，如"1-3,5"（可选，默认全部页面）

output_params:
  - name: output
    type: pdf_file
    description: 旋转后的PDF文件
tag: 输入
---

# pdf_rotate 技能

## 功能说明

该技能旋转PDF页面方向，支持顺时针90度、180度、270度旋转，适用于调整PDF页面方向的场景。

## 核心功能

- 支持90/180/270度顺时针旋转
- 可指定页码范围进行选择性旋转
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_rotate.py --input_path <输入PDF> --output_path <输出PDF> [--angle <角度>] [--pages <页码范围>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出PDF文件路径 |
| angle | int | 否 | 90 | 旋转角度（90/180/270） |
| pages | string | 否 | 全部 | 页码范围，如"1-3,5" |

## 示例

### 示例1：旋转全部页面90度

```bash
python scripts/run_pdf_rotate.py --input_path input.pdf --output_path rotated.pdf --angle 90
```

### 示例2：旋转指定页码180度

```bash
python scripts/run_pdf_rotate.py --input_path input.pdf --output_path rotated.pdf --angle 180 --pages "2-5"
```

### 示例3：旋转全部页面270度

```bash
python scripts/run_pdf_rotate.py --input_path input.pdf --output_path rotated.pdf --angle 270
```

## 注意事项

- 仅支持90、180、270度旋转
- 不指定pages参数时旋转全部页面
- 输出目录不存在时会自动创建
