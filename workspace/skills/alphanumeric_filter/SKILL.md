---
name: alphanumeric_filter
description: |
  字母数字比例过滤器。过滤文本中字母/数字比例不在指定范围内的样本。
  当用户提到文本过滤、比例筛选、字母比例、数字比例、清理乱码文本等需求时使用此skill。
  即使用户没有明确说出"过滤"，只要任务涉及根据文本中字母或数字的比例来筛选数据，
  就应该使用此skill。

name_zh: 字母数字比例过滤器算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: min_ratio
    type: float
    required: false
    default: 0.25
    description: 最小字母数字比例

  - name: max_ratio
    type: float
    required: false
    default: 1.0
    description: 最大字母数字比例

  - name: tokenization
    type: bool
    required: false
    default: false
    description: 是否使用tokenization计算比例

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

output_params:
  - name: output
    type: json_file
    description: 过滤后的JSON文件，包含保留的样本数据
tag: 过滤与筛选

---

# Alphanumeric Filter 字母数字比例过滤 Skill

## 功能概述

本skill根据文本中字母/数字字符的比例进行过滤，只保留比例在指定范围内的样本。
常用于清理乱码文本、过滤特殊字符过多的内容等场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 文本过滤
- 比例筛选
- 字母比例过滤
- 数字比例过滤
- 清理乱码文本
- 特殊字符过滤

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--min_ratio` | 最小字母数字比例 | `0.25` |
| `--max_ratio` | 最大字母数字比例 | `1.0` |
| `--tokenization` | 是否使用tokenization计算 | `False` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {"text": "正常的英文文本内容"},
  {"text": "包含123数字的文本"},
  {"text": "只有符号！！！..."},
  {"text": "混合内容abc123中文"}
]
```

## 使用方法

### 过滤字母数字比例在0.25-1.0之间的样本（默认）
```bash
python scripts/run_alphanumeric_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 过滤字母数字比例在0.3-0.8之间的样本
```bash
python scripts/run_alphanumeric_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_ratio 0.3 \
  --max_ratio 0.8
```

### 使用tokenization模式（更精确但更慢）
```bash
python scripts/run_alphanumeric_filter.py \
  --input ./input.json \
  --output ./output.json \
  --tokenization True
```

## 过滤示例

| 文本 | 字母数字比例 | 过滤结果 (0.2-0.9) |
|------|-------------|---------------------|
| `Hello World` | 高 | 保留 |
| `a=1\nb\nc=1+2+3` | 中 | 保留 |
| `，。、„""«»１»` | 低 | 过滤 |
| `emoji表情😊😸31231` | 中 | 保留 |

## 输出示例

**命令行输出：**
```
[OK] Alphanumeric filtering completed!
   Min ratio: 0.25
   Max ratio: 1.0
   Tokenization: False
   Original documents: 6
   Filtered documents: 5
   Removed documents: 1
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"text": "过滤后保留的文本1"},
  {"text": "过滤后保留的文本2"}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer：
```bash
pip install py-data-juicer
```

## 注意事项

1. **比例计算**：默认按字符计算，`tokenization=True` 时按token计算
2. **默认值**：`max_ratio` 默认无限制（保留所有高比例样本）
3. **过滤逻辑**：只保留比例在 [min_ratio, max_ratio] 范围内的样本
4. **适用场景**：清理乱码、过滤特殊字符过多的文本
