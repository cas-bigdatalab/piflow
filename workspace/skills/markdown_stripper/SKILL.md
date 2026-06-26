---
name: markdown_stripper
description: |
  Markdown标记清除工具。读取Markdown文件，去除Markdown语法标记（标题#、加粗**、斜体*、链接[]()、代码块```、引用>、列表标记等），输出纯文本文件。
  当用户提到Markdown清洗、去除MD标记、MD转纯文本等需求时使用此skill。
  适用于Markdown文件的语法净化，不负责CSV/表格数据的结构清洗。

name_zh: Markdown标记清除算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入文件路径（支持.md、.txt等文本文件）
  - name: output_path
    type: string
    required: true
    description: 输出文件路径（纯文本）
  - name: no_code_blocks
    type: string
    required: false
    description: 是否删除代码块内容（默认保留）
  - name: no_images
    type: string
    required: false
    description: 是否删除图片alt文本（默认保留）
  - name: no_tables
    type: string
    required: false
    description: 是否删除表格（默认转为纯文本）
output_params:
  - name: output_path
    type: file
    description: 去除Markdown标记后的纯文本文件
tag: 清洗
---

# markdown_stripper Markdown标记清除Skill

## 功能概述

读取 Markdown / 纯文本 文件，去除所有 Markdown 语法标记，输出纯文本。

去除的 12 类标记：(1) 标题 `#`；(2) 加粗 `**`；(3) 斜体 `*`；(4) 删除线 `~~`；(5) 链接 `[]()`；(6) 图片 `![]()`；(7) 行内代码 `` ` ``；(8) 围栏代码块 ` ``` ``` `；(9) 引用 `>`；(10) 列表 `-`/`1.`；(11) 水平线 `---`；(12) 表格 `|...|`。

## 触发条件

- Markdown 清洗
- 去除 Markdown 标记
- MD 转纯文本
- 语料净化

## 输入文件格式

支持以下纯文本格式：
- Markdown (.md)
- 纯文本 (.txt)

不支持 .csv / .tsv / .jsonl 等结构化数据文件。会将不支持的扩展名直接拒绝。

## 使用方法

```bash
python scripts/markdown_stripper.py \
    --input_path input.md \
    --output_path output.txt
```

## 核心参数说明

### 必需参数

| 参数 | 说明 |
|------|------|
| `--input_path` | 输入 Markdown 文件路径 |
| `--output_path` | 输出纯文本文件路径 |

### 可选参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `--no_code_blocks` | 删除代码块内容 | 保留 |
| `--no_images` | 删除图片 alt 文本 | 保留 |
| `--no_tables` | 删除表格内容 | 转为纯文本 |

## 输出示例

```
[OK] Markdown标记清除完成 -> output.txt
   keep_code_blocks=True, keep_images=True, keep_tables=False
```

## 环境要求

使用项目 Python 环境运行，无额外依赖。

## 注意事项

1. 处理顺序：先保护代码块 → 处理行级标记 → 处理行内标记 → 恢复代码块
2. 代码块默认保留内容（仅去除围栏标记），用 `--no_code_blocks` 可完全删除
3. 表格默认转为空格连接的纯文本
4. 不支持 .csv / .tsv / .jsonl 等结构化数据文件，会将不支持的扩展名直接拒绝
