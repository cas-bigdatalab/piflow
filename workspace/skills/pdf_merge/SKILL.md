---
name: pdf_merge
description: 将多个PDF文件合并为一个PDF文件。当用户需要合并PDF文档时使用此skill。
license: Proprietary. LICENSE.txt has complete terms

input_params:
  - name: input_paths
    type: list
    required: true
    description: 输入PDF文件路径列表（多个以空格分隔）

  - name: output_path
    type: string
    required: true
    description: 输出PDF文件路径

output_params:
  - name: output
    type: pdf_file
    description: 合并后的PDF文件
tag: 输入
---

# pdf_merge 技能

## 功能说明

该技能将多个PDF文件合并为一个PDF文件，适用于需要将多个文档合并成完整报告的场景。

## 核心功能

- 支持合并多个PDF文件
- 按输入顺序合并页面
- 自动跳过不存在的文件
- 自动创建输出目录

## 使用方法

```bash
python scripts/run_pdf_merge.py --input_paths <文件1> <文件2> ... --output_path <输出PDF>
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| input_paths | list | 是 | - | 输入PDF文件路径列表（多个以空格分隔） |
| output_path | string | 是 | - | 输出PDF文件路径 |

## 示例

### 示例1：合并两个PDF

```bash
python scripts/run_pdf_merge.py --input_paths file1.pdf file2.pdf --output_path merged.pdf
```

### 示例2：合并多个PDF

```bash
python scripts/run_pdf_merge.py --input_paths report1.pdf report2.pdf appendix.pdf --output_path complete_report.pdf
```

## 注意事项

- 输入文件按顺序合并
- 不存在的文件会被跳过并显示警告
- 输出目录不存在时会自动创建
