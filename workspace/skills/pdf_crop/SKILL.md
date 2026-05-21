---
name: pdf_crop
description: 裁剪PDF页面边距。通过指定边界坐标(left,bottom,right,top)来裁剪页面区域。当用户需要裁剪PDF页面时使用此skill。
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

  - name: bbox
    type: string
    required: true
    description: 裁剪边界"left,bottom,right,top"（PDF坐标单位）

  - name: pages
    type: string
    required: false
    description: 页码范围，如"1-3,5"（可选，默认全部页面）

output_params:
  - name: output
    type: pdf_file
    description: 裁剪后的PDF文件
tag: 输入
---

# pdf_crop 技能

## 功能说明

该技能用于裁剪PDF页面边距，通过指定边界坐标（left, bottom, right, top）来精确裁剪页面区域，适用于去除PDF边距、提取特定区域等场景。

## 核心功能

- 支持精确的页面边界裁剪
- 可指定页码范围进行选择性裁剪
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_crop.py --input_path <输入PDF> --output_path <输出PDF> --bbox <裁剪边界> [--pages <页码范围>]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_path | string | 是 | - | 输入PDF文件路径 |
| output_path | string | 是 | - | 输出PDF文件路径 |
| bbox | string | 是 | - | 裁剪边界"left,bottom,right,top"（PDF坐标单位） |
| pages | string | 否 | 全部 | 页码范围，如"1-3,5" |

## 示例

### 示例1：裁剪全部页面

```bash
python scripts/run_pdf_crop.py --input_path input.pdf --output_path cropped.pdf --bbox "50,50,550,750"
```

### 示例2：裁剪指定页码

```bash
python scripts/run_pdf_crop.py --input_path input.pdf --output_path cropped.pdf --bbox "50,50,550,750" --pages "1-10"
```

## 注意事项

- 裁剪边界使用PDF坐标系统（原点在左下角）
- 单位为点（1英寸=72点）
- 裁剪边界值应在页面尺寸范围内
- 输出目录不存在时会自动创建
