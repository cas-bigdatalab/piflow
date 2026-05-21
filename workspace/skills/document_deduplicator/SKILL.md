---
name: document_deduplicator
description: |
  文档去重工具。使用精确匹配（MD5哈希）在文档级别删除重复的样本。
  当用户提到文档去重、删除重复文档、样本去重、文本去重、去除重复内容、
  清洗重复数据、整理文档集合等需求时使用此skill。
  即使用户没有明确说出"去重"，只要任务涉及从多个文档中识别和删除重复内容，
  就应该使用此skill。

input_params:
  - name: input
    type: string
    required: true
    description: 输入文件路径（支持json, txt）

  - name: output
    type: string
    required: true
    description: 输出文件路径（支持json, txt）

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

  - name: lowercase
    type: bool
    required: false
    default: false
    description: 是否将文本转为小写进行比对

  - name: ignore_non_character
    type: bool
    required: false
    default: false
    description: 是否忽略非字母字符（空格、数字、标点）

output_params:
  - name: output
    type: json_file
    description: 去重后的文件（json或txt格式）
tag: 去重
---

# Document Deduplicator 文档去重 Skill

## 功能概述

本skill使用MD5哈希算法进行文档级别的精确匹配去重。
通过计算每个文档内容的哈希值，快速识别并删除完全相同或指定条件下相同的重复文档。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 文档去重
- 删除重复文档
- 样本去重
- 文本去重
- 去除重复内容
- 清洗重复数据
- 整理文档集合

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入文件路径 (支持 json, txt) |
| `--output` | 输出文件路径 (支持 json, txt) |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_key` | 文本字段的键名 | `text` |
| `--lowercase` | 是否将文本转为小写进行比对 | `False` |
| `--ignore_non_character` | 是否忽略非字母字符（空格、数字、标点） | `False` |

## 支持的文件格式

### JSON 格式
```json
{
  "data": [
    {"text": "文档内容1"},
    {"text": "文档内容2"},
    {"text": "文档内容1"}
  ]
}
```

### TXT 格式
```
文档内容1
文档内容2
文档内容1
```

## 使用方法

```bash
# JSON 去重
python scripts/run_document_deduplicator.py \
  --input ./input.json \
  --output ./output.json

# TXT 去重
python scripts/run_document_deduplicator.py \
  --input ./documents.txt \
  --output ./deduplicated.txt

# 忽略大小写去重
python scripts/run_document_deduplicator.py \
  --input ./input.json \
  --output ./output.json \
  --lowercase True
```

## 输出示例

**命令行输出：**
```
[OK] Document deduplication completed!
   Original documents: 5
   Deduplicated documents: 4
   Removed duplicates: 1
   Input file: ./input.json
   Output file: ./output.json
```

## 去重模式说明

| 模式 | 参数组合 | 说明 |
|------|----------|------|
| 精确匹配 | `lowercase=False`<br>`ignore_non_character=False` | 完全相同的文本才会被去重 |
| 忽略大小写 | `lowercase=True`<br>`ignore_non_character=False` | "Hello" 和 "hello" 会被视为重复 |
| 忽略格式 | `lowercase=False`<br>`ignore_non_character=True` | 去除空格、数字、标点后比对 |
| 综合 | `lowercase=True`<br>`ignore_non_character=True` | 转小写且去除非字母字符后比对 |

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer，可用以下指令进行安装：
```bash
pip install py-data-juicer
```

## 注意事项

1. **文件格式**：输入输出自动根据文件扩展名判断格式（json 或 txt）
2. **默认字段**：默认使用 `text` 字段作为文本内容，可通过 `--text_key` 修改
3. **处理逻辑**：保留首次出现的文档，删除后续重复项
4. **编码检测**：自动检测文件编码（utf-8, gbk, gb2312, gb18030等）
