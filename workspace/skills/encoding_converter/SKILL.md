---
name: encoding_converter
description: '多编码文本统一转换工具。读取文本文件或目录，自动识别源编码并转换为目标编码（默认 UTF-8），输出转换后的文件。

  当用户提到编码转换、乱码修复、GBK 转 UTF-8、统一文件编码等需求时使用此 skill。

  即使用户没有明确说出“编码转换”，只要任务涉及把文本文件转成指定编码，就应该使用此 skill。

  不负责非文本二进制文件处理、内容清洗或格式转换。

  '
name_zh: 多编码文本统一转换算子
input_params:
- name: input
  type: string
  required: true
  description: 输入文件或目录路径
- name: output
  type: string
  required: true
  description: 输出文件或目录路径
- name: target_encoding
  type: string
  required: false
  default: utf-8
  description: 目标编码（utf-8/gbk/gb2312/gb18030/latin-1 等）
- name: source_encoding
  type: string
  required: false
  default: auto
  description: 源编码（auto=自动检测，或指定具体编码）
- name: recursive
  type: string
  required: false
  default: "False"
  description: 是否递归处理子目录
- name: file_extensions
  type: string
  required: false
  default: .txt,.md,.csv,.json,.jsonl
  description: 要处理的文件扩展名，逗号分隔
- name: error_handling
  type: string
  required: false
  default: replace
  description: 编码错误处理方式（strict=严格报错, replace=替换为?, ignore=忽略）
- name: add_bom
  type: string
  required: false
  default: "False"
  description: 是否添加 UTF-8 BOM 头
output_params:
- name: output
  type: string
  description: 输出文件或目录路径
- name: converted_count
  type: integer
  description: 成功转换的文件数量
- name: failed_count
  type: integer
  description: 转换失败的文件数量
tag: 格式转换
---

# Encoding Converter 多编码文本统一转换 Skill

## 功能概述

本 skill 用于自动检测文本文件编码并统一转换为目标编码。支持单文件和批量目录处理，适配多源异构科研语料的编码规整工作，解决乱码问题。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 编码转换/统一编码
- 乱码修复
- GBK 转 UTF-8
- 批量转换文件编码
- 文本编码规整

## 核心参数说明

### 必需参数
- `--input`：输入文件或目录路径
- `--output`：输出文件或目录路径

### 可选参数
- `--target_encoding`：目标编码，默认 utf-8
- `--source_encoding`：源编码，默认 auto 自动检测
- `--recursive`：是否递归处理子目录
- `--file_extensions`：要处理的文件扩展名
- `--error_handling`：编码错误处理方式
- `--add_bom`：是否添加 UTF-8 BOM

## 输入文件格式

支持文本文件或目录输入。目录模式下仅处理扩展名匹配的文本文件，不处理二进制文件。

## 使用方法

```bash
python scripts/run_encoding_converter.py \
  --input <input_path> \
  --output <output_path> \
  --recursive true
```

```bash
python scripts/run_encoding_converter.py \
  --input <input_path> \
  --output <output_path> \
  --source_encoding gbk \
  --target_encoding utf-8
```

## 输出示例

```
[OK] Batch encoding conversion completed!
   Input directory: <input_path>
   Output directory: <output_path>
   Target encoding: utf-8
   Files processed: 50
   Successfully converted: 48
   Failed: 2
```

## 环境要求

- Python 3.8+
- 可选依赖：chardet

## 注意事项

1. 自动检测可能不准确，建议对重要文件指定源编码。
2. 二进制文件会被跳过。
3. 转换后文件大小可能变化。
4. 使用 replace 模式时，无法识别的字符会被替换为 ?。
5. 原文件不会被修改，总是输出到新位置。

## 运行示例

```powershell
# 进入仓库根目录，保证相对路径可用
$env:PYTHONIOENCODING='utf-8'

# 运行编码转换，把输入目录里的文本统一转成 UTF-8
.venv\Scripts\python.exe workspace/skills/encoding_converter/scripts/run_encoding_converter.py --input <input_path> --output <output_path> --recursive true
```
